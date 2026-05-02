# Global Terrorism Database AI Systems Capstone

This repository turns the existing GTD notebooks into a full-stack AI systems capstone:
Spark-style data engineering, PostGIS analytics, graph analytics, machine learning,
deep learning, RAG, MCP, W&B tracking, CI/CD, Docker, and algorithmic complexity work.

Code and project-authored documentation are licensed under Apache-2.0. External
datasets retain their own licenses, access rules, and citation requirements.

The project is designed for historical, aggregate analysis only. It must not be used for
tactical, targeting, weaponization, or operational guidance.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
python -m gtd_capstone.pipelines.build_artifacts --sample-rows 20000
uvicorn gtd_capstone.api.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Docker-first stack:

```powershell
docker compose up --build
```

## What Is Implemented

- Bronze/silver/gold data pipeline with Spark-ready design and pandas fallback.
- FastAPI backend exposing the planned public API.
- React/Vite dashboard with analytics, ML, graph, RAG, and complexity pages.
- Weights & Biases integration with offline-safe tracking.
- Graph analytics module with adjacency-list algorithms and Neo4j export schemas.
- RAG chatbot with safe retrieval and refusal guardrails.
- Read-only MCP-style JSON-RPC server for aggregate tools/resources.
- Public policy research layer with country-year panel, governance-capacity models, and source registry.
- Tests for data cleaning, DSA algorithms, API contracts, RAG safety, and W&B offline logging.

## Legacy References

The original exploratory notebooks are kept as historical reference work under
`notebooks/legacy/`:

- `notebooks/legacy/Database.ipynb`
- `notebooks/legacy/GTD Analysis.ipynb`
- `notebooks/legacy/GTD Time Series.ipynb`

The original Plotly HTML export remains available as:

- `global_terror_attacks.html`

Rendered research notebook suite:

- `notebooks/00_project_overview.ipynb`
- `notebooks/01_data_engineering_quality.ipynb`
- `notebooks/02_eda_visual_analytics.ipynb`
- `notebooks/03_geospatial_forecasting.ipynb`
- `notebooks/04_adaptive_severity.ipynb`
- `notebooks/05_feature_store_ml_baselines.ipynb`
- `notebooks/06_ml_experiment_benchmark.ipynb`
- `notebooks/07_deep_learning_lab.ipynb`
- `notebooks/08_graph_analytics.ipynb`
- `notebooks/09_rag_mcp_safety.ipynb`
- `notebooks/10_policy_research_panel.ipynb`
- `notebooks/11_monitoring_drift_mlops.ipynb`

## Main Commands

```powershell
python -m gtd_capstone.pipelines.build_artifacts
python -m gtd_capstone.ml.train --sample-rows 30000
python -m gtd_capstone.ml.experiment_suite --task severity --sample-rows 50000
python -m gtd_capstone.pipelines.build_artifacts --fetch-policy-sources
python -m gtd_capstone.rag.evaluate --output artifacts/gold/rag_eval.json
python scripts/build_notebooks.py --execute
python -m gtd_capstone.mcp_server
pytest
```

## W&B

By default, CI and local smoke tests use `WANDB_MODE=offline`. To track online:

```powershell
$env:WANDB_API_KEY="..."
$env:WANDB_MODE="online"
$env:WANDB_PROJECT="gtd-capstone"
python -m gtd_capstone.ml.train --sample-rows 50000
```

## Documentation

- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Support](SUPPORT.md)
- [Governance](GOVERNANCE.md)
- [Changelog](CHANGELOG.md)
- [Notice](NOTICE.md)
- [Architecture](docs/architecture.md)
- [Curriculum Map](docs/curriculum_map.md)
- [Ethics Policy](docs/ethics.md)
- [Complexity Report](docs/complexity.md)
- [Methodology](docs/methodology.md)
- [Policy Research Paper](docs/research/policy_paper.md)
- [Policy Source Registry](docs/research/source_registry.md)
- [Severity Model Card](docs/model_cards/severity_model.md)
- [Extreme Mode Blueprint](docs/extreme_blueprint.md)
- [Extreme Local Runbook](docs/runbooks/extreme_local_runbook.md)

## License

This project is released under the [Apache License 2.0](LICENSE). The license
applies to repository code and project-authored documentation, not to external
datasets consumed by the pipeline.
