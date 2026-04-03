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


# ── Geração de documentação via IA ──────────────────────────────────────────


def gerar_documentacao(cliente: OpenAI, schema: dict, camada: str) -> str:
    """
    Envia o schema extraído para o GPT-4o-mini e recebe de volta
    uma documentação legível em português para cada campo.

    A IA não inventa informações — ela interpreta os dados reais
    (tipos, nulos, min/max) e escreve descrições úteis para o time.
    """
    # Monta o resumo dos campos para enviar ao modelo
    linhas_campos = []
    for campo in schema.get("campos", []):
        linha = f"- {campo['nome']} | tipo: {campo['tipo']} | nulos: {campo.get('nulos_pct', 'n/a')}%"
        if "minimo" in campo:
            linha += f" | min: {campo['minimo']} | max: {campo['maximo']} | média: {campo['media']}"
        linhas_campos.append(linha)

    resumo_campos = "\n".join(linhas_campos)
    total = schema.get("total_registros", 0)
    tabela = schema.get("tabela", camada)

    prompt = f"""Você é um engenheiro de dados documentando um lakehouse de uma empresa de ride-hailing (como Uber/99) no Brasil.

Abaixo estão os metadados da tabela `{tabela}` da camada {camada.upper()} do pipeline:

Total de registros: {total:,}
Campos:
{resumo_campos}

Para cada campo, escreva uma descrição clara e objetiva em português brasileiro explicando:
1. O que o campo representa no contexto de corridas de aplicativo
2. Se há campos com nulos altos (>10%), explique se isso é esperado ou um problema
3. Para campos numéricos, comente sobre os valores min/max/média

Responda em formato Markdown com uma tabela de campos e depois uma seção de observações de qualidade.
Seja direto e técnico, como um engenheiro de dados escreveria para outros engenheiros."""

    print(f"\n🤖 Gerando documentação para {tabela} com GPT-4o-mini...")

    resposta = cliente.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,  # baixa temperatura = respostas mais consistentes
    )

    return resposta.choices[0].message.content


def salvar_documentacao(conteudo: str, nome_arquivo: str) -> None:
    """
    Salva o Markdown gerado pela IA em catalog/docs/.
    Adiciona cabeçalho com data de geração para rastreabilidade.
    """
    from datetime import datetime

    pasta = Path("catalog/docs")
    pasta.mkdir(parents=True, exist_ok=True)

    caminho = pasta / nome_arquivo

    # Cabeçalho com timestamp para saber quando foi gerado
    cabecalho = f"<!-- Gerado automaticamente pelo DataSentinel em {datetime.now().strftime('%Y-%m-%d %H:%M')} -->\n\n"

    caminho.write_text(cabecalho + conteudo, encoding="utf-8")
    print(f"   📄 Salvo em: {caminho}")


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

    # Passo 4: gera documentação da Silver
    doc_silver = gerar_documentacao(cliente_openai, schema_silver, "silver")
    salvar_documentacao(doc_silver, "silver_ride_events.md")

    # Passo 5: gera documentação de cada tabela Gold
    for tabela in schema_gold["tabelas_gold"]:
        doc_gold = gerar_documentacao(cliente_openai, tabela, "gold")
        salvar_documentacao(doc_gold, f"gold_{tabela['tabela']}.md")

    print("\n🎉 DataSentinel concluído!")
    print(f"   Documentação salva em: catalog/docs/")
