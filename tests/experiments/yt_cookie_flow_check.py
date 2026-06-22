"""Plumbing check for YouTube browser-setup: a consent-only jar (no session
cookie, empty username) must load through CookieStore and resolve auth_user to
"anonymous". No browser, no network.

  backend/venv/bin/python tests/experiments/yt_cookie_flow_check.py
"""
import sys
import tempfile
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from cookies.cookie_store import CookieStore  # noqa: E402
from config.platform_profiles import get_profile  # noqa: E402

SOCS = {
    "name": "SOCS", "value": "CAESEwgDEgk5MjQ0Mjk5NjIaAmVuIAEaBgiAuvjQBg",
    "domain": ".youtube.com", "path": "/", "secure": True,
}

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")


print("Set up browser is routed for YouTube:")
_yt = get_profile("youtube")
check("youtube profile supports setup", bool(_yt and _yt.supports_setup and _yt.base_url == "https://www.youtube.com"))

LOGIN_INFO = {
    "name": "LOGIN_INFO", "value": "AFmmF2switched",
    "domain": ".youtube.com", "path": "/", "secure": True, "httpOnly": True,
}


def auth_user_of(info):
    # mirrors services/job_builder.py
    if info and info["username"]:
        return info["username"]
    if info and info.get("logged_in"):
        return "logged-in"
    return "anonymous"


with tempfile.TemporaryDirectory() as tmp:
    store = CookieStore(Path(tmp))

    store.save_cookies("youtube", [SOCS], username="")  # consent-only, no login
    info = store.get_cookie_info("youtube")
    loaded = store.load_cookies("youtube")
    print("\nConsent-only jar (no login):")
    check("load_cookies returns the jar", bool(loaded) and any(c["name"] == "SOCS" for c in loaded))
    check("logged_in is False", info is not None and info.get("logged_in") is False)
    check('auth_user is "anonymous"', auth_user_of(info) == "anonymous")

    store.save_cookies("youtube", [SOCS, LOGIN_INFO], username="")  # consent + login
    info = store.get_cookie_info("youtube")
    loaded = store.load_cookies("youtube")
    print("\nLogin jar (LOGIN_INFO present):")
    check("load_cookies returns the jar", bool(loaded) and any(c["name"] == "LOGIN_INFO" for c in loaded))
    check("logged_in is True", info is not None and info.get("logged_in") is True)
    check('auth_user is "logged-in"', auth_user_of(info) == "logged-in")

print("\nRESULT:", "ALL PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
