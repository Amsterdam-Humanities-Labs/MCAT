import atexit
import os
import platform
import threading
import time
import weakref
from collections.abc import Callable
from pathlib import Path
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

from config.platform_profiles import get_profile


# Every live pool registers here so a normal interpreter exit (e.g. the desktop
# window being closed) still reaps its chromedriver processes even if the
# explicit cleanup path was missed. WeakSet so pools can still be GC'd normally;
# atexit does NOT fire on SIGKILL, so this is a safety net, not a guarantee.
_live_pools: "weakref.WeakSet[WebDriverPool]" = weakref.WeakSet()
_atexit_registered = False


def _cleanup_all_pools() -> None:
    for pool in list(_live_pools):
        try:
            pool.cleanup()
        except Exception:
            pass


def resolve_chromedriver_path() -> str:
    """Path to a usable chromedriver: the cached build matching the installed
    Chrome major version if present, otherwise auto-installed."""
    import chromedriver_autoinstaller.utils as cdu
    chrome_version = chromedriver_autoinstaller.get_chrome_version()
    if chrome_version:
        major = chrome_version.split('.')[0]
        expected = Path(cdu.get_chromedriver_path()) / major / cdu.get_chromedriver_filename()
        if expected.exists():
            return str(expected)
    path = chromedriver_autoinstaller.install()
    if not path:
        raise RuntimeError("ChromeDriver auto-install returned no path")
    return path


def os_user_agent(major: str) -> str:
    """A complete, current Chrome UA string matching the *real* host OS.

    The OS token must agree with what Chrome reports independently of the UA —
    navigator.platform and the Sec-CH-UA-Platform client hint are derived from
    the actual OS, so a Windows UA on Linux/macOS is a self-contradiction and an
    easy bot tell. We still set it explicitly (rather than letting Chrome use its
    native UA) because headless Chrome otherwise advertises "HeadlessChrome",
    which is its own giveaway; here we keep the real platform but the normal
    "Chrome" token. `major` is the installed Chrome major version.
    """
    system = platform.system()
    if system == "Darwin":
        os_token = "Macintosh; Intel Mac OS X 10_15_7"
    elif system == "Windows":
        os_token = "Windows NT 10.0; Win64; x64"
    else:  # Linux and anything else
        os_token = "X11; Linux x86_64"
    return (
        f"Mozilla/5.0 ({os_token}) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{major}.0.0.0 Safari/537.36"
    )


