import threading
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
import chromedriver_autoinstaller.utils as cdu

from cookies.cookie_store import CookieStore
from core.driver_manager import PLATFORM_DOMAINS

PLATFORM_LOGIN_URLS = {
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "tiktok": "https://www.tiktok.com",
}

# Cookie that indicates a successful login per platform
SESSION_COOKIE_NAMES = {
    "instagram": "sessionid",
    "facebook": "c_user",
    "tiktok": "sessionid",
}


class LoginService:

    def __init__(self, cookie_store: CookieStore):
        self._cookie_store = cookie_store
        self._driver = None
        self._platform = None
        self._lock = threading.Lock()

    @property
    def is_active(self) -> bool:
        return self._driver is not None

    def start_login(self, platform: str) -> dict:
        with self._lock:
            if self._driver is not None:
                return {"success": False, "error": "Login already in progress"}

            login_url = PLATFORM_LOGIN_URLS.get(platform)
            if not login_url:
                return {"success": False, "error": f"Login not supported for {platform}"}

            self._platform = platform
            self._driver = self._create_visible_driver()
            self._driver.get(login_url)

            return {"success": True, "platform": platform}

    def check_login(self) -> dict:
        if not self._driver or not self._platform:
            return {"logged_in": False, "error": "No login in progress"}

        session_cookie_name = SESSION_COOKIE_NAMES.get(self._platform)
        cookies = self._driver.get_cookies()
        session_cookie = next(
            (c for c in cookies if c["name"] == session_cookie_name), None
        )

        if session_cookie:
            username = self._extract_username()
            return {"logged_in": True, "username": username}

        return {"logged_in": False}

    def complete_login(self) -> dict:
        if not self._driver or not self._platform:
            return {"success": False, "error": "No login in progress"}

        status = self.check_login()
        if not status.get("logged_in"):
            return {"success": False, "error": "Not logged in yet"}

        cookies = self._driver.get_cookies()
        username = status.get("username", "")

        self._cookie_store.save_cookies(self._platform, cookies, username=username)
        self._close_driver()

        return {"success": True, "username": username, "cookie_count": len(cookies)}

    def cancel_login(self) -> dict:
        self._close_driver()
        return {"success": True}

    def _extract_username(self) -> str:
        if self._platform == "instagram":
            try:
                cookies = self._driver.get_cookies()
                ds_user = next((c for c in cookies if c["name"] == "ds_user_id"), None)
                if ds_user:
                    return ds_user["value"]
            except Exception:
                pass
        elif self._platform == "facebook":
            try:
                cookies = self._driver.get_cookies()
                c_user = next((c for c in cookies if c["name"] == "c_user"), None)
                if c_user:
                    return c_user["value"]
            except Exception:
                pass
        return ""

    def _create_visible_driver(self):
        # Reuse chromedriver path detection from WebDriverPool
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
        # Visible window — no --headless, no --incognito, no --disable-images
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        opts.add_argument("--window-size=1200,800")

        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(30)
        return driver

    def _close_driver(self):
        with self._lock:
            if self._driver:
                try:
                    self._driver.quit()
                except Exception:
                    pass
                self._driver = None
                self._platform = None
