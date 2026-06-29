from zendriver.core.tab import Tab

from scrapers.base_scraper import BaseScraper, StatusResult


class FacebookScraper(BaseScraper):
    """Facebook post status checker (detection only; flow is in BaseScraper)."""

    # Generic "gone" — FB doesn't reliably attribute a reason, so it's always
    # Unavailable, never an attributed removal.
    UNAVAILABLE_PHRASES = (
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
                return url.split("fbid=")[1].split("&")[0][:self.ID_MAX_LEN]
            if "story_fbid=" in url:
                return url.split("story_fbid=")[1].split("&")[0][:self.ID_MAX_LEN]
            if "?v=" in url:
                return url.split("?v=")[1].split("&")[0][:self.ID_MAX_LEN]
            parts = url.rstrip("/").split("/")
            for i, part in enumerate(parts):
                if part in ("posts", "videos", "reel", "permalink") and i + 1 < len(parts):
                    return parts[i + 1].split("?")[0][:self.ID_MAX_LEN]
            return parts[-1].split("?")[0][:self.ID_MAX_LEN]
        except Exception:
            return "unknown"

    async def _detect_status(self, tab: Tab, initial_title: str = "") -> StatusResult | None:
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
            page_text = (await tab.evaluate("document.body.innerText") or "").lower()
        except Exception:
            return None

        # 1. "Gone" notice
        for phrase in self.UNAVAILABLE_PHRASES:
            if phrase in page_text:
                return ("Unavailable", phrase)

        # 2. The rendered post itself
        if await tab.query_selector('div[role="article"]'):
            return ("Live", "N/A")

        # 3a. og:title, but only if it carries real content
        meta = await tab.query_selector('meta[property="og:title"]')
        if meta:
            content = (meta.attrs.get("content") or "").strip()
            if content and content.lower() not in self.GENERIC_TITLES:
                return ("Live", "N/A")

        # 3b. page title "<content> | Facebook" — check the lead before the suffix
        title = (await tab.evaluate("document.title") or "")
        low = title.strip().lower().removeprefix("(1) ").strip()
        if " | facebook" in low:
            lead = low.split(" | facebook")[0].strip()
            if lead and lead not in self.GENERIC_TITLES:
                return ("Live", "N/A")

        return None
