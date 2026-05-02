from __future__ import annotations

from pathlib import Path


def spark_session(app_name: str = "gtd-extreme-pipeline"):
    try:
        from pyspark.sql import SparkSession
    except Exception as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError(
            "PySpark is not installed. Install optional dependency with `pip install -e .[bigdata]`."
        ) from exc

    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.shuffle.partitions", "16")
        .getOrCreate()
    )


def clean_with_spark(input_parquet: Path, output_parquet: Path) -> dict:
    """Spark-native silver transform for larger-than-memory GTD-style extracts."""
    from pyspark.sql import Window, functions as F

    spark = spark_session()
    df = spark.read.parquet(str(input_parquet))
    cleaned = (
        df.withColumn("eventid", F.col("eventid").cast("string"))
        .dropDuplicates(["eventid"])
        .withColumn("iyear", F.col("iyear").cast("int"))
        .withColumn("imonth", F.coalesce(F.col("imonth").cast("int"), F.lit(0)))
        .withColumn("iday", F.coalesce(F.col("iday").cast("int"), F.lit(0)))
        .withColumn("nkill", F.greatest(F.coalesce(F.col("nkill").cast("double"), F.lit(0.0)), F.lit(0.0)))
        .withColumn("nwound", F.greatest(F.coalesce(F.col("nwound").cast("double"), F.lit(0.0)), F.lit(0.0)))
        .withColumn("casualties", F.col("nkill") + F.col("nwound"))
        .withColumn(
            "severity_score",
            F.log(F.col("casualties") + F.lit(1.0))
            + F.lit(0.75) * F.log(F.col("nkill") + F.lit(1.0))
            + F.lit(0.25) * F.log(F.col("nwound") + F.lit(1.0)),
        )
        .withColumn(
            "severity_score_percentile",
            F.when(F.col("casualties") <= 0, F.lit(0.0)).otherwise(
                F.percent_rank().over(Window.orderBy("severity_score"))
            ),
        )
        .withColumn("severity_cluster", F.lit(-1))
        .withColumn(
            "severity_method",
            F.when(F.col("casualties") <= 0, "none-casualty").otherwise(
                "spark-adaptive-percentile-fallback"
            ),
        )
        .withColumn(
            "severity",
            F.when(F.col("casualties") <= 0, "None")
            .when(F.col("severity_score_percentile") <= 0.55, "Low")
            .when(F.col("severity_score_percentile") <= 0.80, "Medium")
            .when(F.col("severity_score_percentile") <= 0.95, "High")
            .otherwise("Mass Casualty"),
        )
        .withColumn(
            "valid_coordinates",
            F.col("latitude").between(-90, 90) & F.col("longitude").between(-180, 180),
        )
        .withColumn("year_month", F.format_string("%04d-%02d", F.col("iyear"), F.greatest(F.col("imonth"), F.lit(1))))
    )
    cleaned.write.mode("overwrite").parquet(str(output_parquet))
    rows = cleaned.count()
    spark.stop()
    return {"rows": int(rows), "output": str(output_parquet), "engine": "spark"}


def spark_sql_gold_views(silver_parquet: Path, output_dir: Path) -> dict:
    spark = spark_session("gtd-gold-views")
    df = spark.read.parquet(str(silver_parquet))
    df.createOrReplaceTempView("incidents")
    trend = spark.sql(
        """
        SELECT iyear, region_txt, COUNT(*) attacks, SUM(nkill) fatalities, SUM(nwound) wounded
        FROM incidents
        GROUP BY iyear, region_txt
        ORDER BY iyear, region_txt
        """
    )
    hotspots = spark.sql(
        """
        SELECT country_txt, COUNT(*) attacks, SUM(nkill) fatalities, SUM(nwound) wounded,
               AVG(latitude) latitude, AVG(longitude) longitude
        FROM incidents
        WHERE valid_coordinates
        GROUP BY country_txt
        HAVING attacks >= 5
        ORDER BY attacks DESC
        """
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    trend.write.mode("overwrite").parquet(str(output_dir / "spark_trend_region_year"))
    hotspots.write.mode("overwrite").parquet(str(output_dir / "spark_hotspots_country"))
    spark.stop()
    return {"trend": str(output_dir / "spark_trend_region_year"), "hotspots": str(output_dir / "spark_hotspots_country")}
