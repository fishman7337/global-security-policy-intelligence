from __future__ import annotations

from pathlib import Path

import pandas as pd

from gtd_capstone.graph.analytics import graph_edges_from_incidents, neo4j_cypher_schema


def export_graph_csv(df: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    edges = graph_edges_from_incidents(df)
    edge_frame = pd.DataFrame(edges, columns=["source", "target", "relationship"])
    nodes = sorted(set(edge_frame["source"]).union(edge_frame["target"]))
    node_frame = pd.DataFrame(
        {
            "node_id": nodes,
            "label": [str(node).split(":", 1)[0] for node in nodes],
            "name": [str(node).split(":", 1)[1] if ":" in str(node) else str(node) for node in nodes],
        }
    )
    node_path = output_dir / "neo4j_nodes.csv"
    edge_path = output_dir / "neo4j_edges.csv"
    cypher_path = output_dir / "neo4j_schema.cypher"
    node_frame.to_csv(node_path, index=False)
    edge_frame.to_csv(edge_path, index=False)
    cypher_path.write_text("\n".join(neo4j_cypher_schema()) + "\n", encoding="utf-8")
    return {"nodes": node_path, "edges": edge_path, "schema": cypher_path}

