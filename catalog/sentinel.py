import os

os.environ["HADOOP_HOME"] = "C:\\hadoop"
os.environ["PATH"] = "C:\\hadoop\\bin" + os.pathsep + os.environ.get("PATH", "")

import duckdb
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip


# ── Configuração ────────────────────────────────────────────────────────────


def carregar_config() -> OpenAI:
    """
    Carrega variáveis de ambiente e inicializa o cliente OpenAI.
    Retorna o cliente pronto para uso.
    """
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada no .env")

    print("✅ Configuração carregada com sucesso")
    return OpenAI(api_key=api_key)


# ── Leitura da camada Silver ─────────────────────────────────────────────────


def criar_spark_session() -> SparkSession:
    """
    Cria sessão Spark mínima para leitura da Silver.
    Sem Kafka — apenas Delta Lake para leitura estática.
    """
    builder = (
        SparkSession.builder.appName("RideStream-DataSentinel")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
    )

    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    # Reduz logs para não poluir a saída do sentinel
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def extrair_schema_silver(spark: SparkSession) -> dict:
    """
    Lê a tabela Silver em modo batch (não streaming) e extrai:
    - Nome e tipo de cada campo
    - Contagem total de registros
    - Percentual de nulos por campo
    - Valor mínimo e máximo para campos numéricos

    Retorna um dicionário com todas essas informações.
    """
    caminho_silver = "data/silver/ride_events"

    print(f"\n🔍 Lendo Silver em: {caminho_silver}")
    df = spark.read.format("delta").load(caminho_silver)

    total = df.count()
    print(f"   Total de registros: {total:,}")

    campos = []
    for field in df.schema.fields:
        nome = field.name
        tipo = str(field.dataType)

        # Calcula percentual de nulos para detectar problemas de qualidade
        nulos = df.filter(df[nome].isNull()).count()
        pct_nulos = round((nulos / total) * 100, 2) if total > 0 else 0

        info = {
            "nome": nome,
            "tipo": tipo,
            "nulos_pct": pct_nulos,
        }

        # Estatísticas numéricas ajudam o modelo a descrever o campo
        # com contexto real (ex: "valores entre R$4 e R$89")
        tipos_numericos = ("DoubleType", "FloatType", "IntegerType", "LongType")
        if any(t in tipo for t in tipos_numericos):
            stats = df.selectExpr(
                f"min({nome}) as minimo",
                f"max({nome}) as maximo",
                f"round(avg({nome}), 2) as media",
            ).collect()[0]
            info["minimo"] = stats["minimo"]
            info["maximo"] = stats["maximo"]
            info["media"] = stats["media"]

        campos.append(info)
        print(f"   campo: {nome} | tipo: {tipo} | nulos: {pct_nulos}%")

    return {
        "tabela": "silver_ride_events",
        "caminho": caminho_silver,
        "total_registros": total,
        "campos": campos,
    }


# ── Leitura da camada Gold ───────────────────────────────────────────────────


def extrair_schema_gold() -> dict:
    """
    Conecta ao DuckDB e extrai o schema de todas as tabelas Gold.
    Retorna lista de tabelas com seus campos e tipos.
    """
    caminho_duckdb = "data/gold/ridestream.duckdb"

    print(f"\n🔍 Lendo Gold em: {caminho_duckdb}")
    con = duckdb.connect(caminho_duckdb, read_only=True)

    # Lista todas as tabelas presentes no banco Gold
    tabelas = con.execute("SHOW TABLES").fetchall()
    tabelas = [t[0] for t in tabelas]
    print(f"   Tabelas encontradas: {tabelas}")

    resultado = []
    for tabela in tabelas:
        colunas = con.execute(f"DESCRIBE {tabela}").fetchall()
        total = con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]

        campos = [{"nome": col[0], "tipo": col[1]} for col in colunas]

        resultado.append(
            {
                "tabela": tabela,
                "total_registros": total,
                "campos": campos,
            }
        )
        print(f"   {tabela}: {len(campos)} campos, {total:,} registros")

    con.close()

    return {"tabelas_gold": resultado}


# ── Ponto de entrada ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🛡️  DataSentinel — Catálogo Inteligente RideStream")
    print("=" * 52)

    # Passo 1: configuração
    cliente_openai = carregar_config()

    # Passo 2: leitura da Silver
    spark = criar_spark_session()
    schema_silver = extrair_schema_silver(spark)
    spark.stop()

    # Passo 3: leitura do Gold
    schema_gold = extrair_schema_gold()

    print("\n✅ Schemas extraídos com sucesso!")
    print(f"   Silver: {len(schema_silver['campos'])} campos")
    print(f"   Gold:   {len(schema_gold['tabelas_gold'])} tabelas")
