# Architecture

The capstone is designed as a local-first, Docker-ready AI analytics platform.

## Services

- React/Vite frontend for dashboards, model labs, graph views, RAG chat, and complexity reporting.
- FastAPI backend for analytics, predictions, forecasts, graph summaries, and chatbot calls.
- Postgres/PostGIS for curated incident facts, geospatial aggregation, and analytical views.
- Neo4j Graph Data Science for knowledge graph algorithms.
- Qdrant for vector retrieval in the RAG layer.
- Weights & Biases for experiment tracking, artifacts, sweeps, and reports.

## Data Flow

1. Raw GTD Excel files are treated as immutable source data.
2. Bronze layer stores raw extracted rows in Parquet.
3. Silver layer normalizes schema, types, dates, categories, casualties, and coordinate validity.
4. Gold layer creates dashboard aggregates, model features, graph CSV exports, RAG documents, and quality reports.
5. API and frontend read gold assets by default, with database adapters ready for PostGIS/Neo4j/Qdrant deployment.

## Safety Boundary

The platform supports historical aggregate analysis. Exact incident-point maps, tactical advice, target recommendations, weaponization, and evasion guidance are out of scope.

