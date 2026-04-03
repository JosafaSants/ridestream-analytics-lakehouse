# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**RideStream Analytics Lakehouse** is a real-time data pipeline portfolio project simulating ride-hailing event processing (à la Uber/99). It ingests ride events via Apache Kafka, processes them with Spark Structured Streaming, and stores them in a Data Lakehouse using Medallion Architecture (Bronze → Silver → Gold).

**Current state:** v0.6 — Kafka infrastructure is live, the ride event producer is working, the Bronze layer job is implemented, the Silver layer job is implemented, and the Gold layer is implemented with dbt-duckdb. DataSentinel is not yet implemented.

## Infrastructure Commands

```bash
# Start Kafka cluster (Zookeeper + Kafka broker + Kafka UI)
docker compose -f infra/docker-compose.yml up -d

# Stop the cluster
docker compose -f infra/docker-compose.yml down

# View logs
docker compose -f infra/docker-compose.yml logs -f kafka
```

Kafka UI is accessible at `http://localhost:8080` (cluster name: `ridestream-local`).
Kafka broker for local producers/consumers: `localhost:9092`.
Internal Docker network address: `kafka:29092`.

## Architecture

### Data Flow
```
producer/ → Kafka (localhost:9092) → Spark Streaming → spark/bronze/ → spark/silver/ → spark/gold/
                                                                                              ↓
                                                                                    dbt/ (Gold models)
                                                                                              ↓
                                                                                catalog/ (DataSentinel AI)
```

### Medallion Layers
- **Bronze** (`spark/bronze/`) — Raw ingestion from Kafka to Delta Lake, minimal transformation (bytes→string, partition columns only)
- **Silver** (`spark/silver/`) — Cleaning, validation, deduplication
- **Gold** (`spark/gold/`) — Business KPIs and aggregations
- **dbt** (`dbt/`) — SQL transformations over the Gold layer
- **DataSentinel** (`catalog/`) — AI-powered data catalog using the Claude API

### Silver Layer (`spark/silver/silver_job.py`)

Reads from the Bronze Delta table as a streaming source and writes cleaned, deduplicated events to Delta Lake. Key details:

- **Source:** `data/bronze/ride_events/` — read via `readStream.format("delta")` with `ignoreChanges=True`
- **Output path:** `data/silver/ride_events/` — partitioned by `year/month/day`
- **Checkpoint path:** `data/checkpoints/silver/` — never delete; holds streaming offset state
- **Transformations applied:**
  1. `from_json(col("payload"), schema)` — parses the raw JSON string using an explicit schema
  2. Filter — drops records where `ride_id`, `status`, or `timestamp` are null (corrupted messages)
  3. `dropDuplicates(["ride_id", "timestamp"])` — removes Kafka at-least-once redeliveries
  4. Partition columns — `year`, `month`, `day` extracted from the event `timestamp` (not Kafka timestamp)
- **`rating` field:** nullable — only populated when `status == "completed"`
- **Windows config:** `HADOOP_HOME` and `PATH` set programmatically at the top of the file, same as Bronze

Run the Silver job:
```bash
# Requires Bronze data already in data/bronze/ride_events/ (or Bronze job running in parallel)
python spark/silver/silver_job.py
```

### Bronze Layer (`spark/bronze/bronze_job.py`)

Reads from the `ride-events` Kafka topic and writes to Delta Lake. Key details:

- **Kafka broker:** `localhost:9092` (host-facing port; use this when running Spark outside Docker)
- **Output path:** `data/bronze/ride_events/` — partitioned by `year/month/day`
- **Checkpoint path:** `data/checkpoints/bronze/` — never delete; holds streaming offset state
- **Retained Kafka columns:** `topic`, `partition`, `offset` — kept for auditability and reprocessing
- **Dropped columns:** `key`, `value` (promoted to `payload`), `headers`
- **Windows config:** `HADOOP_HOME` and `PATH` are set programmatically at the top of the file — no manual env var setup needed, but `C:\hadoop\bin\winutils.exe` must exist (Hadoop 3.x)

Run the Bronze job:
```bash
# Install Spark dependencies (requires Java 17 with JAVA_HOME set)
pip install pyspark==3.5.1 delta-spark==3.2.0

# Run the job (keep Kafka running first)
python spark/bronze/bronze_job.py
```

### Gold Layer (`dbt/ridestream/models/gold/`)

Reads Silver Parquet files via DuckDB and materializes business KPI tables. Key details:

