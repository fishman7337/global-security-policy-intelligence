"""Distribution-drift metrics for historical GTD aggregate monitoring."""

from __future__ import annotations

from collections import Counter
from typing import Iterable

import numpy as np
import pandas as pd


def population_stability_index(
    baseline: Iterable[float],
    current: Iterable[float],
    bins: int = 10,
) -> float:
    """Compute population stability index for numeric distributions.

    Args:
        baseline: Reference numeric observations.
        current: Comparison numeric observations.
        bins: Number of baseline-quantile bins.

    Returns:
        PSI score. Larger values indicate stronger distribution shift.
    """
    base = np.asarray(list(baseline), dtype=float)
    curr = np.asarray(list(current), dtype=float)
    base = base[~np.isnan(base)]
    curr = curr[~np.isnan(curr)]
    if len(base) == 0 or len(curr) == 0:
        return 0.0
    quantiles = np.unique(np.quantile(base, np.linspace(0, 1, bins + 1)))
    if len(quantiles) <= 2:
        quantiles = np.linspace(min(base.min(), curr.min()), max(base.max(), curr.max()) + 1, bins + 1)
    base_counts, _ = np.histogram(base, bins=quantiles)
    curr_counts, _ = np.histogram(curr, bins=quantiles)
    base_pct = np.maximum(base_counts / max(base_counts.sum(), 1), 1e-6)
    curr_pct = np.maximum(curr_counts / max(curr_counts.sum(), 1), 1e-6)
    return float(np.sum((curr_pct - base_pct) * np.log(curr_pct / base_pct)))


def categorical_js_divergence(baseline: Iterable[str], current: Iterable[str]) -> float:
    """Compute Jensen-Shannon divergence between categorical distributions.

    Args:
        baseline: Reference category values.
        current: Comparison category values.

    Returns:
        Symmetric divergence score between the two empirical distributions.
    """
    base_counts = Counter(str(x) for x in baseline)
    curr_counts = Counter(str(x) for x in current)
    keys = sorted(set(base_counts) | set(curr_counts))
    base_total = sum(base_counts.values()) or 1
    curr_total = sum(curr_counts.values()) or 1
    p = np.array([base_counts[key] / base_total for key in keys], dtype=float)
    q = np.array([curr_counts[key] / curr_total for key in keys], dtype=float)
    m = 0.5 * (p + q)

    def kl(a: np.ndarray, b: np.ndarray) -> float:
        """Return KL divergence for non-zero probability entries."""
        mask = a > 0
        return float(np.sum(a[mask] * np.log(a[mask] / np.maximum(b[mask], 1e-12))))

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def drift_report(
    df: pd.DataFrame,
    split_year: int = 2014,
    numeric_columns: list[str] | None = None,
    categorical_columns: list[str] | None = None,
) -> dict:
    """Build a compact drift report before and after a split year.

    Args:
        df: Cleaned incident dataframe with an `iyear` column.
        split_year: First year assigned to the current comparison period.
        numeric_columns: Numeric columns to score with PSI.
        categorical_columns: Categorical columns to score with JS divergence.

    Returns:
        JSON-serializable drift report with per-column scores and severity.
    """
    numeric_columns = numeric_columns or ["nkill", "nwound", "casualties"]
    categorical_columns = categorical_columns or [
        "region_txt",
        "attacktype1_txt",
        "targtype1_txt",
        "weaptype1_txt",
    ]
    baseline = df[df["iyear"] < split_year]
    current = df[df["iyear"] >= split_year]
    numeric = {
        column: population_stability_index(baseline[column], current[column])
        for column in numeric_columns
        if column in df.columns
    }
    categorical = {
        column: categorical_js_divergence(baseline[column], current[column])
        for column in categorical_columns
        if column in df.columns
    }
    all_scores = [*numeric.values(), *categorical.values()]
    max_score = max(all_scores) if all_scores else 0.0
    return {
        "split_year": split_year,
        "baseline_rows": int(len(baseline)),
        "current_rows": int(len(current)),
        "numeric_psi": numeric,
        "categorical_js": categorical,
        "max_score": float(max_score),
        "severity": "high" if max_score > 0.25 else "medium" if max_score > 0.1 else "low",
    }
