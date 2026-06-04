from zendriver.core.tab import Tab

from scrapers.base_scraper import BaseScraper, StatusResult


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

    # Consent dismissal not overridden: the per-project jar captures YouTube's
    # SOCS consent cookie during Set up browser, which suppresses the consent
    # redirect; initial_title (captured pre-redirect) covers the anonymous case.

    async def _detect_status(self, tab: Tab, initial_title: str = "") -> StatusResult | None:
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
            page_text = (await tab.evaluate("document.body.innerText") or "").lower()
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
            warn = await tab.evaluate("""(() => {
              for (const el of document.querySelectorAll('[class*="warning"],[class*="restricted"]')) {
                const t = (el.innerText || '').trim();
                if (t) return t.slice(0, 200);
              }
              return '';
            })()""")
            if warn:
                return ("Restricted", warn)
        except Exception:
            pass

        # --- Positive signals (evidence the video is live) ---

        # Primary: h1 title element rendered by SPA
        try:
            h1 = await tab.evaluate(
                "(document.querySelector('h1.ytd-watch-metadata, h1.title') || {}).innerText || ''"
            )
            if h1 and h1.strip():
                return ("Live", "N/A")
        except Exception:
            pass

        # Fallback: page title set to "<Video Title> - YouTube"
        # Check both current title and initial_title (captured before YouTube
        # redirects incognito browsers to the consent page).
        try:
            current_title = await tab.evaluate("document.title") or ""
        except Exception:
            current_title = ""
        for title in (current_title, initial_title):
            if title and title != "YouTube" and " - YouTube" in title:
                return ("Live", "N/A")

        return None
