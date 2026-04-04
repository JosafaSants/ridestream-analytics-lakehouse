import os

# No Windows, o Spark depende do Hadoop para acessar o sistema de arquivos local.
# Sem o HADOOP_HOME apontando para uma instalação mínima (winutils.exe),
# o job falha ao tentar criar diretórios de output ou checkpoint.
# Definir aqui garante que qualquer desenvolvedor Windows rode o job
# sem precisar configurar variáveis de ambiente manualmente na máquina.
os.environ["HADOOP_HOME"] = "C:\\hadoop"
os.environ["PATH"] = "C:\\hadoop\\bin" + os.pathsep + os.environ.get("PATH", "")

# Importações do PySpark para processamento distribuído
from pyspark.sql import SparkSession

# Funções de coluna necessárias para parsear JSON e extrair campos
from pyspark.sql.functions import col, dayofmonth, from_json, month, year

# Tipos usados para definir o schema do JSON dos eventos de corrida
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

# Integração Delta Lake com o Spark — injeta extensões e pacotes Maven necessários
from delta import configure_spark_with_delta_pip


def definir_schema_payload() -> StructType:
    # Este schema espelha exatamente o JSON que o producer envia para o Kafka.
    # Definir o schema explicitamente é mais eficiente do que inferir via inferSchema:
    # evita um segundo scan dos dados e garante tipos corretos desde a leitura.
    # O campo "rating" é o único nullable porque só corridas com status "completed"
    # recebem avaliação do passageiro — nas demais, o producer envia null.
    return StructType(
        [
            StructField("ride_id", StringType(), nullable=False),
            StructField("status", StringType(), nullable=False),
            StructField("timestamp", TimestampType(), nullable=False),
            StructField("driver_id", StringType(), nullable=False),
            StructField("passenger_id", StringType(), nullable=False),
            StructField("origin_lat", DoubleType(), nullable=False),
            StructField("origin_lon", DoubleType(), nullable=False),
            StructField("dest_lat", DoubleType(), nullable=False),
            StructField("dest_lon", DoubleType(), nullable=False),
            StructField("fare", DoubleType(), nullable=False),
            # Nullable: só preenchido quando o passageiro avalia a corrida concluída
            StructField("rating", DoubleType(), nullable=True),
        ]
    )


def criar_spark_session() -> SparkSession:
    # Cria um builder com o nome da aplicação — aparece na Spark UI
    builder = SparkSession.builder.appName("RideStream-Silver")

    # hadoop-aws e aws-java-sdk-bundle são necessários para o prefixo s3a://
    # funcionar tanto com MinIO local quanto com AWS S3 em produção
    builder = configure_spark_with_delta_pip(
        builder,
        extra_packages=[
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1",
            "org.apache.spark:spark-streaming-kafka-0-10_2.12:3.5.1",
            "org.apache.hadoop:hadoop-aws:3.3.4",
            "com.amazonaws:aws-java-sdk-bundle:1.12.262",
        ],
    )

    # Extensões Delta Lake
    builder = builder.config(
        "spark.sql.extensions",
        "io.delta.sql.DeltaSparkSessionExtension",
    )

    # Catálogo Delta como padrão
    builder = builder.config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    )

    # --- Configurações do MinIO (equivalente ao S3 em produção) ---
    # Em produção na AWS, remover estas 4 linhas — credenciais via IAM role
    builder = builder.config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9100")
    builder = builder.config("spark.hadoop.fs.s3a.access.key", "ridestream")
    builder = builder.config("spark.hadoop.fs.s3a.secret.key", "ridestream123")
    # Path style necessário para MinIO — em AWS S3 remover esta linha
    builder = builder.config("spark.hadoop.fs.s3a.path.style.access", "true")

    # AQE: otimiza o plano de execução em tempo real
    builder = builder.config("spark.sql.adaptive.enabled", "true")
    builder = builder.config("spark.sql.adaptive.coalescePartitions.enabled", "true")

    return builder.getOrCreate()


def ler_bronze(spark: SparkSession):
    # Lemos a Bronze do MinIO via protocolo s3a — mesmo comportamento
    # de antes, só o caminho mudou de data/bronze/ para s3a://ridestream/bronze/
    # ignoreChanges=True: evita erros quando a Bronze reescreve arquivos
    # durante compactações ou reprocessamentos
    return (
        spark.readStream.format("delta")
        .option("ignoreChanges", True)
        .load("s3a://ridestream/bronze/ride_events")
    )


