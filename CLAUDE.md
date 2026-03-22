# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**RideStream Analytics Lakehouse** is a real-time data pipeline portfolio project simulating ride-hailing event processing (à la Uber/99). It ingests ride events via Apache Kafka, processes them with Spark Structured Streaming, and stores them in a Data Lakehouse using Medallion Architecture (Bronze → Silver → Gold).

**Current state:** v0.2 — Kafka infrastructure is live; Bronze/Silver/Gold layers and DataSentinel are not yet implemented.

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
- **Bronze** (`spark/bronze/`) — Raw ingestion from Kafka to Parquet, no transformations
- **Silver** (`spark/silver/`) — Cleaning, validation, deduplication
- **Gold** (`spark/gold/`) — Business KPIs and aggregations
- **dbt** (`dbt/`) — SQL transformations over the Gold layer
- **DataSentinel** (`catalog/`) — AI-powered data catalog using the Claude API

### Event Types
Ride events produced to Kafka: ride requests, GPS updates, payments, ratings.

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

- `data/` directory is gitignored — Parquet files and raw data are never committed
- Spark checkpoints go to `checkpoints/` (gitignored) — these hold streaming state
- Python virtual environments go in `venv/` or `.venv/` (gitignored)
- Replication factor is set to 1 locally; production AWS MSK target is 3

## Roadmap Context

| Version | Scope |
|---------|-------|
| ✅ v0.1 | Project setup, VS Code, folder structure |
| ✅ v0.2 | Kafka + Zookeeper via Docker Compose |
| 🔜 v0.3 | Bronze layer — raw Kafka → Parquet ingestion |
| 🔜 v0.4 | Silver layer — cleaning and deduplication |
| 🔜 v0.5 | Gold layer — KPIs with dbt |
| 🔜 v0.6 | DataSentinel — AI catalog with Claude API |
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