"""Build country-year public-policy panels from GTD and external sources."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from gtd_capstone.config import Settings, get_settings
from gtd_capstone.policy.methods import build_event_study, run_policy_models
from gtd_capstone.policy.sources import (
    fetch_world_bank_panel,
    load_normalized_local_sources,
    merge_source_frames,
    source_registry,
)
from gtd_capstone.safety import aggregate_only_note


MAIN_GOVERNANCE_COLUMNS = ["government_effectiveness", "rule_of_law", "control_of_corruption"]
ROBUSTNESS_COLUMNS = [
    "political_stability",
    "voice_accountability",
    "regulatory_quality",
    "vdem_electoral_democracy",
    "hdi",
    "freedom_house_total",
    "ucdp_best_fatalities",
    "press_freedom_score",
]
CONTROL_COLUMNS = [
    "population",
    "gdp_per_capita",
    "urban_population_pct",
    "unemployment_pct",
    "life_expectancy",
    "internet_users_pct",
]

COUNTRY_ISO_OVERRIDES = {
    "afghanistan": "AFG",
    "albania": "ALB",
    "algeria": "DZA",
    "angola": "AGO",
    "argentina": "ARG",
    "armenia": "ARM",
    "australia": "AUS",
    "austria": "AUT",
    "azerbaijan": "AZE",
    "bahrain": "BHR",
    "bangladesh": "BGD",
    "belarus": "BLR",
    "belgium": "BEL",
    "bolivia": "BOL",
    "bosnia-herzegovina": "BIH",
    "bosnia and herzegovina": "BIH",
    "brazil": "BRA",
    "brunei": "BRN",
    "bulgaria": "BGR",
    "burkina faso": "BFA",
    "burundi": "BDI",
    "cambodia": "KHM",
    "cameroon": "CMR",
    "canada": "CAN",
    "central african republic": "CAF",
    "chad": "TCD",
    "chile": "CHL",
    "china": "CHN",
    "colombia": "COL",
    "democratic republic of the congo": "COD",
    "republic of the congo": "COG",
    "costa rica": "CRI",
    "croatia": "HRV",
    "cuba": "CUB",
    "cyprus": "CYP",
    "czech republic": "CZE",
    "denmark": "DNK",
    "dominican republic": "DOM",
    "east timor": "TLS",
    "ecuador": "ECU",
    "egypt": "EGY",
    "el salvador": "SLV",
    "eritrea": "ERI",
    "estonia": "EST",
    "ethiopia": "ETH",
    "finland": "FIN",
    "france": "FRA",
    "georgia": "GEO",
    "germany": "DEU",
    "ghana": "GHA",
    "greece": "GRC",
    "guatemala": "GTM",
    "guinea": "GIN",
    "haiti": "HTI",
    "honduras": "HND",
    "hungary": "HUN",
    "india": "IND",
    "indonesia": "IDN",
    "iran": "IRN",
    "iraq": "IRQ",
    "ireland": "IRL",
    "israel": "ISR",
    "italy": "ITA",
    "ivory coast": "CIV",
    "japan": "JPN",
    "jordan": "JOR",
    "kazakhstan": "KAZ",
    "kenya": "KEN",
    "kosovo": "XKX",
    "kuwait": "KWT",
    "kyrgyzstan": "KGZ",
    "laos": "LAO",
    "latvia": "LVA",
    "lebanon": "LBN",
    "liberia": "LBR",
    "libya": "LBY",
    "lithuania": "LTU",
    "macedonia": "MKD",
    "madagascar": "MDG",
    "malawi": "MWI",
    "malaysia": "MYS",
    "mali": "MLI",
    "mexico": "MEX",
    "moldova": "MDA",
    "morocco": "MAR",
    "mozambique": "MOZ",
    "myanmar": "MMR",
    "nepal": "NPL",
    "netherlands": "NLD",
    "new zealand": "NZL",
    "nicaragua": "NIC",
    "niger": "NER",
    "nigeria": "NGA",
    "north korea": "PRK",
    "norway": "NOR",
    "pakistan": "PAK",
    "panama": "PAN",
    "papua new guinea": "PNG",
    "paraguay": "PRY",
    "peru": "PER",
    "philippines": "PHL",
    "poland": "POL",
    "portugal": "PRT",
    "qatar": "QAT",
    "romania": "ROU",
    "russia": "RUS",
    "rwanda": "RWA",
    "saudi arabia": "SAU",
    "senegal": "SEN",
    "serbia": "SRB",
    "sierra leone": "SLE",
    "singapore": "SGP",
    "slovak republic": "SVK",
    "slovakia": "SVK",
    "slovenia": "SVN",
    "somalia": "SOM",
    "south africa": "ZAF",
    "south korea": "KOR",
    "south sudan": "SSD",
    "spain": "ESP",
    "sri lanka": "LKA",
    "sudan": "SDN",
    "sweden": "SWE",
    "switzerland": "CHE",
    "syria": "SYR",
    "taiwan": "TWN",
    "tajikistan": "TJK",
    "tanzania": "TZA",
    "thailand": "THA",
    "tunisia": "TUN",
    "turkey": "TUR",
    "uganda": "UGA",
    "ukraine": "UKR",
    "united arab emirates": "ARE",
    "united kingdom": "GBR",
    "united states": "USA",
    "uruguay": "URY",
    "uzbekistan": "UZB",
    "venezuela": "VEN",
    "vietnam": "VNM",
    "west bank and gaza strip": "PSE",
    "yemen": "YEM",
    "zambia": "ZMB",
    "zimbabwe": "ZWE",
}


def build_policy_panel(
    incidents: pd.DataFrame,
    external_sources: pd.DataFrame | None = None,
    start_year: int = 1996,
    end_year: int = 2021,
) -> pd.DataFrame:
    """Build a merged country-year policy panel.

    Args:
        incidents: Cleaned incident-level GTD dataframe.
        external_sources: Optional normalized source dataframe keyed by
            `iso3` and `year`.
        start_year: First analysis year to include.
        end_year: Last analysis year to include.

    Returns:
        Balanced country-year panel with outcomes, covariates, lags, and
        completeness flags.
    """
    outcomes = aggregate_gtd_country_year(incidents, start_year=start_year, end_year=end_year)
    external = external_sources.copy() if external_sources is not None else pd.DataFrame()
    if not external.empty:
        external["iso3"] = external["iso3"].astype(str).str.upper().str.strip()
        external["year"] = pd.to_numeric(external["year"], errors="coerce").astype("Int64")
        external = external[external["year"].notna()].copy()
        external["year"] = external["year"].astype(int)
        outcomes = outcomes.merge(external, on=["iso3", "year"], how="left")

    panel = add_policy_features(outcomes)
    return panel.sort_values(["iso3", "year"]).reset_index(drop=True)


def aggregate_gtd_country_year(
    incidents: pd.DataFrame,
    start_year: int = 1996,
    end_year: int = 2021,
) -> pd.DataFrame:
    """Aggregate incident-level GTD data into country-year outcomes.

    Args:
        incidents: Cleaned incident dataframe.
        start_year: First year to include.
        end_year: Last year to include.

    Returns:
        Balanced country-year dataframe with terrorism outcome measures.
    """
    df = incidents.copy()
    df = df[df["iyear"].between(start_year, end_year)].copy()
    if df.empty:
        return pd.DataFrame()
    df["iso3"] = df["country_txt"].map(country_to_iso3)
    df["country_key"] = df["iso3"].fillna(df["country_txt"].map(_normalized_country))
    df["high_severity_flag"] = df["severity"].isin(["High", "Mass Casualty"]).astype(int)
    df["mass_casualty_flag"] = df["severity"].eq("Mass Casualty").astype(int)

    grouped = (
        df.groupby(["country_key", "country_txt", "region_txt", "iso3", "iyear"], dropna=False)
        .agg(
            attacks=("eventid", "count"),
            fatalities=("nkill", "sum"),
            wounded=("nwound", "sum"),
            casualties=("casualties", "sum"),
            high_severity_count=("high_severity_flag", "sum"),
            mass_casualty_count=("mass_casualty_flag", "sum"),
        )
        .reset_index()
        .rename(columns={"iyear": "year"})
    )
    country_meta = (
        grouped.sort_values(["country_key", "attacks"], ascending=[True, False])
        .drop_duplicates("country_key")[["country_key", "country_txt", "region_txt", "iso3"]]
    )
    years = pd.DataFrame({"year": list(range(start_year, end_year + 1))})
    balanced = country_meta.assign(_join=1).merge(years.assign(_join=1), on="_join").drop(columns="_join")
    panel = balanced.merge(
        grouped.drop(columns=["country_txt", "region_txt", "iso3"]),
        on=["country_key", "year"],
        how="left",
    )
    for column in [
        "attacks",
        "fatalities",
        "wounded",
        "casualties",
        "high_severity_count",
        "mass_casualty_count",
    ]:
        panel[column] = panel[column].fillna(0).astype(float)
    panel["high_severity_share"] = np.where(
        panel["attacks"].gt(0), panel["high_severity_count"] / panel["attacks"], 0.0
    )
    panel["log_attacks"] = np.log1p(panel["attacks"])
    panel["log_casualties"] = np.log1p(panel["casualties"])
    panel["log_fatalities"] = np.log1p(panel["fatalities"])
    panel["severity_burden_index"] = (
        _zscore(panel["log_casualties"])
        + _zscore(panel["log_attacks"])
        + _zscore(panel["high_severity_share"])
        + _zscore(np.log1p(panel["mass_casualty_count"]))
    ) / 4.0
    return panel


def add_policy_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Add derived policy features, lags, and completeness flags.

    Args:
        panel: Country-year dataframe with GTD outcomes and optional sources.

    Returns:
        Panel with governance capacity, transformed controls, one-year lags,
        reporting-bias proxy, and complete-case flag.
    """
    if panel.empty:
        return panel
    data = panel.copy()
    for column in [*MAIN_GOVERNANCE_COLUMNS, *CONTROL_COLUMNS, *ROBUSTNESS_COLUMNS]:
        if column not in data.columns:
            data[column] = np.nan

    data["governance_capacity"] = data[MAIN_GOVERNANCE_COLUMNS].mean(axis=1, skipna=True)
    data["governance_capacity_components_available"] = data[MAIN_GOVERNANCE_COLUMNS].notna().sum(axis=1)
    data["development_controls_available"] = data[CONTROL_COLUMNS].notna().sum(axis=1)
    data["robustness_sources_available"] = data[ROBUSTNESS_COLUMNS].notna().sum(axis=1)
    data["log_population"] = np.log(data["population"].where(data["population"].gt(0)))
    data["log_gdp_per_capita"] = np.log(data["gdp_per_capita"].where(data["gdp_per_capita"].gt(0)))
    data["post_2011"] = data["year"].ge(2011).astype(int)

    lag_columns = [
        *MAIN_GOVERNANCE_COLUMNS,
        "governance_capacity",
        *CONTROL_COLUMNS,
        "log_population",
        "log_gdp_per_capita",
        "political_stability",
        "vdem_electoral_democracy",
        "hdi",
        "ucdp_best_fatalities",
        "internet_users_pct",
    ]
    for column in dict.fromkeys(lag_columns):
        if column in data.columns:
            data[f"{column}_lag1"] = data.groupby("iso3", dropna=False)[column].shift(1)

    data["reporting_bias_proxy"] = data[["internet_users_pct", "press_freedom_score"]].mean(
        axis=1, skipna=True
    )
    data["policy_panel_complete_case"] = data[
        ["governance_capacity_lag1", "log_population_lag1", "log_gdp_per_capita_lag1"]
    ].notna().all(axis=1)
    return data


