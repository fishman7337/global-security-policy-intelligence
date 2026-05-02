from __future__ import annotations

from pathlib import Path

import pandas as pd


STREAM_COLUMNS = ["eventid", "iyear", "region_txt", "country_txt", "attacktype1_txt", "nkill", "nwound"]


def create_micro_batches(input_parquet: Path, output_dir: Path, batch_size: int = 1000) -> dict:
    """Create deterministic file-streaming micro-batches for Spark Structured Streaming demos."""
    output_dir.mkdir(parents=True, exist_ok=True)
    all_columns = pd.read_parquet(input_parquet).columns
    df = pd.read_parquet(input_parquet, columns=[c for c in STREAM_COLUMNS if c in all_columns])
    written = 0
    for index, start in enumerate(range(0, len(df), batch_size)):
        batch = df.iloc[start : start + batch_size]
        if batch.empty:
            continue
        batch.to_csv(output_dir / f"batch_{index:04d}.csv", index=False)
        written += 1
    return {"batches": written, "rows": int(len(df)), "output_dir": str(output_dir)}


def structured_streaming_query(input_dir: Path, checkpoint_dir: Path, output_dir: Path) -> str:
    """Return the Spark query skeleton instead of launching a long-running stream by default."""
    return f"""
from pyspark.sql import SparkSession, functions as F
spark = SparkSession.builder.appName("gtd-streaming-demo").getOrCreate()
schema = "eventid STRING, iyear INT, region_txt STRING, country_txt STRING, attacktype1_txt STRING, nkill DOUBLE, nwound DOUBLE"
stream = spark.readStream.schema(schema).option("header", True).csv(r"{input_dir}")
agg = stream.groupBy("iyear", "region_txt").agg(F.count("*").alias("attacks"), F.sum("nkill").alias("fatalities"))
query = agg.writeStream.outputMode("complete").format("parquet").option("checkpointLocation", r"{checkpoint_dir}").start(r"{output_dir}")
query.awaitTermination()
"""
