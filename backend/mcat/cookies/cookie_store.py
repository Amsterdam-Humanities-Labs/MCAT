import json
import time
from datetime import datetime
from pathlib import Path

SESSION_COOKIE_NAMES = {
    "instagram": "sessionid",
    "facebook": "c_user",
    "tiktok": "sessionid",
}


class CookieStore:
    """Save and load Selenium session cookies per platform, scoped to a project folder."""

    def __init__(self, project_path: Path):
        self._dir = Path(project_path) / "cookies"

    def _path(self, platform: str) -> Path:
        return self._dir / f"{platform}.json"

    def _is_expired(self, platform: str, cookies: list[dict]) -> bool:
        cookie_name = SESSION_COOKIE_NAMES.get(platform)
        if not cookie_name:
            return False
        session = next((c for c in cookies if c.get("name") == cookie_name), None)
        if not session:
            return True
        expiry = session.get("expiry")
        if expiry and expiry < time.time():
            return True
        return False

    def save_cookies(self, platform: str, cookies: list[dict], username: str = "") -> Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._path(platform)
        data = {
            "platform": platform,
            "username": username,
            "captured_at": datetime.now().isoformat(),
            "cookies": cookies,
        }
        path.write_text(json.dumps(data, indent=2))
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
            }
        except (json.JSONDecodeError, KeyError):
            return None
