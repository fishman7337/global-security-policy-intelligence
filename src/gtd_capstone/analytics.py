from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from gtd_capstone.data.cleaning import _label_from_percentile, _severity_score
from gtd_capstone.safety import aggregate_only_note


def summary(df: pd.DataFrame) -> dict:
    return {
        "rows": int(len(df)),
        "year_min": int(df["iyear"].min()) if len(df) else None,
        "year_max": int(df["iyear"].max()) if len(df) else None,
        "countries": int(df["country_txt"].nunique()),
        "regions": int(df["region_txt"].nunique()),
        "total_fatalities": float(df["nkill"].sum()),
        "total_wounded": float(df["nwound"].sum()),
        "success_rate": float(df["success"].mean()) if len(df) else 0.0,
        "aggregate_policy": aggregate_only_note(),
    }


def trend_points(df: pd.DataFrame, grain: str = "year", group_by: str | None = "region_txt") -> list[dict]:
    working = df.copy()
    if grain == "month":
        working["period"] = working["year_month"]
    else:
        working["period"] = working["iyear"].astype(str)

    group_cols = ["period"]
    if group_by and group_by in working.columns:
        group_cols.append(group_by)

    grouped = (
        working.groupby(group_cols, dropna=False)
        .agg(
            attacks=("eventid", "count"),
            fatalities=("nkill", "sum"),
            wounded=("nwound", "sum"),
            casualties=("casualties", "sum"),
        )
        .reset_index()
        .sort_values(group_cols)
    )
    if group_by and group_by in working.columns:
        grouped = grouped.rename(columns={group_by: "group"})
    else:
        grouped["group"] = "Global"
    return grouped.to_dict(orient="records")


def distributions(df: pd.DataFrame, limit: int = 12) -> dict[str, list[dict]]:
    fields = {
        "regions": "region_txt",
        "countries": "country_txt",
        "attack_types": "attacktype1_txt",
        "target_types": "targtype1_txt",
        "weapon_types": "weaptype1_txt",
        "groups": "gname",
        "severity": "severity",
    }
    output: dict[str, list[dict]] = {}
    for key, column in fields.items():
        counts = Counter(df[column].fillna("Unknown"))
        output[key] = [
            {"label": str(label), "count": int(count)}
            for label, count in counts.most_common(limit)
            if str(label) != ""
        ]
    return output


def hotspots(df: pd.DataFrame, level: str = "country", limit: int = 50, min_events: int = 5) -> list[dict]:
    if level == "city":
        group_cols = ["country_txt", "city"]
    else:
        group_cols = ["country_txt"]

    geo = df[df["valid_coordinates"]].copy()
    grouped = (
        geo.groupby(group_cols, dropna=False)
        .agg(
            attacks=("eventid", "count"),
            fatalities=("nkill", "sum"),
            wounded=("nwound", "sum"),
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
        )
        .reset_index()
    )
    grouped = grouped[grouped["attacks"] >= min_events]
    grouped["severity_score"] = grouped["fatalities"] * 2 + grouped["wounded"] + grouped["attacks"]
    grouped = grouped.sort_values("severity_score", ascending=False).head(limit)
    records = grouped.to_dict(orient="records")
    for row in records:
        row["level"] = level
        row["name"] = row.get("city") if level == "city" else row.get("country_txt")
        row["aggregate_only"] = True
    return records


def simple_forecasts(df: pd.DataFrame, horizon: int = 12) -> list[dict]:
    monthly = (
        df[df["incident_date"].notna()]
        .groupby(["year_month", "region_txt"])
        .agg(attacks=("eventid", "count"), fatalities=("nkill", "sum"))
        .reset_index()
        .sort_values("year_month")
    )
    if monthly.empty:
        return []

    output: list[dict] = []
    for region, group in monthly.groupby("region_txt"):
        last_period = pd.Period(group["year_month"].max(), freq="M")
        attack_tail = group["attacks"].tail(12)
        fatal_tail = group["fatalities"].tail(12)
        attack_mean = float(attack_tail.mean())
        fatal_mean = float(fatal_tail.mean())
        attack_std = float(attack_tail.std(ddof=0) or 0.0)
        fatal_std = float(fatal_tail.std(ddof=0) or 0.0)
        for step in range(1, horizon + 1):
            period = str(last_period + step)
            output.append(
                {
                    "period": period,
                    "scope": str(region),
                    "metric": "attacks",
                    "prediction": attack_mean,
                    "lower": max(0.0, attack_mean - 1.96 * attack_std),
                    "upper": attack_mean + 1.96 * attack_std,
                    "method": "seasonal-naive-mean",
                }
            )
            output.append(
                {
                    "period": period,
                    "scope": str(region),
                    "metric": "fatalities",
                    "prediction": fatal_mean,
                    "lower": max(0.0, fatal_mean - 1.96 * fatal_std),
                    "upper": fatal_mean + 1.96 * fatal_std,
                    "method": "seasonal-naive-mean",
                }
            )
    return output


