# Extreme Local Runbook

## Full Artifact Build

```powershell
$env:PYTHONPATH="src"
python -m gtd_capstone.pipelines.build_artifacts
```

Outputs:

- `artifacts/bronze/raw_extract.parquet`
- `artifacts/silver/incidents.parquet`
- `artifacts/gold/incidents.parquet`
- `artifacts/gold/data_contract.json`
- `artifacts/gold/drift.json`
- `artifacts/gold/rag_eval.json`
- `artifacts/gold/graph/neo4j_nodes.csv`
- `artifacts/gold/graph/neo4j_edges.csv`
- `artifacts/gold/graph/neo4j_gds_playbook.cypher`

## Multi-Model W&B Experiment

```powershell
$env:PYTHONPATH="src"
$env:WANDB_MODE="offline"
python -m gtd_capstone.ml.experiment_suite --task severity --model-family random_forest --sample-rows 50000
python -m gtd_capstone.ml.experiment_suite --task success --model-family extra_trees --sample-rows 50000
python -m gtd_capstone.ml.experiment_suite --task nkill --sample-rows 50000
python -m gtd_capstone.ml.experiment_suite --task clustering --sample-rows 50000
```

## PostGIS Load

Start Docker Compose, then:

```powershell
$env:PYTHONPATH="src"
python -m gtd_capstone.db.load_postgis --database-url "postgresql+psycopg://gtd:gtd@localhost:5432/gtd"
```

## Neo4j Graph

Use the generated CSV exports and execute:

```powershell
Get-Content artifacts/gold/graph/neo4j_gds_playbook.cypher
```

The playbook contains projection, PageRank, Louvain, node similarity, and FastRP queries.

## RAG Evaluation

```powershell
$env:PYTHONPATH="src"
python -m gtd_capstone.rag.evaluate --output artifacts/gold/rag_eval.json
```

The evaluation checks citation presence for safe questions and refusal for unsafe prompts.

