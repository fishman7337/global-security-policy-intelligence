"""Causal-policy model helpers for country-year GTD panels."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


POLICY_OUTCOMES = [
    "log_casualties",
    "log_attacks",
    "high_severity_share",
    "severity_burden_index",
]


def run_policy_models(panel: pd.DataFrame) -> dict[str, Any]:
    """Estimate the primary fixed-effects policy models.

    Args:
        panel: Country-year policy panel with outcomes and lagged covariates.

    Returns:
        JSON-serializable model result bundle.
    """
    models = [
        _fit_fixed_effects(panel, outcome=outcome, predictor="governance_capacity_lag1")
        for outcome in POLICY_OUTCOMES
    ]
    return {
        "research_design": (
            "Country and year fixed effects with one-year lagged governance capacity. "
            "Interpretation is cautious and associational unless a stronger quasi-experimental "
            "design is supplied."
        ),
        "primary_predictor": "governance_capacity_lag1",
        "models": models,
        "limitations": [
            "Open-source terrorism event data are vulnerable to reporting and media-access bias.",
            "WGI political stability is excluded from the main governance index because it overlaps with violence.",
            "Fixed effects reduce many confounds but do not by themselves prove causality.",
        ],
    }


def _fit_fixed_effects(
    panel: pd.DataFrame,
    outcome: str,
    predictor: str,
    minimum_rows: int = 40,
    minimum_countries: int = 5,
) -> dict[str, Any]:
    """Fit one country-year fixed-effects model when data are sufficient."""
    controls = _available_controls(panel)
    terms = [predictor, *controls]
    required = ["iso3", "year", outcome, *terms]
    missing = [column for column in required if column not in panel.columns]
    formula = f"{outcome} ~ {' + '.join(terms)} + C(iso3) + C(year)"
    if missing:
        return _skipped(outcome, predictor, formula, f"Missing columns: {', '.join(missing)}")

    data = panel[required].replace([np.inf, -np.inf], np.nan).dropna().copy()
    country_count = int(data["iso3"].nunique()) if "iso3" in data else 0
    if len(data) < minimum_rows or country_count < minimum_countries:
        return _skipped(
            outcome,
            predictor,
            formula,
            f"Insufficient complete rows for fixed effects ({len(data)} rows, {country_count} countries).",
        )

    try:
        import statsmodels.formula.api as smf

        fit = smf.ols(formula=formula, data=data)
        if country_count >= 3:
            result = fit.fit(cov_type="cluster", cov_kwds={"groups": data["iso3"]})
            covariance = "clustered-by-country"
        else:
            result = fit.fit(cov_type="HC1")
            covariance = "HC1"
        conf = result.conf_int().loc[predictor].tolist()
        coefficient = float(result.params[predictor])
        return {
            "name": f"{predictor}_on_{outcome}",
            "status": "estimated",
            "outcome": outcome,
            "predictor": predictor,
            "coefficient": coefficient,
            "std_error": float(result.bse[predictor]),
            "p_value": float(result.pvalues[predictor]),
            "conf_low": float(conf[0]),
            "conf_high": float(conf[1]),
            "nobs": int(result.nobs),
            "countries": country_count,
            "year_min": int(data["year"].min()),
            "year_max": int(data["year"].max()),
            "controls": controls,
            "formula": formula,
            "covariance": covariance,
            "interpretation": _interpretation(coefficient, outcome),
        }
    except Exception as exc:
        return _skipped(outcome, predictor, formula, f"Estimation failed: {str(exc)[:260]}")


def build_event_study(
    panel: pd.DataFrame,
    event_column: str = "autocratization_episode",
    outcome: str = "severity_burden_index",
    window: int = 5,
) -> dict[str, Any]:
    """Build a descriptive event-study series around policy events.

    Args:
        panel: Country-year policy panel.
        event_column: Binary or numeric event indicator column.
        outcome: Outcome column to summarize around event timing.
        window: Lead/lag window around the first event per country.

    Returns:
        JSON-serializable event-study payload.
    """
    if event_column not in panel.columns:
        return {
            "status": "unavailable",
            "event_column": event_column,
            "outcome": outcome,
            "window": window,
            "points": [],
            "note": "No V-Dem regime transformation event column is available in the current policy panel.",
        }
    required = ["iso3", "year", outcome, event_column]
    data = panel[required].dropna(subset=["iso3", "year", outcome]).copy()
    events = (
        data[data[event_column].fillna(0).astype(float).gt(0)]
        .sort_values(["iso3", "year"])
        .drop_duplicates("iso3")[["iso3", "year"]]
        .rename(columns={"year": "event_year"})
    )
    if events.empty:
        return {
            "status": "unavailable",
            "event_column": event_column,
            "outcome": outcome,
            "window": window,
            "points": [],
            "note": "No regime transformation events were found in the current panel.",
        }
    study = data.merge(events, on="iso3", how="inner")
    study["relative_year"] = study["year"] - study["event_year"]
    study = study[study["relative_year"].between(-window, window)]
    points = (
        study.groupby("relative_year")
        .agg(mean_outcome=(outcome, "mean"), observations=(outcome, "size"), countries=("iso3", "nunique"))
        .reset_index()
        .sort_values("relative_year")
    )
    return {
        "status": "estimated",
        "event_column": event_column,
        "outcome": outcome,
        "window": window,
        "event_countries": int(events["iso3"].nunique()),
        "points": points.to_dict(orient="records"),
        "note": "Descriptive event-study means around the first observed event per country.",
    }


def _available_controls(panel: pd.DataFrame) -> list[str]:
    """Return model controls with enough complete observations."""
    candidates = [
        "log_population_lag1",
        "log_gdp_per_capita_lag1",
        "urban_population_pct_lag1",
        "unemployment_pct_lag1",
        "internet_users_pct_lag1",
        "ucdp_best_fatalities_lag1",
    ]
    available = []
    for column in candidates:
        if column in panel.columns and panel[column].notna().sum() >= 40:
            available.append(column)
    return available


def _skipped(outcome: str, predictor: str, formula: str, reason: str) -> dict[str, Any]:
    """Return a standard skipped-model payload."""
    return {
        "name": f"{predictor}_on_{outcome}",
        "status": "skipped",
        "outcome": outcome,
        "predictor": predictor,
        "formula": formula,
        "reason": reason,
    }


def _interpretation(coefficient: float, outcome: str) -> str:
    """Create cautious policy interpretation text for one coefficient."""
    direction = "lower" if coefficient < 0 else "higher"
    return (
        f"In this fixed-effects specification, higher lagged governance capacity is associated "
        f"with {direction} {outcome}. This is a cautious policy-research association, not an "
        "operational forecast or standalone causal proof."
    )