def model_catalog() -> list[dict]:
    return [
        {
            "name": "casualty-severity-classifier",
            "type": "supervised-classification",
            "tracker": "Weights & Biases",
            "status": "implemented-trainable",
            "features": ["year", "region", "country", "attack type", "target type", "weapon type"],
        },
        {
            "name": "fatality-regressor",
            "type": "supervised-regression",
            "tracker": "Weights & Biases",
            "status": "planned-trainable",
            "features": ["categoricals", "temporal features", "historical aggregates"],
        },
        {
            "name": "sequence-forecast",
            "type": "deep-learning-time-series",
            "tracker": "Weights & Biases",
            "status": "scaffolded",
            "features": ["monthly sequences", "region embeddings"],
        },
        {
            "name": "rag-chatbot",
            "type": "retrieval-augmented-generation",
            "tracker": "evaluation suite",
            "status": "implemented-local-retrieval",
            "features": ["docs", "model cards", "ethics", "complexity", "aggregate summaries"],
        },
    ]


def predict_severity_rule(payload: dict, reference_df: pd.DataFrame | None = None) -> dict:
    """Score a hypothetical record against the current adaptive severity distribution."""
    fatalities = float(payload.get("nkill", 0) or 0)
    wounded = float(payload.get("nwound", 0) or 0)
    casualties = fatalities + wounded
    if casualties <= 0:
        label = "None"
        percentile = 0.0
    else:
        score = _severity_score(
            pd.DataFrame({"nkill": [fatalities], "nwound": [wounded], "casualties": [casualties]})
        ).iloc[0]
        if reference_df is not None and "severity_score" in reference_df.columns:
            reference = reference_df[reference_df["casualties"].fillna(0).gt(0)]["severity_score"]
            percentile = float(reference.le(score).mean()) if len(reference) else 1.0
        else:
            percentile = 1.0
        label = _label_from_percentile(percentile)

    labels = ["None", "Low", "Medium", "High", "Mass Casualty"]
    probs = {name: 0.03 for name in labels}
    probs[label] = 0.88
    total = sum(probs.values())
    probs = {key: value / total for key, value in probs.items()}
    return {
        "severity": label,
        "severity_score_percentile": percentile,
        "probabilities": probs,
        "model_version": "adaptive-reference-distribution-v2",
        "explanations": [
            "Prediction is scored against the current artifact's adaptive severity-score distribution.",
            "Silver artifact severity labels are assigned by OPTICS density clustering with percentile fallback.",
            "Train the W&B classifier for learned predictions and calibrated probabilities.",
        ],
    }


def clusters(df: pd.DataFrame, limit: int = 8) -> list[dict]:
    profiles = (
        df.groupby(["region_txt", "attacktype1_txt", "weaptype1_txt"])
        .agg(size=("eventid", "count"), fatalities=("nkill", "sum"), wounded=("nwound", "sum"))
        .reset_index()
        .sort_values(["size", "fatalities"], ascending=False)
        .head(limit)
    )
    profiles["cluster_id"] = np.arange(len(profiles))
    profiles["dominant_features"] = profiles.apply(
        lambda row: [row["region_txt"], row["attacktype1_txt"], row["weaptype1_txt"]], axis=1
    )
    return profiles[
        ["cluster_id", "size", "fatalities", "wounded", "dominant_features"]
    ].to_dict(orient="records")
