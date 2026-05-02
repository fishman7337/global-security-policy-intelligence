"""External public-policy source ingestion for the country-year panel."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class WorldBankIndicator:
    """World Bank indicator metadata used by the source fetcher.

    Attributes:
        column: Output column name in the normalized policy panel.
        indicator: World Bank indicator identifier.
        source_id: World Bank source ID.
        label: Human-readable indicator name.
        tier: Analytical tier used in the source registry.
    """

    column: str
    indicator: str
    source_id: int
    label: str
    tier: str


WORLD_BANK_INDICATORS = [
    WorldBankIndicator(
        "government_effectiveness",
        "GOV_WGI_GE.EST",
        3,
        "Government Effectiveness",
        "core-governance",
    ),
    WorldBankIndicator("rule_of_law", "GOV_WGI_RL.EST", 3, "Rule of Law", "core-governance"),
    WorldBankIndicator(
        "control_of_corruption",
        "GOV_WGI_CC.EST",
        3,
        "Control of Corruption",
        "core-governance",
    ),
    WorldBankIndicator(
        "political_stability",
        "GOV_WGI_PV.EST",
        3,
        "Political Stability and Absence of Violence/Terrorism",
        "robustness-only",
    ),
    WorldBankIndicator("voice_accountability", "GOV_WGI_VA.EST", 3, "Voice and Accountability", "robustness"),
    WorldBankIndicator("regulatory_quality", "GOV_WGI_RQ.EST", 3, "Regulatory Quality", "robustness"),
    WorldBankIndicator("population", "SP.POP.TOTL", 2, "Population, total", "development-control"),
    WorldBankIndicator(
        "gdp_per_capita",
        "NY.GDP.PCAP.KD",
        2,
        "GDP per capita, constant local currency",
        "development-control",
    ),
    WorldBankIndicator(
        "urban_population_pct",
        "SP.URB.TOTL.IN.ZS",
        2,
        "Urban population (% of total)",
        "development-control",
    ),
    WorldBankIndicator(
        "unemployment_pct",
        "SL.UEM.TOTL.ZS",
        2,
        "Unemployment, total (% of labor force)",
        "development-control",
    ),
    WorldBankIndicator(
        "life_expectancy",
        "SP.DYN.LE00.IN",
        2,
        "Life expectancy at birth, total",
        "development-control",
    ),
    WorldBankIndicator(
        "internet_users_pct",
        "IT.NET.USER.ZS",
        2,
        "Individuals using the Internet (% of population)",
        "reporting-bias-proxy",
    ),
]


def source_registry() -> list[dict[str, Any]]:
    """Return the public-policy source registry.

    Returns:
        List of source metadata dictionaries.
    """
    return [
        {
            "name": "Global Terrorism Database",
            "tier": "outcome",
            "coverage_used": "1970-2021 local files; policy panel uses 1996-2021",
            "url": "https://www.start.umd.edu/download-global-terrorism-database",
            "role": "Country-year terrorism outcomes and severity burden.",
            "credential_required": False,
        },
        {
            "name": "Worldwide Governance Indicators",
            "tier": "core-governance",
            "coverage_used": "1996-2021",
            "url": "https://datacatalog.worldbank.org/search/dataset/0038026/worldwide-governance-indicators",
            "role": "Government effectiveness, rule of law, and control of corruption.",
            "credential_required": False,
        },
        {
            "name": "World Development Indicators",
            "tier": "development-control",
            "coverage_used": "1996-2021 where available",
            "url": "https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators",
            "role": "Population, GDP per capita, urbanization, unemployment, health, and internet access controls.",
            "credential_required": False,
        },
        {
            "name": "V-Dem",
            "tier": "democracy-robustness",
            "coverage_used": "Optional normalized local file",
            "url": "https://v-dem.net/data/",
            "role": "Democracy indices, regime type, democratization/autocratization episodes.",
            "credential_required": False,
        },
        {
            "name": "UNDP Human Development Index",
            "tier": "development-robustness",
            "coverage_used": "Optional normalized local file",
            "url": "https://hdr.undp.org/data-center/human-development-index",
            "role": "Human-development robustness controls.",
            "credential_required": False,
        },
        {
            "name": "UCDP",
            "tier": "conflict-robustness",
            "coverage_used": "Optional normalized local file",
            "url": "https://ucdp.uu.se/downloads/",
            "role": "Organized-violence controls and conflict-burden robustness.",
            "credential_required": False,
        },
        {
            "name": "Freedom House",
            "tier": "democracy-robustness",
            "coverage_used": "Optional normalized local file",
            "url": "https://freedomhouse.org/report-types/freedom-world",
            "role": "Alternative civil-liberties and political-rights sensitivity checks.",
            "credential_required": False,
        },
        {
            "name": "International IDEA",
            "tier": "democracy-robustness",
            "coverage_used": "Optional normalized local file",
            "url": "https://www.idea.int/data-tools/tools/global-state-democracy-indices",
            "role": "Alternative democracy-performance sensitivity checks.",
            "credential_required": False,
        },
    ]


def fetch_world_bank_panel(
    start_year: int = 1996,
    end_year: int = 2021,
    indicators: list[WorldBankIndicator] | None = None,
    timeout_seconds: int = 30,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Fetch credential-free World Bank panel indicators.

    Args:
        start_year: First year to request.
        end_year: Last year to request.
        indicators: Optional indicator metadata list.
        timeout_seconds: Per-request timeout.

    Returns:
        Tuple of normalized indicator dataframe and fetch-status reports.
    """
    indicators = indicators or WORLD_BANK_INDICATORS
    frames: list[pd.DataFrame] = []
    reports: list[dict[str, Any]] = []
    for indicator in indicators:
        try:
            frame = _fetch_world_bank_indicator(indicator, start_year, end_year, timeout_seconds)
            frames.append(frame)
            reports.append(
                {
                    "column": indicator.column,
                    "indicator": indicator.indicator,
                    "source_id": indicator.source_id,
                    "rows": int(len(frame)),
                    "status": "fetched",
                }
            )
        except Exception as exc:  # pragma: no cover - network failures are environment-specific.
            reports.append(
                {
                    "column": indicator.column,
                    "indicator": indicator.indicator,
                    "source_id": indicator.source_id,
                    "rows": 0,
                    "status": "unavailable",
                    "error": str(exc)[:240],
                }
            )
    return merge_source_frames(frames), reports


