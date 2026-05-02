from __future__ import annotations

import heapq
import math
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from typing import Hashable, Iterable

import pandas as pd


def top_k_counter(values: Iterable[Hashable], k: int) -> list[tuple[Hashable, int]]:
    """Top-k frequency via hash table + heap. Complexity: O(n + m log k)."""
    counts = Counter(values)
    return heapq.nlargest(k, counts.items(), key=lambda item: item[1])


def build_adjacency(edges: Iterable[tuple[Hashable, Hashable]]) -> dict[Hashable, set[Hashable]]:
    adjacency: dict[Hashable, set[Hashable]] = defaultdict(set)
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    return dict(adjacency)


def bfs_shortest_path(
    adjacency: dict[Hashable, set[Hashable]],
    start: Hashable,
    goal: Hashable,
) -> list[Hashable]:
    """Unweighted shortest path. Complexity: O(V + E)."""
    if start == goal:
        return [start]
    queue: deque[tuple[Hashable, list[Hashable]]] = deque([(start, [start])])
    seen = {start}
    while queue:
        node, path = queue.popleft()
        for neighbor in adjacency.get(node, set()):
            if neighbor in seen:
                continue
            next_path = [*path, neighbor]
            if neighbor == goal:
                return next_path
            seen.add(neighbor)
            queue.append((neighbor, next_path))
    return []


def dijkstra(
    adjacency: dict[Hashable, list[tuple[Hashable, float]]],
    start: Hashable,
) -> dict[Hashable, float]:
    """Weighted shortest paths. Complexity: O((V + E) log V)."""
    distances: dict[Hashable, float] = defaultdict(lambda: math.inf)
    distances[start] = 0.0
    heap: list[tuple[float, Hashable]] = [(0.0, start)]
    while heap:
        current_distance, node = heapq.heappop(heap)
        if current_distance > distances[node]:
            continue
        for neighbor, weight in adjacency.get(node, []):
            candidate = current_distance + weight
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                heapq.heappush(heap, (candidate, neighbor))
    return dict(distances)


@dataclass
class UnionFind:
    parent: dict[Hashable, Hashable]
    rank: dict[Hashable, int]

    @classmethod
    def create(cls, values: Iterable[Hashable]) -> "UnionFind":
        unique = set(values)
        return cls(parent={value: value for value in unique}, rank={value: 0 for value in unique})

    def find(self, value: Hashable) -> Hashable:
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, left: Hashable, right: Hashable) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        if self.rank[root_left] < self.rank[root_right]:
            self.parent[root_left] = root_right
        elif self.rank[root_left] > self.rank[root_right]:
            self.parent[root_right] = root_left
        else:
            self.parent[root_right] = root_left
            self.rank[root_left] += 1


def complexity_catalog() -> list[dict]:
    return [
        {
            "topic": "Spark bronze/silver ETL",
            "data_structure": "DataFrame partitions, columnar Parquet",
            "complexity": "O(n) scans plus O(n log n) for global sort/dedup shuffles",
            "capstone_use": "Clean 214k GTD rows now; scales to larger historical/security datasets.",
        },
        {
            "topic": "Hash aggregation",
            "data_structure": "dictionary / hash map",
            "complexity": "O(n) expected time, O(k) memory",
            "capstone_use": "Counts by country, attack type, target type, group, and severity.",
        },
        {
            "topic": "Top-k dashboard cards",
            "data_structure": "Counter + heap",
            "complexity": "O(n + k log m) or O(n + m log k)",
            "capstone_use": "Fast top countries, groups, weapons, and hotspots.",
        },
        {
            "topic": "BFS graph traversal",
            "data_structure": "queue + adjacency list",
            "complexity": "O(V + E)",
            "capstone_use": "Explain shortest unweighted connections in the knowledge graph.",
        },
        {
            "topic": "Dijkstra pathfinding",
            "data_structure": "priority queue",
            "complexity": "O((V + E) log V)",
            "capstone_use": "Weighted relationship path exploration when edge costs are meaningful.",
        },
        {
            "topic": "Union-find communities",
            "data_structure": "disjoint set forest",
            "complexity": "Near O(alpha(n)) per operation",
            "capstone_use": "Simple connected components baseline before Neo4j Louvain.",
        },
        {
            "topic": "PageRank",
            "data_structure": "sparse graph",
            "complexity": "O(iterations * E)",
            "capstone_use": "Graph centrality for influential countries, groups, and attack patterns.",
        },
        {
            "topic": "Approximate nearest neighbor retrieval",
            "data_structure": "vector index",
            "complexity": "Sublinear approximate search after indexing",
            "capstone_use": "RAG chatbot over methodology, model cards, and aggregate summaries.",
        },
    ]


def benchmark_dataframe(df: pd.DataFrame) -> dict:
    started = time.perf_counter()
    top_regions = top_k_counter(df["region_txt"], 5)
    topk_seconds = time.perf_counter() - started

    started = time.perf_counter()
    grouped = df.groupby("region_txt").agg(attacks=("eventid", "count")).reset_index()
    groupby_seconds = time.perf_counter() - started

    return {
        "rows": int(len(df)),
        "topk_seconds": round(topk_seconds, 6),
        "groupby_seconds": round(groupby_seconds, 6),
        "top_regions": [{"label": str(label), "count": int(count)} for label, count in top_regions],
        "grouped_rows": int(len(grouped)),
        "notes": "Benchmarks are local smoke measurements; Spark comparisons are generated when PySpark is installed.",
    }

