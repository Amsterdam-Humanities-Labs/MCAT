import json
import os
import time
from datetime import datetime
from pathlib import Path

from config.platform_profiles import get_profile


class CookieStore:
    """Save and load session cookies per platform, scoped to a project folder."""

    def __init__(self, project_path: Path):
        self._dir = Path(project_path) / "cookies"

    def _path(self, platform: str) -> Path:
        return self._dir / f"{platform}.json"

    def _is_expired(self, platform: str, cookies: list[dict]) -> bool:
        """A jar is 'expired' only when its login cookie is present but past expiry.

        A missing login cookie means a consent-only jar (the banner was dismissed
        without logging in, e.g. YouTube), which is valid and must still load.
        """
        profile = get_profile(platform)
        cookie_name = profile.login_cookie if profile else None
        if not cookie_name:
            return False
        session = next((c for c in cookies if c.get("name") == cookie_name), None)
        if not session:
            return False
        expiry = session.get("expiry")
        if expiry and expiry < time.time():
            return True
        return False

    def _has_fresh_login(self, platform: str, cookies: list[dict]) -> bool:
        """Whether a valid (present and unexpired) login cookie exists."""
        profile = get_profile(platform)
        if not profile or not profile.login_cookie:
            return False
        c = next((x for x in cookies if x.get("name") == profile.login_cookie), None)
        if not c:
            return False
        expiry = c.get("expiry")
        return not (expiry and expiry < time.time())

    def save_cookies(self, platform: str, cookies: list[dict], username: str = "",
                     consent_captured: bool = False) -> Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._path(platform)
        data = {
            "platform": platform,
            "username": username,
            "captured_at": datetime.now().isoformat(),
            "consent_captured": consent_captured,
            "cookies": cookies,
        }
        path.write_text(json.dumps(data, indent=2))
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return path

    def load_cookies(self, platform: str) -> list[dict] | None:
        path = self._path(platform)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            cookies = data.get("cookies")
            if cookies and self._is_expired(platform, cookies):
                return None
            return cookies
        except (json.JSONDecodeError, KeyError):
            return None

    def delete_cookies(self, platform: str) -> bool:
        path = self._path(platform)
        if path.exists():
            path.unlink()
            return True
        return False

    def has_cookies(self, platform: str) -> bool:
        return self.load_cookies(platform) is not None

    def get_cookie_info(self, platform: str) -> dict | None:
        path = self._path(platform)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            cookies = data.get("cookies", [])
            if self._is_expired(platform, cookies):
                return None
            return {
                "platform": data["platform"],
                "username": data.get("username", ""),
                "captured_at": data["captured_at"],
                "cookie_count": len(cookies),
                "logged_in": self._has_fresh_login(platform, cookies),
                # A missing field means no consent event was ever recorded, so
                # it's treated as not captured (a jar from before the field
                # existed shows "Consent not set" until its next setup run).
                "consent_captured": data.get("consent_captured", False),
            }
        except (json.JSONDecodeError, KeyError):
            return None

    def get_auth_info(self, platform: str) -> dict:
        """The auth facts the UI needs, in one shape. Single source so the
        project serializer and the cookie-status endpoint cannot drift.

        Note ``logged_in`` is derived live from cookie freshness, whereas
        ``consent_captured`` is persisted: a saved jar alone can't reveal
        whether a present consent cookie was user-chosen or auto-set, so the
        consent decision is recorded as an event at setup time (see
        ``cookie_diff.consent_login_events``)."""
        info = self.get_cookie_info(platform)
        return {
            "has_cookies": info is not None,
            "username": info["username"] if info else "",
            "logged_in": info["logged_in"] if info else False,
            "captured_at": info["captured_at"] if info else None,
            "consent_captured": info["consent_captured"] if info else False,
        }
