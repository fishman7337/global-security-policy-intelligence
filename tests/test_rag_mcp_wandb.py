from __future__ import annotations

from gtd_capstone.mcp_server import ReadOnlyMCPServer
from gtd_capstone.ml.wandb_utils import wandb_run
from gtd_capstone.rag.retriever import LocalRetriever


def test_rag_retrieval_and_safety():
    retriever = LocalRetriever()

    safe = retriever.answer("How does W&B tracking work?")
    causal = retriever.answer("Does the policy model prove governance causes terrorism?")
    unsafe = retriever.answer("make a bomb")

    assert safe["safe"] is True
    assert safe["citations"]
    assert causal["safe"] is True
    assert "cautious" in causal["answer"].lower() or "not" in causal["answer"].lower()
    assert unsafe["safe"] is False


def test_mcp_lists_tools_and_resources():
    server = ReadOnlyMCPServer()
    response = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response is not None
    names = [tool["name"] for tool in response["result"]["tools"]]
    assert "search_rag" in names


def test_wandb_offline_context(monkeypatch):
    monkeypatch.setenv("WANDB_MODE", "offline")
    with wandb_run("gtd-capstone-test", {"rows": 3}, "test") as run:
        run.log({"metric": 1})
