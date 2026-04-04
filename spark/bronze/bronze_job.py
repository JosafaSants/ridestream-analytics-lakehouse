import os

# Importações do PySpark para processamento distribuído
from pyspark.sql import DataFrame, SparkSession

# Funções de coluna do PySpark: col, cast, year, month, day
from pyspark.sql import functions as F

# Importações do Delta Lake para armazenamento no formato Delta
from delta import configure_spark_with_delta_pip

# No Windows, o Spark depende do Hadoop para acessar o sistema de arquivos local.
# Sem o HADOOP_HOME apontando para uma instalação mínima (winutils.exe),
# o job falha ao tentar criar diretórios de output ou checkpoint.
# Definir aqui garante que qualquer desenvolvedor Windows rode o job
# sem precisar configurar variáveis de ambiente manualmente na máquina.
os.environ["HADOOP_HOME"] = "C:\\hadoop"
os.environ["PATH"] = "C:\\hadoop\\bin" + os.pathsep + os.environ.get("PATH", "")


def criar_spark_session() -> SparkSession:
    # Cria um builder com o nome da aplicação — aparece na Spark UI
    builder = SparkSession.builder.appName("ridestream-bronze")

    # Ativa o suporte a tabelas Delta Lake no Spark e injeta os pacotes Kafka juntos.
    # hadoop-aws é obrigatório para o prefixo s3a:// funcionar — sem ele o Spark
    # não sabe como se comunicar com o MinIO (ou S3 em produção).
    # aws-java-sdk-bundle é a dependência que o hadoop-aws precisa para autenticar.
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
    # Em produção na AWS, basta remover estas 4 linhas — o Spark usa
    # as credenciais IAM automaticamente via instance profile
    builder = builder.config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9100")
    builder = builder.config("spark.hadoop.fs.s3a.access.key", "ridestream")
    builder = builder.config("spark.hadoop.fs.s3a.secret.key", "ridestream123")
    # Desabilita verificação de região — necessário para MinIO local
    # Em produção com AWS, remover esta linha
    builder = builder.config("spark.hadoop.fs.s3a.path.style.access", "true")

    # AQE: Adaptive Query Execution — otimiza o plano de execução em tempo real
    # reduz shuffles desnecessários e lida melhor com dados desbalanceados
    builder = builder.config("spark.sql.adaptive.enabled", "true")
    builder = builder.config("spark.sql.adaptive.coalescePartitions.enabled", "true")

    return builder.getOrCreate()


def ler_kafka(spark: SparkSession):
    # Endereço do broker Kafka — porta 29092 é a porta interna do Docker
    # usada quando o Spark roda dentro da mesma rede que o container Kafka
    kafka_bootstrap = "localhost:9092"

    # Nome do tópico que o producer escreve os eventos de corrida
    topico = "ride-events"

    return (
        spark.readStream
        # Define o formato da fonte como Kafka (requer o conector kafka JAR)
        .format("kafka")
        # Endereço do broker — pode ser uma lista separada por vírgula em produção
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        # Tópico a ser consumido
        .option("subscribe", topico)
        # Começa a leitura desde a mensagem mais antiga disponível no tópico
        # útil para reprocessamento; em produção pode ser "latest"
        .option("startingOffsets", "earliest")
        # Evita que o job quebre caso uma partição ou offset seja perdido no Kafka
        # seguro para desenvolvimento; em produção avalie com cuidado
        .option("failOnDataLoss", "false")
        .load()
    )


def transformar_bronze(df_raw: DataFrame) -> DataFrame:
    return (
        df_raw
        # Converte a coluna "value" de bytes para string UTF-8
        # o Kafka trafega tudo como bytes; precisamos do texto para parsear o JSON depois
        .withColumn("payload", F.col("value").cast("string"))
        # Mantém o timestamp original do Kafka — registra quando a mensagem chegou ao broker
        # útil para auditoria e detecção de atraso (lag) no pipeline
        .withColumn("timestamp", F.col("timestamp"))
        # Extrai o ano do timestamp — usado para particionar os dados no storage
        # particionar por data reduz o custo de leitura no S3/Delta (query pushdown)
        .withColumn("year", F.year(F.col("timestamp")))
        # Extrai o mês do timestamp
        .withColumn("month", F.month(F.col("timestamp")))
        # Extrai o dia do timestamp
        .withColumn("day", F.dayofmonth(F.col("timestamp")))
        # Remove apenas as colunas que não agregam valor na Bronze:
        # - "key": não usamos chave de particionamento Kafka neste producer
        # - "value": já foi convertido para "payload" acima
        # - "headers": metadados opcionais do Kafka, não populados pelo nosso producer
        # topic, partition e offset são MANTIDOS intencionalmente — permitem rastrear
        # exatamente de qual partição e posição no Kafka cada evento veio,
        # o que é essencial para auditoria, reprocessamento e depuração de falhas
        .drop("key", "value", "headers")
    )


def escrever_bronze(
    df_bronze: DataFrame,
    caminho_saida: str,
    caminho_checkpoint: str,
):
    return (
        df_bronze.writeStream
        # Formato Delta Lake — suporta ACID, versionamento e time travel
        .format("delta")
        # Modo append: cada micro-batch só adiciona novos registros, nunca sobrescreve
        # é o único modo seguro para dados de streaming em Delta
        .outputMode("append")
        # Particiona os arquivos físicos por data no storage
        # estrutura resultante: data/bronze/ride_events/year=2026/month=03/day=26/
        # no S3, isso reduz drasticamente o volume de dados lidos por queries filtradas
        .partitionBy("year", "month", "day")
        # Diretório de checkpoint: Spark salva aqui o progresso do stream (offsets já processados)
        # se o job reiniciar, ele retoma deste ponto sem reprocessar mensagens antigas
        .option("checkpointLocation", caminho_checkpoint)
        # Caminho de destino onde os arquivos Delta serão gravados
        .start(caminho_saida)
    )


if __name__ == "__main__":
    # Caminhos no MinIO usando protocolo s3a — compatível com AWS S3 em produção.
    # Em produção, basta trocar "localhost:9100" pelo endpoint S3 real no .env
    CAMINHO_SAIDA = "s3a://ridestream/bronze/ride_events"
    CAMINHO_CHECKPOINT = "s3a://ridestream/checkpoints/bronze"

    spark = criar_spark_session()
    df_raw = ler_kafka(spark)
    df_bronze = transformar_bronze(df_raw)
    query = escrever_bronze(df_bronze, CAMINHO_SAIDA, CAMINHO_CHECKPOINT)
    query.awaitTermination()
