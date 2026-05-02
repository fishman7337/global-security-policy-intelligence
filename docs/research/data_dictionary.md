# Policy Panel Data Dictionary

The policy panel lives at `artifacts/gold/policy/country_year_panel.parquet`.

## Keys

| Column | Meaning |
|---|---|
| `iso3` | ISO-3 country code used for source joins. |
| `country_txt` | GTD country name. |
| `region_txt` | GTD region name. |
| `year` | Calendar year. |

## GTD Outcomes

| Column | Meaning |
|---|---|
| `attacks` | Number of GTD incidents in the country-year. |
| `fatalities` | Sum of GTD `nkill`. |
| `wounded` | Sum of GTD `nwound`. |
| `casualties` | Fatalities plus wounded. |
| `high_severity_count` | Incidents labelled High or Mass Casualty by the adaptive OPTICS severity layer. |
| `mass_casualty_count` | Incidents labelled Mass Casualty by the adaptive OPTICS severity layer. |
| `high_severity_share` | High-severity incidents divided by attacks. |
| `severity_burden_index` | Average of standardized log attacks, log casualties, high-severity share, and mass-casualty count. |

Incident-level `severity` is produced by the silver pipeline using logged casualty-burden features
and OPTICS density clustering. `severity_score`, `severity_score_percentile`, `severity_cluster`,
and `severity_method` record how the label was assigned.

## Governance Variables

| Column | Source | Main Use |
|---|---|---|
| `government_effectiveness` | WGI | Main governance-capacity component. |
| `rule_of_law` | WGI | Main governance-capacity component. |
| `control_of_corruption` | WGI | Main governance-capacity component. |
| `governance_capacity` | Derived | Row mean of the three main governance components. |
| `political_stability` | WGI | Robustness only due conceptual overlap with violence. |
| `voice_accountability` | WGI | Robustness. |
| `regulatory_quality` | WGI | Robustness. |

Lagged versions use the `_lag1` suffix and are created within each country.

## Development Controls

| Column | Source | Main Use |
|---|---|---|
| `population` | WDI | Scale control. |
| `gdp_per_capita` | WDI | Development control. |
| `urban_population_pct` | WDI | Urbanization control. |
| `unemployment_pct` | WDI | Labor-market control. |
| `life_expectancy` | WDI | Human-development proxy. |
| `internet_users_pct` | WDI | Reporting/media-access proxy. |

## Optional Robustness Inputs

Normalized local files can be placed in `Dataset/policy/` as `.csv`, `.xlsx`, or `.parquet`.
They must include `iso3` and `year`. Recognized optional variables include:

- `vdem_electoral_democracy`
- `vdem_liberal_democracy`
- `vdem_regime_type`
- `autocratization_episode`
- `democratization_episode`
- `hdi`
- `ucdp_best_fatalities`
- `freedom_house_total`
- `press_freedom_score`

## Safety Boundary

The panel is country-year aggregate only. It is designed for historical public-policy analysis and
must not be used for tactical forecasting, targeting, or operational recommendations.
