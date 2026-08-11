"""FastAPI surface for aggregate GTD analytics and model services."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Any, Literal

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, StringConstraints

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

TrendGrain = Literal["year", "month"]
TrendGroupBy = Literal[
    "region_txt",
    "country_txt",
    "attacktype1_txt",
    "targtype1_txt",
    "weaptype1_txt",
    "severity",
]

MAX_RESULT_LIMIT = 100
MAX_HOTSPOT_MIN_EVENTS = 10_000
MAX_FORECAST_HORIZON = 60


class PredictionRequest(BaseModel):
    """Validated incident attributes accepted by the severity endpoint."""

    iyear: int = Field(default=2021, ge=1970, le=2100)
    imonth: int = Field(default=1, ge=1, le=12)
    region_txt: str = Field(default="South Asia", min_length=1, max_length=100)
    country_txt: str = Field(default="Afghanistan", min_length=1, max_length=100)
    attacktype1_txt: str = Field(default="Armed Assault", min_length=1, max_length=100)
    targtype1_txt: str = Field(default="Military", min_length=1, max_length=100)
    weaptype1_txt: str = Field(default="Firearms", min_length=1, max_length=100)
    suicide: int = Field(default=0, ge=0, le=1)
    property: int = Field(default=0, ge=0, le=1)
    ishostkid: int = Field(default=0, ge=0, le=1)
    nkill: float = Field(default=0, ge=0)
    nwound: float = Field(default=0, ge=0)


class ChatRequest(BaseModel):
    """Validated question accepted by the retrieval endpoint."""

    question: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
    ]


@lru_cache(maxsize=1)
def repo() -> DataRepository:
    """Return the process-wide incident repository."""
    return DataRepository()


@lru_cache(maxsize=1)
def retriever() -> LocalRetriever:
    """Return the process-wide local document retriever."""
    return LocalRetriever()


def incidents():
    """Load curated incidents through the cached repository."""
    return repo().load_incidents()


@lru_cache(maxsize=1)
def policy_bundle() -> dict:
    """Build and cache the policy-analysis result bundle."""
    return load_policy_bundle(incidents=incidents(), settings=repo().settings)


app = FastAPI(
    title="GTD AI Systems Capstone API",
    version="0.1.0",
    description="Historical aggregate GTD analytics, ML, graph, RAG, and MLOps API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    """Report whether the API process is responsive."""
    return {"status": "ok", "message": "GTD capstone API is running"}


@app.get("/api/summary")
def get_summary() -> dict:
    """Return aggregate incident coverage and impact measures."""
    return analytics.summary(incidents())


@app.get("/api/data-quality")
def get_data_quality() -> dict:
    """Return the persisted data-quality report."""
    return repo().load_quality()


@app.get("/api/data-contract")
def get_data_contract() -> dict:
    """Validate curated incidents against the declared data contract."""
    return validate_data_contract(incidents())


@app.get("/api/analytics/trends")
def get_trends(
    grain: TrendGrain = "year",
    group_by: TrendGroupBy = "region_txt",
) -> list[dict]:
    """Return temporal trends using the requested grain and grouping."""
    return analytics.trend_points(incidents(), grain=grain, group_by=group_by)


@app.get("/api/analytics/distributions")
def get_distributions(
    limit: Annotated[int, Query(ge=1, le=MAX_RESULT_LIMIT)] = 12,
) -> dict[str, list[dict]]:
    """Return leading categorical distributions up to ``limit`` entries."""
    return analytics.distributions(incidents(), limit=limit)


@app.get("/api/geo/hotspots")
def get_hotspots(
    level: Literal["country", "city"] = "country",
    limit: Annotated[int, Query(ge=1, le=MAX_RESULT_LIMIT)] = 50,
    min_events: Annotated[int, Query(ge=1, le=MAX_HOTSPOT_MIN_EVENTS)] = 5,
) -> list[dict]:
    """Return safely aggregated hotspots at the requested geographic level."""
    return analytics.hotspots(incidents(), level=level, limit=limit, min_events=min_events)


@app.get("/api/graph/centrality")
def get_graph_centrality(
    algorithm: Literal["degree", "pagerank"] = "degree",
) -> list[dict]:
    """Return graph centrality scores from degree or PageRank analysis."""
    if algorithm == "pagerank":
        return pagerank_baseline(incidents())
    return degree_centrality(incidents())


@app.get("/api/graph/communities")
def get_graph_communities() -> list[dict]:
    """Return connected components from the aggregate incident graph."""
    return connected_components(incidents())


@app.get("/api/graph/gds-playbook")
def get_gds_playbook() -> list[dict]:
    """Return the Neo4j Graph Data Science query catalog."""
    return gds_query_catalog()


@app.get("/api/forecasts")
def get_forecasts(
    horizon: Annotated[int, Query(ge=1, le=MAX_FORECAST_HORIZON)] = 12,
) -> list[dict]:
    """Return regional monthly baseline forecasts for ``horizon`` periods."""
    return analytics.simple_forecasts(incidents(), horizon=horizon)


@app.get("/api/clusters")
def get_clusters(
    limit: Annotated[int, Query(ge=1, le=MAX_RESULT_LIMIT)] = 8,
) -> list[dict]:
    """Return the leading descriptive incident profiles."""
    return analytics.clusters(incidents(), limit=limit)


@app.get("/api/models")
def get_models() -> list[dict]:
    """Return the project model catalog."""
    return analytics.model_catalog()


@app.get("/api/complexity")
def get_complexity() -> dict[str, Any]:
    """Return algorithm-complexity notes and a live dataframe benchmark."""
    df = incidents()
    return {"catalog": complexity_catalog(), "benchmark": benchmark_dataframe(df)}


@app.get("/api/monitoring/drift")
def get_drift(split_year: int = 2014) -> dict:
    """Compare feature distributions before and after ``split_year``."""
    return drift_report(incidents(), split_year=split_year)


@app.get("/api/policy/panel-summary")
def get_policy_panel_summary() -> dict:
    """Return aggregate policy-panel coverage and source metadata."""
    bundle = policy_bundle()
    return {**bundle["summary"], "sources": bundle["sources"]}


@app.get("/api/policy/results")
def get_policy_results() -> dict:
    """Return policy-analysis model results."""
    return policy_bundle()["results"]


@app.get("/api/policy/event-study")
def get_policy_event_study() -> dict:
    """Return event-study estimates from the policy panel."""
    return policy_bundle()["event_study"]


@app.get("/api/policy/country/{iso3}")
def get_policy_country(iso3: str) -> dict:
    """Return the aggregate policy profile for an ISO alpha-3 country code."""
    return country_policy_profile(policy_bundle()["panel"], iso3)


@app.get("/api/rag/evaluation")
def get_rag_evaluation() -> dict:
    """Run and return the local RAG evaluation suite."""
    return evaluate_rag()


@app.post("/api/predict/severity")
def predict_severity(payload: PredictionRequest) -> dict:
    """Score a validated hypothetical incident with the transparent rule."""
    return analytics.predict_severity_rule(payload.model_dump(), reference_df=incidents())


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict:
    """Answer a validated question using the safe local retriever."""
    response = retriever().answer(payload.question)
    response["policy"] = aggregate_only_note()
    return response
