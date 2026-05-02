from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _load_yaml_like(path: Path) -> dict[str, Any]:
    """Load simple YAML through PyYAML when available, else a JSON-compatible fallback."""
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            return json.loads(text)
        raise RuntimeError("Install PyYAML to parse YAML contract files.")


def validate_data_contract(
    df: pd.DataFrame,
    contract_path: Path = Path("configs/data_contract.yaml"),
) -> dict[str, Any]:
    contract = _load_yaml_like(contract_path)
    expected = contract.get("expected", {})
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    min_rows = int(expected.get("min_rows", 0))
    add("min_rows", len(df) >= min_rows, f"Observed {len(df)} rows; expected >= {min_rows}.")

    if expected.get("unique_eventid", False):
        dupes = int(df["eventid"].duplicated().sum()) if "eventid" in df else -1
        add("unique_eventid", dupes == 0, f"Duplicate event IDs: {dupes}.")

    if "iyear" in df:
        year_min = int(df["iyear"].min())
        year_max = int(df["iyear"].max())
        add("year_min", year_min <= int(expected["year_min"]), f"Observed min year {year_min}.")
        add("year_max", year_max >= int(expected["year_max"]), f"Observed max year {year_max}.")

    for column, spec in contract.get("columns", {}).items():
        add(f"column_present:{column}", column in df.columns, f"{column} required by contract.")
        if column not in df.columns:
            continue
        if not spec.get("nullable", True):
            missing = int(df[column].isna().sum())
            add(f"not_null:{column}", missing == 0, f"{column} missing rows: {missing}.")
        if "min" in spec:
            observed = pd.to_numeric(df[column], errors="coerce").min()
            add(f"min:{column}", observed >= spec["min"], f"{column} observed min {observed}.")
        if "max" in spec:
            observed = pd.to_numeric(df[column], errors="coerce").max()
            add(f"max:{column}", observed <= spec["max"], f"{column} observed max {observed}.")
        if "values" in spec:
            invalid = sorted(set(df[column].dropna()) - set(spec["values"]))
            add(f"values:{column}", not invalid, f"Invalid values: {invalid[:10]}.")

    return {
        "contract": contract.get("dataset", "unknown"),
        "version": contract.get("version", "unknown"),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }

