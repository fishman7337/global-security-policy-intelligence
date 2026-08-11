"""Feature-store specification loading and dataframe materialization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from gtd_capstone.contracts import _load_yaml_like


def load_feature_spec(path: Path = Path("configs/feature_store.yaml")) -> dict[str, Any]:
    """Load the versioned feature-store specification from disk."""
    return _load_yaml_like(path)


def materialize_feature_set(
    df: pd.DataFrame,
    feature_set: str = "incident_core_v1",
    spec_path: Path = Path("configs/feature_store.yaml"),
) -> pd.DataFrame:
    """Select a declared feature set and attach leakage metadata.

    Args:
        df: Curated incident dataframe.
        feature_set: Named feature-set definition to materialize.
        spec_path: Feature-store specification path.

    Returns:
        A copied dataframe containing available entity, feature, and label columns.

    """
    spec = load_feature_spec(spec_path)
    definition = spec["feature_sets"][feature_set]
    entity = definition["entity"]
    columns = [entity, *definition.get("features", []), *definition.get("labels", [])]
    present = [column for column in columns if column in df.columns]
    frame = df[present].copy()
    leakage = set(definition.get("leakage_blocklist", []))
    frame.attrs["leakage_blocklist"] = sorted(leakage)
    frame.attrs["feature_set"] = feature_set
    return frame
