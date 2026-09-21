# Workspace

## Overview

pnpm workspace monorepo using TypeScript, plus a Python MCP server for Korea Medical Tourism data.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.

## MCP Server (`mcp-server/`)

Python 3.11 MCP (Model Context Protocol) server wrapping the Korea Tourism Organization Medical Tourism API (`MdclTursmService`).

- **Transport**: Streamable HTTP at `/mcp`
- **Port**: 8000 (routed via proxy at `/mcp`)
- **Secret**: `VISITKOREA_API_KEY` — Encoding and Decoding variants are accepted
- **Run**: `uv run visitkorea-mcp` (the legacy `mcp-server/main.py` is a shim)
- **Package**: `src/mcp_server`
- **Tests**: `uv run --frozen python -m unittest discover -s tests -p 'test_*.py'`

### Tools (8 total)
- `get_ldong_code` — administrative district codes
- `get_area_based_list` — facilities by region
- `get_location_based_list` — facilities by GPS radius
- `search_medical_by_keyword` — keyword search
- `get_medical_sync_list` — full sync list
- `get_detail_common` — common detail (title, address, GPS)
- `get_detail_intro` — intro detail (hours, parking)
- `get_detail_medical` — medical detail (specialties, languages)

### MCP Connector JSON
```json
{
  "mcpServers": {
    "visitkorea-medicaltourism": {
      "type": "streamableHttp",
      "url": "https://<your-replit-url>/mcp"
    }
  }
}
```
