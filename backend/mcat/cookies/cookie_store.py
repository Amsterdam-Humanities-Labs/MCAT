import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class CookieStore:
    """Save and load Selenium session cookies per platform, scoped to a project folder."""

    def __init__(self, project_path: Path):
        self._dir = Path(project_path) / "cookies"

    def _path(self, platform: str) -> Path:
        return self._dir / f"{platform}.json"

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

    def load_cookies(self, platform: str) -> Optional[list[dict]]:
        path = self._path(platform)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return data.get("cookies")
        except (json.JSONDecodeError, KeyError):
            return None

    def delete_cookies(self, platform: str) -> bool:
        path = self._path(platform)
        if path.exists():
            path.unlink()
            return True
        return False

    def has_cookies(self, platform: str) -> bool:
        return self._path(platform).exists()

    def get_cookie_info(self, platform: str) -> Optional[dict]:
        path = self._path(platform)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return {
                "platform": data["platform"],
                "username": data.get("username", ""),
                "captured_at": data["captured_at"],
                "cookie_count": len(data.get("cookies", [])),
            }
        except (json.JSONDecodeError, KeyError):
            return None