def base_chrome_options() -> Options:
    """Chrome options shared by the headless pool and the visible login driver:
    stability plus the anti-bot-detection flags."""
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    return opts


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

        # Register for best-effort teardown on interpreter exit.
        global _atexit_registered
        _live_pools.add(self)
        if not _atexit_registered:
            atexit.register(_cleanup_all_pools)
            _atexit_registered = True

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
        try:
            self.chromedriver_path = resolve_chromedriver_path()
        except Exception as e:
            raise Exception(f"Failed to install ChromeDriver: {e}")

    def _create_driver_options(self) -> Options:
        """Create Chrome options for headless pool drivers."""
        chrome_options = base_chrome_options()

        if self.headless:
            # New headless runs the full Chrome (GPU, extensions, complete feature
            # set) instead of the old stripped-down headless shell, so its
            # fingerprint is much closer to a real browser.
            chrome_options.add_argument("--headless=new")

        # Performance and stability options. --disable-gpu is deliberately NOT
        # set: it disables WebGL entirely (renderer reports null), which is a
        # strong bot tell since real browsers always expose WebGL. Without it,
        # new headless provides WebGL (SwiftShader in software, or the real GPU
        # when present). Verified via tests/experiments/fingerprint_probe.py.
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
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

        # User agent: a complete, current Chrome UA whose OS token matches the
        # real host. It must be well-formed — a malformed token (missing
        # "Chrome/<major>.0.0.0 Safari/537.36") makes some sites such as Instagram
        # serve degraded media — and it must match the actual OS, since Chrome
        # reports the real platform via client hints regardless of this string.
        # Built from the installed Chrome version so it tracks the real browser.
        major = (chromedriver_autoinstaller.get_chrome_version() or "124.0").split(".")[0]
        chrome_options.add_argument(f"--user-agent={os_user_agent(major)}")

        return chrome_options

    def _inject_cookies(self, driver: webdriver.Chrome) -> None:
        """Inject saved cookies into a driver. Requires navigating to the domain first."""
        if not self._platform or not self._cookies:
            return
        profile = get_profile(self._platform)
        if not profile:
            return
        driver.get(profile.base_url)
        for cookie in self._cookies:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass

    def _initialize_pool(self) -> None:
        """Initialize the driver pool with browser instances."""
        self._log(f"Initializing WebDriver pool with {self.pool_size} instances...")

        for i in range(self.pool_size):
            try:
                # Each driver gets its OWN Service and Options. A single shared
                # Service only retains a reference to its most recently launched
                # chromedriver, so cleanup() could reap just the last one and
                # leaked the rest (browser closed, chromedriver server orphaned);
                # reusing a started Service/Options can also fail later drivers
                # outright. A fresh pair keeps driver.service.process correct for
                # every driver so each chromedriver is reaped on cleanup.
                service = Service(self.chromedriver_path)
                driver = webdriver.Chrome(service=service, options=self._create_driver_options())
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
        """Return a driver to the pool, resetting state for per-request isolation.

        Each scrape must look like a fresh session to the platform, so we wipe
        cookies + storage and re-inject the canonical set (consent + optional
        login) on every return. add_cookie only applies on the matching domain
        and delete_all_cookies only clears the current domain, so if the driver
        drifted off-platform (consent subdomain, external redirect, about:blank)
        we navigate back first; otherwise the wipe hits the wrong store and the
        re-injection is silently dropped, leaving the driver logged-out or
        consent-less for the rest of the batch.
        """
        if driver and driver in self.all_drivers:
            try:
                if self._cookies and self._platform:
                    profile = get_profile(self._platform)
                    domain = profile.base_url if profile else ""
                    host = domain.split("://")[-1]
                    if host and host not in (driver.current_url or ""):
                        driver.get(domain)  # only navigate when drifted off-domain
                    driver.delete_all_cookies()
                    driver.execute_script("window.localStorage.clear();")
                    driver.execute_script("window.sessionStorage.clear();")
                    for cookie in self._cookies:
                        try:
                            driver.add_cookie(cookie)
                        except Exception:
                            pass
                else:
                    driver.delete_all_cookies()
                    driver.execute_script("window.localStorage.clear();")
                    driver.execute_script("window.sessionStorage.clear();")
            except Exception as e:
                self._log(f"Driver reset on return failed: {e}", "warning")

            self.available_drivers.put(driver)
        elif driver:
            # Pool was cleaned up but worker still has driver - dispose it
            self._dispose_driver(driver)

    def _dispose_driver(self, driver: webdriver.Chrome) -> None:
        """Quit a driver and make sure its own chromedriver process is reaped.

        quit() normally stops the chromedriver via service.stop(), but if it
        raises (unresponsive browser) the server can survive — so we kill its
        process directly as a fallback and wait() to avoid leaving a zombie.
        Relies on each driver owning its own Service (see _initialize_pool).
        """
        process = None
        try:
            process = driver.service.process
        except Exception:
            pass

        try:
            driver.quit()
        except Exception as e:
            print(f"Warning: driver.quit() failed: {e}", flush=True)

        if process and process.poll() is None:
            try:
                process.kill()
                process.wait(timeout=5)
            except Exception:
                pass

    def cleanup(self) -> None:
        """Clean up all drivers in the pool."""
        self._log("Cleaning up WebDriver pool...", "debug")

        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        with self.lock:
            for driver in self.all_drivers:
                self._dispose_driver(driver)

            self.all_drivers.clear()

            while not self.available_drivers.empty():
                try:
                    self.available_drivers.get_nowait()
                except Exception:
                    break

