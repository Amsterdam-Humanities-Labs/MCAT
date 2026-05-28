from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Optional

from scrapers.base_scraper import BaseScraper, ScrapingResult


class TwitterScraper(BaseScraper):
    """Twitter/X post status checker with pooled drivers and rate limiting.

    Uses full page text scanning against a curated dictionary of known
    moderation notices. This approach is more resilient than CSS selectors
    because Twitter/X changes DOM structure frequently but notice text
    stays stable.
    """

    RATE_LIMIT_MIN = 1.5
    RATE_LIMIT_MAX = 3.5

    DRIVER_POOL_TIMEOUT = 30
    PAGE_LOAD_TIMEOUT = 15
    SCROLL_PAUSE = 2
    SCROLL_COUNT = 3

    MAX_RETRIES = 2
    RETRY_DELAY = 2.0

    # Notices grouped by app status.
    # Order matters within each group — first match wins.
    # The matched notice text is stored in result.info for the researcher.

    REMOVED_NOTICES = [
        "Account suspended",
        "Hmm... this page doesn't exist. Try searching for something else.",
        "Hmm...this page doesn't exist. Try searching for something else.",
        "Sorry, that page doesn't exist!",
        "This account doesn't exist. Try searching for another.",
        "This page is from a suspended account.",
        "This page is from an account that no longer exists.",
        "This page is unavailable.",
        "This post is from a suspended account.",
        "This post is from an account that no longer exists.",
        "This post is unavailable.",
        "This post was deleted by its author,",
        "This post was deleted by the post author,",
        "This post was deleted by the post author",
        "This Tweet is from a suspended account.",
        "This Tweet is from an account that no longer exists.",
        "This Tweet is unavailable.",
        "This Tweet was deleted by the Tweet author",
        "This page violated the X Rules.",
        "This page violated the X Rules,",
        "This post violated the X Rules.",
        "This post violated the Twitter Rules.",
        "This post violated the Twitter Rules about civic and election integrity,",
        "This post violated the Twitter Rules about glorifying violence.",
        "This post violated the Twitter Rules",
        "This Tweet violated the Twitter Rules.",
        "This Tweet violated the Twitter Rules about civic and election integrity,",
        "This Tweet violated the Twitter Rules about glorifying violence.",
        "This Tweet violated the Twitter Rules",
    ]

    RESTRICTED_NOTICES = [
        "account is temporarily unavailable",
        "Age-restricted adult content. This content might not be appropriate for everyone. To view this media, you'll need to add your birthdate to your profile. Twitter also uses your age to show more relevant content, including ads, as explained in our Privacy Policy.",
        "Age-restricted adult content. This content might not be appropriate for everyone. To view this media, you'll need to add your birthdate to your profile. X also uses your age to show more relevant content, including ads, as explained in our Privacy Policy.",
        "Age-restricted adult content. This content might not be appropriate for people under 18 years old. To view this media, you'll need to log in to Twitter.",
        "Age-restricted adult content. This content might not be appropriate for people under 18 years old. To view this media, you'll need to log in to X.",
        "Age-restricted adult content. This content might not be appropriate for people under 18 years old.",
        "Get the facts about COVID-19.",
        "has been withheld",
        "Manipulated media",
        "page to remain accessible.",
        "post to remain accessible.",
        "Tweet to remain accessible.",
        "Readers added context they thought people might want to know",
        "Some or all of the content shared in this Post is disputed and might be misleading about an election or other civic process.",
        "Some or all of the content shared in this Tweet is disputed and might be misleading about an election or other civic process.",
        "The following media includes potentially sensitive content. Change settings,",
        "The following media includes potentially sensitive content.",
        "This account is temporarily restricted.",
        "This account owner limits who can view their pages.",
        "This account owner limits who can view their posts.",
        "This account owner limits who can view their Tweets.",
        "This claim of election fraud is disputed, and this post can't be replied to, reposted, or liked due to a risk of violence,",
        "This claim of election fraud is disputed, and this Tweet can't be replied to, Retweeted, or liked due to a risk of violence,",
        "This page includes a word you muted.",
        "This page is from an account you blocked.",
        "This page is from an account you muted.",
        "This page may include sensitive content.",
        "This post includes a word you muted.",
        "This post is from an account you blocked.",
        "This post is from an account you muted.",
        "This post may include sensitive content.",
        "This post violated the X Rules about . However, X has determined that it may be in the public's interest for the post to remain accessible.",
        "This post violated the X Rules about glorifying violence. However, X has determined that it may be in the public's interest for the post to remain accessible.",
        "This post violated the Twitter Rules about glorifying violence. However, Twitter has determined that it may be in the public's interest for the post to remain accessible.",
        "This Tweet includes a word you muted.",
        "This Tweet is from an account you blocked.",
        "This Tweet is from an account you muted.",
        "This Tweet may include sensitive content.",
        "This Tweet violated the Twitter Rules about glorifying violence. However, Twitter has determined that it may be in the public's interest for the Tweet to remain accessible.",
        "You reported this page.",
        "You reported this post.",
        "You reported this Tweet.",
    ]

    ERROR_NOTICES = [
        "Something went wrong. Try reloading.",
    ]

    def __init__(self, driver_pool):
        self.driver_pool = driver_pool
        self.min_delay = self.RATE_LIMIT_MIN
        self.max_delay = self.RATE_LIMIT_MAX
        self.last_request_time = 0

        self.pause_event = None

        self.save_screenshots: bool = False
        self.screenshot_base_path: Optional[Path] = None

        # Pre-compute lowercased notice tuples for matching
        self._removed = [(n, n.lower()) for n in self.REMOVED_NOTICES]
        self._restricted = [(n, n.lower()) for n in self.RESTRICTED_NOTICES]
        self._error = [(n, n.lower()) for n in self.ERROR_NOTICES]

    def get_platform_name(self) -> str:
        return "twitter"

    def _apply_rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        if time_since_last < delay:
            time.sleep(delay - time_since_last)
        self.last_request_time = time.time()

    def _check_pause(self):
        if self.pause_event:
            self.pause_event.wait()

    def set_pause_event(self, pause_event):
        self.pause_event = pause_event

    def _log(self, message: str):
        if not self.is_cancelled():
            print(message)

    def enable_screenshots(self, enabled: bool, base_path: str) -> None:
        self.save_screenshots = enabled
        if enabled:
            self.screenshot_base_path = Path(base_path) / "screenshots"

    def _save_screenshot(self, driver, url: str, status: str) -> str:
        if not self.screenshot_base_path:
            return ""
        try:
            post_id = self._extract_post_id(url)
            screenshot_dir = self.screenshot_base_path / status.lower()
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{post_id}_{timestamp}.png"
            filepath = screenshot_dir / filename
            driver.save_screenshot(str(filepath))
            print(f"Screenshot saved: {filepath.name}")
            return str(filepath)
        except Exception as e:
            print(f"Warning: Screenshot failed for {url}: {e}")
            return ""

    def _extract_post_id(self, url: str) -> str:
        """Extract post ID from Twitter/X URL.

        Handles formats like:
            https://twitter.com/user/status/123456
            https://x.com/user/status/123456
        """
        try:
            parts = url.rstrip("/").split("/")
            for i, part in enumerate(parts):
                if part == "status" and i + 1 < len(parts):
                    return parts[i + 1].split("?")[0][:20]
            return parts[-1].split("?")[0][:20]
        except Exception:
            return "unknown"

    def _scroll_page(self, driver):
        """Scroll to trigger lazy-loaded content."""
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(self.SCROLL_COUNT):
            if self.is_cancelled():
                return
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.SCROLL_PAUSE)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def check_url_status(self, url: str) -> ScrapingResult:
        result = ScrapingResult(url=url)
        for attempt in range(self.MAX_RETRIES + 1):
            if self.is_cancelled():
                result = ScrapingResult()
                result.url = url
        
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
                return result

            result = self._check_url_once(url)

            if result.status != "Error":
                return result

            if attempt == self.MAX_RETRIES:
                return result

            print(f"Warning: Retry {attempt + 1}/{self.MAX_RETRIES} for {url}: {result.error_message}")
            for _ in range(int(self.RETRY_DELAY * 10)):
                if self.is_cancelled():
                    result.status = "Cancelled"
                    result.info = "Processing was cancelled"
                    return result
                time.sleep(0.1)

        return result

    def _check_url_once(self, url: str) -> ScrapingResult:
        self._log(f"Checking Twitter URL: {url}")

        result = ScrapingResult()
        result.url = url


        if self.is_cancelled():
            result.status = "Cancelled"
            result.info = "Processing was cancelled"
            return result

        driver = None
        try:
            driver = self.driver_pool.get_driver(timeout=self.DRIVER_POOL_TIMEOUT)

            if self.is_cancelled():
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
                return result

            self._check_pause()
            self._apply_rate_limit()

            driver.get(url)

            try:
                WebDriverWait(driver, self.PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                result.status = "Error"
                result.error_message = "Page load timeout"
                self._log(f"Error: {url}: {result.status} - {result.error_message}")
                return result

            # Scroll to trigger lazy-loaded notices
            self._scroll_page(driver)

            if self.is_cancelled():
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
                return result

            # Get all visible page text
            try:
                page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            except Exception:
                page_text = driver.page_source.lower()

            # Match against categorized notices
            for notice, notice_lower in self._removed:
                if notice_lower in page_text:
                    result.status = "Removed"
                    result.info = notice
                    self._log(f"OK: {url}: {result.status} - {result.info}")
                    if self.save_screenshots:
                        result.screenshot_path = self._save_screenshot(driver, url, result.status)
                    return result

            for notice, notice_lower in self._restricted:
                if notice_lower in page_text:
                    result.status = "Restricted"
                    result.info = notice
                    self._log(f"OK: {url}: {result.status} - {result.info}")
                    if self.save_screenshots:
                        result.screenshot_path = self._save_screenshot(driver, url, result.status)
                    return result

            for notice, notice_lower in self._error:
                if notice_lower in page_text:
                    result.status = "Error"
                    result.info = notice
                    self._log(f"OK: {url}: {result.status} - {result.info}")
                    return result

            # Positive check: tweet article present → Live
            try:
                article = driver.find_element(By.CSS_SELECTOR, 'article[data-testid="tweet"], article[role="article"]')
                if article:
                    result.status = "Live"
                    result.info = "N/A"
                    self._log(f"OK: {url}: {result.status} - {result.info}")
                    if self.save_screenshots:
                        result.screenshot_path = self._save_screenshot(driver, url, result.status)
                    return result
            except Exception:
                pass

            # No positive Live indicator, no known notice → Unknown
            result.status = "Unknown"
            result.info = "N/A"
            self._log(f"OK: {url}: {result.status} - {result.info}")
            if self.save_screenshots:
                result.screenshot_path = self._save_screenshot(driver, url, result.status)
            return result

        except Exception as e:
            if self.is_cancelled():
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
            else:
                result.status = "Error"
                result.error_message = str(e)
                self._log(f"Error: {url}: {result.status} - {result.error_message}")
            return result
        finally:
            if driver:
                if self.is_cancelled():
                    pass
                else:
                    try:
                        driver.current_url
                        self.driver_pool.return_driver(driver)
                    except Exception as e:
                        print(f"Warning: Driver unresponsive, discarding: {e}")

    def cleanup(self):
        pass
