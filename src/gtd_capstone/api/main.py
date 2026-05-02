from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from gtd_capstone import analytics
from gtd_capstone.contracts import validate_data_contract
from gtd_capstone.data.repository import DataRepository
from gtd_capstone.dsa.algorithms import benchmark_dataframe, complexity_catalog
from gtd_capstone.graph.analytics import connected_components, degree_centrality, pagerank_baseline
from gtd_capstone.graph.gds_playbook import gds_query_catalog
from gtd_capstone.monitoring.drift import drift_report
from gtd_capstone.policy.panel import country_policy_profile, load_policy_bundle
from gtd_capstone.rag.evaluate import evaluate_rag
from gtd_capstone.rag.retriever import LocalRetriever
from gtd_capstone.safety import aggregate_only_note


class PredictionRequest(BaseModel):
    iyear: int = Field(default=2021)
    imonth: int = Field(default=1)
    region_txt: str = Field(default="South Asia")
    country_txt: str = Field(default="Afghanistan")
    attacktype1_txt: str = Field(default="Armed Assault")
    targtype1_txt: str = Field(default="Military")
    weaptype1_txt: str = Field(default="Firearms")
    suicide: int = Field(default=0)
    property: int = Field(default=0)
    ishostkid: int = Field(default=0)
    nkill: float = Field(default=0)
    nwound: float = Field(default=0)


class ChatRequest(BaseModel):
    question: str


@lru_cache(maxsize=1)
def repo() -> DataRepository:
    return DataRepository()


@lru_cache(maxsize=1)
def retriever() -> LocalRetriever:
    return LocalRetriever()


def incidents():
    return repo().load_incidents()


@lru_cache(maxsize=1)
def policy_bundle() -> dict:
    return load_policy_bundle(incidents=incidents(), settings=repo().settings)


app = FastAPI(
    title="GTD AI Systems Capstone API",
    version="0.1.0",
    description="Historical aggregate GTD analytics, ML, graph, RAG, and MLOps API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "message": "GTD capstone API is running"}


@app.get("/api/summary")
def get_summary() -> dict:
    return analytics.summary(incidents())


@app.get("/api/data-quality")
def get_data_quality() -> dict:
    return repo().load_quality()


@app.get("/api/data-contract")
def get_data_contract() -> dict:
    return validate_data_contract(incidents())


@app.get("/api/analytics/trends")
def get_trends(grain: str = "year", group_by: str = "region_txt") -> list[dict]:
    return analytics.trend_points(incidents(), grain=grain, group_by=group_by)


@app.get("/api/analytics/distributions")
def get_distributions(limit: int = 12) -> dict[str, list[dict]]:
    return analytics.distributions(incidents(), limit=limit)


@app.get("/api/geo/hotspots")
def get_hotspots(level: str = "country", limit: int = 50, min_events: int = 5) -> list[dict]:
    return analytics.hotspots(incidents(), level=level, limit=limit, min_events=min_events)


@app.get("/api/graph/centrality")
def get_graph_centrality(algorithm: str = "degree") -> list[dict]:
    if algorithm == "pagerank":
        return pagerank_baseline(incidents())
    return degree_centrality(incidents())


@app.get("/api/graph/communities")
def get_graph_communities() -> list[dict]:
    return connected_components(incidents())


@app.get("/api/graph/gds-playbook")
def get_gds_playbook() -> list[dict]:
    return gds_query_catalog()


@app.get("/api/forecasts")
def get_forecasts(horizon: int = 12) -> list[dict]:
    return analytics.simple_forecasts(incidents(), horizon=horizon)


@app.get("/api/clusters")
def get_clusters(limit: int = 8) -> list[dict]:
    return analytics.clusters(incidents(), limit=limit)


@app.get("/api/models")
def get_models() -> list[dict]:
    return analytics.model_catalog()


@app.get("/api/complexity")
def get_complexity() -> dict[str, Any]:
    df = incidents()
    return {"catalog": complexity_catalog(), "benchmark": benchmark_dataframe(df)}


@app.get("/api/monitoring/drift")
def get_drift(split_year: int = 2014) -> dict:
    return drift_report(incidents(), split_year=split_year)


@app.get("/api/policy/panel-summary")
def get_policy_panel_summary() -> dict:
    bundle = policy_bundle()
    return {**bundle["summary"], "sources": bundle["sources"]}


@app.get("/api/policy/results")
def get_policy_results() -> dict:
    return policy_bundle()["results"]


@app.get("/api/policy/event-study")
def get_policy_event_study() -> dict:
    return policy_bundle()["event_study"]


@app.get("/api/policy/country/{iso3}")
def get_policy_country(iso3: str) -> dict:
    return country_policy_profile(policy_bundle()["panel"], iso3)


@app.get("/api/rag/evaluation")
def get_rag_evaluation() -> dict:
    return evaluate_rag()


@app.post("/api/predict/severity")
def predict_severity(payload: PredictionRequest) -> dict:
    return analytics.predict_severity_rule(payload.model_dump(), reference_df=incidents())


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict:
    response = retriever().answer(payload.question)
    response["policy"] = aggregate_only_note()
    return response
