# Data Structures and Algorithms Complexity Report

The capstone exposes algorithmic thinking explicitly instead of hiding it behind libraries.

| Component | Data Structure | Complexity | Use |
|---|---|---|---|
| Cleaning scans | DataFrame partitions | O(n) | Type conversion, null handling, coordinate validation |
| Deduplication | Hash set / distributed shuffle | O(n) expected locally | `eventid` uniqueness |
| Aggregations | Hash map | O(n) expected | Counts by region, country, attack type, target type |
| Top-k cards | Counter + heap | O(n + m log k) | Top countries, groups, weapons, hotspots |
| BFS | Queue + adjacency list | O(V + E) | Shortest unweighted graph paths |
| Dijkstra | Priority queue | O((V + E) log V) | Weighted graph pathfinding extension |
| Union-find | Disjoint set forest | Almost O(1) amortized | Connected-component community baseline |
| PageRank | Sparse adjacency graph | O(iterations × E) | Graph centrality |
| KMeans-style clustering | Matrix arrays | O(iterations × n × k × d) | Incident profile clustering |
| Vector retrieval | ANN index | Approximate sublinear search | RAG retrieval over docs and model cards |

Benchmarks are exposed through `GET /api/complexity` and generated into gold artifacts by `python -m gtd_capstone.pipelines.build_artifacts`.

