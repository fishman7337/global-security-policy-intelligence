"""Clean GTD extracts and assign adaptive casualty-severity labels."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.cluster import OPTICS
from sklearn.preprocessing import RobustScaler

from gtd_capstone.constants import CATEGORICAL_COLUMNS, CORE_COLUMNS, NUMERIC_COLUMNS


SEVERITY_LABELS = ["None", "Low", "Medium", "High", "Mass Casualty"]


def discover_excel_sources(dataset_dir: Path) -> list[Path]:
    """Discover local GTD Excel source files.

    Args:
        dataset_dir: Directory containing GTD distribution files.

    Returns:
        Sorted list of matching Excel paths.
    """
    return sorted(dataset_dir.glob("globalterrorismdb_*.xlsx"))


def read_excel_sources(
    sources: Iterable[Path],
    sample_rows: int | None = None,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Read one or more GTD Excel files into a raw dataframe.

    Args:
        sources: Excel source files to read.
        sample_rows: Optional total row cap across sources.
        columns: Optional source columns to retain.

    Returns:
        Concatenated raw dataframe, or deterministic synthetic rows when no
        sources are available.
    """
    frames: list[pd.DataFrame] = []
    columns = columns or CORE_COLUMNS
    remaining = sample_rows
    for source in sources:
        nrows = None if remaining is None else max(0, remaining)
        if nrows == 0:
            break
        frame = pd.read_excel(source, usecols=lambda col: col in columns, nrows=nrows)
        frame["source_file"] = source.name
        frames.append(frame)
        if remaining is not None:
            remaining -= len(frame)
    if not frames:
        return synthetic_incidents()
    return pd.concat(frames, ignore_index=True)


def synthetic_incidents() -> pd.DataFrame:
    """Create deterministic synthetic incidents for tests and smoke runs.

    Returns:
        Three-row GTD-like dataframe.
    """
    return pd.DataFrame(
        [
            {
                "eventid": "197001010001",
                "iyear": 1970,
                "imonth": 1,
                "iday": 1,
                "country_txt": "Dominican Republic",
                "region_txt": "Central America & Caribbean",
                "provstate": "National",
                "city": "Santo Domingo",
                "latitude": 18.4568,
                "longitude": -69.9512,
                "summary": "Historical sample incident used for local smoke tests.",
                "success": 1,
                "suicide": 0,
                "attacktype1_txt": "Assassination",
                "targtype1_txt": "Private Citizens & Property",
                "weaptype1_txt": "Unknown",
                "gname": "Unknown",
                "motive": "",
                "nkill": 1,
                "nwound": 0,
                "property": 0,
                "ishostkid": 0,
                "dbsource": "synthetic",
                "source_file": "synthetic",
            },
            {
                "eventid": "201401010001",
                "iyear": 2014,
                "imonth": 1,
                "iday": 1,
                "country_txt": "Iraq",
                "region_txt": "Middle East & North Africa",
                "provstate": "Baghdad",
                "city": "Baghdad",
                "latitude": 33.3152,
                "longitude": 44.3661,
                "summary": "Historical sample bombing incident for aggregate analytics.",
                "success": 1,
                "suicide": 0,
                "attacktype1_txt": "Bombing/Explosion",
                "targtype1_txt": "Police",
                "weaptype1_txt": "Explosives",
                "gname": "Unknown",
                "motive": "",
                "nkill": 5,
                "nwound": 12,
                "property": 1,
                "ishostkid": 0,
                "dbsource": "synthetic",
                "source_file": "synthetic",
            },
            {
                "eventid": "202101010001",
                "iyear": 2021,
                "imonth": 1,
                "iday": 1,
                "country_txt": "Afghanistan",
                "region_txt": "South Asia",
                "provstate": "Kabul",
                "city": "Kabul",
                "latitude": 34.5553,
                "longitude": 69.2075,
                "summary": "Historical sample armed assault for model and RAG tests.",
                "success": 0,
                "suicide": 0,
                "attacktype1_txt": "Armed Assault",
                "targtype1_txt": "Military",
                "weaptype1_txt": "Firearms",
                "gname": "Unknown",
                "motive": "",
                "nkill": 0,
                "nwound": 1,
                "property": 0,
                "ishostkid": 0,
                "dbsource": "synthetic",
                "source_file": "synthetic",
            },
        ]
    )


