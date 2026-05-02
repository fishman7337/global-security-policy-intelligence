# Model Card: Casualty Severity Classifier

## Purpose

Classify historical GTD incidents into casualty severity bands for educational model comparison and dashboard explanation.

## Target

Severity is now an adaptive label, not a fixed casualty threshold. The cleaning pipeline computes
a casualty burden score from logged fatalities, wounded counts, and total casualties, then uses
OPTICS density clustering to identify severity structure among non-zero casualty incidents.

Rows with zero casualties remain `None`. Non-zero rows receive one of:

- `Low`
- `Medium`
- `High`
- `Mass Casualty`

For tiny smoke-test samples or degenerate data where density clustering is not meaningful, the
pipeline uses ranked score percentiles as a transparent fallback. The output includes
`severity_score`, `severity_score_percentile`, `severity_cluster`, and `severity_method` so the
label provenance is auditable.

## Features

The baseline uses year, month, region, country, attack type, target type, weapon type, suicide flag, property flag, and hostage/kidnap flag.

## Tracking

Experiments are tracked in Weights & Biases. CI uses offline mode.

## Limitations

The model is not an operational risk system. It reflects historical reporting patterns, data
quality limitations, and the adaptive clustering choices used to define the target. It must not be
used for tactical decisions, target assessment, or intervention planning.

## Evaluation

Metrics include accuracy, macro F1, weighted F1, and per-class precision/recall. Future extensions should add calibration, fairness/error slicing, uncertainty, and SHAP explanations.

## Public Policy Use

The classifier is separate from the country-year policy panel. Policy analysis should use aggregate
outcomes such as casualties, attacks, high-severity share, and severity burden. Incident-level
severity predictions must not be used for tactical decisions, country ranking, or operational
intervention planning.
