"""Generate and execute the rendered GTD capstone notebook suite.

The notebooks are intentionally compact rendered reports: they call package
modules, show small tables, and avoid embedding large raw data dumps or heavy
interactive figures.
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path
from typing import Iterable

import nbformat
from nbclient import NotebookClient
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
DEFAULT_TIMEOUT_SECONDS = 180


def md(source: str):
    """Create a markdown notebook cell."""
    return new_markdown_cell(textwrap.dedent(source).strip())


def code(source: str):
    """Create a code notebook cell."""
    return new_code_cell(textwrap.dedent(source).strip())


SETUP = code(
    """
    from pathlib import Path
    import json
    import os
    import sys

    ROOT = Path.cwd()
    if not (ROOT / "src").exists():
        for parent in ROOT.parents:
            if (parent / "src").exists():
                ROOT = parent
                break

    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))

    os.chdir(ROOT)
    SAMPLE_ROWS = int(os.getenv("GTD_NOTEBOOK_SAMPLE_ROWS", "25000"))
    print(f"Project root: {ROOT}")
    print(f"Notebook sample rows: {SAMPLE_ROWS:,}")
    """
)


def notebook(title: str, summary: str, cells: list) -> nbformat.NotebookNode:
    """Build a notebook object with shared metadata.

    Args:
        title: Notebook title.
        summary: Introductory markdown summary.
        cells: Notebook body cells.

    Returns:
        Notebook node ready to write or execute.
    """
    return new_notebook(
        cells=[md(f"# {title}\n\n{summary}"), SETUP, *cells],
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
    )


def notebook_specs() -> list[tuple[str, nbformat.NotebookNode]]:
    """Return the ordered full-capstone notebook specifications."""
    return [
        (
            "00_project_overview.ipynb",
            notebook(
                "Project Overview",
                "Architecture, artifact map, and aggregate-only safety boundary.",
                [
                    code(
                        """
                        from gtd_capstone.config import get_settings
                        from gtd_capstone.data.repository import DataRepository
                        from gtd_capstone.safety import aggregate_only_note

                        settings = get_settings()
                        repo = DataRepository(settings)
                        incidents = repo.load_incidents(sample_rows=SAMPLE_ROWS)
                        artifact_map = {
                            "bronze": str(settings.bronze_dir),
                            "silver": str(settings.silver_dir),
                            "gold": str(settings.gold_dir),
                            "models": str(settings.artifact_dir / "models"),
                            "policy": str(settings.gold_dir / "policy"),
                        }
                        {"rows_loaded": len(incidents), "artifact_map": artifact_map, "safety": aggregate_only_note()}
                        """
                    ),
                    code(
                        """
                        docs = [
                            "docs/architecture.md",
                            "docs/methodology.md",
                            "docs/ethics.md",
                            "docs/research/policy_paper.md",
                            "docs/model_cards/severity_model.md",
                        ]
                        {path: (ROOT / path).exists() for path in docs}
                        """
                    ),
                ],
            ),
        ),
        (
            "01_data_engineering_quality.ipynb",
            notebook(
                "Data Engineering and Quality",
                "Bronze/silver/gold artifacts, data contract checks, and missingness profile.",
                [
                    code(
                        """
                        from gtd_capstone.contracts import validate_data_contract
                        from gtd_capstone.data.cleaning import data_quality_report
                        from gtd_capstone.data.repository import DataRepository

                        repo = DataRepository()
                        incidents = repo.load_incidents(sample_rows=SAMPLE_ROWS)
                        quality = data_quality_report(incidents)
                        contract = validate_data_contract(incidents)
                        {
                            "rows": quality["rows"],
                            "columns": quality["columns"],
                            "duplicate_eventids": quality["duplicate_eventids"],
                            "contract_passed": contract["passed"],
                        }
                        """
                    ),
                    code(
                        """
                        import pandas as pd

                        pd.DataFrame(quality["checks"])
                        """
                    ),
                    code(
                        """
                        missing = (
                            incidents.isna()
                            .sum()
                            .sort_values(ascending=False)
                            .head(12)
                            .rename("missing_rows")
                            .reset_index()
                            .rename(columns={"index": "column"})
                        )
                        missing
                        """
                    ),
                ],
            ),
        ),
        (
            "02_eda_visual_analytics.ipynb",
            notebook(
                "EDA and Visual Analytics",
                "Compact exploratory tables for trends, severity, and categorical profiles.",
                [
                    code(
                        """
                        import pandas as pd

                        from gtd_capstone import analytics
                        from gtd_capstone.data.repository import DataRepository

                        incidents = DataRepository().load_incidents(sample_rows=SAMPLE_ROWS)
                        analytics.summary(incidents)
                        """
                    ),
                    code(
                        """
                        distributions = analytics.distributions(incidents, limit=8)
                        pd.DataFrame(distributions["severity"])
                        """
                    ),
                    code(
                        """
                        pd.DataFrame(distributions["attack_types"])
                        """
                    ),
                    code(
                        """
                        trends = pd.DataFrame(analytics.trend_points(incidents, "year", "region_txt"))
                        (
                            trends.groupby("period", as_index=False)["attacks"]
                            .sum()
                            .tail(12)
                        )
                        """
                    ),
                ],
            ),
        ),
        (
            "03_geospatial_forecasting.ipynb",
            notebook(
                "Geospatial Aggregates and Forecasting",
                "Country-level aggregate hotspots and simple regional forecast outputs.",
                [
                    code(
                        """
                        import pandas as pd

                        from gtd_capstone import analytics
                        from gtd_capstone.data.repository import DataRepository

                        incidents = DataRepository().load_incidents(sample_rows=SAMPLE_ROWS)
                        hotspots = pd.DataFrame(analytics.hotspots(incidents, "country", limit=10, min_events=1))
                        hotspots[["name", "attacks", "fatalities", "wounded", "aggregate_only"]]
                        """
                    ),
                    code(
                        """
                        forecasts = pd.DataFrame(analytics.simple_forecasts(incidents, horizon=3))
                        forecasts.head(12)
                        """
                    ),
                ],
            ),
        ),
        (
            "04_adaptive_severity.ipynb",
            notebook(
                "Adaptive Severity",
                "OPTICS severity audit and score/cluster diagnostics.",
                [
                    code(
                        """
                        import pandas as pd

                        from gtd_capstone.data.repository import DataRepository

                        incidents = DataRepository().load_incidents(sample_rows=SAMPLE_ROWS)
                        severity_cols = [
                            "severity",
                            "severity_score",
                            "severity_score_percentile",
                            "severity_cluster",
                            "severity_method",
                        ]
                        incidents[severity_cols].head()
                        """
                    ),
                    code(
                        """
                        (
                            incidents.groupby(["severity", "severity_method"])
                            .agg(
                                rows=("eventid", "count"),
                                median_score=("severity_score", "median"),
                                median_casualties=("casualties", "median"),
                            )
                            .reset_index()
                            .sort_values(["median_score", "rows"], ascending=[True, False])
                        )
                        """
                    ),
                ],
            ),
        ),
        (
            "05_feature_store_ml_baselines.ipynb",
            notebook(
                "Feature Store and ML Baselines",
                "Feature-set materialization, leakage guardrails, and baseline train/test shape.",
                [
                    code(
                        """
                        from sklearn.model_selection import train_test_split

                        from gtd_capstone.data.repository import DataRepository
                        from gtd_capstone.features.store import materialize_feature_set
                        from gtd_capstone.ml.experiment_suite import FEATURES

                        incidents = DataRepository().load_incidents(sample_rows=min(SAMPLE_ROWS, 10000))
                        features = materialize_feature_set(incidents)
                        x = features[FEATURES]
                        y = features["severity"]
                        x_train, x_test, y_train, y_test = train_test_split(
                            x,
                            y,
                            test_size=0.25,
                            random_state=42,
                            stratify=y if y.value_counts().min() >= 2 else None,
                        )
                        {
                            "feature_set": features.attrs["feature_set"],
                            "leakage_blocklist": features.attrs["leakage_blocklist"],
                            "train_rows": len(x_train),
                            "test_rows": len(x_test),
                            "features": FEATURES,
                        }
                        """
                    ),
                    code(
                        """
                        y.value_counts().rename_axis("severity").reset_index(name="rows")
                        """
                    ),
                ],
            ),
        ),
        (
            "06_ml_experiment_benchmark.ipynb",
            notebook(
                "ML Experiment Benchmark",
                "Small rendered ML benchmark using the project preprocessing and classifier helpers.",
                [
                    code(
                        """
                        import pandas as pd
                        from sklearn.metrics import accuracy_score, f1_score
                        from sklearn.model_selection import train_test_split
                        from sklearn.pipeline import Pipeline

                        from gtd_capstone.data.repository import DataRepository
                        from gtd_capstone.features.store import materialize_feature_set
                        from gtd_capstone.ml.experiment_suite import FEATURES, classifier, preprocess

                        incidents = DataRepository().load_incidents(sample_rows=min(SAMPLE_ROWS, 4000))
                        frame = materialize_feature_set(incidents)
                        x = frame[FEATURES]
                        y = frame["severity"]
                        x_train, x_test, y_train, y_test = train_test_split(
                            x,
                            y,
                            test_size=0.25,
                            random_state=42,
                            stratify=y if y.value_counts().min() >= 2 else None,
                        )
                        rows = []
                        for family in ["logistic_regression", "random_forest"]:
                            model = Pipeline([("preprocess", preprocess()), ("model", classifier(family))])
                            model.fit(x_train, y_train)
                            pred = model.predict(x_test)
                            rows.append(
                                {
                                    "family": family,
                                    "accuracy": accuracy_score(y_test, pred),
                                    "macro_f1": f1_score(y_test, pred, average="macro", zero_division=0),
                                    "weighted_f1": f1_score(y_test, pred, average="weighted", zero_division=0),
                                }
                            )
                        pd.DataFrame(rows)
                        """
                    ),
                    code(
                        """
                        metrics_path = ROOT / "artifacts" / "models" / "severity_metrics.json"
                        if metrics_path.exists():
                            json.loads(metrics_path.read_text())["metrics"]
                        else:
                            {"note": "No persisted severity metrics artifact found."}
                        """
                    ),
                ],
            ),
        ),
        (
            "07_deep_learning_lab.ipynb",
            notebook(
                "Deep Learning Lab",
                "Sequence-window and optional TensorFlow MLP scaffolds with graceful dependency handling.",
                [
                    code(
                        """
                        import numpy as np
                        import pandas as pd

                        from gtd_capstone.data.repository import DataRepository
                        from gtd_capstone.ml.deep_learning import build_tabular_mlp, window_series

                        incidents = DataRepository().load_incidents(sample_rows=SAMPLE_ROWS)
                        yearly = (
                            incidents.groupby("iyear")["eventid"]
                            .count()
                            .sort_index()
                            .to_numpy(dtype=float)
                        )
                        x_seq, y_seq = window_series(yearly, window=min(12, max(2, len(yearly) // 4)))
                        {"sequence_windows": x_seq.shape, "sequence_targets": y_seq.shape}
                        """
                    ),
                    code(
                        """
                        try:
                            model = build_tabular_mlp(input_dim=12, output_classes=5)
                            result = {
                                "tensorflow_available": True,
                                "layers": [layer.__class__.__name__ for layer in model.layers],
                                "output_shape": str(model.output_shape),
                            }
                        except RuntimeError as exc:
                            result = {"tensorflow_available": False, "reason": str(exc)}
                        result
                        """
                    ),
                ],
            ),
        ),
        (
            "08_graph_analytics.ipynb",
            notebook(
                "Graph Analytics",
                "Graph edge construction, centrality, communities, and Neo4j GDS playbook pointers.",
                [
                    code(
                        """
                        import pandas as pd

                        from gtd_capstone.data.repository import DataRepository
                        from gtd_capstone.graph.analytics import (
                            connected_components,
                            degree_centrality,
                            graph_edges_from_incidents,
                            pagerank_baseline,
                        )
                        from gtd_capstone.graph.gds_playbook import gds_query_catalog

                        incidents = DataRepository().load_incidents(sample_rows=min(SAMPLE_ROWS, 3000))
                        edges = graph_edges_from_incidents(incidents)
                        {"incident_rows": len(incidents), "graph_edges": len(edges)}
                        """
                    ),
                    code("pd.DataFrame(degree_centrality(incidents, limit=10))"),
                    code("pd.DataFrame(pagerank_baseline(incidents, iterations=5)).head(10)"),
                    code("pd.DataFrame(connected_components(incidents, limit=5))"),
                    code(
                        """
                        gds = pd.DataFrame(gds_query_catalog())
                        gds["cypher_excerpt"] = gds["cypher"].str.slice(0, 140)
                        gds[["name", "cypher_excerpt"]].head(8)
                        """
                    ),
                ],
            ),
        ),
        (
            "09_rag_mcp_safety.ipynb",
            notebook(
                "RAG, MCP, and Safety",
                "Retrieval quality, citation behavior, refusal tests, and read-only MCP tool surface.",
                [
                    code(
                        """
                        import pandas as pd

                        from gtd_capstone.mcp_server import ReadOnlyMCPServer
                        from gtd_capstone.rag.evaluate import evaluate_rag
                        from gtd_capstone.rag.retriever import LocalRetriever

                        report = evaluate_rag()
                        {
                            "citation_rate": report["citation_rate"],
                            "refusal_rate": report["refusal_rate"],
                            "passed": report["passed"],
                        }
                        """
                    ),
                    code(
                        """
                        retriever = LocalRetriever()
                        answer = retriever.answer("Does the policy model prove governance causes terrorism?")
                        {"safe": answer["safe"], "answer_excerpt": answer["answer"][:500], "citations": answer["citations"]}
                        """
                    ),
                    code(
                        """
                        server = ReadOnlyMCPServer()
                        tools = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
                        pd.DataFrame(tools["result"]["tools"])[["name", "description"]]
                        """
                    ),
                ],
            ),
        ),
        (
            "10_policy_research_panel.ipynb",
            notebook(
                "Policy Research Panel",
                "Country-year panel coverage, WGI/WDI covariates, and fixed-effects results.",
                [
                    code(
                        """
                        import pandas as pd

                        policy_dir = ROOT / "artifacts" / "gold" / "policy"
                        panel = pd.read_parquet(policy_dir / "country_year_panel.parquet")
                        summary = json.loads((policy_dir / "panel_summary.json").read_text())
                        results = json.loads((policy_dir / "results.json").read_text())
                        {
                            "rows": summary["rows"],
                            "countries": summary["countries"],
                            "window": f"{summary['year_min']}-{summary['year_max']}",
                            "complete_case_rows": summary["complete_case_rows"],
                        }
                        """
                    ),
                    code(
                        """
                        coverage = pd.DataFrame(summary["covariate_coverage"]).T.reset_index()
                        coverage.rename(columns={"index": "variable"}).sort_values(
                            "coverage_pct",
                            ascending=False,
                        ).head(12)
                        """
                    ),
                    code(
                        """
                        pd.DataFrame(results["models"])[
                            [
                                "outcome",
                                "status",
                                "coefficient",
                                "conf_low",
                                "conf_high",
                                "p_value",
                                "nobs",
                                "countries",
                            ]
                        ]
                        """
                    ),
                ],
            ),
        ),
        (
            "11_monitoring_drift_mlops.ipynb",
            notebook(
                "Monitoring, Drift, and MLOps",
                "Drift metrics, W&B artifact posture, and reproducibility checks.",
                [
                    code(
                        """
                        import pandas as pd

                        from gtd_capstone.data.repository import DataRepository
                        from gtd_capstone.monitoring.drift import drift_report

                        incidents = DataRepository().load_incidents(sample_rows=SAMPLE_ROWS)
                        report = drift_report(
                            incidents,
                            split_year=2014,
                            numeric_columns=["nkill", "nwound", "casualties", "severity_score"],
                            categorical_columns=["region_txt", "attacktype1_txt", "severity"],
                        )
                        {"severity": report["severity"], "max_score": report["max_score"]}
                        """
                    ),
                    code(
                        """
                        rows = [
                            {"metric": key, "score": value, "kind": "numeric_psi"}
                            for key, value in report["numeric_psi"].items()
                        ] + [
                            {"metric": key, "score": value, "kind": "categorical_js"}
                            for key, value in report["categorical_js"].items()
                        ]
                        pd.DataFrame(rows).sort_values("score", ascending=False)
                        """
                    ),
                    code(
                        """
                        model_dir = ROOT / "artifacts" / "models"
                        wandb_dir = ROOT / "wandb"
                        {
                            "model_artifacts": sorted(path.name for path in model_dir.glob("*"))[:10]
                            if model_dir.exists()
                            else [],
                            "wandb_offline_runs": len(list(wandb_dir.glob("offline-run-*")))
                            if wandb_dir.exists()
                            else 0,
                            "notebook_sample_rows": SAMPLE_ROWS,
                        }
                        """
                    ),
                ],
            ),
        ),
    ]


def write_notebooks(specs: Iterable[tuple[str, nbformat.NotebookNode]]) -> list[Path]:
    """Write notebooks to the notebook directory.

    Args:
        specs: Ordered notebook filename and node pairs.

    Returns:
        Written notebook paths.
    """
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for name, nb in specs:
        path = NOTEBOOK_DIR / name
        nbformat.write(nb, path)
        written.append(path)
    return written


def execute_notebooks(paths: Iterable[Path], timeout: int = DEFAULT_TIMEOUT_SECONDS) -> None:
    """Execute notebooks in place.

    Args:
        paths: Notebook paths to execute.
        timeout: Per-cell timeout in seconds.
    """
    for path in paths:
        print(f"Executing {path.relative_to(ROOT)}")
        nb = nbformat.read(path, as_version=4)
        client = NotebookClient(
            nb,
            timeout=timeout,
            kernel_name="python3",
            resources={"metadata": {"path": str(ROOT)}},
        )
        client.execute()
        nbformat.write(nb, path)


def main() -> None:
    """Generate and optionally execute the notebook suite."""
    parser = argparse.ArgumentParser(description="Build the rendered GTD notebook suite.")
    parser.add_argument("--execute", action="store_true", help="Execute notebooks after generation.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    specs = notebook_specs()
    paths = write_notebooks(specs)
    if args.execute:
        execute_notebooks(paths, timeout=args.timeout)
    print(f"Wrote {len(paths)} notebooks to {NOTEBOOK_DIR}")


if __name__ == "__main__":
    main()
