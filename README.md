<div align="center">

# 🚀 RideStream Analytics Lakehouse

**Pipeline de Dados em Tempo Real para Análise de Corridas**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-2.8+-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)](https://kafka.apache.org)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.5+-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)](https://spark.apache.org)
[![dbt](https://img.shields.io/badge/dbt-1.7+-FF694B?style=for-the-badge&logo=dbt&logoColor=white)](https://getdbt.com)
[![Delta Lake](https://img.shields.io/badge/Delta_Lake-3.0+-003366?style=for-the-badge)](https://delta.io)
[![Docker](https://img.shields.io/badge/Docker-24+-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Em_Construção-orange?style=for-the-badge)]()

<br/>

> Pipeline de streaming em tempo real que ingere eventos de corridas via Apache Kafka,  
> processa com Spark Structured Streaming e organiza em um Data Lakehouse  
> com Arquitetura Medalhão (Bronze → Silver → Gold).

<br/>

</div>

---

## 📌 O que é este projeto?

O **RideStream Analytics Lakehouse** é uma plataforma de dados em tempo real inspirada nos desafios reais de empresas como Uber e 99. A cada segundo, eventos de corridas são gerados — solicitações, atualizações de GPS, pagamentos e avaliações — e precisam ser ingeridos, limpos e transformados em insights de negócio com baixa latência.

O projeto demonstra na prática como construir um pipeline de dados moderno do zero, aplicando boas práticas de engenharia de dados, FinOps e governança de dados.

> 📖 **Projeto de portfólio em construção** — desenvolvido do zero, passo a passo, com documentação de cada decisão técnica. Acompanhe a evolução pelos [commits](../../commits).

---

## ✨ Status das Funcionalidades

| Funcionalidade | Descrição | Versão |
|---|---|---|
| ⚙️ **Setup do Ambiente** | VS Code, Git e estrutura de pastas | ✅ v0.1 |
| 🏗️ **Infraestrutura** | Kafka e Zookeeper via Docker Compose | ✅ v0.2 |
| 📡 **Producer** | Simulador de eventos de corridas para o Kafka | ✅ v0.3 |
| 🥉 **Camada Bronze** | Ingestão raw do Kafka para Delta Lake | ✅ v0.4 |
| 🥈 **Camada Silver** | Limpeza, validação e deduplicação | ✅ v0.5 |
| 🥇 **Camada Gold** | KPIs e agregações de negócio com dbt | ✅ v0.6 |
| 🛡️ **DataSentinel** | Catálogo inteligente de dados com IA | 🔜 v0.7 |
| ☁️ **Deploy AWS** | Subida para nuvem com FinOps aplicado | 🔜 v1.0 |

---

## 🏗️ Arquitetura do Sistema
```
┌─────────────────────────────────────────────────────────────┐
│                 RideStream Analytics Lakehouse               │
└─────────────────────────────────────────────────────────────┘

  📱 EVENTOS              🔄 STREAMING             🗄️ LAKEHOUSE
  ┌──────────┐           ┌──────────────┐          ┌──────────────┐
  │ Corridas │──producer─▶   Apache     │          │   🥉 Bronze  │
  │ GPS      │           │    Kafka     │─Spark───▶│   🥈 Silver  │
  │ Pagamento│           │              │Streaming │   🥇 Gold    │
  │ Avaliação│           └──────────────┘          └──────┬───────┘
  └──────────┘                                            │
                                                          │
  🛡️ DATASENTINEL         📊 CONSUMO                      │
  ┌──────────────┐       ┌──────────────┐                 │
  │  Catálogo IA │       │  Dashboards  │◀────────────────┘
  │  Alertas     │       │  dbt Models  │
  │  Duplicatas  │       │  Analytics   │
  └──────────────┘       └──────────────┘
```

---

## 🛠️ Stack Tecnológica

| Categoria | Tecnologia | Versão |
|---|---|---|
| Linguagem | Python | 3.11 |
| Mensageria | Apache Kafka | 2.8+ |
| Processamento | Apache Spark Structured Streaming | 3.5+ |
| Formato de Dados | Parquet + Delta Lake | 3.0+ |
| Transformação | dbt | 1.7+ |
| Catálogo IA | DataSentinel (Claude API) | - |
| Infraestrutura | Docker + Docker Compose | 24+ |
| Nuvem | AWS (S3, MSK, EMR) | - |

---

## 📁 Estrutura do Projeto
```
ridestream-analytics-lakehouse/
│
├── 📂 infra/              # Docker Compose, Kafka e configurações
├── 📂 producer/           # Simulador de eventos de corridas
├── 📂 spark/              # Jobs Spark por camada
│   ├── 📂 bronze/         # Ingestão raw do Kafka
│   ├── 📂 silver/         # Limpeza e deduplicação
│   └── 📂 gold/           # Agregações de negócio
├── 📂 dbt/                # Modelos dbt para a camada Gold
├── 📂 catalog/            # DataSentinel — catálogo inteligente
├── 📂 data/               # Dados locais (ignorado pelo Git)
├── 📂 docs/               # Diagramas e documentação
└── 📄 README.md
```

---

## 🚀 Como Executar

### 1. Infraestrutura Kafka

```bash
# Subir o cluster Kafka (Zookeeper + Broker + Kafka UI)
docker compose -f infra/docker-compose.yml up -d
```

Kafka UI disponível em `http://localhost:8080`.

### 2. Producer de Eventos

```bash
# Ativar o ambiente virtual
source venv/Scripts/activate   # Windows

# Instalar dependências
pip install -r requirements.txt

# Rodar o producer
python producer/ride_producer.py
```

### 3. Camada Bronze — Job Spark

```bash
# Instalar dependências Spark (requer Java 17)
pip install pyspark==3.5.1 delta-spark==3.2.0

# Rodar o job Bronze
python spark/bronze/bronze_job.py
```

> **Pré-requisitos para Windows:** Java 17 instalado e `JAVA_HOME` configurado. O job configura `HADOOP_HOME` automaticamente, mas requer o `winutils.exe` em `C:\hadoop\bin` — baixe a versão compatível com Hadoop 3.x em [cdarlint/winutils](https://github.com/cdarlint/winutils).

### 4. Camada Silver — Job Spark

```bash
# Com o job Bronze rodando (ou dados já gravados em data/bronze/ride_events/):
python spark/silver/silver_job.py
```

---

## 🗺️ Roadmap

- [x] **v0.1** — Setup do ambiente, Git e estrutura de pastas ✅
- [x] **v0.2** — Infraestrutura Kafka via Docker Compose ✅
- [x] **v0.3** — Producer de eventos de corridas ✅
- [x] **v0.4** — Camada Bronze — ingestão raw para Delta Lake ✅
- [x] **v0.5** — Camada Silver — limpeza e deduplicação ✅
- [x] **v0.6** — Camada Gold implementada com dbt-duckdb: 6 modelos SQL, 15 testes de qualidade aprovados ✅
- [ ] **v0.7** — DataSentinel — catálogo inteligente com Claude API 🔜
- [ ] **v1.0** — Deploy AWS com FinOps aplicado 🔜

---

## 📝 Diário de Desenvolvimento

### ✅ v0.1 — Setup do Ambiente
- Repositório criado no GitHub com proteção da branch `main`
- VS Code configurado com extensões profissionais de engenharia de dados
- Estrutura de pastas do projeto definida seguindo boas práticas
- `.gitignore` configurado para projetos de dados com Spark e Kafka

### ✅ v0.2 — Infraestrutura com Docker e Kafka
- Docker Desktop v4.65.0 instalado e configurado no Windows
- WSL 2 atualizado para suportar o Docker
- Kafka, Zookeeper e Kafka UI configurados via Docker Compose
- Interface visual do Kafka acessível em `http://localhost:8080`
- Cluster `ridestream-local` online e pronto para receber eventos

### ✅ v0.3 — Producer de Eventos de Corridas
- Producer criado com `kafka-python` 2.3.0 e configuração via `python-dotenv`
- `Faker` configurado com locale `pt_BR` para gerar dados realistas brasileiros
- Eventos simulam 6 status do ciclo de vida de uma corrida: `requested`, `accepted`, `arrived`, `in_progress`, `completed` e `cancelled`
- Coordenadas de origem e destino geradas dentro dos limites reais de São Paulo
- Campo `rating` preenchido apenas quando `status == "completed"`, refletindo o fluxo real do app
- 94 eventos enviados com sucesso para o tópico `ride-events` e validados via Kafka UI

### ✅ v0.5 — Camada Silver

**O que a Silver faz:** lê a Bronze como uma fonte de streaming Delta e aplica as transformações de qualidade que promovem os dados brutos a registros confiáveis para análise.

**Fluxo de transformações em `spark/silver/silver_job.py`:**

1. **Parse do JSON** — a coluna `payload` (string bruta) é interpretada com `from_json` usando um schema explícito que espelha exatamente o que o producer envia
2. **Filtro de inválidos** — registros onde `ride_id`, `status` ou `timestamp` são nulos são descartados; isso captura mensagens corrompidas ou incompletas que chegaram da Bronze
3. **Deduplicação** — `dropDuplicates(["ride_id", "timestamp"])` elimina reentregas do Kafka (o broker garante *at least once*, não *exactly once*)
4. **Colunas de partição** — `year`, `month` e `day` são extraídos do `timestamp` do evento (não do Kafka) para garantir que corridas com atraso caiam na partição correta

**Estrutura de arquivos gerada:**

```
data/
└── silver/
│   └── ride_events/
│       └── year=2026/
│           └── month=03/
│               └── day=26/
│                   └── part-00000-*.snappy.parquet
└── checkpoints/
    └── silver/        # Estado do stream — nunca deletar
```

**Decisões técnicas:**
- Schema explícito evita o custo de inferência e garante tipos corretos desde a leitura
- `ignoreChanges=True` na leitura Delta tolera compactações e reprocessamentos na Bronze sem falhar
- Checkpoint independente da Bronze: deletar o checkpoint da Silver reprocessa toda a Bronze sem afetar o job Bronze

---

### ✅ v0.4 — Camada Bronze

**O que a Bronze faz:** ingere os eventos brutos do Kafka e os persiste em Delta Lake sem nenhuma transformação de negócio — apenas o mínimo necessário para armazenar e rastrear os dados. É a fonte da verdade do pipeline: tudo que chega aqui é preservado.

**Dependências adicionadas:**

| Dependência | Versão | Função |
|---|---|---|
| Java 17 | 17+ | Runtime obrigatório para o Spark |
| PySpark | 3.5.1 | Engine de processamento distribuído |
| delta-spark | 3.2.0 | Formato Delta Lake com ACID e versionamento |
| winutils | Hadoop 3.x | Compatibilidade do Spark com o sistema de arquivos Windows |

**Estrutura de arquivos gerada:**

```
data/
└── bronze/
│   └── ride_events/
│       └── year=2026/
│           └── month=03/
│               └── day=26/
│                   └── part-00000-*.snappy.parquet
└── checkpoints/
    └── bronze/        # Estado do stream — nunca deletar
```

**Decisões técnicas:**
- Particionamento por `year/month/day` para query pushdown no S3 (redução de custo)
- Colunas `topic`, `partition` e `offset` mantidas para rastreabilidade e reprocessamento
- Checkpoint em `data/checkpoints/bronze` garante exactly-once semantics entre reinicializações

### ✅ v0.6 — Camada Gold com dbt-duckdb

**O que a Gold faz:** consome os Parquet da Silver e os transforma em tabelas analíticas prontas para consumo — KPIs de receita, cancelamentos, demanda por hora e desempenho de motoristas.

**Dependências adicionadas:**

| Dependência | Versão | Função |
|---|---|---|
| dbt-core | 1.11.7 | Orquestração e materialização dos modelos SQL |
| dbt-duckdb | 1.9.1 | Adapter que conecta dbt ao DuckDB local |

**Modelos implementados em `dbt/ridestream/models/gold/`:**

| Modelo | Tipo | Pergunta respondida |
|---|---|---|
| `fct_rides_completed` | Fato | Quais corridas geraram receita? |
| `fct_rides_cancelled` | Fato | Quais corridas foram perdidas? |
| `dim_drivers` | Dimensão | Qual o desempenho de cada motorista? |
| `agg_rides_hourly` | Agregação | Em que horário há mais demanda? |
| `agg_cancellation_rate` | Agregação | A operação está saudável por dia? |
| `agg_avg_rating` | Agregação | Quais motoristas têm melhor avaliação? |

**15 testes de qualidade definidos em `schema.yml`:** `not_null` e `unique` nas colunas-chave de cada modelo.

**Decisões técnicas:**
- DuckDB lê os Parquet da Silver com `read_parquet(..., hive_partitioning=true)` — sem servidor, sem custo
- `{{ ref('fct_rides_completed') }}` nos modelos dependentes: o dbt resolve a ordem de execução automaticamente
- `profiles.yml` fora do repositório (`~/.dbt/`) — credenciais nunca entram no git

---

## 🧑‍💻 Sobre o Desenvolvedor

Construído do zero como projeto de portfólio em **Engenharia de Dados**, documentando não apenas o produto final, mas cada decisão técnica tomada ao longo do desenvolvimento.

<div align="center">

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Josafa_Santos-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/josafa-barbosa-dos-santos/)
[![GitHub](https://img.shields.io/badge/GitHub-JosafaSants-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/JosafaSants)

</div>

---

## 📄 Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE).

---

<div align="center">

Feito com ☕ e muita dedicação

⭐ Se este projeto te ajudou, deixe uma estrela!

</div>