def transformar_silver(df, schema: StructType):
    # --- Etapa 1: parsear o JSON da coluna "payload" ---
    # Na Bronze, cada evento de corrida chegou do Kafka como texto puro (string JSON).
    # O from_json interpreta essa string usando o schema que definimos e cria uma
    # coluna estruturada chamada "dados" — como abrir uma caixa e organizar o conteúdo.
    df_parsed = df.withColumn("dados", from_json(col("payload"), schema))

    # --- Etapa 2: achatar a struct em colunas individuais ---
    # Após o from_json, "dados" é uma coluna do tipo StructType (objeto aninhado).
    # Selecionamos cada campo individualmente para ter um DataFrame plano,
    # mais fácil de consultar com SQL e de gravar no Delta Lake.
    df_flat = df_parsed.select(
        col("dados.ride_id"),
        col("dados.status"),
        col("dados.timestamp"),
        col("dados.driver_id"),
        col("dados.passenger_id"),
        col("dados.origin_lat"),
        col("dados.origin_lon"),
        col("dados.dest_lat"),
        col("dados.dest_lon"),
        col("dados.fare"),
        col("dados.rating"),  # nullable: None quando a corrida não foi concluída
    )

    # --- Etapa 3: filtrar registros inválidos ---
    # Se o JSON chegou corrompido ou incompleto, o from_json retorna null nos campos
    # obrigatórios. Removemos esses registros antes de gravar na Silver para garantir
    # que apenas eventos íntegros avancem no pipeline — é a "portaria" da camada.
    df_valido = df_flat.filter(
        col("ride_id").isNotNull()
        & col("status").isNotNull()
        & col("timestamp").isNotNull()
    )

    # --- Etapa 4: remover duplicatas ---
    # O Kafka garante entrega "at least once": o mesmo evento pode chegar mais de uma vez
    # em caso de retentativas do producer ou rebalanceamento de partições.
    # Deduplica pela combinação ride_id + timestamp — um mesmo evento de corrida
    # não pode ter dois timestamps idênticos; se tiver, é duplicata.
    df_dedup = df_valido.dropDuplicates(["ride_id", "timestamp"])

    # --- Etapa 5: adicionar colunas de partição ---
    # Extraímos year/month/day do timestamp do evento (não do Kafka) para particionamento.
    # Usar o timestamp do evento garante que corridas do mesmo dia fiquem na mesma
    # partição mesmo que cheguem com atraso — importante para consultas por data.
    df_silver = (
        df_dedup.withColumn("year", year(col("timestamp")).cast(IntegerType()))
        .withColumn("month", month(col("timestamp")).cast(IntegerType()))
        .withColumn("day", dayofmonth(col("timestamp")).cast(IntegerType()))
    )

    return df_silver


def escrever_silver(df):
    # Grava no MinIO via s3a — mesma semântica de antes:
    # append + checkpoint garantem exactly-once e retomada sem perda de dados
    return (
        df.writeStream.format("delta")
        .outputMode("append")
        .partitionBy("year", "month", "day")
        .option("checkpointLocation", "s3a://ridestream/checkpoints/silver")
        .start("s3a://ridestream/silver/ride_events")
    )


if __name__ == "__main__":
    # Inicializa o Spark com suporte a Delta Lake e os pacotes Kafka necessários
    spark = criar_spark_session()

    # Carrega o schema dos eventos de corrida — usado para parsear o JSON da Bronze
    schema = definir_schema_payload()

    # Abre o stream de leitura apontando para a tabela Delta da camada Bronze
    df_bronze = ler_bronze(spark)

    # Parseia o JSON, filtra inválidos, remove duplicatas e adiciona colunas de partição
    df_silver = transformar_silver(df_bronze, schema)

    # Inicia a escrita contínua no Delta Lake da Silver e obtém o handle da query
    query = escrever_silver(df_silver)

    # Mantém o job rodando indefinidamente até ser interrompido manualmente.
    # Sem isso o processo encerraria imediatamente após iniciar o stream,
    # sem processar nenhum dado — o awaitTermination "segura" o processo vivo.
    query.awaitTermination()
