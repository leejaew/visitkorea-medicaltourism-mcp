"""Compatibility launcher for the VisitKorea Medical Tourism MCP server."""

from dotenv import load_dotenv

from visitkorea_mcp.server import run


if __name__ == "__main__":
    load_dotenv()
    run()