def build_policy_bundle(
    incidents: pd.DataFrame,
    settings: Settings | None = None,
    fetch_sources: bool = False,
    start_year: int = 1996,
    end_year: int = 2021,
) -> dict[str, Any]:
    """Build the full policy artifact bundle.

    Args:
        incidents: Cleaned incident-level dataframe.
        settings: Optional project settings override.
        fetch_sources: Whether to fetch credential-free World Bank sources.
        start_year: First analysis year.
        end_year: Last analysis year.

    Returns:
        Dictionary containing panel dataframe, summaries, model results,
        event-study output, source registry, and source reports.
    """
    settings = settings or get_settings()
    source_frames: list[pd.DataFrame] = []
    source_reports: list[dict[str, Any]] = []

    local_sources, local_report = load_normalized_local_sources(settings.dataset_dir / "policy")
    if not local_sources.empty:
        source_frames.append(local_sources)
    source_reports.extend(local_report)

    if fetch_sources:
        world_bank, world_bank_report = fetch_world_bank_panel(start_year=start_year, end_year=end_year)
        if not world_bank.empty:
            source_frames.append(world_bank)
        source_reports.extend(world_bank_report)

    external_sources = merge_source_frames(source_frames)
    panel = build_policy_panel(
        incidents,
        external_sources=external_sources,
        start_year=start_year,
        end_year=end_year,
    )
    summary = policy_panel_summary(panel, source_reports=source_reports, fetch_sources=fetch_sources)
    results = run_policy_models(panel)
    event_study = build_event_study(panel)
    return {
        "panel": panel,
        "summary": summary,
        "results": results,
        "event_study": event_study,
        "sources": source_registry(),
        "source_reports": source_reports,
    }


