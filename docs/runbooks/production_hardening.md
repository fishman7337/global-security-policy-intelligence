# Production Hardening Runbook

This project is local-first. To harden it further:

1. Replace local files with object storage for bronze/silver/gold artifacts.
2. Use a migration tool for PostGIS schema changes.
3. Load Neo4j with batched import rather than row-by-row writes.
4. Replace TF-IDF RAG with Qdrant + sentence embeddings.
5. Add authentication before exposing any API outside localhost.
6. Add API rate limits and audit logs for chatbot and MCP calls.
7. Use W&B model registry promotion stages.
8. Add scheduled drift jobs and alert thresholds.
9. Add frontend code splitting for Plotly-heavy pages.
10. Add Playwright visual regression tests.

Safety still takes priority over feature depth: aggregate-only outputs and refusal behavior must survive every deployment environment.

