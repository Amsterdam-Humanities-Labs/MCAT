"""Mock scraper factory for MCAT_MOCK mode.

Provides a factory function that creates MockScraper instances,
used by BatchProcessor via dependency injection.
"""

import os
import sys
from pathlib import Path

tests_dir = str(Path(__file__).parent)
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

from mock_scraper import MockScraper

_run_count = 0


def create_mock_scraper(platform: str) -> MockScraper:
    """Factory that returns a MockScraper regardless of platform."""
    global _run_count
    _run_count += 1
    os.environ["MCAT_MOCK_RUN"] = str(_run_count)
    return MockScraper()
