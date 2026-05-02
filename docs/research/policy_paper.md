# Governance Capacity and Terrorism Severity Burden

## Abstract

This research extension studies whether governance capacity is associated with lower terrorism
severity burden in a global country-year panel. The terrorism outcomes come from the Global
Terrorism Database and are aggregated to country-year level for historical public-policy analysis.
The main explanatory construct combines World Bank Worldwide Governance Indicators for
government effectiveness, rule of law, and control of corruption.

The design uses country fixed effects, year fixed effects, one-year lagged governance variables,
and development controls. The results should be read as cautious causal-policy evidence, not as
operational prediction or a standalone proof of causality.

## Research Question

How does governance capacity relate to terrorism severity burden after accounting for stable
country differences, global year shocks, development conditions, and conflict context?

## Main Hypothesis

Countries with stronger governance capacity will tend to have lower annual terrorism severity
burden, measured through casualties, attack frequency, high-severity share, and a composite
severity burden index.

## Data

- GTD: country-year attacks, fatalities, wounded, casualties, high-severity share, and mass-casualty counts.
- WGI: government effectiveness, rule of law, and control of corruption.
- WDI: population, GDP per capita, urbanization, unemployment, life expectancy, and internet access.
- V-Dem: democracy and regime transformation variables when supplied as normalized local data.
- UCDP: organized-violence controls when supplied as normalized local data.
- Freedom House and International IDEA: alternative democracy robustness checks.

The primary analysis window is 1996-2021, matching WGI availability and the local GTD files.

## Identification Strategy

The main specification estimates country and year fixed-effects models:

`outcome_country_year ~ lagged_governance_capacity + controls + country FE + year FE`

Country fixed effects absorb time-invariant country traits. Year fixed effects absorb global shocks
shared across countries. Lagged governance variables reduce simultaneity concerns but do not
eliminate all endogeneity.

## Outcomes

- `log1p(casualties)`
- `log1p(attacks)`
- `high_severity_share`
- `severity_burden_index`

The severity burden index averages standardized annual attack volume, casualty volume,
high-severity share, and mass-casualty counts.

## Robustness Plan

- Replace the governance-capacity index with each WGI component.
- Add WGI political stability only as a robustness variable because it overlaps with violence.
- Add conflict burden controls from UCDP where available.
- Add democracy measures from V-Dem, Freedom House, or International IDEA.
- Re-estimate excluding selected regions and comparing pre/post-2011 periods.
- Add media and reporting-bias proxies such as internet access or press-freedom scores.

## Policy Interpretation

The intended policy contribution is institutional and preventive: better governance capacity may
matter through rule enforcement, service delivery, legitimacy, corruption reduction, and conflict
management. The system does not recommend tactical interventions, targets, or operational action.

## Limitations

Terrorism event data are shaped by media access, state reporting capacity, source availability,
and coding uncertainty. Governance indicators are perception-based and may themselves reflect
security conditions. Fixed effects make the comparison stronger than raw correlations, but the
project uses cautious causal language unless a future quasi-experimental design is added.
