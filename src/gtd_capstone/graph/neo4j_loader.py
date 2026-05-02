from __future__ import annotations

from pathlib import Path

from gtd_capstone.config import get_settings


def load_graph_to_neo4j(
    nodes_csv: Path = Path("artifacts/gold/graph/neo4j_nodes.csv"),
    edges_csv: Path = Path("artifacts/gold/graph/neo4j_edges.csv"),
) -> dict:
    try:
        from neo4j import GraphDatabase
    except Exception as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError("Install optional dependency with `pip install -e .[graph]`.") from exc

    settings = get_settings()
    driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    node_count = 0
    edge_count = 0
    with driver.session() as session:
        session.run("CREATE CONSTRAINT node_id IF NOT EXISTS FOR (n:Node) REQUIRE n.node_id IS UNIQUE")
        with nodes_csv.open(encoding="utf-8") as handle:
            import csv

            for row in csv.DictReader(handle):
                session.run(
                    "MERGE (n:Node {node_id: $node_id}) SET n.name=$name, n.label=$label",
                    row,
                )
                node_count += 1
        with edges_csv.open(encoding="utf-8") as handle:
            import csv

            for row in csv.DictReader(handle):
                session.run(
                    """
                    MATCH (s:Node {node_id: $source})
                    MATCH (t:Node {node_id: $target})
                    MERGE (s)-[r:RELATED {relationship: $relationship}]->(t)
                    """,
                    row,
                )
                edge_count += 1
    driver.close()
    return {"nodes": node_count, "edges": edge_count, "uri": settings.neo4j_uri}

