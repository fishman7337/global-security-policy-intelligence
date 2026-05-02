from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from gtd_capstone import analytics
from gtd_capstone.config import Settings, ensure_artifact_dirs, get_settings
from gtd_capstone.contracts import validate_data_contract
from gtd_capstone.data.cleaning import (
    clean_incidents,
    data_quality_report,
    discover_excel_sources,
    read_excel_sources,
)
from gtd_capstone.dsa.algorithms import benchmark_dataframe, complexity_catalog
from gtd_capstone.graph.gds_playbook import write_gds_playbook
from gtd_capstone.graph.neo4j_export import export_graph_csv
from gtd_capstone.monitoring.drift import drift_report
from gtd_capstone.policy.panel import build_policy_bundle, write_policy_artifacts
from gtd_capstone.rag.evaluate import evaluate_rag


def pyspark_available() -> bool:
    try:
        import pyspark  # noqa: F401

        return True
    except Exception:
        return False


def build_artifacts(
    settings: Settings | None = None,
    sample_rows: int | None = None,
    fetch_policy_sources: bool = False,
) -> dict:
    settings = settings or get_settings()
    ensure_artifact_dirs(settings)
    sources = discover_excel_sources(settings.dataset_dir)
    raw = read_excel_sources(sources, sample_rows=sample_rows)
    raw_path = settings.bronze_dir / "raw_extract.parquet"
    raw.to_parquet(raw_path, index=False)

    incidents = clean_incidents(raw)
    silver_path = settings.silver_dir / "incidents.parquet"
    gold_incident_path = settings.gold_dir / "incidents.parquet"
    incidents.to_parquet(silver_path, index=False)
    incidents.to_parquet(gold_incident_path, index=False)

    outputs = {
        "summary": analytics.summary(incidents),
        "quality": data_quality_report(incidents),
        "distributions": analytics.distributions(incidents),
        "forecasts": analytics.simple_forecasts(incidents, horizon=12),
        "clusters": analytics.clusters(incidents),
        "complexity": {
            "catalog": complexity_catalog(),
            "benchmark": benchmark_dataframe(incidents),
            "spark_available": pyspark_available(),
        },
        "data_contract": validate_data_contract(incidents),
        "drift": drift_report(incidents),
    }
    for name, payload in outputs.items():
        (settings.gold_dir / f"{name}.json").write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8"
        )

    pd.DataFrame(analytics.trend_points(incidents, "year", "region_txt")).to_parquet(
        settings.gold_dir / "trends_year_region.parquet", index=False
    )
    pd.DataFrame(analytics.hotspots(incidents, "country", min_events=1)).to_parquet(
        settings.gold_dir / "hotspots_country.parquet", index=False
    )
    graph_paths = export_graph_csv(incidents, settings.gold_dir / "graph")
    gds_playbook = write_gds_playbook(settings.gold_dir / "graph" / "neo4j_gds_playbook.cypher")
    rag_eval = evaluate_rag(output_path=settings.gold_dir / "rag_eval.json")
    policy_bundle = build_policy_bundle(
        incidents,
        settings=settings,
        fetch_sources=fetch_policy_sources,
    )
    policy_paths = write_policy_artifacts(policy_bundle, settings.gold_dir / "policy")

    return {
        "raw_path": str(raw_path),
        "silver_path": str(silver_path),
        "gold_incident_path": str(gold_incident_path),
        "rows": len(incidents),
        "graph_paths": {key: str(value) for key, value in graph_paths.items()},
        "gds_playbook": str(gds_playbook),
        "rag_eval_passed": bool(rag_eval["passed"]),
        "policy_paths": policy_paths,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GTD bronze/silver/gold artifacts.")
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=None,
        help="Optional smoke-test sample size. Omit this flag to process the full local GTD files.",
    )
    parser.add_argument("--artifact-dir", type=Path, default=None)
    parser.add_argument(
        "--fetch-policy-sources",
        action="store_true",
        help="Fetch credential-free World Bank WGI/WDI policy covariates during artifact build.",
    )
    args = parser.parse_args()
    settings = get_settings()
    if args.artifact_dir is not None:
        settings = Settings(artifact_dir=args.artifact_dir)
    result = build_artifacts(
        settings=settings,
        sample_rows=args.sample_rows,
        fetch_policy_sources=args.fetch_policy_sources,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
