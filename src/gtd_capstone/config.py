from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    dataset_dir: Path = Path(os.getenv("GTD_DATASET_DIR", "Dataset"))
    artifact_dir: Path = Path(os.getenv("GTD_ARTIFACT_DIR", "artifacts"))
    sample_rows: int = int(os.getenv("GTD_SAMPLE_ROWS", "25000"))
    api_host: str = os.getenv("GTD_API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("GTD_API_PORT", "8000"))
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://gtd:gtd@localhost:5432/gtd"
    )
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "gtd-graph-password")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    wandb_project: str = os.getenv("WANDB_PROJECT", "gtd-capstone")
    wandb_mode: str = os.getenv("WANDB_MODE", "offline")

    @property
    def bronze_dir(self) -> Path:
        return self.artifact_dir / "bronze"

    @property
    def silver_dir(self) -> Path:
        return self.artifact_dir / "silver"

    @property
    def gold_dir(self) -> Path:
        return self.artifact_dir / "gold"


def get_settings() -> Settings:
    return Settings()


def ensure_artifact_dirs(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    for path in [settings.artifact_dir, settings.bronze_dir, settings.silver_dir, settings.gold_dir]:
        path.mkdir(parents=True, exist_ok=True)

