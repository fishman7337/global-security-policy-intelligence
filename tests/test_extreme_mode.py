from __future__ import annotations

from gtd_capstone.contracts import validate_data_contract
from gtd_capstone.data.cleaning import clean_incidents, synthetic_incidents
from gtd_capstone.features.store import materialize_feature_set
from gtd_capstone.graph.gds_playbook import gds_query_catalog
from gtd_capstone.monitoring.drift import drift_report
from gtd_capstone.rag.evaluate import evaluate_rag


def test_contract_feature_store_and_drift_outputs():
    df = clean_incidents(synthetic_incidents())

    contract = validate_data_contract(df)
    features = materialize_feature_set(df)
    drift = drift_report(df, split_year=2014)

    assert contract["checks"]
    assert features.attrs["feature_set"] == "incident_core_v1"
    assert "severity" in features.columns
    assert drift["severity"] in {"low", "medium", "high"}


def test_rag_eval_and_gds_catalog():
    rag_report = evaluate_rag()
    gds = gds_query_catalog()

    assert rag_report["passed"] is True
    assert any(query["name"] == "pagerank" for query in gds)

