# Contributing to Global Terrorism Database AI Systems Capstone

Thank you for improving this project. Contributions should be focused, reproducible, evidence-based, and safe to review. By participating, you agree to follow the repository's `CODE_OF_CONDUCT.md` and security policy.

## Development setup

1. Read `README.md` for project-specific prerequisites, data boundaries, and architecture.
2. Create a branch from the current default branch; do not develop directly on `main`.
3. Install only the dependencies needed for the change. Never commit virtual environments, caches, secrets, generated databases, or unlicensed datasets.

Typical setup and quality commands are:

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

On Windows, activate a Python environment with `.venv\Scripts\Activate.ps1`; on POSIX shells use `source .venv/bin/activate`. The GitHub Actions workflow remains the authoritative cross-platform gate.

### Repository-specific CI-equivalent checks

Before opening a pull request, run the applicable heavier validation below. Commands that require Docker, Windows packaging, LaTeX, credentials, external data, or optional services are expected to report their documented prerequisite rather than be silently skipped.

```text
python -m bandit -q -r src scripts
python -m pip_audit -r requirements.txt --progress-spinner off
```

## Development workflow

1. Link the change to a clear issue or problem statement.
2. Keep commits and pull requests small enough to review independently.
3. Add or update tests before changing behaviour, including failure and boundary cases.
4. Update generated artifacts through their source script; do not hand-edit generated outputs.
5. Re-run the full local quality gate and inspect `git diff --check` before requesting review.

Use descriptive branch names such as `fix/model-validation`, `docs/evidence-table`, or `feat/batch-import`. Prefer imperative, scoped commit messages such as `fix: reject malformed labels`.

## Quality checks

All applicable lint, formatting, test, build, notebook, security, and dependency checks must pass. Python production APIs follow PEP 8 and PEP 257 with Google-style docstrings; tests may rely on descriptive test names where the Ruff configuration explicitly allows it.

Do not weaken a quality threshold, skip a security finding, or add a blanket exclusion merely to make CI green. Any narrowly necessary suppression must identify the rule or advisory, explain the risk decision, and include an owner or review condition.

## Documentation and evidence

- Update `README.md`, architecture/model/data documentation, and examples when behaviour or interfaces change.
- Preserve the denominator, dataset version, split, model/run, date range, and calculation method for every numerical claim.
- Distinguish implemented capability from measured outcome. Tests, CI, and deployment scaffolding do not prove that a system is secure, production-deployed, real-time, accurate, or impactful.
- Keep notebooks reproducible: run cells in order, remove stored exception outputs, record seeds/configuration, and avoid committing local absolute paths.
- Document data provenance and licensing. Do not add personal, confidential, credentialed, or copyrighted data without explicit authorization.

## Pull requests

A pull request should include:

- a concise problem statement and solution summary;
- the exact commands run and their results;
- screenshots or artifacts for visible behaviour changes;
- data/model migration and rollback notes where relevant;
- updated documentation and an evidence source for new claims; and
- confirmation that no secret, personal data, or unrelated generated file is included.

Reviewers should be able to reproduce the result from a clean checkout. Resolve all review threads and keep the branch current before merge.

## Security and conduct

Report vulnerabilities through the private process in `SECURITY.md`; do not open a public exploit issue. Follow `CODE_OF_CONDUCT.md` in all project spaces. Academic or portfolio contributions must preserve attribution and must not misrepresent collaborators, results, or institutional endorsement.
