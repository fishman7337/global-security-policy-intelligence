from __future__ import annotations

from pathlib import Path


GDS_QUERIES = {
    "projection": """
CALL gds.graph.project(
  'gtd-knowledge-graph',
  ['Incident', 'Country', 'Region', 'Group', 'AttackType', 'TargetType', 'WeaponType', 'Year'],
  {
    OCCURRED_IN: {orientation: 'UNDIRECTED'},
    PART_OF_REGION: {orientation: 'UNDIRECTED'},
    USED_ATTACK_TYPE: {orientation: 'UNDIRECTED'},
    TARGETED: {orientation: 'UNDIRECTED'},
    USED_WEAPON: {orientation: 'UNDIRECTED'},
    ATTRIBUTED_TO: {orientation: 'UNDIRECTED'},
    HAPPENED_DURING: {orientation: 'UNDIRECTED'}
  }
);
""",
    "pagerank": """
CALL gds.pageRank.write('gtd-knowledge-graph', {
  maxIterations: 30,
  dampingFactor: 0.85,
  writeProperty: 'pagerank'
})
YIELD nodePropertiesWritten, ranIterations;
""",
    "louvain": """
CALL gds.louvain.write('gtd-knowledge-graph', {
  writeProperty: 'communityId'
})
YIELD communityCount, modularity;
""",
    "node_similarity": """
CALL gds.nodeSimilarity.write('gtd-knowledge-graph', {
  writeRelationshipType: 'SIMILAR_TO',
  writeProperty: 'score',
  topK: 10
})
YIELD nodesCompared, relationshipsWritten;
""",
    "fastrp": """
CALL gds.fastRP.write('gtd-knowledge-graph', {
  embeddingDimension: 128,
  iterationWeights: [0.8, 1.0, 1.0, 1.0],
  writeProperty: 'fastrpEmbedding'
})
YIELD nodePropertiesWritten;
""",
    "country_profile": """
MATCH (c:Country)
RETURN c.name AS country, c.pagerank AS pagerank, c.communityId AS community
ORDER BY pagerank DESC
LIMIT 25;
""",
}


def write_gds_playbook(path: Path = Path("artifacts/gold/graph/neo4j_gds_playbook.cypher")) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n\n".join(f"// {name}\n{query.strip()}" for name, query in GDS_QUERIES.items())
    path.write_text(text + "\n", encoding="utf-8")
    return path


def gds_query_catalog() -> list[dict]:
    return [{"name": name, "cypher": query.strip()} for name, query in GDS_QUERIES.items()]

