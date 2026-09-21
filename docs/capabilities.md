# Capabilities

The service exposes exactly eight tools: district codes, area search, location
search, keyword search, synchronization, and common, introductory, and medical
detail records. Every operation returns a list of dictionaries and retains the
VisitKorea endpoint mappings and established defaults. `GET /healthz` is a
liveness endpoint; MCP traffic uses Streamable HTTP at `/mcp`.