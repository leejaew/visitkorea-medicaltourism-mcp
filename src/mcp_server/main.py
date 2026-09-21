"""Console entry point."""

from dotenv import load_dotenv

from .transports.http import run as run_http


def run() -> None:
    """Load local configuration and start the HTTP transport."""
    load_dotenv()
    run_http()


if __name__ == "__main__":
    run()
