from __future__ import annotations

from collections import Counter, defaultdict
from typing import Hashable

import pandas as pd

from gtd_capstone.dsa.algorithms import UnionFind, build_adjacency


def graph_edges_from_incidents(df: pd.DataFrame) -> list[tuple[str, str, str]]:
    edges: list[tuple[str, str, str]] = []
    for row in df.itertuples(index=False):
        incident = f"Incident:{row.eventid}"
        country = f"Country:{row.country_txt}"
        region = f"Region:{row.region_txt}"
        attack = f"AttackType:{row.attacktype1_txt}"
        target = f"TargetType:{row.targtype1_txt}"
        weapon = f"WeaponType:{row.weaptype1_txt}"
        group = f"Group:{row.gname}"
        year = f"Year:{row.iyear}"
        edges.extend(
            [
                (incident, country, "OCCURRED_IN"),
                (country, region, "PART_OF_REGION"),
                (incident, attack, "USED_ATTACK_TYPE"),
                (incident, target, "TARGETED"),
                (incident, weapon, "USED_WEAPON"),
                (incident, group, "ATTRIBUTED_TO"),
                (incident, year, "HAPPENED_DURING"),
            ]
        )
    return edges


def degree_centrality(df: pd.DataFrame, limit: int = 25) -> list[dict]:
    degree = Counter()
    relation_counts = Counter()
    for left, right, relation in graph_edges_from_incidents(df):
        degree[left] += 1
        degree[right] += 1
        relation_counts[relation] += 1
    return [
        {"node": str(node), "degree": int(value), "algorithm": "degree-centrality"}
        for node, value in degree.most_common(limit)
    ]


def pagerank_baseline(df: pd.DataFrame, iterations: int = 10, damping: float = 0.85) -> list[dict]:
    plain_edges = [(left, right) for left, right, _ in graph_edges_from_incidents(df)]
    adjacency = build_adjacency(plain_edges)
    nodes = list(adjacency)
    if not nodes:
        return []
    rank = {node: 1.0 / len(nodes) for node in nodes}
    for _ in range(iterations):
        next_rank = {node: (1 - damping) / len(nodes) for node in nodes}
        for node, neighbors in adjacency.items():
            if not neighbors:
                continue
            share = rank[node] / len(neighbors)
            for neighbor in neighbors:
                next_rank[neighbor] += damping * share
        rank = next_rank
    return [
        {"node": str(node), "score": float(score), "algorithm": "pagerank-baseline"}
        for node, score in sorted(rank.items(), key=lambda item: item[1], reverse=True)[:25]
    ]


def connected_components(df: pd.DataFrame, limit: int = 20) -> list[dict]:
    edges = [(left, right) for left, right, _ in graph_edges_from_incidents(df)]
    nodes: set[Hashable] = set()
    for left, right in edges:
        nodes.add(left)
        nodes.add(right)
    uf = UnionFind.create(nodes)
    for left, right in edges:
        uf.union(left, right)
    components: dict[Hashable, list[Hashable]] = defaultdict(list)
    for node in nodes:
        components[uf.find(node)].append(node)
    rows = sorted(components.values(), key=len, reverse=True)[:limit]
    return [
        {
            "community_id": index,
            "size": len(component),
            "sample_nodes": [str(node) for node in component[:8]],
            "algorithm": "union-find-connected-components-baseline",
        }
        for index, component in enumerate(rows)
    ]


def neo4j_cypher_schema() -> list[str]:
    return [
        "CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (n:Incident) REQUIRE n.eventid IS UNIQUE;",
        "CREATE INDEX country_name IF NOT EXISTS FOR (n:Country) ON (n.name);",
        "CREATE INDEX group_name IF NOT EXISTS FOR (n:Group) ON (n.name);",
        "CREATE INDEX attack_type_name IF NOT EXISTS FOR (n:AttackType) ON (n.name);",
        "CREATE INDEX target_type_name IF NOT EXISTS FOR (n:TargetType) ON (n.name);",
        "CREATE INDEX weapon_type_name IF NOT EXISTS FOR (n:WeaponType) ON (n.name);",
    ]

