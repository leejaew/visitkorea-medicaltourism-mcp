"""Streamable HTTP startup boundary."""

from ..server import create_server


def run() -> None:
    create_server().run(transport="streamable-http")
