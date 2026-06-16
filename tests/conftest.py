"""Pytest bootstrap — make backend/mcat and the tests dir importable.

Lets test modules do `from utils.csv_handler import ...`, `from scrapers... import`,
and `from _fakes import FakeTab` regardless of how pytest is invoked.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
for p in (ROOT / "backend" / "mcat", ROOT / "tests"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)