def write_policy_artifacts(bundle: dict[str, Any], policy_dir: Path) -> dict[str, str]:
    """Persist policy panel artifacts to disk.

    Args:
        bundle: Output from `build_policy_bundle`.
        policy_dir: Directory for policy gold artifacts.

    Returns:
        Mapping of artifact names to written file paths.
    """
    policy_dir.mkdir(parents=True, exist_ok=True)
    panel_path = policy_dir / "country_year_panel.parquet"
    summary_path = policy_dir / "panel_summary.json"
    results_path = policy_dir / "results.json"
    event_study_path = policy_dir / "event_study.json"
    sources_path = policy_dir / "source_registry.json"
    bundle["panel"].to_parquet(panel_path, index=False)
    summary_path.write_text(json.dumps(bundle["summary"], indent=2, default=str), encoding="utf-8")
    results_path.write_text(json.dumps(bundle["results"], indent=2, default=str), encoding="utf-8")
    event_study_path.write_text(json.dumps(bundle["event_study"], indent=2, default=str), encoding="utf-8")
    sources_path.write_text(json.dumps(bundle["sources"], indent=2, default=str), encoding="utf-8")
    return {
        "panel": str(panel_path),
        "summary": str(summary_path),
        "results": str(results_path),
        "event_study": str(event_study_path),
        "sources": str(sources_path),
    }


