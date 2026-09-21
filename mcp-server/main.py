"""Compatibility launcher; the implementation lives in the src package."""

import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
run = import_module("mcp_server.main").run


if __name__ == "__main__":
    run()
