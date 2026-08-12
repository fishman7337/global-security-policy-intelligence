# API

This package contains FastAPI application routes and response contracts.

API endpoints should expose aggregate analytics, diagnostics, and policy
research outputs. Keep endpoint behavior covered by tests and avoid adding
incident-level operational guidance.

## Input contracts

- `POST /api/chat` trims the question and accepts between 1 and 2,000
  non-whitespace characters.
- `GET /api/analytics/trends` accepts `year` or `month` grain and one of
  `region_txt`, `country_txt`, `attacktype1_txt`, `targtype1_txt`,
  `weaptype1_txt`, or `severity` for `group_by`.
- `GET /api/analytics/distributions`, `GET /api/geo/hotspots`, and
  `GET /api/clusters` accept limits from 1 to 100, bounding each response.
  Hotspot `min_events` accepts 1 to 10,000 events.
- `GET /api/forecasts` accepts an integer horizon from 1 to 60 monthly
  periods. The five-year ceiling bounds output from a seasonal-naive method
  estimated from a 12-month tail.
- `GET /api/graph/centrality` accepts `degree` or `pagerank`.
- `GET /api/geo/hotspots` accepts the `country` or `city` aggregation level.

FastAPI returns HTTP `422` for requests that violate these contracts, before
loading the incident dataset or running an analysis.
