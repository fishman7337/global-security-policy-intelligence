# Policy Source Registry

This registry separates core analytical sources from robustness and measurement-bias sources.
The project should stay disciplined: the main claim uses a small core panel, while extra datasets
test whether the finding survives alternative measurement choices.

## Core Sources

| Source | Role | URL |
|---|---|---|
| Global Terrorism Database | Terrorism outcomes aggregated to country-year level. | https://www.start.umd.edu/download-global-terrorism-database |
| Worldwide Governance Indicators | Government effectiveness, rule of law, and control of corruption. | https://datacatalog.worldbank.org/search/dataset/0038026/worldwide-governance-indicators |
| World Development Indicators | Population, GDP per capita, urbanization, unemployment, health, and internet controls. | https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators |

## Robustness Sources

| Source | Role | URL |
|---|---|---|
| V-Dem | Democracy measures and regime transformation episodes. | https://v-dem.net/data/ |
| UNDP HDI | Human-development robustness controls. | https://hdr.undp.org/data-center/human-development-index |
| UCDP | Organized-violence and conflict-burden controls. | https://ucdp.uu.se/downloads/ |
| Freedom House | Political-rights and civil-liberties robustness checks. | https://freedomhouse.org/report-types/freedom-world |
| International IDEA | Alternative democracy-performance checks. | https://www.idea.int/data-tools/tools/global-state-democracy-indices |

## Measurement-Bias Sources

| Source | Role |
|---|---|
| WDI internet usage | Proxy for media/information access that may affect terrorism reporting. |
| Press-freedom datasets | Optional reporting-bias sensitivity checks when supplied as normalized files. |

## Implementation Notes

The build command can fetch credential-free World Bank indicators:

```powershell
python -m gtd_capstone.pipelines.build_artifacts --fetch-policy-sources
```

Optional non-World-Bank sources should be normalized to `iso3`, `year`, and named variables, then
placed under `Dataset/policy/`. This keeps the pipeline reproducible without embedding private
API credentials or brittle scraping logic.

ACLED is excluded from v1 because it requires registration and would shift the project toward
near-real-time conflict monitoring rather than historical public-policy research.
