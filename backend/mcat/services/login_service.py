import asyncio
import threading
from collections.abc import Callable

import zendriver as zd
from zendriver import cdp

from cookies.cookie_store import CookieStore
from config.platform_profiles import get_profile
from core.browser_manager import cookie_to_dict


class LoginService:
    """Drives the Set up browser flow: opens a VISIBLE zendriver browser so the
    user can dismiss consent and (optionally) log in, then captures the cookie
    jar. Runs its own event loop on a background thread; the public methods stay
    synchronous for the API handlers.
    """

    def __init__(self, cookie_store: CookieStore, log_callback: Callable | None = None, on_login: Callable | None = None):
        self._cookie_store: CookieStore = cookie_store
        self._log_callback: Callable | None = log_callback
        self._on_login: Callable | None = on_login
        self._active: bool = False
        self._lock: threading.Lock = threading.Lock()

    @property
    def is_active(self) -> bool:
        return self._active

    def _log(self, message: str, level: str = "info") -> None:
        if self._log_callback:
            self._log_callback(message, level)

    def start_login(self, platform: str) -> dict:
        with self._lock:
            if self._active:
                return {"success": False, "error": "Login already in progress"}
            profile = get_profile(platform)
            if not profile or not profile.supports_setup:
                return {"success": False, "error": f"Login not supported for {platform}"}
            self._active = True

        threading.Thread(target=self._run, args=(platform,), daemon=True).start()
        return {"success": True, "platform": platform}

    def _run(self, platform: str) -> None:
        try:
            asyncio.run(self._login_flow(platform))
        except Exception as e:
            self._log(f"Browser setup error: {e}", "warning")
        finally:
            self._active = False

    async def _login_flow(self, platform: str) -> None:
        profile = get_profile(platform)
        if not profile:
            return
        cookie_name = profile.login_cookie
        # Visible window, real UA (no spoof — Google blocks sign-in from a
        # spoofed Windows UA; zendriver's native UA matches the host OS).
        # --test-type suppresses Chrome's "unsupported flag --no-sandbox" infobar
        # in the visible setup window (chromedriver used to hide it automatically).
        browser = await zd.start(
            headless=False, sandbox=False,
            browser_args=["--window-size=1200,800", "--disable-dev-shm-usage", "--test-type"],
        )
        last_cookies: list[dict] = []
        announced = False
        try:
            tab = await browser.get(profile.base_url)
            while not getattr(browser, "stopped", False):
                try:
                    # Network.getCookies on the tab — browser.cookies reads the
                    # wrong context and returns nothing (see browser_manager).
                    raw = await tab.send(cdp.network.get_cookies())
                except Exception:
                    break  # window closed by user -> connection dropped
                cookies = [cookie_to_dict(c) for c in raw]
                if cookies:
                    last_cookies = cookies

                # Announce login once for immediate feedback, but keep polling so
                # consent dismissed AFTER sign-in is still captured on close.
                if not announced and cookie_name and any(c["name"] == cookie_name for c in cookies):
                    announced = True
                    username = self._extract_username(platform, cookies)
                    self._cookie_store.save_cookies(platform, cookies, username=username)
                    self._log(f"Logged in as {username}" if username else "Login detected")
                    if self._on_login:
                        self._on_login()

                await asyncio.sleep(0.5)
        finally:
            # Window closed (or error) -> persist the final, complete jar.
            if last_cookies:
                username = self._extract_username(platform, last_cookies)
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
            try:
                await browser.stop()
            except Exception:
                pass

    def logout(self, platform: str) -> bool:
        return self._cookie_store.delete_cookies(platform)

    def _extract_username(self, platform: str, cookies: list[dict]) -> str:
        profile = get_profile(platform)
        if not profile or not profile.username_cookie:
            return ""
        match = next((c for c in cookies if c["name"] == profile.username_cookie), None)
        return match["value"] if match else ""

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
