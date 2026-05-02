from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from gtd_capstone.config import get_settings
from gtd_capstone.data.repository import DataRepository


WAREHOUSE_COLUMNS = [
    "eventid",
    "iyear",
    "imonth",
    "iday",
    "incident_date",
    "year_month",
    "country_txt",
    "region_txt",
    "provstate",
    "city",
    "latitude",
    "longitude",
    "attacktype1_txt",
    "targtype1_txt",
    "weaptype1_txt",
    "gname",
    "success",
    "suicide",
    "nkill",
    "nwound",
    "casualties",
    "severity",
    "valid_coordinates",
    "geo_precision",
]


def load_postgis(database_url: str | None = None, schema_path: Path = Path("db/schema.sql")) -> dict:
    settings = get_settings()
    database_url = database_url or settings.database_url
    engine = create_engine(database_url)
    df = DataRepository(settings).load_incidents()
    frame = df[[column for column in WAREHOUSE_COLUMNS if column in df.columns]].copy()
    frame["incident_date"] = pd.to_datetime(frame["incident_date"], errors="coerce").dt.date

    with engine.begin() as conn:
        conn.execute(text(schema_path.read_text(encoding="utf-8")))
        conn.execute(text("TRUNCATE TABLE incidents;"))
        frame.to_sql("incidents", conn, if_exists="append", index=False, method="multi", chunksize=2000)
        conn.execute(
            text(
                """
                UPDATE incidents
                SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                WHERE valid_coordinates = TRUE;
                """
            )
        )
    return {"table": "incidents", "rows": int(len(frame)), "database_url": database_url}


def main() -> None:
    parser = argparse.ArgumentParser(description="Load curated GTD incidents into PostGIS.")
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()
    print(load_postgis(args.database_url))


if __name__ == "__main__":
    main()

