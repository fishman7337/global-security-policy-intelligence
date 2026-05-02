from __future__ import annotations

from gtd_capstone.data.cleaning import clean_incidents, synthetic_incidents
from gtd_capstone.dsa.algorithms import bfs_shortest_path, build_adjacency, top_k_counter
from gtd_capstone.graph.analytics import connected_components, degree_centrality


def test_top_k_counter_and_bfs():
    assert top_k_counter(["a", "b", "a", "c"], 2)[0] == ("a", 2)
    adjacency = build_adjacency([("A", "B"), ("B", "C")])

    assert bfs_shortest_path(adjacency, "A", "C") == ["A", "B", "C"]


def test_graph_baselines_return_profiles():
    df = clean_incidents(synthetic_incidents())

    assert degree_centrality(df)
    assert connected_components(df)

