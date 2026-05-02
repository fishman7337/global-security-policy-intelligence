# Contributing

Thank you for helping improve Global Security Policy Intelligence. This
project combines public-policy research, historical terrorism data, machine
learning, graph analytics, RAG, and MLOps, so contributions need to be both
technically sound and safety-aware.

## Safety First

This repository is for historical, aggregate, non-operational analysis. Do not
submit code, data, prompts, notebooks, or documentation that provide tactical
guidance, targeting support, weaponization details, evasion advice, or
incident-level operational recommendations.

## Contribution Types

- Data engineering improvements that preserve data contracts.
- Public-policy panel methods, robustness checks, and documentation.
- Model, monitoring, graph, and RAG improvements with tests.
- Notebook updates that stay compact and reproducible.
- Documentation that clarifies methods, limitations, ethics, or setup.
- Frontend improvements that make aggregate analysis easier to inspect.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
cd frontend
npm ci
```

## Required Checks

Run these before opening a pull request:

```powershell
python -m ruff check src tests scripts/build_notebooks.py
pytest
cd frontend
npm run build
```

When notebooks change, also run:

```powershell
python scripts/build_notebooks.py --execute
```

## Pull Request Guidelines

- Keep pull requests scoped to one coherent change.
- Describe why the change matters and what evidence supports it.
- Mention affected datasets, artifacts, API routes, notebooks, and docs.
- Include tests for behavior changes.
- Avoid committing raw datasets, generated artifacts, local caches, secrets,
  model binaries, or build output.
- Update documentation when behavior, assumptions, or limitations change.

## Code Style

Python code should follow PEP 8 and use PEP 257 compatible Google-style
docstrings for research-critical modules. Prefer existing package utilities
over notebook-only duplication.

Frontend code should keep the dashboard focused on aggregate research,
diagnostics, and limitations rather than tactical incident use.

## Data and Licensing

The code is licensed under Apache-2.0. Data sources such as GTD, WGI, WDI,
V-Dem, UCDP, UNDP HDI, Freedom House, and International IDEA retain their own
licenses, attribution rules, and access terms. Do not redistribute raw data
unless the provider terms explicitly allow it.
