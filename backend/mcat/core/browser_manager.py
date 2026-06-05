"""Async browser layer: one zendriver Chrome process driven over CDP, with a
fixed pool of tabs.

The canonical cookie jar (consent + optional login) is injected once at startup
and shared by all tabs. Concurrency is bounded by the tab pool: acquire_tab()
blocks while all tabs are busy. Teardown is a single browser.stop().
"""
import asyncio
import functools
import platform
import re
import subprocess
from collections.abc import Callable

import zendriver as zd
from zendriver import cdp
from zendriver.core.config import find_executable

# Perf/stability flags only. zendriver masks automation itself, so no stealth
# flags are needed; --disable-gpu is omitted on purpose because it disables WebGL
# entirely, which is a bot tell.
BROWSER_ARGS = [
    "--disable-dev-shm-usage",
    "--mute-audio",
    "--disable-background-media-download",
]


@functools.lru_cache(maxsize=1)
def _chrome_major() -> str:
    """Installed Chrome major version, via zendriver's browser finder + --version.
    Cached; falls back to a recent version if detection fails."""
    try:
        out = subprocess.run([str(find_executable()), "--version"],
                             capture_output=True, text=True, timeout=5).stdout
        m = re.search(r"(\d+)\.", out)
        if m:
            return m.group(1)
    except Exception:
        pass
    return "131"


def os_user_agent(major: str) -> str:
    """A complete, current Chrome UA string matching the real host OS.

    The OS token must agree with what Chrome reports independently of the UA
    (navigator.platform, Sec-CH-UA-Platform), so a Windows UA on Linux/macOS is a
    self-contradiction and an easy bot tell.
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


def resolved_user_agent() -> str:
    """The exact UA string the browser uses — OS-correct, current Chrome version."""
    return os_user_agent(_chrome_major())


def to_cookie_param(c: dict) -> cdp.network.CookieParam:
    """Convert a stored cookie dict (the on-disk jar format) to a zendriver
    CookieParam, for injecting saved cookies into a tab."""
    cdp_dict: dict = {
        "name": c["name"],
        "value": c["value"],
        "domain": c.get("domain"),
        "path": c.get("path", "/"),
        "secure": bool(c.get("secure", False)),
        "httpOnly": bool(c.get("httpOnly", False)),
    }
    if c.get("expiry") is not None:
        cdp_dict["expires"] = float(c["expiry"])
    same_site = c.get("sameSite")
    if same_site in ("Strict", "Lax", "None"):
        cdp_dict["sameSite"] = same_site
    return cdp.network.CookieParam.from_json(cdp_dict)


def cookie_to_dict(c) -> dict:
    """Inverse of to_cookie_param: a zendriver/CDP Cookie -> the stored dict
    (on-disk jar) format, for capturing cookies during Set up browser."""
    d: dict = {
        "name": c.name,
        "value": c.value,
        "domain": getattr(c, "domain", "") or "",
        "path": getattr(c, "path", "/") or "/",
        "secure": bool(getattr(c, "secure", False)),
        "httpOnly": bool(getattr(c, "http_only", False)),
    }
    expires = getattr(c, "expires", None)
    if expires and expires > 0:
        d["expiry"] = int(expires)
    same_site = getattr(c, "same_site", None)
    if same_site is not None:
        d["sameSite"] = same_site.value if hasattr(same_site, "value") else str(same_site)
    return d


class BrowserSession:
    """One zendriver Browser plus a fixed pool of reusable tabs."""

    def __init__(self, log_callback: Callable | None = None) -> None:
        self._browser: zd.Browser | None = None
        self._tabs: asyncio.Queue = asyncio.Queue()
        self._all_tabs: list = []
        self._log_callback: Callable | None = log_callback

    def _log(self, message: str, level: str = "info") -> None:
        if self._log_callback:
            self._log_callback(message, level)
        print(message, flush=True)

    @classmethod
    async def create(
        cls,
        pool_size: int,
        headless: bool = True,
        log_callback: Callable | None = None,
        cookies: list[dict] | None = None,
        platform: str | None = None,
        browser_executable_path: str | None = None,
    ) -> "BrowserSession":
        self = cls(log_callback)
        self._log(f"Starting browser with {pool_size} tabs...")
        browser = await zd.start(
            headless=headless,
            sandbox=False,
            user_agent=resolved_user_agent(),
            browser_args=BROWSER_ARGS,
            browser_executable_path=browser_executable_path,
        )
        self._browser = browser

        params = []
        for c in (cookies or []):
            try:
                params.append(to_cookie_param(c))
            except Exception:
                pass

        # Reuse the browser's initial tab as pool slot 1, open the rest.
        first = browser.main_tab
        tabs = [first] if first is not None else []
        for _ in range(max(0, pool_size - len(tabs))):
            tabs.append(await browser.get("about:blank", new_tab=True))

        # Inject the jar per-tab via Network.setCookies: zendriver's browser.cookies
        # uses Storage on the wrong browser context, so cookies set that way never
        # reach the tab's navigation. Network.setCookies on the tab does.
        for tab in tabs:
            if params:
                try:
                    await tab.send(cdp.network.set_cookies(params))
                except Exception as e:
                    self._log(f"Cookie injection failed on a tab: {e}", "warning")
            self._all_tabs.append(tab)
            self._tabs.put_nowait(tab)

        if params:
            self._log(f"Injected {len(params)} cookies for {platform}")
        return self

    async def acquire_tab(self):
        """Get a tab from the pool (blocks until one is free)."""
        return await self._tabs.get()

    async def release_tab(self, tab) -> None:
        self._tabs.put_nowait(tab)

    async def stop(self) -> None:
        if self._browser is not None:
            try:
                await self._browser.stop()
            except Exception as e:
                self._log(f"Browser stop failed: {e}", "warning")
            self._browser = None
