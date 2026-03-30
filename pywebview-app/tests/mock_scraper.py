"""
Mock scraper for testing without real browsers.

Reads status results from a scenario file. The run number comes from
MCAT_MOCK_RUN env var (set by the processing handler based on project run count).
URLs not listed in a scenario use the "default" status.

Usage: MCAT_MOCK=1 pnpm dev
"""

import json
import os
import time
from pathlib import Path
from scrapers.base_scraper import BaseScraper, ScrapingResult

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SCENARIO_PATH = FIXTURES_DIR / "scenario.json"


class MockScraper(BaseScraper):
    """Scraper that returns scripted statuses from scenario.json."""

    SIMULATED_DELAY = 0.15  # seconds per URL, fast but visible in progress

    def __init__(self):
        self.cancel_event = None
        self.pause_event = None
        self.run_number = int(os.environ.get("MCAT_MOCK_RUN", "1"))
        self.scenario = self._load_scenario()
        print(f"[MockScraper] Run #{self.run_number}", flush=True)

    def _load_scenario(self) -> dict:
        if not SCENARIO_PATH.exists():
            return {"default": "Live"}
        with open(SCENARIO_PATH, "r") as f:
            data = json.load(f)
        available = sorted([k for k in data.keys() if k.startswith("run_")])
        if not available:
            print(f"[MockScraper] No scenarios found, using all Live", flush=True)
            return {"default": "Live"}
        # Cycle through available scenarios
        idx = (self.run_number - 1) % len(available)
        key = available[idx]
        print(f"[MockScraper] Run #{self.run_number} → using scenario {key}", flush=True)
        return data[key]

    def check_url_status(self, url: str) -> ScrapingResult:
        result = ScrapingResult()
        result.url = url
        result.platform = self.get_platform_name()

        if self.is_cancelled():
            result.status = "Cancelled"
            return result

        if self.pause_event:
            self.pause_event.wait()

        time.sleep(self.SIMULATED_DELAY)

        url_id = self._extract_id(url)
        status = self.scenario.get(url_id, self.scenario.get("default", "Live"))

        result.status = status
        if status == "Removed":
            result.info = "Content removed by platform"
        elif status == "Restricted":
            result.info = "Age-restricted content"
        elif status == "Private":
            result.info = "Private video"

        return result

    def _extract_id(self, url: str) -> str:
        for part in url.split("="):
            if part.startswith("TEST"):
                return part
        return url

    def get_platform_name(self) -> str:
        return "youtube"

    def set_pause_event(self, pause_event):
        self.pause_event = pause_event

    def enable_screenshots(self, enabled: bool, base_path: str) -> None:
        pass
