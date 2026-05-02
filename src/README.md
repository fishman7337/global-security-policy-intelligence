# Source

This folder contains the Python package source tree.

Install the package in editable mode from the repository root:

```powershell
pip install -e .[dev]
```

Package modules should expose reusable pipeline, analytics, model, monitoring,
policy, graph, RAG, and API logic that notebooks and scripts can call instead
of duplicating implementation.
