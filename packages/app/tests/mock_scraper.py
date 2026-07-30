"""
Mock scraper for testing without real browsers.

Reads status results from a scenario file. The run number comes from
MCAT_MOCK_RUN env var (set by the processing handler based on project run count).
URLs not listed in a scenario use the "default" status.

Usage: MCAT_MOCK=1 pnpm dev
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from scrapers.base_scraper import BaseScraper, ScrapingResult

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SCENARIO_PATH = FIXTURES_DIR / "scenario.json"

# 1x1 PNG — smallest valid image (transparent pixel)
DUMMY_PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c6300010000000500010d0a2db40000000049454e44ae426082"
)


class MockScraper(BaseScraper):
    """Scraper that returns scripted statuses from scenario.json."""

    SIMULATED_DELAY = 0.15  # seconds per URL, fast but visible in progress

    def __init__(self):
        self.cancel_event = None
        self.pause_event = None
        self.run_number = int(os.environ.get("MCAT_MOCK_RUN", "1"))
        self.scenario = self._load_scenario()
        self.save_screenshots: bool = False
        self.screenshot_base_path: Optional[Path] = None
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

    async def check_url_status(self, url: str) -> ScrapingResult:
        result = ScrapingResult()
        result.url = url

        if self.is_cancelled():
            result.status = "Cancelled"
            return result

        await self._check_pause()

        await asyncio.sleep(self.SIMULATED_DELAY)

        url_id = self._extract_id(url)
        status = self.scenario.get(url_id, self.scenario.get("default", "Live"))

        result.status = status
        result.info = {
            "Unavailable": "Content no longer available",
            "Moderated": "Taken down by the platform",
            "Restricted": "Age-restricted content",
            "Login Required": "Requires sign-in to view",
        }.get(status, "")

        if self.save_screenshots:
            result.screenshot_path = self._save_screenshot(url, status)

        return result

    def _save_screenshot(self, url: str, status: str) -> str:
        if not self.screenshot_base_path:
            return ""
        try:
            url_id = self._extract_id(url)
            screenshot_dir = self.screenshot_base_path / status.lower()
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = screenshot_dir / f"{url_id}_{timestamp}.png"
            filepath.write_bytes(DUMMY_PNG_BYTES)
            return str(filepath)
        except Exception as e:
            print(f"[MockScraper] Screenshot save failed: {e}", flush=True)
            return ""

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
        self.save_screenshots = enabled
        if enabled:
            self.screenshot_base_path = Path(base_path) / "screenshots"
