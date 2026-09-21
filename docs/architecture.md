# Architecture

The server is a `src/mcp_server` package with explicit boundaries. MCP adapters
in `tools/` validate inputs and delegate to `MedicalTourismService`; only
`clients/visitkorea.py` performs upstream HTTP. `server.py` composes FastMCP
and owns the lifespan, while `transports/http.py` starts Streamable HTTP.
Each lifespan creates and closes its client, preserving stateless requests.