# Extreme Mode Blueprint

This is the version of the project that moves from “good capstone” to “serious AI systems portfolio.”

## What Extreme Means

Extreme does not mean adding random technologies. It means every subsystem has:

- A clear interface.
- A correctness check.
- A scalability story.
- An evaluation method.
- A failure mode.
- A safety boundary.
- A documented next experiment.

## Component Targets

| Component | Extreme Standard | Current Implementation |
|---|---|---|
| Data lake | Bronze/silver/gold, Parquet, Spark-native jobs, data contract | Implemented with pandas fallback and Spark-native extension |
| Data quality | Contract checks, row/year/ID validation, missingness, drift | Implemented via `configs/data_contract.yaml` and `/api/data-contract` |
| Warehouse | PostGIS schema, indexes, aggregate views, loader | Implemented with `db/schema.sql` and `load_postgis.py` |
| Big data | Spark cleaning, Spark SQL gold views, streaming demo | Implemented as optional PySpark modules |
| ML | Multi-model benchmark, leakage guard, W&B tracking, artifacts | Implemented with `experiment_suite.py` and sweep config |
| Deep learning | MLP and sequence scaffolds | Implemented scaffold; full training remains extension work |
| MLOps | W&B offline/online, sweeps, model artifacts, CI smoke tests | Implemented |
| Monitoring | PSI and Jensen-Shannon drift reports | Implemented via `/api/monitoring/drift` |
| Graph analytics | Graph exports, centrality, communities, Neo4j GDS queries | Implemented with CSV exports and GDS playbook |
| RAG | Retrieval, citations, refusal tests, evaluation report | Implemented via `rag/evaluate.py` |
| MCP | Read-only tools/resources, no arbitrary SQL or shell | Implemented |
| Frontend | Multi-page operational dashboard | Implemented v1, next step is deeper interactions |
| DevOps | Docker Compose, CI, scripts | Implemented |

## Research-Grade Extensions

- Add calibrated uncertainty for severity and fatality models.
- Run proper W&B sweeps over model families and feature sets.
- Add graph embeddings from Neo4j FastRP into the supervised models.
- Compare pandas vs Spark runtime on expanded or synthetically scaled GTD-like data.
- Add a true Qdrant-backed vector index once `qdrant-client` and an embedding model are installed.
- Add model drift alerts from W&B or scheduled CI.
- Code split the frontend Plotly bundle for production performance.

## Non-Negotiable Safety Boundary

All outputs remain historical and aggregate. The system must refuse operational, tactical, targeting, weaponization, or evasion guidance.

