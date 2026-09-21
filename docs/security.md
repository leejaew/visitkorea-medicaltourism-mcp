# Security

`VISITKOREA_API_KEY` is loaded only from the environment and is excluded from
cache keys and application errors. HTTP client loggers are raised to WARNING
to prevent query-string credentials from reaching stderr. Host and Origin
allow-lists are configured through `MCP_ALLOWED_HOSTS`, `MCP_ALLOWED_ORIGINS`,
and the Replit domain fallback. TLS verification remains enabled.