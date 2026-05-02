"""Repository helpers for loading GTD artifacts and source extracts."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

from gtd_capstone.config import Settings, get_settings
from gtd_capstone.data.cleaning import clean_incidents, discover_excel_sources, read_excel_sources


class DataRepository:
    """Load GTD data products from configured local artifact locations.

    Args:
        settings: Optional project settings override.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the repository with project settings."""
        self.settings = settings or get_settings()

    def load_incidents(self, sample_rows: int | None = None) -> pd.DataFrame:
        """Load cleaned incident rows from gold, silver, or raw source data.

        Args:
            sample_rows: Optional row limit used for smoke tests.

        Returns:
            Cleaned incident dataframe.
        """
        gold_path = self.settings.gold_dir / "incidents.parquet"
        silver_path = self.settings.silver_dir / "incidents.parquet"
        for path in [gold_path, silver_path]:
            if path.exists():
                frame = pd.read_parquet(path)
                return frame.head(sample_rows) if sample_rows else frame

        sources = discover_excel_sources(self.settings.dataset_dir)
        frame = read_excel_sources(sources, sample_rows=sample_rows or self.settings.sample_rows)
        return clean_incidents(frame)

    def load_quality(self) -> dict:
        """Load or compute the current data-quality report.

        Returns:
            JSON-serializable data-quality report.
        """
        quality_path = self.settings.gold_dir / "data_quality.json"
        if quality_path.exists():
            return json.loads(quality_path.read_text(encoding="utf-8"))
        from gtd_capstone.data.cleaning import data_quality_report

        return data_quality_report(self.load_incidents())

    def artifact_path(self, *parts: str) -> Path:
        """Build a path below the configured artifact directory.

        Args:
            *parts: Path components below `settings.artifact_dir`.

        Returns:
            Joined artifact path.
        """
        return self.settings.artifact_dir.joinpath(*parts)


@lru_cache(maxsize=1)
def get_repository() -> DataRepository:
    """Return a cached default data repository.

    Returns:
        Repository configured from environment-backed settings.
    """
    return DataRepository()
