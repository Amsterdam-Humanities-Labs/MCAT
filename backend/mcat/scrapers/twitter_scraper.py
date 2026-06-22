from zendriver.core.tab import Tab

from scrapers.base_scraper import BaseScraper, StatusResult


class TwitterScraper(BaseScraper):
    """X (Twitter) post status checker (detection only; flow is in BaseScraper)."""

    # Explicit takedown/deletion -> Removed.
    REMOVED_PHRASES = ("this post was deleted", "account suspended")
    # Gone but reason indeterminate (logged-out shows one page for deleted/
    # suspended/protected/never-existed) -> Unavailable.
    UNAVAILABLE_PHRASES = (
        "nothing to see here",
        "this post is unavailable",
        "these posts are protected",
        "hmm...this page doesn",
    )

    def get_platform_name(self) -> str:
        return "twitter"

    def _extract_id(self, url: str) -> str:
        if "/status/" in url:
            return url.split("/status/")[1].split("/")[0].split("?")[0][:self.ID_MAX_LEN]
        return url.rstrip("/").split("/")[-1].split("?")[0][:self.ID_MAX_LEN]

    async def _detect_status(self, tab: Tab, initial_title: str = "") -> StatusResult | None:
        try:
            page_text = (await tab.evaluate("document.body.innerText") or "").lower()
        except Exception:
            return None

        # --- Negative signals ---
        for phrase in self.REMOVED_PHRASES:
            if phrase in page_text:
                return ("Removed", phrase)
        for phrase in self.UNAVAILABLE_PHRASES:
            if phrase in page_text:
                return ("Unavailable", phrase)

        try:
            title = await tab.evaluate("document.title") or ""
        except Exception:
            title = ""
        # The logged-out "gone" page sets the title to "X / ?".
        if title.strip() == "X / ?":
            return ("Unavailable", title)

        # --- Positive signals (live tweet) ---
        # og:title is server-rendered even logged-out: "<Author> (@handle) on X".
        meta = await tab.query_selector('meta[property="og:title"]')
        if meta:
            content = meta.attrs.get("content") or ""
            if " on X" in content:
                return ("Live", "N/A")

        # Rendered tweet element (logged-in view).
        if await tab.query_selector('article[data-testid="tweet"]'):
            return ("Live", "N/A")

        # Page title "<Author> on X: ..." (logged-out live view).
        if " on X:" in title:
            return ("Live", "N/A")

        return None
