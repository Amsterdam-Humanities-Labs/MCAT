from zendriver.core.tab import Tab

from scrapers.base_scraper import BaseScraper, StatusResult


class InstagramScraper(BaseScraper):
    """Instagram post status checker (detection only; flow is in BaseScraper)."""

    # Generic "gone" — IG never says why (deleted/removed/private/never-existed
    # are one page), so it's always Unavailable, never an attributed removal.
    UNAVAILABLE_PHRASES = (
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
                    return parts[i + 1][:self.ID_MAX_LEN]
            return url.split('/')[-1][:self.ID_MAX_LEN]
        except Exception:
            return "unknown"

    async def _detect_status(self, tab: Tab, initial_title: str = "") -> StatusResult | None:
        """
        Check all detection signals on current page state.
        Returns (status, info) or None if no signal yet.

        Triage: negative signals first, then positive, then login detection.
        """
        try:
            page_text = (await tab.evaluate("document.body.innerText") or "").lower()
        except Exception:
            return None

        # --- Negative signals ---

        # Page title check
        try:
            title = await tab.evaluate("document.title") or ""
            if title and "isn't available" in title.lower():
                return ("Unavailable", title)
        except Exception:
            pass

        # Error SVG icon
        if await tab.query_selector('svg[aria-label="error"]'):
            return ("Unavailable", "error icon displayed")

        # Error text in body
        for phrase in self.UNAVAILABLE_PHRASES:
            if phrase in page_text:
                return ("Unavailable", phrase)

        # --- Positive signals ---

        # og:title meta tag — reliable even in logged-out view
        meta = await tab.query_selector('meta[property="og:title"]')
        if meta:
            content = meta.attrs.get("content") or ""
            if " on Instagram:" in content:
                return ("Live", "N/A")

        # article element — works when logged in
        if await tab.query_selector('article[role="presentation"]'):
            return ("Live", "N/A")

        # --- Login detection ---

        if "log in" in page_text and "sign up" in page_text:
            return ("Login Required", "N/A")

        return None
