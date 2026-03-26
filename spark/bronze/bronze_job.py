# Importações do PySpark para processamento distribuído
from pyspark.sql import DataFrame, SparkSession

# Funções de coluna do PySpark: col, cast, year, month, day
from pyspark.sql import functions as F

# Importações do Delta Lake para armazenamento no formato Delta
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable


def criar_spark_session() -> SparkSession:
    # Cria um builder com o nome da aplicação — aparece na Spark UI
    builder = SparkSession.builder.appName("ridestream-bronze")

    # Adiciona o conector Kafka para Spark 3.5.1 (structured streaming)
    builder = builder.config(
        "spark.jars.packages",
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1",
    )

    # Ativa o suporte a tabelas Delta Lake no Spark
    # (registra o formato "delta" e as extensões SQL necessárias)
    builder = configure_spark_with_delta_pip(builder)

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


def ler_kafka(spark: SparkSession):
    # Endereço do broker Kafka — porta 29092 é a porta interna do Docker
    # usada quando o Spark roda dentro da mesma rede que o container Kafka
    kafka_bootstrap = "localhost:29092"

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
    # Caminhos de saída e checkpoint — relativos à raiz do projeto
    # o diretório "data/" é ignorado pelo git (ver .gitignore)
    CAMINHO_SAIDA = "data/bronze/ride_events"
    CAMINHO_CHECKPOINT = "data/checkpoints/bronze"

    spark = criar_spark_session()

    # Inicia o stream de leitura do Kafka — ainda não processa nada,
    # apenas declara a fonte de dados
    df_raw = ler_kafka(spark)

    # Aplica as transformações mínimas da camada Bronze:
    # converte bytes em string, mantém o timestamp e adiciona colunas de partição
    df_bronze = transformar_bronze(df_raw)

    # Inicia a escrita contínua no Delta Lake e obtém o handle da query
    query = escrever_bronze(df_bronze, CAMINHO_SAIDA, CAMINHO_CHECKPOINT)

    # Mantém o job rodando indefinidamente até ser interrompido manualmente
    # sem isso, o processo terminaria imediatamente após iniciar o stream
    query.awaitTermination()