def load_policy_bundle(
    incidents: pd.DataFrame | None = None,
    settings: Settings | None = None,
    fetch_sources: bool = False,
) -> dict[str, Any]:
    """Load policy artifacts from disk or build them on demand.

    Args:
        incidents: Optional cleaned incident dataframe for fallback builds.
        settings: Optional project settings override.
        fetch_sources: Whether fallback builds should fetch World Bank data.

    Returns:
        Policy bundle with panel, results, summaries, and source metadata.
    """
    settings = settings or get_settings()
    policy_dir = settings.gold_dir / "policy"
    panel_path = policy_dir / "country_year_panel.parquet"
    summary_path = policy_dir / "panel_summary.json"
    results_path = policy_dir / "results.json"
    event_study_path = policy_dir / "event_study.json"
    sources_path = policy_dir / "source_registry.json"
    if all(path.exists() for path in [panel_path, summary_path, results_path, event_study_path, sources_path]):
        panel = pd.read_parquet(panel_path)
        return {
            "panel": panel,
            "summary": json.loads(summary_path.read_text(encoding="utf-8")),
            "results": json.loads(results_path.read_text(encoding="utf-8")),
            "event_study": json.loads(event_study_path.read_text(encoding="utf-8")),
            "sources": json.loads(sources_path.read_text(encoding="utf-8")),
            "source_reports": [],
        }
    if incidents is None:
        from gtd_capstone.data.repository import DataRepository

        incidents = DataRepository(settings).load_incidents()
    return build_policy_bundle(incidents, settings=settings, fetch_sources=fetch_sources)


