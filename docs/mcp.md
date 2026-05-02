# MCP Server

The local MCP server is read-only and exposes safe aggregate GTD tools.

Run:

```powershell
python -m gtd_capstone.mcp_server
```

Tools:

- `get_schema`
- `query_aggregate_trends`
- `get_hotspots`
- `get_forecast`
- `get_model_card`
- `search_rag`
- `get_graph_profile`

The server does not expose arbitrary SQL, shell commands, file writes, or destructive operations.

