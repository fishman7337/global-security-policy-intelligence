from __future__ import annotations

import json
import sys
from typing import Any

from gtd_capstone import analytics
from gtd_capstone.data.repository import DataRepository
from gtd_capstone.graph.analytics import connected_components, degree_centrality
from gtd_capstone.rag.retriever import LocalRetriever


class ReadOnlyMCPServer:
    """Small JSON-RPC MCP-compatible server for local read-only GTD tools."""

    def __init__(self) -> None:
        self.repo = DataRepository()
        self.retriever = LocalRetriever()

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        request_id = message.get("id")
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2025-06-18",
                    "serverInfo": {"name": "gtd-capstone-readonly", "version": "0.1.0"},
                    "capabilities": {"tools": {"listChanged": False}, "resources": {}},
                }
            elif method == "tools/list":
                result = {"tools": self.tools()}
            elif method == "tools/call":
                params = message.get("params", {})
                result = self.call_tool(params.get("name"), params.get("arguments", {}))
            elif method == "resources/list":
                result = {"resources": self.resources()}
            elif method == "resources/read":
                uri = message.get("params", {}).get("uri", "")
                result = self.read_resource(uri)
            elif method and method.startswith("notifications/"):
                return None
            else:
                raise ValueError(f"Unsupported method: {method}")
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(exc)},
            }

    def tools(self) -> list[dict]:
        return [
            {
                "name": "get_schema",
                "title": "Get GTD Schema",
                "description": "Return curated incident columns and aggregate-only policy.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "query_aggregate_trends",
                "title": "Query Aggregate Trends",
                "description": "Return year or month aggregate trends from curated GTD data.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "grain": {"type": "string", "enum": ["year", "month"], "default": "year"}
                    },
                },
            },
            {
                "name": "get_hotspots",
                "title": "Get Aggregate Hotspots",
                "description": "Return country or city aggregate hotspots with minimum event thresholds.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string", "enum": ["country", "city"], "default": "country"}
                    },
                },
            },
            {
                "name": "get_forecast",
                "title": "Get Forecast",
                "description": "Return aggregate monthly forecast outputs.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "get_model_card",
                "title": "Get Model Card",
                "description": "Return model catalog and safety caveats.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "search_rag",
                "title": "Search RAG Corpus",
                "description": "Search documentation and aggregate methodology corpus.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
            {
                "name": "get_graph_profile",
                "title": "Get Graph Profile",
                "description": "Return graph centrality and community summaries.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    def resources(self) -> list[dict]:
        return [
            {
                "uri": "gtd://docs/ethics",
                "name": "Ethics Policy",
                "mimeType": "text/markdown",
                "description": "Aggregate-only safety and responsible AI policy.",
            },
            {
                "uri": "gtd://docs/complexity",
                "name": "Complexity Report",
                "mimeType": "text/markdown",
                "description": "DSA and runtime complexity notes.",
            },
        ]

    def read_resource(self, uri: str) -> dict:
        if uri == "gtd://docs/ethics":
            text = "Historical aggregate analysis only; no tactical, targeting, or operational guidance."
        elif uri == "gtd://docs/complexity":
            text = json.dumps(analytics.model_catalog(), indent=2)
        else:
            raise ValueError("Unknown resource URI.")
        return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]}

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict:
        df = self.repo.load_incidents()
        if name == "get_schema":
            return self.tool_text({"columns": list(df.columns), "aggregate_only": True})
        if name == "query_aggregate_trends":
            return self.tool_json(analytics.trend_points(df, grain=arguments.get("grain", "year")))
        if name == "get_hotspots":
            return self.tool_json(analytics.hotspots(df, level=arguments.get("level", "country")))
        if name == "get_forecast":
            return self.tool_json(analytics.simple_forecasts(df))
        if name == "get_model_card":
            return self.tool_json(analytics.model_catalog())
        if name == "search_rag":
            return self.tool_json(self.retriever.search(arguments["query"]))
        if name == "get_graph_profile":
            return self.tool_json(
                {
                    "centrality": degree_centrality(df),
                    "communities": connected_components(df),
                }
            )
        raise ValueError(f"Unknown tool: {name}")

    @staticmethod
    def tool_json(payload: Any) -> dict:
        return {"content": [{"type": "text", "text": json.dumps(payload, indent=2, default=str)}]}

    @staticmethod
    def tool_text(payload: Any) -> dict:
        return {"content": [{"type": "text", "text": json.dumps(payload, indent=2, default=str)}]}


def main() -> None:
    server = ReadOnlyMCPServer()
    for line in sys.stdin:
        if not line.strip():
            continue
        response = server.handle(json.loads(line))
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()