def _fetch_world_bank_indicator(
    indicator: WorldBankIndicator,
    start_year: int,
    end_year: int,
    timeout_seconds: int,
) -> pd.DataFrame:
    """Fetch and normalize one World Bank indicator."""
    params = urllib.parse.urlencode(
        {
            "format": "json",
            "per_page": 20000,
            "date": f"{start_year}:{end_year}",
            "source": indicator.source_id,
        }
    )
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator.indicator}?{params}"
    payload = None
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8-sig"))
            break
        except Exception as exc:  # pragma: no cover - depends on remote API behavior.
            last_error = exc
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    if payload is None:
        raise RuntimeError(str(last_error))
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        raise RuntimeError(f"Unexpected World Bank response for {indicator.indicator}")

    rows = []
    for item in payload[1]:
        iso3 = str(item.get("countryiso3code") or "").strip()
        country = item.get("country", {}) or {}
        country_name = str(country.get("value") or "").strip()
        country_id = str(country.get("id") or "").strip()
        if not iso3 and len(country_id) == 3:
            iso3 = country_id
        if len(iso3) != 3:
            continue
        rows.append(
            {
                "iso3": iso3.upper(),
                "country_name_source": country_name,
                "year": int(item["date"]),
                indicator.column: item.get("value"),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=["iso3", "year", "country_name_source", indicator.column])
    frame[indicator.column] = pd.to_numeric(frame[indicator.column], errors="coerce")
    return frame.drop_duplicates(["iso3", "year"])


def load_normalized_local_sources(source_dir: Path | None) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Load normalized optional policy sources from a local directory.

    Args:
        source_dir: Directory containing `.csv`, `.parquet`, or `.xlsx` files.

    Returns:
        Tuple of merged source dataframe and file-status reports.
    """
    if source_dir is None or not source_dir.exists():
        return pd.DataFrame(), []

    frames: list[pd.DataFrame] = []
    reports: list[dict[str, Any]] = []
    for path in sorted(source_dir.glob("*")):
        if path.suffix.lower() not in {".csv", ".parquet", ".xlsx"}:
            continue
        try:
            raw = _read_source_file(path)
            frame = normalize_external_source(raw)
            if frame.empty:
                reports.append({"file": str(path), "rows": 0, "status": "ignored-missing-iso3-year"})
                continue
            frames.append(frame)
            reports.append({"file": str(path), "rows": int(len(frame)), "status": "loaded"})
        except Exception as exc:
            reports.append({"file": str(path), "rows": 0, "status": "unavailable", "error": str(exc)[:240]})
    return merge_source_frames(frames), reports


def normalize_external_source(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize one optional external policy source.

    Args:
        frame: Source dataframe with at least ISO-3 and year fields.

    Returns:
        Normalized dataframe keyed by `iso3` and `year`, or an empty
        dataframe when required keys are absent.
    """
    if frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    rename = {
        "countryiso3code": "iso3",
        "country_text_id": "iso3",
        "country_code": "iso3",
        "iso_code": "iso3",
        "time": "year",
        "iyear": "year",
        "year_num": "year",
        "v2x_polyarchy": "vdem_electoral_democracy",
        "v2x_libdem": "vdem_liberal_democracy",
        "v2x_regime": "vdem_regime_type",
        "hdi_value": "hdi",
        "human_development_index": "hdi",
        "best": "ucdp_best_fatalities",
        "deaths": "ucdp_best_fatalities",
        "total_score": "freedom_house_total",
        "political_rights": "freedom_house_political_rights",
        "civil_liberties": "freedom_house_civil_liberties",
        "press_freedom_score": "press_freedom_score",
    }
    data = data.rename(columns={key: value for key, value in rename.items() if key in data.columns})
    if "iso3" not in data.columns or "year" not in data.columns:
        return pd.DataFrame()
    data["iso3"] = data["iso3"].astype(str).str.upper().str.strip()
    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    data = data[data["iso3"].str.len().eq(3) & data["year"].notna()].copy()
    data["year"] = data["year"].astype(int)
    id_cols = {"iso3", "year", "country_name", "country_name_source"}
    keep = ["iso3", "year", *[col for col in data.columns if col not in id_cols]]
    numeric_cols = [col for col in keep if col not in {"iso3", "year"}]
    for column in numeric_cols:
        if data[column].dtype == object:
            converted = pd.to_numeric(data[column], errors="ignore")
            data[column] = converted
    return data[keep].drop_duplicates(["iso3", "year"])


def merge_source_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Outer-merge source frames on ISO-3 country code and year.

    Args:
        frames: Normalized source dataframes.

    Returns:
        Merged country-year source dataframe.
    """
    frames = [frame for frame in frames if frame is not None and not frame.empty]
    if not frames:
        return pd.DataFrame()
    merged = frames[0].copy()
    for frame in frames[1:]:
        overlap = [col for col in frame.columns if col in merged.columns and col not in {"iso3", "year"}]
        if overlap:
            frame = frame.drop(columns=overlap)
        merged = merged.merge(frame, on=["iso3", "year"], how="outer")
    return merged.drop_duplicates(["iso3", "year"])


def _read_source_file(path: Path) -> pd.DataFrame:
    """Read a supported local source file."""
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".xlsx":
        return pd.read_excel(path)
    return pd.read_csv(path)
