# Notebooks

This folder contains the rendered, reproducible research notebook suite.

The notebooks cover data engineering, EDA, geospatial analysis, adaptive
severity, ML, deep learning scaffolds, graph analytics, RAG/MCP safety,
policy research, and monitoring/MLOps.

`legacy/` contains the original exploratory notebooks that preceded the clean
rendered suite. They are preserved for provenance, but the numbered notebooks
are the canonical reproducible research path.

Regenerate compact executed notebooks with:

```powershell
python scripts/build_notebooks.py --execute
```

Do not commit large raw tables, bulky map payloads, secrets, or unrestricted
data dumps in notebook outputs.
