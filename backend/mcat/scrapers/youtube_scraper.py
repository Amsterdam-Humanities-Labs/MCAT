from zendriver.core.tab import Tab

from scrapers.base_scraper import BaseScraper, StatusResult


class YouTubeScraper(BaseScraper):
    """YouTube video status checker (detection only; flow is in BaseScraper)."""

    # Platform action -> Moderated; everything else gone -> Unavailable.
    MODERATED_PHRASES = ("account has been terminated",)
    UNAVAILABLE_PHRASES = (
        "video unavailable", "this video is not available",
        "this video isn't available", "video isn't available anymore",
        "removed by the user",
    )

    def get_platform_name(self) -> str:
        return "youtube"

    def _extract_id(self, url: str) -> str:
        return url.split('v=')[-1].split('&')[0]

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

        # --- Negative signals ---

        for phrase in self.MODERATED_PHRASES:
            if phrase in page_text:
                return ("Moderated", phrase)

        # Restricted: gated but present; specific reason in the detail.
        if 'age-restricted' in page_text or 'sign in to confirm your age' in page_text:
            return ("Restricted", "age-restricted")
        if 'not available in your country' in page_text:
            return ("Restricted", "geo-blocked")
        if 'private video' in page_text:
            return ("Restricted", "private")

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

        for phrase in self.UNAVAILABLE_PHRASES:
            if phrase in page_text:
                return ("Unavailable", phrase)

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
