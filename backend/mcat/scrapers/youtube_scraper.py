from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from scrapers.base_scraper import BaseScraper
from cookies.youtube_cookie_handler import dismiss_youtube_cookies


class YouTubeScraper(BaseScraper):
    """YouTube video status checker (detection only; flow is in BaseScraper)."""

    RATE_LIMIT_MIN = 1.0
    RATE_LIMIT_MAX = 3.0

    REMOVAL_PHRASES = (
        'video unavailable', 'this video is not available',
        "this video isn't available", "video isn't available anymore",
        'removed by the user', 'account has been terminated',
    )

    def get_platform_name(self) -> str:
        return "youtube"

    def _extract_id(self, url: str) -> str:
        return url.split('v=')[-1].split('&')[0]

    def _dismiss_consent(self, driver: WebDriver) -> None:
        dismiss_youtube_cookies(driver, timeout=3)

    def _detect_status(self, driver: WebDriver, initial_title: str = "") -> tuple[str, str] | None:
        """
        Check all detection signals on the current page state.

        Returns (status, info) if a conclusive signal is found, or None
        if no signal is present yet (keep polling).

        Triage order matters: negative signals (removal/restriction) are
        checked before positive signals (Live) so we never conclude Live
        before a removal notice has had a chance to appear.
        """
        # Get visible text (not raw HTML which contains JS template strings)
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        except Exception:
            return None  # Page not ready yet

        # --- Negative signals (positive evidence of removal/restriction) ---

        for phrase in self.REMOVAL_PHRASES:
            if phrase in page_text:
                return ("Removed", phrase)

        if 'age-restricted' in page_text:
            return ("Age-restricted", "age-restricted")
        if 'sign in to confirm your age' in page_text:
            return ("Age-restricted", "sign in to confirm your age")

        if 'not available in your country' in page_text:
            return ("Geo-blocked", "not available in your country")

        if 'private video' in page_text:
            return ("Private", "private video")

        # Warning/restricted elements
        try:
            warning_elements = driver.find_elements(
                By.CSS_SELECTOR, '[class*="warning"], [class*="restricted"]'
            )
            for el in warning_elements:
                text = el.text.strip()
                if text:
                    return ("Restricted", text[:200])
        except Exception:
            pass

        # --- Positive signals (evidence the video is live) ---

        # Primary: h1 title element rendered by SPA
        try:
            title_el = driver.find_element(
                By.CSS_SELECTOR, 'h1.ytd-watch-metadata, h1.title'
            )
            h1_text = driver.execute_script('return arguments[0].innerText', title_el)
            if h1_text and h1_text.strip():
                return ("Live", "N/A")
        except Exception:
            pass

        # Fallback: page title set to "<Video Title> - YouTube"
        # Check both current title and initial_title (captured before YouTube
        # redirects incognito browsers to the consent page).
        for title in (driver.title, initial_title):
            try:
                if title and title != "YouTube" and " - YouTube" in title:
                    return ("Live", "N/A")
            except Exception:
                pass

        return None
