# Methodology

## Data Engineering

The project uses a lakehouse-style pattern.

- Bronze: raw GTD Excel rows are extracted to Parquet with source metadata.
- Silver: rows are cleaned, typed, deduplicated by `eventid`, assigned dates, validated for coordinates, and labelled with adaptive casualty severity.
- Gold: aggregates, model features, forecasts, graph exports, RAG documents, complexity reports, and quality summaries are generated.

The code is Spark-ready. If PySpark is unavailable, the same transformations run through pandas so the project remains runnable on a local laptop.

## Modelling

The first trainable model is a casualty severity classifier tracked with Weights & Biases. Its
target is no longer a blind fixed threshold over total casualties: the silver pipeline computes a
logged casualty-burden score and uses OPTICS density clustering for non-zero casualty incidents,
with a percentile fallback only for tiny or degenerate samples. The classifier uses
non-leakage-controlled historical descriptors such as year, region, country, attack type, target
type, weapon type, and binary context fields.

Planned and scaffolded extensions include fatality regression, attack success classification, attack type classification, clustering, sequence forecasting, NLP classification, and graph neural network experimentation.

## W&B

W&B logs configs, metrics, model artifacts, report artifacts, and local offline runs. CI uses `WANDB_MODE=offline`; local online tracking uses `WANDB_API_KEY`.

## RAG

The chatbot retrieves project documentation, ethics policy, model cards, methodology, complexity notes, and aggregate summaries. It cites sources and refuses unsafe operational requests.

## Graph

The graph layer models incidents, countries, regions, groups, years, attack types, target types, and weapon types. Local baseline algorithms are included; Neo4j GDS can run PageRank, Louvain, node similarity, shortest path, and FastRP embeddings after loading the exported graph CSVs.

## Public Policy Panel

The policy layer aggregates GTD to country-year outcomes for 1996-2021 and merges optional
credential-free public-policy covariates. The main governance-capacity construct averages WGI
government effectiveness, rule of law, and control of corruption. Development controls come from
WDI, while V-Dem, HDI, UCDP, Freedom House, International IDEA, and press-freedom variables are
treated as optional robustness or reporting-bias sources.

The main research design is country and year fixed effects with one-year lagged governance
variables. Results are reported as cautious public-policy associations, not operational forecasts.
