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

    # og:title / page-title values that are generic chrome (login or error
    # pages), never a real post — used to guard the metadata fallbacks.
    GENERIC_TITLES = {"facebook", "log in to facebook", "log into facebook"}

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
        Triage, in order:
          1. removal notice (strongest, mode-independent)
          2. the rendered post element (reliable anonymous and logged-in)
          3. content-specific og:title / page title

        The metadata fallbacks (3) must be content-specific: a non-empty
        og:title or title is NOT enough on its own, because Facebook serves a
        generic "Facebook" / "Log in to Facebook" title on login and error
        pages, which would otherwise be misread as Live.

        There is deliberately no login-wall branch: the body always contains
        "log in" and the login form is embedded on every anonymous page, so
        there is no reliable per-post login signal. An undecided page returns
        None -> Unknown for the human to judge from the screenshot.
        """
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        except Exception:
            return None

        # 1. Removal notice
        for phrase in self.REMOVAL_PHRASES:
            if phrase in page_text:
                return ("Removed", phrase)

        # 2. The rendered post itself
        try:
            driver.find_element(By.CSS_SELECTOR, 'div[role="article"]')
            return ("Live", "N/A")
        except Exception:
            pass

        # 3a. og:title, but only if it carries real content
        try:
            meta = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
            content = (meta.get_attribute("content") or "").strip()
            if content and content.lower() not in self.GENERIC_TITLES:
                return ("Live", "N/A")
        except Exception:
            pass

        # 3b. page title "<content> | Facebook" — check the lead before the suffix
        try:
            low = (driver.title or "").strip().lower().removeprefix("(1) ").strip()
            if " | facebook" in low:
                lead = low.split(" | facebook")[0].strip()
                if lead and lead not in self.GENERIC_TITLES:
                    return ("Live", "N/A")
        except Exception:
            pass

        return None
