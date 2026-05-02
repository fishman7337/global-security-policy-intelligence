$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src;$env:PYTHONPATH"
python -m gtd_capstone.pipelines.build_artifacts --fetch-policy-sources
python -m gtd_capstone.rag.evaluate --output artifacts/gold/rag_eval.json
@'
from pathlib import Path
from gtd_capstone.graph.gds_playbook import write_gds_playbook
print(write_gds_playbook(Path("artifacts/gold/graph/neo4j_gds_playbook.cypher")))
'@ | python -
