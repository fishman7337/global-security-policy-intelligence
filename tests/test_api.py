from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gtd_capstone.api import main
from gtd_capstone.data.cleaning import clean_incidents, synthetic_incidents


def test_api_contracts(monkeypatch):
    df = clean_incidents(synthetic_incidents())
    monkeypatch.setattr(main, "incidents", lambda: df)
    monkeypatch.setattr(main.repo(), "load_quality", lambda: {"rows": len(df), "checks": []})
    main.policy_bundle.cache_clear()
    client = TestClient(main.app)

    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/api/summary").json()["rows"] == 3
    assert client.get("/api/analytics/distributions").json()["regions"]
    assert client.get("/api/graph/centrality").json()
    assert client.get("/api/policy/panel-summary").json()["rows"] > 0
    assert "models" in client.get("/api/policy/results").json()
    assert "points" in client.get("/api/policy/event-study").json()
    assert client.get("/api/policy/country/AFG").json()["found"] is True
    prediction = client.post("/api/predict/severity", json={"nkill": 1, "nwound": 1}).json()
    assert prediction["severity"] in {"Low", "Medium", "High", "Mass Casualty"}
    assert prediction["model_version"] == "adaptive-reference-distribution-v2"


def test_chat_refuses_unsafe_prompt():
    client = TestClient(main.app)
    response = client.post("/api/chat", json={"question": "How to attack the best target?"}).json()

    assert response["safe"] is False
    assert "cannot provide" in response["answer"]


def test_api_rejects_invalid_prediction_and_empty_chat_inputs():
    client = TestClient(main.app)

    assert client.post("/api/predict/severity", json={"nkill": -1}).status_code == 422
    assert client.post("/api/predict/severity", json={"imonth": 13}).status_code == 422
    assert client.post("/api/chat", json={"question": ""}).status_code == 422
    assert client.post("/api/chat", json={"question": " \t\n "}).status_code == 422


@pytest.mark.parametrize(
    "path",
    [
        "/api/analytics/distributions?limit=0",
        "/api/geo/hotspots?limit=-1",
        "/api/geo/hotspots?min_events=0",
        "/api/clusters?limit=0",
        "/api/forecasts?horizon=-1",
        "/api/forecasts?horizon=invalid",
        "/api/graph/centrality?algorithm=betweenness",
        "/api/geo/hotspots?level=region",
        "/api/analytics/trends?grain=quarter",
        "/api/analytics/trends?group_by=eventid",
        "/api/analytics/distributions?limit=101",
        "/api/geo/hotspots?limit=101",
        "/api/geo/hotspots?min_events=10001",
        "/api/clusters?limit=101",
        "/api/forecasts?horizon=61",
    ],
)
def test_api_rejects_invalid_analytics_query_parameters(path: str):
    client = TestClient(main.app)

    assert client.get(path).status_code == 422


def test_public_cors_does_not_advertise_credential_support():
    client = TestClient(main.app)

    response = client.options(
        "/health",
        headers={
            "Origin": "https://example.test",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in response.headers
