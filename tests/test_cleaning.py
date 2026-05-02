from __future__ import annotations

from gtd_capstone.data.cleaning import clean_incidents, data_quality_report, synthetic_incidents


def test_clean_incidents_adds_dates_severity_and_geo_flags():
    df = clean_incidents(synthetic_incidents())

    assert df["eventid"].is_unique
    assert {
        "incident_date",
        "year_month",
        "severity",
        "severity_cluster",
        "severity_score",
        "severity_method",
        "valid_coordinates",
    }.issubset(df.columns)
    assert set(df["severity"]).issubset({"None", "Low", "Medium", "High", "Mass Casualty"})
    assert df["severity_score"].ge(0).all()
    assert df["severity_method"].str.startswith("adaptive-").any()
    assert df["valid_coordinates"].all()


def test_data_quality_report_has_expected_checks():
    df = clean_incidents(synthetic_incidents())
    report = data_quality_report(df)

    assert report["rows"] == 3
    assert report["duplicate_eventids"] == 0
    assert all("passed" in check for check in report["checks"])
