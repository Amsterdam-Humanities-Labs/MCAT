import os
import threading
import time
from collections.abc import Callable
from pathlib import Path
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller


PLATFORM_DOMAINS = {
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "tiktok": "https://www.tiktok.com",
    "youtube": "https://www.youtube.com",
    "twitter": "https://x.com",
}


class WebDriverPool:
    """Thread-safe WebDriver pool for reusing browser instances."""

    def __init__(self, pool_size: int, headless: bool = True, log_callback: Callable | None = None,
                 cookies: list[dict] | None = None, platform: str | None = None):
        self.pool_size: int = pool_size
        self.headless: bool = headless
        self.chromedriver_path: str | None = None
        self._log_callback: Callable | None = log_callback
        self._cookies: list[dict] | None = cookies
        self._platform: str | None = platform
        self._setup_chromedriver()

        # Thread-safe driver pool
        self.available_drivers: Queue[webdriver.Chrome] = Queue()
        self.all_drivers: list[webdriver.Chrome] = []
        self.lock: threading.Lock = threading.Lock()

        # Initialize the pool
        self._initialize_pool()

    def _log(self, message: str, level: str = "info") -> None:
        """Log message via callback or print."""
        if self._log_callback:
            self._log_callback(message, level)
        print(message, flush=True)

    def __del__(self):
        """Destructor to ensure cleanup on object deletion."""
        try:
            self.cleanup()
        except Exception:
            pass

    def _setup_chromedriver(self) -> None:
        """Install and setup ChromeDriver automatically."""
        import chromedriver_autoinstaller.utils as cdu
        # Check if chromedriver is already installed at the expected path
        chrome_version = chromedriver_autoinstaller.get_chrome_version()
        if chrome_version:
            major = chrome_version.split('.')[0]
            expected = Path(cdu.get_chromedriver_path()) / major / cdu.get_chromedriver_filename()
            if expected.exists():
                self.chromedriver_path = str(expected)
                return
        try:
            self.chromedriver_path = chromedriver_autoinstaller.install()
        except Exception as e:
            raise Exception(f"Failed to install ChromeDriver: {e}")

    def _create_driver_options(self) -> Options:
        """Create Chrome options for driver instances."""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Performance and stability options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--ignore-certificate-errors")
        if not self._cookies:
            chrome_options.add_argument("--incognito")

        # Disable audio/video to prevent YouTube sound and reduce CPU usage
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--disable-audio-output")
        chrome_options.add_argument("--disable-background-media-download")
        chrome_options.add_argument("--disable-media-device-discovery")
        chrome_options.add_argument("--disable-media-session-api")
        chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")

        # User agent to avoid detection
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        # Disable automation flags to avoid bot detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Disable WebDriver flag that sites check for bots
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        return chrome_options

    def _inject_cookies(self, driver: webdriver.Chrome) -> None:
        """Inject saved cookies into a driver. Requires navigating to the domain first."""
        if not self._platform or not self._cookies:
            return
        domain = PLATFORM_DOMAINS.get(self._platform)
        if not domain:
            return
        driver.get(domain)
        for cookie in self._cookies:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass

    def _initialize_pool(self) -> None:
        """Initialize the driver pool with browser instances."""
        self._log(f"Initializing WebDriver pool with {self.pool_size} instances...")
        chrome_options = self._create_driver_options()
        service = Service(self.chromedriver_path)

        for i in range(self.pool_size):
            try:
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.set_page_load_timeout(30)
                if self._cookies:
                    self._inject_cookies(driver)
                self.all_drivers.append(driver)
                self.available_drivers.put(driver)
                self._log(f"WebDriver {i+1}/{self.pool_size} initialized")
            except Exception as e:
                self._log(f"Failed to create WebDriver {i+1}: {e}", "error")
                break

        if self._cookies:
            self._log(f"Injected {len(self._cookies)} cookies for {self._platform}")

    def get_driver(self, timeout: int = 30) -> webdriver.Chrome:
        """Get a driver from the pool (blocks if none available)."""
        try:
            # Get driver from pool (blocks until available)
            driver = self.available_drivers.get(timeout=timeout)
            return driver
        except Exception:
            raise Exception("No WebDriver available in pool (timeout)")

    def return_driver(self, driver: webdriver.Chrome) -> None:
        """Return a driver to the pool."""
        if driver and driver in self.all_drivers:
            if not self._cookies:
                try:
                    driver.delete_all_cookies()
                    driver.execute_script("window.localStorage.clear();")
                    driver.execute_script("window.sessionStorage.clear();")
                except Exception:
                    pass

            self.available_drivers.put(driver)
        elif driver:
            # Pool was cleaned up but worker still has driver - quit it
            try:
                driver.quit()
            except Exception:
                pass

    def cleanup(self) -> None:
        """Clean up all drivers in the pool."""
        self._log("Cleaning up WebDriver pool...", "debug")

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        with self.lock:
            for driver in self.all_drivers:
                process = None
                try:
                    process = driver.service.process
                except Exception:
                    pass

                try:
                    driver.implicitly_wait(1)
                    driver.quit()
                except Exception as e:
                    print(f"Warning: driver.quit() failed: {e}", flush=True)

                if process and process.poll() is None:
                    process.kill()

            self.all_drivers.clear()

            while not self.available_drivers.empty():
                try:
                    self.available_drivers.get_nowait()
                except Exception:
                    break

