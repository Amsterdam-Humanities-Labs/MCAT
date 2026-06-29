from zendriver.core.tab import Tab

from scrapers.base_scraper import BaseScraper, StatusResult


class TwitterScraper(BaseScraper):
    """X (Twitter) post status checker (detection only; flow is in BaseScraper)."""

    # Only phrases observed in live probing.
    MODERATED_PHRASES = ("suspended account",)      # "This Post is from a suspended account" (logged in)
    UNAVAILABLE_PHRASES = ("nothing to see here",)  # logged-out "gone" page (title "X / ?")

    def get_platform_name(self) -> str:
        return "twitter"

    def _extract_id(self, url: str) -> str:
        if "/status/" in url:
            return url.split("/status/")[1].split("/")[0].split("?")[0][:self.ID_MAX_LEN]
        return url.rstrip("/").split("/")[-1].split("?")[0][:self.ID_MAX_LEN]

    async def _detect_status(self, tab: Tab, initial_title: str = "") -> StatusResult | None:
        # Positive first: X only renders the tweet when it's live, so a rendered
        # tweet is conclusive and isn't misread as moderated when the post text
        # merely mentions moderation.
        try:
            title = await tab.evaluate("document.title") or ""
        except Exception:
            title = ""
        meta = await tab.query_selector('meta[property="og:title"]')
        og = (meta.attrs.get("content") or "") if meta else ""
        if " on X:" in title or " on X" in og or await tab.query_selector('article[data-testid="tweet"]'):
            return ("Live", "N/A")

        try:
            page_text = (await tab.evaluate("document.body.innerText") or "").lower()
        except Exception:
            return None
        for phrase in self.MODERATED_PHRASES:
            if phrase in page_text:
                return ("Moderated", phrase)
        for phrase in self.UNAVAILABLE_PHRASES:
            if phrase in page_text:
                return ("Unavailable", phrase)
        if title.strip() == "X / ?":
            return ("Unavailable", title)

        return None
