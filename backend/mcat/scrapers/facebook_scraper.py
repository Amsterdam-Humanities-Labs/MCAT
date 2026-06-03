from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from scrapers.base_scraper import BaseScraper
from cookies.facebook_cookie_handler import dismiss_facebook_cookies


class FacebookScraper(BaseScraper):
    """Facebook post status checker (detection only; flow is in BaseScraper)."""

    RATE_LIMIT_MIN = 1.5
    RATE_LIMIT_MAX = 3.5

    REMOVAL_PHRASES = (
        "this content isn't available",
        "this page isn't available",
        "content isn't available right now",
        "sorry, this content isn't available",
        "the link you followed may be broken",
        "page not found",
        "this content has been removed",
    )

    def get_platform_name(self) -> str:
        return "facebook"

    def _extract_id(self, url: str) -> str:
        try:
            if "fbid=" in url:
                return url.split("fbid=")[1].split("&")[0][:20]
            if "story_fbid=" in url:
                return url.split("story_fbid=")[1].split("&")[0][:20]
            if "?v=" in url:
                return url.split("?v=")[1].split("&")[0][:20]
            parts = url.rstrip("/").split("/")
            for i, part in enumerate(parts):
                if part in ("posts", "videos", "reel", "permalink") and i + 1 < len(parts):
                    return parts[i + 1].split("?")[0][:20]
            return parts[-1].split("?")[0][:20]
        except Exception:
            return "unknown"

    def _dismiss_consent(self, driver: WebDriver) -> None:
        dismiss_facebook_cookies(driver, timeout=3)

    def _detect_status(self, driver: WebDriver, initial_title: str = "") -> tuple[str, str] | None:
        """
        Check all detection signals on current page state.
        Returns (status, info) or None if no signal yet.

        Triage: negative signals first, then positive.
        """
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        except Exception:
            return None

        # --- Negative signals ---

        for phrase in self.REMOVAL_PHRASES:
            if phrase in page_text:
                return ("Removed", phrase)

        # --- Positive signals ---

        # Article element
        try:
            driver.find_element(By.CSS_SELECTOR, 'div[role="article"]')
            return ("Live", "N/A")
        except Exception:
            pass

        # og:title meta tag
        try:
            meta = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
            content = meta.get_attribute("content")
            if content:
                return ("Live", "N/A")
        except Exception:
            pass

        # Page title pattern: "Post text - Page Name | Facebook"
        try:
            title = driver.title
            if title and title != "Facebook" and " | Facebook" in title:
                return ("Live", "N/A")
        except Exception:
            pass

        # --- Login detection ---

        if "log in" in page_text and "create new account" in page_text:
            return ("Login Required", "N/A")

        return None
