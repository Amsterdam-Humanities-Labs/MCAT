import threading
from collections.abc import Callable
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import chromedriver_autoinstaller.utils as cdu

from cookies.cookie_store import CookieStore
from config.platform_profiles import get_profile


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

        while self._driver is not None:
            try:
                cookies = self._driver.get_cookies()
                if cookies:
                    last_cookies = cookies

                session = next((c for c in cookies if c["name"] == cookie_name), None)
                if session:
                    username = self._extract_username(cookies)
                    self._cookie_store.save_cookies(platform, cookies, username=username)
                    self._log(f"Logged in as {username}")
                    if self._on_login:
                        self._on_login()
                    return
            except Exception:
                # Browser was closed by user — save whatever cookies we captured
                if last_cookies:
                    username = self._extract_username(last_cookies)
                    self._cookie_store.save_cookies(platform, last_cookies, username=username)
                    self._log("Browser setup saved")
                    if self._on_login:
                        self._on_login()
                self._driver = None
                self._platform = None
                return

            time.sleep(2)

    def logout(self, platform: str) -> bool:
        return self._cookie_store.delete_cookies(platform)

    def _extract_username(self, cookies: list[dict]) -> str:
        profile = get_profile(self._platform)
        if not profile or not profile.username_cookie:
            return ""
        match = next((c for c in cookies if c["name"] == profile.username_cookie), None)
        return match["value"] if match else ""

    def _create_visible_driver(self) -> webdriver.Chrome:
        chrome_version = chromedriver_autoinstaller.get_chrome_version()
        chromedriver_path = None
        if chrome_version:
            major = chrome_version.split('.')[0]
            expected = Path(cdu.get_chromedriver_path()) / major / cdu.get_chromedriver_filename()
            if expected.exists():
                chromedriver_path = str(expected)
        if not chromedriver_path:
            chromedriver_path = chromedriver_autoinstaller.install()

        opts = Options()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        opts.add_argument("--window-size=1200,800")

        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(30)
        return driver
