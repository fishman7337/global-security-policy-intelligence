# Repository agent instructions

## Scope and precedence

These instructions apply to the entire repository. If a future directory contains a more specific `AGENTS.md`, follow that file for work inside its directory. Direct maintainer instructions take precedence.

## Project context

- **Project:** Global Terrorism Database AI Systems Capstone
- **Repository shape:** Python, Node.js, Jupyter notebooks
- Read `README.md` before changing behaviour, architecture, data handling, or public claims.
- Treat `CONTRIBUTING.md` as the authoritative development workflow and command reference.
- Follow `SECURITY.md` for vulnerability reporting and `CODE_OF_CONDUCT.md` for collaboration.
- Use the workflows under `.github/workflows/` as the final cross-platform CI contract.

## Working agreement

1. Keep each change focused on a clear problem; avoid unrelated cleanup.
2. Inspect nearby tests, configuration, documentation, and generated artifacts before editing.
3. Add or update tests for behavioural changes, including failure and boundary cases.
4. Preserve public APIs and file formats unless the change explicitly includes a documented migration.
5. Never commit credentials, personal data, local environments, caches, or unlicensed datasets.
6. Do not weaken lint, coverage, security, or dependency gates merely to obtain a passing run.
7. After code or architecture changes, run `graphify update .` and review the graph diff; do not commit cache-only churn.
8. Do not stage, commit, push, or publish changes unless the maintainer explicitly requests that action.

## Required validation

Run commands from the repository root. Use a clean environment when dependency or packaging behaviour changes.

### Standard development gate

```text
python -m venv .venv
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m pytest
python -m compileall scripts src tests
npm --prefix frontend ci
npm --prefix frontend run build
npm --prefix frontend audit --omit=dev --audit-level=moderate
```

### Repository-specific CI-equivalent checks

```text
python -m bandit -q -r src scripts
python -m pip_audit -r requirements.txt --progress-spinner off
```

Also run `git diff --check`. Record exactly which commands ran, their outcomes, and any documented prerequisite that prevented a check. Do not describe an unexecuted check as passing.

### Conditional or integration setup

- Use `docker compose up --build` only when exercising the Docker stack.
- Use `python scripts/build_notebooks.py` to regenerate notebooks; add `--execute` only when the required data and runtime dependencies are available.
- Online Weights & Biases tracking is opt-in and requires `WANDB_API_KEY`, `WANDB_MODE=online`, and `WANDB_PROJECT`; default validation remains offline.

## Managed artifacts and data

- Treat `scripts/build_notebooks.py` as the generator for the maintained notebook suite.
- Do not commit local runtime output under `artifacts/`, `data_lake/`, `models/`, `wandb/`, or `frontend/dist/`.

## Integration and claim boundaries

- The source GTD dataset is not redistributed; complete builds require a separately obtained, appropriately licensed copy.
- TensorFlow, PySpark, Neo4j, and vector-database integrations are optional and outside the default CPU-only CI job.
- Describe the repository as a research platform; do not infer causal policy impact from its analyses or scaffolding.
- **Verified local capability:** Python, Bandit, pip-audit, npm audit, and Vite production build.
- **Known boundary:** Descriptive research platform; no causal policy-impact claim.

## Code, documentation, and evidence standards

- For Python, follow PEP 8, PEP 257, and Google-style docstrings in the production scopes configured by Ruff.
- For JavaScript or TypeScript, follow the repository's ESLint and Prettier configuration and avoid untyped or silently coerced inputs.
- Prefer small, typed, testable units and explicit error handling. Avoid silent fallbacks that hide invalid data, missing models, credentials, or services.
- Update README, architecture, data/model documentation, examples, and changelog material when interfaces or behaviour change.
- Every quantitative claim must retain its denominator, dataset/version, split, date range, run/configuration, and calculation method.
- Distinguish measured results from targets, examples, heuristics, previews, and prior runs. Do not infer deployment, accuracy, security, causality, or impact from tests or scaffolding alone.
- Update generated files through their source script. If no generator exists, document the manual process and verify semantic equivalence.

## Review and handoff

Before handing off a change, provide a concise summary, list changed files, report validation evidence, and call out residual risks or unavailable integrations. Keep commits imperative and scoped; do not add tool-attribution or automated co-author trailers.
