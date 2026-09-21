import logging
import unittest

from mcp_server.observability.logging import configure_logging


class SecurityTests(unittest.TestCase):
    def test_http_loggers_are_not_verbose(self):
        configure_logging()
        self.assertGreaterEqual(logging.getLogger("httpx").level, logging.WARNING)
        self.assertGreaterEqual(logging.getLogger("httpcore").level, logging.WARNING)
