import threading
from collections.abc import Callable
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import chromedriver_autoinstaller.utils as cdu

from cookies.cookie_store import CookieStore, SESSION_COOKIE_NAMES

PLATFORM_URLS = {
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "tiktok": "https://www.tiktok.com",
}


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

        url = PLATFORM_URLS.get(platform)
        if not url:
            return {"success": False, "error": f"Login not supported for {platform}"}

        self._platform = platform
        self._driver = self._create_visible_driver()
        self._driver.get(url)

        threading.Thread(target=self._poll_for_login, daemon=True).start()

        return {"success": True, "platform": platform}

    def _poll_for_login(self) -> None:
        import time
        if not self._platform:
            return
        cookie_name = SESSION_COOKIE_NAMES.get(self._platform)
        platform = self._platform

        while self._driver is not None:
            try:
                cookies = self._driver.get_cookies()
                session = next((c for c in cookies if c["name"] == cookie_name), None)
                if session:
                    username = self._extract_username(cookies)
                    self._cookie_store.save_cookies(platform, cookies, username=username)
                    self._log(f"Logged in as {username}")
                    if self._on_login:
                        self._on_login()
                    return
            except Exception:
                # Browser was closed by user or crashed
                self._driver = None
                self._platform = None
                return

            time.sleep(2)

    def logout(self, platform: str) -> bool:
        return self._cookie_store.delete_cookies(platform)

    def _extract_username(self, cookies: list[dict]) -> str:
        if self._platform == "instagram":
            ds_user = next((c for c in cookies if c["name"] == "ds_user_id"), None)
            if ds_user:
                return ds_user["value"]
        elif self._platform == "facebook":
            c_user = next((c for c in cookies if c["name"] == "c_user"), None)
            if c_user:
                return c_user["value"]
        return ""

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
