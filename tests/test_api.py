from __future__ import annotations

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
