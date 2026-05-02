# Governance

## Project Direction

Global Security Policy Intelligence is maintained as a research-oriented,
aggregate-analysis platform. The project prioritizes:

- Historical reproducibility.
- Public-policy relevance.
- Ethical and non-operational framing.
- Transparent limitations.
- Testable data and model behavior.
- Clear documentation for reviewers and future contributors.

## Maintainer Responsibilities

Maintainers are responsible for reviewing contributions, enforcing the Code of
Conduct, protecting safety boundaries, preserving data-source terms, and
keeping CI green.

## Decision Criteria

Changes should be accepted when they:

- Improve correctness, reproducibility, interpretability, or usability.
- Preserve the aggregate, non-operational scope.
- Include appropriate tests or documentation.
- Avoid unnecessary data, dependency, or infrastructure burden.

Changes should be rejected or revised when they:

- Enable tactical misuse or incident-level operational decisions.
- Overclaim causal or predictive validity.
- Violate data-source licenses or access terms.
- Add unnecessary complexity without clear research value.

## Release Practice

This project uses lightweight, changelog-based releases. Significant changes
should update `CHANGELOG.md`, relevant model cards, research documentation,
and folder READMEs when applicable.
