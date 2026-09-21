# Deployment

Install the root package with `uv sync`, copy the root `.env.example` to `.env`
for local development (or provide the same variables through deployment
secrets), and
start `visitkorea-mcp` (or `python -m mcp_server`). The process listens on
`PORT` (default 8000). Deployments should expose `/mcp` through the HTTPS
proxy and use `/healthz` for liveness checks. No upstream calls are made by
package import or server construction.