def policy_panel_summary(
    panel: pd.DataFrame,
    source_reports: list[dict[str, Any]] | None = None,
    fetch_sources: bool = False,
) -> dict[str, Any]:
    """Summarize country-year policy panel coverage and safety posture.

    Args:
        panel: Country-year policy panel.
        source_reports: Optional source-ingestion status records.
        fetch_sources: Whether external source fetching was requested.

    Returns:
        JSON-serializable panel summary.
    """
    if panel.empty:
        return {"rows": 0, "countries": 0, "years": [], "aggregate_policy": aggregate_only_note()}
    coverage = {}
    for column in [*MAIN_GOVERNANCE_COLUMNS, *CONTROL_COLUMNS, *ROBUSTNESS_COLUMNS]:
        if column in panel.columns:
            coverage[column] = {
                "non_null_rows": int(panel[column].notna().sum()),
                "coverage_pct": float(panel[column].notna().mean()),
            }
    return {
        "rows": int(len(panel)),
        "countries": int(panel["iso3"].nunique()),
        "year_min": int(panel["year"].min()),
        "year_max": int(panel["year"].max()),
        "total_attacks": int(panel["attacks"].sum()),
        "total_casualties": float(panel["casualties"].sum()),
        "mean_severity_burden": float(panel["severity_burden_index"].mean()),
        "complete_case_rows": int(panel.get("policy_panel_complete_case", pd.Series(False)).sum()),
        "main_window": "1996-2021",
        "fetch_sources": bool(fetch_sources),
        "covariate_coverage": coverage,
        "source_reports": source_reports or [],
        "aggregate_policy": aggregate_only_note(),
        "causal_language": (
            "Cautious causal-policy language only: fixed effects and lags support stronger "
            "research design than raw correlations, but they do not prove causality alone."
        ),
    }


def country_policy_profile(panel: pd.DataFrame, iso3: str) -> dict[str, Any]:
    """Return a single-country policy profile.

    Args:
        panel: Country-year policy panel.
        iso3: ISO-3 country code.

    Returns:
        Country metadata and year-by-year policy records.
    """
    code = iso3.upper()
    rows = panel[panel["iso3"].eq(code)].sort_values("year")
    if rows.empty:
        return {"iso3": code, "found": False, "records": []}
    latest = rows.iloc[-1]
    return {
        "iso3": code,
        "found": True,
        "country": str(latest["country_txt"]),
        "region": str(latest["region_txt"]),
        "year_min": int(rows["year"].min()),
        "year_max": int(rows["year"].max()),
        "total_attacks": int(rows["attacks"].sum()),
        "total_casualties": float(rows["casualties"].sum()),
        "records": rows[
            [
                "year",
                "attacks",
                "casualties",
                "high_severity_share",
                "severity_burden_index",
                "governance_capacity",
                "government_effectiveness",
                "rule_of_law",
                "control_of_corruption",
            ]
        ].replace({np.nan: None}).to_dict(orient="records"),
    }


def country_to_iso3(name: str) -> str | None:
    """Resolve a GTD country name to an ISO-3 code when available."""
    return COUNTRY_ISO_OVERRIDES.get(_normalized_country(name))


def _normalized_country(name: str) -> str:
    """Normalize country names for deterministic local matching."""
    text = str(name or "").lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[^\w\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _zscore(values: pd.Series | np.ndarray) -> pd.Series:
    """Return z-scored values with a zero-variance guard."""
    series = pd.Series(values, dtype=float)
    std = series.std(ddof=0)
    if not np.isfinite(std) or std == 0:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - series.mean()) / std
