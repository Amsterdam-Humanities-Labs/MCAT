from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from scrapers.base_scraper import BaseScraper
from cookies.instagram_cookie_handler import dismiss_instagram_cookies


class InstagramScraper(BaseScraper):
    """Instagram post status checker (detection only; flow is in BaseScraper)."""

    RATE_LIMIT_MIN = 1.5
    RATE_LIMIT_MAX = 3.5

    REMOVAL_PHRASES = (
        "post isn't available",
        "sorry, this page isn't available",
        "this page isn't available",
        "page not found",
        "content isn't available",
    )

    def get_platform_name(self) -> str:
        return "instagram"

    def _extract_id(self, url: str) -> str:
        try:
            parts = url.rstrip('/').split('/')
            for i, part in enumerate(parts):
                if part in ('p', 'reel', 'tv') and i + 1 < len(parts):
                    return parts[i + 1][:20]
            return url.split('/')[-1][:20]
        except Exception:
            return "unknown"

    def _dismiss_consent(self, driver: WebDriver) -> None:
        dismiss_instagram_cookies(driver, timeout=3)

    def _detect_status(self, driver: WebDriver, initial_title: str = "") -> tuple[str, str] | None:
        """
        Check all detection signals on current page state.
        Returns (status, info) or None if no signal yet.

        Triage: negative signals first, then positive, then login detection.
        """
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        except Exception:
            return None

        # --- Negative signals ---

        # Page title check
        try:
            title = driver.title
            if title and "isn't available" in title.lower():
                return ("Removed", title)
        except Exception:
            pass

        # Error SVG icon
        try:
            driver.find_element(By.CSS_SELECTOR, 'svg[aria-label="error"]')
            return ("Removed", "error icon displayed")
        except Exception:
            pass

        # Error text in body
        for phrase in self.REMOVAL_PHRASES:
            if phrase in page_text:
                return ("Removed", phrase)

        # --- Positive signals ---

        # og:title meta tag — reliable even in logged-out view
        try:
            meta = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
            content = meta.get_attribute("content")
            if content and " on Instagram:" in content:
                return ("Live", "N/A")
        except Exception:
            pass

        # article element — works when logged in
        try:
            driver.find_element(By.CSS_SELECTOR, 'article[role="presentation"]')
            return ("Live", "N/A")
        except Exception:
            pass

        # --- Login detection ---

        if "log in" in page_text and "sign up" in page_text:
            return ("Login Required", "N/A")

        return None
