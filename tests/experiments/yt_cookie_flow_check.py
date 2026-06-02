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
from services.login_service import PLATFORM_URLS  # noqa: E402

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
check("youtube in PLATFORM_URLS", PLATFORM_URLS.get("youtube") == "https://www.youtube.com")

with tempfile.TemporaryDirectory() as tmp:
    store = CookieStore(Path(tmp))
    store.save_cookies("youtube", [SOCS], username="")  # consent-only, no login

    loaded = store.load_cookies("youtube")
    info = store.get_cookie_info("youtube")
    print("\nConsent-only jar survives load (youtube not gated by session cookie):")
    check("load_cookies returns the jar", bool(loaded) and any(c["name"] == "SOCS" for c in loaded))
    check("get_cookie_info is not None", info is not None)
    check("username is empty", info is not None and info["username"] == "")

    # replicate job_builder.auth_user
    auth_user = (info["username"] if info else "") or "anonymous"
    print("\nauth_user derivation:")
    check('empty username -> "anonymous"', auth_user == "anonymous")

print("\nRESULT:", "ALL PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
