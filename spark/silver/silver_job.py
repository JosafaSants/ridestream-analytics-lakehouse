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

    # Ativa o suporte a tabelas Delta Lake no Spark e injeta os pacotes Kafka juntos
    # extra_packages evita conflito de versão: o Delta resolve todas as dependências
    # Maven em uma única passagem, sem sobrescrever o spark.jars.packages internamente
    # - spark-sql-kafka: integração do DataFrame/Dataset API com o Kafka
    # - spark-streaming-kafka: camada de baixo nível que o SQL depende para consumir offsets
    builder = configure_spark_with_delta_pip(
        builder,
        extra_packages=[
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1",
            "org.apache.spark:spark-streaming-kafka-0-10_2.12:3.5.1",
        ],
    )

    # Habilita o catálogo de sessão estendido do Delta Lake
    # sem isso o Spark não reconhece comandos como DESCRIBE HISTORY
    builder = builder.config(
        "spark.sql.extensions",
        "io.delta.sql.DeltaSparkSessionExtension",
    )

    # Define o catálogo padrão do Spark como o catálogo Delta
    # permite usar sintaxe SQL padrão com tabelas Delta
    builder = builder.config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    )

    return builder.getOrCreate()


def ler_bronze(spark: SparkSession):
    # Lemos a Bronze como uma fonte de streaming Delta, não como um batch.
    # O Spark rastreia automaticamente quais arquivos Parquet já foram processados
    # usando o diretório de checkpoint da Silver — a cada micro-batch, ele só lê
    # os arquivos novos que o job Bronze gravou desde a última execução.
    # É como um "cursor" que avança conforme a Bronze cresce.
    #
    # ignoreChanges=True: a Bronze usa .partitionBy(), o que pode causar
    # reescrita de arquivos existentes durante compactações ou reprocessamentos.
    # Sem essa opção, o Spark jogaria um erro ao detectar um arquivo já visto
    # sendo modificado. Com ela, simplesmente ignoramos essas mudanças.
    return (
        spark.readStream
        .format("delta")
        .option("ignoreChanges", True)
        .load("data/bronze/ride_events")
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
        df_dedup
        .withColumn("year", year(col("timestamp")).cast(IntegerType()))
        .withColumn("month", month(col("timestamp")).cast(IntegerType()))
        .withColumn("day", dayofmonth(col("timestamp")).cast(IntegerType()))
    )

    return df_silver


def escrever_silver(df):
    # Modo "append": cada micro-batch apenas adiciona novos registros ao Delta Lake.
    # Nunca sobrescrevemos dados já gravados — isso é fundamental em pipelines de dados
    # porque permite auditoria, time travel e reprocessamento sem perda de histórico.
    # O modo "complete" reescreveria a tabela inteira a cada micro-batch, o que seria
    # inviável em produção: imagine reescrever meses de corridas a cada 10 segundos.
    #
    # Exactly-once semantics (exatamente uma vez):
    # O checkpoint registra dois estados essenciais:
    #   1. Quais offsets da fonte (Bronze Delta) já foram lidos
    #   2. Quais micro-batches já foram confirmados como gravados
    # Se o job cair no meio de um micro-batch, ao reiniciar o Spark verifica o checkpoint:
    # se o batch foi lido mas não confirmado, ele reprocessa; se já foi confirmado,
    # pula. Combinado com as garantias ACID do Delta Lake, isso garante que nenhuma
    # corrida seja gravada duas vezes nem perdida — mesmo em caso de falha.
    return (
        df.writeStream
        .format("delta")
        .outputMode("append")
        .partitionBy("year", "month", "day")
        .option("checkpointLocation", "data/checkpoints/silver")
        .start("data/silver/ride_events")
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
