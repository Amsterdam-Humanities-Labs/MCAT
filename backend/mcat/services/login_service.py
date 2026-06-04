import threading
from collections.abc import Callable

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from cookies.cookie_store import CookieStore
from config.platform_profiles import get_profile
from core.driver_manager import resolve_chromedriver_path, base_chrome_options


class LoginService:

    def __init__(self, cookie_store: CookieStore, log_callback: Callable | None = None, on_login: Callable | None = None):
        self._cookie_store: CookieStore = cookie_store
        self._log_callback: Callable | None = log_callback
        self._on_login: Callable | None = on_login
        self._driver: webdriver.Chrome | None = None
        self._platform: str | None = None

    @property
    def is_active(self) -> bool:
        return self._driver is not None

    def _log(self, message: str, level: str = "info") -> None:
        if self._log_callback:
            self._log_callback(message, level)

    def start_login(self, platform: str) -> dict:
        if self._driver is not None:
            return {"success": False, "error": "Login already in progress"}

        profile = get_profile(platform)
        if not profile or not profile.supports_setup:
            return {"success": False, "error": f"Login not supported for {platform}"}

        self._platform = platform
        self._driver = self._create_visible_driver()
        self._driver.get(profile.base_url)

        threading.Thread(target=self._poll_for_login, daemon=True).start()

        return {"success": True, "platform": platform}

    def _poll_for_login(self) -> None:
        import time
        if not self._platform:
            return
        profile = get_profile(self._platform)
        cookie_name = profile.login_cookie if profile else None
        platform = self._platform
        last_cookies: list[dict] = []
        announced_login = False

        while self._driver is not None:
            try:
                cookies = self._driver.get_cookies()
                if cookies:
                    last_cookies = cookies

                # Announce login once for immediate toolbar feedback, but keep
                # polling instead of returning, so consent cookies dismissed
                # AFTER signing in are still captured. The authoritative, complete
                # set is persisted on window close below.
                session = next((c for c in cookies if c["name"] == cookie_name), None)
                if session and not announced_login:
                    announced_login = True
                    username = self._extract_username(cookies)
                    self._cookie_store.save_cookies(platform, cookies, username=username)
                    self._log(f"Logged in as {username}" if username else "Login detected")
                    if self._on_login:
                        self._on_login()
            except Exception:
                # Browser was closed by user — persist the final, complete set
                # (login + consent dismissed in any order) and report exactly
                # what was captured, since this jar is the authoritative result.
                if last_cookies:
                    username = self._extract_username(last_cookies)
                    self._cookie_store.save_cookies(platform, last_cookies, username=username)
                    self._log_capture_summary(platform, last_cookies)
                    if self._on_login:
                        self._on_login()
                else:
                    self._log(
                        f"Browser setup for {platform}: no cookies captured — nothing saved "
                        f"(the window may have closed before the page finished loading).",
                        "warning",
                    )
                self._driver = None
                self._platform = None
                return

            time.sleep(2)

    def _log_capture_summary(self, platform: str, cookies: list[dict]) -> None:
        """Report which consent / login cookies the setup session captured.

        Classification uses the profile's reporting-only name sets; anything
        unrecognised is counted as "other". Names only are ever logged, never
        values. A missing consent set is surfaced as a warning because the
        scraper modal will likely reappear without it.
        """
        profile = get_profile(platform)
        consent_names = set(profile.consent_cookies) if profile else set()
        login_names = set(profile.login_cookies) if profile else set()

        names = [c.get("name", "") for c in cookies if c.get("name")]
        consent = list(dict.fromkeys(n for n in names if n in consent_names))
        login = list(dict.fromkeys(n for n in names if n in login_names))
        other = max(0, len(set(names)) - len(consent) - len(login))

        def seg(found: list[str], noun: str, empty: str) -> str:
            if not found:
                return empty
            s = "" if len(found) == 1 else "s"
            return f"{len(found)} {noun} cookie{s} ({', '.join(found)})"

        consent_seg = seg(consent, "consent", "no consent cookies")
        login_seg = seg(login, "login", "no login cookies (anonymous)")
        extra = f", +{other} other" if other else ""
        self._log(f"Browser setup for {platform}: captured {consent_seg}, {login_seg}{extra}.")

        if not consent:
            self._log(
                f"No consent cookies captured for {platform} — the cookie banner may reappear "
                f"during scraping. Dismiss it in the Set up browser window before closing.",
                "warning",
            )

    def logout(self, platform: str) -> bool:
        return self._cookie_store.delete_cookies(platform)

    def _extract_username(self, cookies: list[dict]) -> str:
        profile = get_profile(self._platform)
        if not profile or not profile.username_cookie:
            return ""
        match = next((c for c in cookies if c["name"] == profile.username_cookie), None)
        return match["value"] if match else ""

    def _create_visible_driver(self) -> webdriver.Chrome:
        # Visible (non-headless) driver for the Set up browser flow. Shares the
        # base stealth/stability options with the pool, but keeps the real UA
        # (Google blocks sign-in from the spoofed Windows UA) and is windowed.
        opts = base_chrome_options()
        opts.add_argument("--window-size=1200,800")
        driver = webdriver.Chrome(service=Service(resolve_chromedriver_path()), options=opts)
        driver.set_page_load_timeout(30)
        return driver