- **dbt-core version:** 1.11.7
- **dbt-duckdb version:** 1.9.1 (installed in `venv/`)
- **profiles.yml:** `C:\Users\JosafaBarbosadosSant\.dbt\profiles.yml` — outside the repo, never commit
- **DuckDB database:** `data/gold/ridestream.duckdb` — gitignored, created on first `dbt run`
- **Source:** `data/silver/ride_events/**/*.parquet` — read with `read_parquet(..., hive_partitioning=true)`
- **Models:**
  - `fct_rides_completed` — completed rides with fare and rating (revenue events)
  - `fct_rides_cancelled` — cancelled rides (lost revenue events)
  - `dim_drivers` — driver dimension with aggregated performance metrics
  - `agg_rides_hourly` — ride volume by hour of day (demand analysis)
  - `agg_cancellation_rate` — daily cancellation rate (operational health)
  - `agg_avg_rating` — average rating ranking per driver
- **Quality tests:** 15 tests defined in `schema.yml` (`not_null`, `unique` on key columns)
- **Dependency resolution:** `dim_drivers` and `agg_avg_rating` use `{{ ref('fct_rides_completed') }}` — dbt handles execution order automatically

Run the Gold layer:
```bash
cd dbt\ridestream
dbt run       # materializes all 6 models into DuckDB
dbt test      # runs 15 quality tests
```

### Producer (`producer/ride_producer.py`)

Simulates ride events and publishes them to Kafka. Key details:

- **Kafka topic:** `ride-events`
- **Ride status lifecycle:** `requested` → `accepted` → `arrived` → `in_progress` → `completed` / `cancelled`
- **São Paulo coordinate bounds:** lat `[-23.68, -23.46]`, lon `[-46.82, -46.36]`
- **`rating` field:** only populated when `status == "completed"`, `None` otherwise
- **Environment config:** reads from `.env` (use `.env.example` as template); falls back to `localhost:9092` and `ride-events` if absent

Run the producer:
```bash
python producer/ride_producer.py
```

### Tech Stack
| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Streaming | Apache Kafka 2.8+ (Confluent Platform 7.5.0) |
| Processing | Apache Spark Structured Streaming 3.5+ |
| Storage format | Parquet + Delta Lake 3.0+ |
| Transformations | dbt 1.7+ |
| AI Catalog | Claude API (DataSentinel) |
| Infrastructure | Docker Compose |
| Cloud target | AWS (S3, MSK, EMR) |

## Development Notes

- Python virtual environment: `venv/` (gitignored) — activate with `source venv/Scripts/activate` on Windows
- Dependencies: `requirements.txt` (kafka-python, faker, python-dotenv, tzdata)
- Environment variables: `.env` file (gitignored) — copy `.env.example` to create yours
- `data/` directory is gitignored — Parquet files and raw data are never committed
- Spark checkpoints go to `checkpoints/` (gitignored) — these hold streaming state
- Replication factor is set to 1 locally; production AWS MSK target is 3

## Roadmap Context

| Version | Scope |
|---------|-------|
| ✅ v0.1 | Project setup, VS Code, folder structure |
| ✅ v0.2 | Kafka + Zookeeper via Docker Compose |
| ✅ v0.3 | Ride event producer (`producer/ride_producer.py`) |
| ✅ v0.4 | Bronze layer — raw Kafka → Delta Lake (`spark/bronze/bronze_job.py`) |
| ✅ v0.5 | Silver layer — cleaning and deduplication (`spark/silver/silver_job.py`) |
| ✅ v0.6 | Gold layer — dbt-duckdb with 6 SQL models and 15 quality tests |
| 🔜 v0.7 | DataSentinel — AI catalog with Claude API |
| 🔜 v1.0 | AWS deployment with FinOps |


## Mentorship Guidelines

When assisting with this project, always follow these rules:

### Teaching Style
- Explain concepts step by step — never give the full solution at once
- Use simple, human comments in Brazilian Portuguese in all code
- Explain the "why" behind each line, not just the "what"
- Use real-world analogies related to ride-hailing apps (Uber/99)
- Wait for confirmation before moving to the next step

### Code Standards
- All code comments must be written in Brazilian Portuguese
- Follow Conventional Commits: feat, fix, docs, chore, refactor
- Always suggest git commands after completing each step
- Format Python with Ruff (line length 88)

### FinOps Rules
- Always save data in Parquet format (columnar, compressed)
- Always partition data by date (year/month/day) for query pushdown
- Explain cost impact whenever a technical decision affects cloud spend

### When Explaining Code
- Break down complex files into small logical blocks
- Explain one block at a time and wait for confirmation
- Connect every technical concept to a real business problem