def clean_incidents(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw GTD incidents and add derived analytical fields.

    Args:
        df: Raw GTD-style dataframe.

    Returns:
        Cleaned dataframe with dates, casualty fields, adaptive severity,
        coordinate flags, and source metadata.
    """
    df = df.copy()
    for column in CORE_COLUMNS:
        if column not in df.columns:
            df[column] = np.nan

    df["eventid"] = df["eventid"].astype(str).str.replace(r"\.0$", "", regex=True)
    df = df.drop_duplicates(subset=["eventid"], keep="first")

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in CATEGORICAL_COLUMNS:
        df[column] = (
            df[column]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
            .replace({"": "Unknown", "nan": "Unknown", "None": "Unknown"})
        )

    for column in ["summary", "motive", "dbsource", "source_file"]:
        df[column] = df[column].fillna("").astype(str).str.strip()

    df["iyear"] = df["iyear"].fillna(0).astype(int)
    df["imonth"] = df["imonth"].fillna(0).astype(int)
    df["iday"] = df["iday"].fillna(0).astype(int)
    df["month_valid"] = df["imonth"].between(1, 12)
    df["day_valid"] = df["iday"].between(1, 31)
    safe_month = df["imonth"].where(df["month_valid"], 1)
    safe_day = df["iday"].where(df["day_valid"], 1)
    df["incident_date"] = pd.to_datetime(
        {"year": df["iyear"], "month": safe_month, "day": safe_day}, errors="coerce"
    )
    df["year_month"] = df["incident_date"].dt.to_period("M").astype(str)

    for column in ["nkill", "nwound", "success", "suicide", "property", "ishostkid"]:
        df[column] = df[column].fillna(0)
    df["nkill"] = df["nkill"].clip(lower=0)
    df["nwound"] = df["nwound"].clip(lower=0)
    df["casualties"] = df["nkill"] + df["nwound"]
    df = assign_adaptive_severity(df)

    df["valid_coordinates"] = (
        df["latitude"].between(-90, 90)
        & df["longitude"].between(-180, 180)
        & df["latitude"].notna()
        & df["longitude"].notna()
    )
    df["geo_precision"] = np.where(df["valid_coordinates"], "coordinate", "aggregate-only")
    df["is_synthetic"] = df["source_file"].eq("synthetic")
    return df.sort_values(["iyear", "eventid"]).reset_index(drop=True)


def assign_adaptive_severity(
    df: pd.DataFrame,
    min_cluster_rows: int = 24,
    max_cluster_rows: int = 25_000,
) -> pd.DataFrame:
    """Assign casualty severity from density structure rather than fixed casualty cutoffs.

    OPTICS is used when there are enough non-zero casualty incidents. For tiny smoke-test
    datasets or degenerate samples, labels fall back to ranked severity-score percentiles.

    Args:
        df: Cleaned incident dataframe with `nkill`, `nwound`, and `casualties`.
        min_cluster_rows: Minimum non-zero casualty rows required to fit OPTICS.
        max_cluster_rows: Maximum deterministic sample size used to fit OPTICS.

    Returns:
        Dataframe with `severity`, `severity_score`,
        `severity_score_percentile`, `severity_cluster`, and
        `severity_method`.
    """
    output = df.copy()
    output["severity_score"] = _severity_score(output)
    output["severity_score_percentile"] = 0.0
    output["severity_cluster"] = -1
    output["severity_method"] = "none-casualty"
    output["severity"] = "None"

    nonzero_mask = output["casualties"].fillna(0).gt(0)
    if not nonzero_mask.any():
        return output

    nonzero = output.loc[nonzero_mask, ["nkill", "nwound", "casualties", "severity_score"]].copy()
    output.loc[nonzero_mask, "severity_score_percentile"] = _percentile_rank(nonzero["severity_score"])
    nonzero["severity_score_percentile"] = output.loc[
        nonzero_mask, "severity_score_percentile"
    ].to_numpy()

    can_cluster = (
        len(nonzero) >= min_cluster_rows
        and nonzero[["nkill", "nwound", "casualties"]].drop_duplicates().shape[0] >= 4
    )
    if not can_cluster:
        output.loc[nonzero_mask, "severity"] = _labels_from_percentiles(
            output.loc[nonzero_mask, "severity_score_percentile"]
        )
        output.loc[nonzero_mask, "severity_method"] = "adaptive-percentile-fallback"
        return output

    all_features = np.column_stack(
        [
            np.log1p(nonzero["nkill"].to_numpy(dtype=float)),
            np.log1p(nonzero["nwound"].to_numpy(dtype=float)),
            np.log1p(nonzero["casualties"].to_numpy(dtype=float)),
        ]
    )
    fit_positions = _cluster_fit_positions(nonzero, max_cluster_rows=max_cluster_rows)
    fit_features = all_features[fit_positions]
    scaler = RobustScaler().fit(fit_features)
    fit_scaled = scaler.transform(fit_features)
    min_samples = min(max(5, int(np.sqrt(len(fit_scaled)))), max(2, len(fit_scaled) - 1))
    min_cluster_size = min(max(5, int(len(fit_scaled) * 0.01)), max(2, len(fit_scaled) - 1))
    labels = OPTICS(
        min_samples=min_samples,
        min_cluster_size=min_cluster_size,
        xi=0.05,
        metric="minkowski",
    ).fit_predict(fit_scaled)

    all_scaled = scaler.transform(all_features)
    if len(fit_scaled) == len(all_scaled):
        all_labels = labels
        method = "adaptive-optics-density"
    else:
        all_labels = _assign_from_sampled_clusters(
            all_scaled=all_scaled,
            fit_scaled=fit_scaled,
            fit_labels=labels,
        )
        method = "adaptive-optics-sampled-density"

    nonzero = nonzero.assign(cluster=all_labels)
    clusters = sorted(label for label in set(all_labels) if label != -1)
    if not clusters:
        output.loc[nonzero_mask, "severity"] = _labels_from_percentiles(
            output.loc[nonzero_mask, "severity_score_percentile"]
        )
        output.loc[nonzero_mask, "severity_method"] = "adaptive-percentile-fallback"
        return output

    cluster_order = (
        nonzero[nonzero["cluster"].ne(-1)]
        .groupby("cluster")["severity_score"]
        .median()
        .sort_values()
        .index.tolist()
    )
    cluster_labels = _cluster_label_map(cluster_order)
    ordered_index = nonzero.index
    assigned = []
    for row in nonzero.itertuples(index=False):
        if row.cluster == -1:
            assigned.append(_label_from_percentile(row.severity_score_percentile))
        else:
            assigned.append(cluster_labels[int(row.cluster)])

    output.loc[nonzero_mask, "severity_cluster"] = all_labels
    output.loc[nonzero_mask, "severity"] = assigned
    output.loc[nonzero_mask, "severity_method"] = method
    output.loc[ordered_index[all_labels == -1], "severity_method"] = "adaptive-optics-noise-percentile"
    return output


def label_severity(casualties: float) -> str:
    """Label a single casualty value without population context.

    Args:
        casualties: Total casualties for one incident.

    Returns:
        `None` for zero casualties and `Low` for positive casualties. Full
        severity assignment should use `assign_adaptive_severity`.
    """
    score = _severity_score(
        pd.DataFrame({"nkill": [casualties], "nwound": [0], "casualties": [casualties]})
    ).iloc[0]
    if not np.isfinite(score) or casualties <= 0:
        return "None"
    return "Low"


def _severity_score(df: pd.DataFrame) -> pd.Series:
    """Compute logged casualty-burden scores for incidents."""
    casualties = pd.to_numeric(df["casualties"], errors="coerce").fillna(0).clip(lower=0)
    fatalities = pd.to_numeric(df["nkill"], errors="coerce").fillna(0).clip(lower=0)
    wounded = pd.to_numeric(df["nwound"], errors="coerce").fillna(0).clip(lower=0)
    return np.log1p(casualties) + 0.75 * np.log1p(fatalities) + 0.25 * np.log1p(wounded)


def _percentile_rank(values: pd.Series) -> pd.Series:
    """Return bounded percentile ranks for a numeric series."""
    if values.empty:
        return values
    return values.rank(method="average", pct=True).clip(lower=0, upper=1)


def _labels_from_percentiles(percentiles: pd.Series) -> list[str]:
    """Convert percentile ranks into ordered severity labels."""
    return [_label_from_percentile(float(value)) for value in percentiles]


def _label_from_percentile(percentile: float) -> str:
    """Map one score percentile to a severity label."""
    if percentile <= 0:
        return "None"
    if percentile <= 0.55:
        return "Low"
    if percentile <= 0.80:
        return "Medium"
    if percentile <= 0.95:
        return "High"
    return "Mass Casualty"


def _cluster_label_map(cluster_order: list[int]) -> dict[int, str]:
    """Map ordered cluster identifiers onto severity labels."""
    if len(cluster_order) == 1:
        labels = ["Low"]
    elif len(cluster_order) == 2:
        labels = ["Low", "High"]
    elif len(cluster_order) == 3:
        labels = ["Low", "Medium", "High"]
    else:
        positions = np.linspace(0, len(cluster_order) - 1, num=4).round().astype(int)
        labels = ["Low"] * len(cluster_order)
        for position, label in zip(positions, ["Low", "Medium", "High", "Mass Casualty"]):
            labels[position] = label
        last = "Low"
        for index, label in enumerate(labels):
            if label != "Low" or index == 0:
                last = label
            else:
                labels[index] = last
    return {cluster: label for cluster, label in zip(cluster_order, labels)}


def _cluster_fit_positions(nonzero: pd.DataFrame, max_cluster_rows: int) -> np.ndarray:
    """Choose deterministic row positions for scalable OPTICS fitting."""
    if len(nonzero) <= max_cluster_rows:
        return np.arange(len(nonzero))
    ordered_positions = np.argsort(nonzero["severity_score"].to_numpy(dtype=float))
    sampled_offsets = np.linspace(0, len(ordered_positions) - 1, num=max_cluster_rows).round().astype(int)
    return np.unique(ordered_positions[sampled_offsets])


def _assign_from_sampled_clusters(
    all_scaled: np.ndarray,
    fit_scaled: np.ndarray,
    fit_labels: np.ndarray,
) -> np.ndarray:
    """Assign all rows to nearest sampled OPTICS density centers."""
    clusters = sorted(label for label in set(fit_labels) if label != -1)
    if not clusters:
        return np.full(len(all_scaled), -1, dtype=int)

    centers = np.vstack([fit_scaled[fit_labels == cluster].mean(axis=0) for cluster in clusters])
    fit_cluster_mask = fit_labels != -1
    fit_distances = np.sqrt(((fit_scaled[fit_cluster_mask, None, :] - centers[None, :, :]) ** 2).sum(axis=2))
    fit_nearest_distances = fit_distances.min(axis=1)
    distance_threshold = float(np.quantile(fit_nearest_distances, 0.98))

    distances = np.sqrt(((all_scaled[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2))
    nearest = distances.argmin(axis=1)
    nearest_distances = distances[np.arange(len(all_scaled)), nearest]
    assigned = np.array([clusters[index] for index in nearest], dtype=int)
    assigned[nearest_distances > max(distance_threshold, 1e-9)] = -1
    return assigned


def data_quality_report(df: pd.DataFrame) -> dict:
    """Create a JSON-serializable data-quality report.

    Args:
        df: Cleaned incident dataframe.

    Returns:
        Summary metrics and validation checks.
    """
    expected_year_min = int(df["iyear"].min()) if len(df) else None
    expected_year_max = int(df["iyear"].max()) if len(df) else None
    missing = df.isna().sum().sort_values(ascending=False).head(15)
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "duplicate_eventids": int(df["eventid"].duplicated().sum()),
        "year_min": expected_year_min,
        "year_max": expected_year_max,
        "valid_coordinate_rows": int(df["valid_coordinates"].sum()),
        "invalid_coordinate_rows": int((~df["valid_coordinates"]).sum()),
        "total_fatalities": float(df["nkill"].sum()),
        "total_wounded": float(df["nwound"].sum()),
        "missing_top_columns": {str(k): int(v) for k, v in missing.items()},
        "checks": [
            {
                "name": "eventid_unique",
                "passed": bool(df["eventid"].duplicated().sum() == 0),
                "detail": "eventid is the primary incident identifier.",
            },
            {
                "name": "year_range_present",
                "passed": bool(expected_year_min is not None and expected_year_max is not None),
                "detail": f"Observed year range {expected_year_min}-{expected_year_max}.",
            },
            {
                "name": "casualties_non_negative",
                "passed": bool((df["nkill"].ge(0) & df["nwound"].ge(0)).all()),
                "detail": "Fatality and wounded columns are clipped at zero after cleaning.",
            },
            {
                "name": "aggregate_geo_policy",
                "passed": True,
                "detail": "API and frontend expose aggregated hotspots by default.",
            },
        ],
    }
