# Research Agenda

The capstone can support serious applied AI investigation without crossing into operational misuse.

## Questions

- How do reporting patterns and missingness change across decades and regions?
- How robust are severity models under temporal split evaluation?
- Can graph community structure improve aggregate historical explanation?
- How much do graph embeddings improve tabular models?
- Which forecasting methods remain stable under political shock periods?
- How well does the RAG assistant ground answers in project documentation?
- How does governance capacity relate to country-year terrorism severity burden?
- Do democracy, conflict burden, and reporting-bias proxies change the governance association?

## Experiments

- Temporal validation: train before 2014, test from 2014 onward.
- Region holdout: evaluate models on held-out regions.
- Graph-enhanced ML: add PageRank, community ID, and FastRP embeddings to tabular features.
- Forecast benchmark: seasonal naive vs ARIMA vs tree regressors vs sequence models.
- RAG benchmark: TF-IDF vs Qdrant embeddings.
- Data scale benchmark: pandas vs Spark on synthetic row multipliers.
- Country-year policy panel: GTD outcomes merged with WGI, WDI, V-Dem, HDI, UCDP, and democracy robustness sources.
- Fixed-effects policy models: lagged governance capacity with country and year effects.
- Event-study extension: regime transformation episodes from V-Dem, where normalized local data are available.

## Evaluation Principles

- Prefer macro F1 and calibration for imbalanced classification.
- Report uncertainty, not only point estimates.
- Use temporal splits where possible.
- Document missing data and reporting bias.
- Refuse unsafe operational interpretations.
- Separate cautious causal-policy claims from prediction or operational guidance.
