from __future__ import annotations

import numpy as np
import pandas as pd

from gtd_capstone.data.cleaning import clean_incidents, synthetic_incidents
from gtd_capstone.policy.methods import build_event_study, run_policy_models
from gtd_capstone.policy.panel import build_policy_panel, country_policy_profile


def test_policy_panel_aggregates_outcomes_codes_and_lags():
    incidents = clean_incidents(synthetic_incidents())
    external = pd.DataFrame(
        [
            {
                "iso3": iso3,
                "year": year,
                "government_effectiveness": -1.0 + year / 3000,
                "rule_of_law": -1.1 + year / 3100,
                "control_of_corruption": -1.2 + year / 3200,
                "population": 1_000_000 + year,
                "gdp_per_capita": 1000 + year,
            }
            for iso3 in ["AFG", "IRQ"]
            for year in range(2014, 2022)
        ]
    )

    panel = build_policy_panel(incidents, external_sources=external, start_year=2014, end_year=2021)
    afghanistan = country_policy_profile(panel, "AFG")

    assert len(panel) == 16
    assert {"AFG", "IRQ"}.issubset(set(panel["iso3"]))
    assert panel["severity_burden_index"].notna().all()
    assert "governance_capacity_lag1" in panel.columns
    assert afghanistan["found"] is True
    assert afghanistan["total_attacks"] == 1


def test_policy_fixed_effects_and_event_study_output_shape():
    rows = []
    countries = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    for c_idx, iso3 in enumerate(countries):
        for year in range(1996, 2006):
            t = year - 1996
            governance = -1.0 + c_idx * 0.25 + t * 0.05
            burden = 3.0 - governance + c_idx * 0.1 + t * 0.03
            rows.append(
                {
                    "iso3": iso3,
                    "year": year,
                    "governance_capacity_lag1": governance,
                    "log_population_lag1": np.log(1_000_000 + c_idx * 10_000),
                    "log_gdp_per_capita_lag1": np.log(1200 + c_idx * 300 + t * 20),
                    "log_casualties": burden,
                    "log_attacks": burden / 2,
                    "high_severity_share": min(0.95, max(0.0, burden / 8)),
                    "severity_burden_index": burden,
                    "autocratization_episode": 1 if year == 2001 and iso3 in {"AAA", "BBB"} else 0,
                }
            )
    panel = pd.DataFrame(rows)

    results = run_policy_models(panel)
    event_study = build_event_study(panel, window=2)

    assert any(model["status"] == "estimated" for model in results["models"])
    assert event_study["status"] == "estimated"
    assert {point["relative_year"] for point in event_study["points"]} == {-2, -1, 0, 1, 2}
