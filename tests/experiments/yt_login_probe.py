"""Probe: does an injected Google/YouTube login jar keep the headless pool
browser logged in, and does it survive the per-request isolation wipe?

I can't log into Google for you (credentials/2FA, needs a human at the visible
window). So this reads the login jar a project already captured and tests only
the injection half. To produce a login jar: Set up browser on a YouTube project,
dismiss consent AND sign in to Google, then close the window.

Prints cookie NAMES only, never values.

  backend/venv/bin/python tests/experiments/yt_login_probe.py <project_path>
"""
import sys
import json
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from core.driver_manager import WebDriverPool  # noqa: E402

# Cookies that indicate a logged-in Google/YouTube session.
LOGIN_HINTS = {"LOGIN_INFO", "SID", "__Secure-1PSID", "__Secure-3PSID",
               "SAPISID", "__Secure-1PAPISID", "__Secure-3PAPISID", "HSID", "SSID"}

SHOTS = Path(__file__).resolve().parent / "shots"
SHOTS.mkdir(exist_ok=True)

HOME = "https://www.youtube.com/"


def signals(driver):
    """Return (logged_in_flag, sign_in_buttons, account_buttons)."""
    ytcfg = driver.execute_script(
        "try { return (window.ytcfg && ytcfg.get) ? !!ytcfg.get('LOGGED_IN') : null } catch (e) { return null }"
    )
    signin = driver.execute_script(
        "return document.querySelectorAll("
        "'a[aria-label=\"Sign in\"], a[href*=\"accounts.google.com/ServiceLogin\"], "
        "tp-yt-paper-button[aria-label=\"Sign in\"]').length"
    )
    account = driver.execute_script(
        "return document.querySelectorAll("
        "'#avatar-btn, button[aria-label*=\"Account menu\"], ytd-topbar-menu-button-renderer img').length"
    )
    return ytcfg, signin, account


def report(label, driver):
    ytcfg, signin, account = signals(driver)
    driver.save_screenshot(str(SHOTS / f"login_{label}.png"))
    print(f"  [{label}] ytcfg.LOGGED_IN={ytcfg} | sign-in buttons={signin} | account buttons={account}")
    return ytcfg, signin, account


def main():
    if len(sys.argv) < 2:
        print("usage: yt_login_probe.py <project_path>")
        sys.exit(2)

    jar_file = Path(sys.argv[1]) / "cookies" / "youtube.json"
    if not jar_file.exists():
        print(f"No youtube.json at {jar_file}")
        sys.exit(2)

    data = json.loads(jar_file.read_text())
    cookies = data.get("cookies", [])
    names = sorted(c["name"] for c in cookies)
    login_names = [n for n in names if n in LOGIN_HINTS]

    print(f"jar: {len(cookies)} cookies | names: {names}")
    print(f"login cookies present: {login_names or 'NONE'}")

    if not login_names:
        print("\nThis jar is consent-only (no Google login cookies). Nothing to test.")
        print("Run Set up browser on a YouTube project, dismiss consent AND sign in,")
        print("close the window, then re-run this probe against that project.")
        return

    print("\nInjecting login jar into a headless pool (production config)...")
    pool = WebDriverPool(pool_size=1, headless=True, cookies=cookies, platform="youtube")
    d = pool.get_driver()
    d.set_page_load_timeout(25)
    try:
        d.get(HOME)
    except Exception as e:
        print(f"  get() raised {type(e).__name__}")
    fresh = report("fresh", d)

    # production isolation cycle: wipe localStorage + reinject cookies, reuse
    pool.return_driver(d)
    d2 = pool.get_driver()
    d2.set_page_load_timeout(25)
    try:
        d2.get(HOME)
    except Exception as e:
        print(f"  get() raised {type(e).__name__}")
    after = report("after_wipe", d2)
    pool.cleanup()

    print("\nVERDICT")
    logged_in_fresh = fresh[0] is True or (fresh[2] > 0 and fresh[1] == 0)
    logged_in_after = after[0] is True or (after[2] > 0 and after[1] == 0)
    if logged_in_fresh and logged_in_after:
        print("  PASS: injected Google login survives headless AND the isolation wipe.")
    elif logged_in_fresh and not logged_in_after:
        print("  PARTIAL: logged in on fresh inject but NOT after the wipe (isolation drops it).")
    else:
        print("  FAIL: headless browser is not logged in despite injected cookies")
        print("  (Google likely challenged/invalidated the session under headless). Inspect shots/login_*.png.")


if __name__ == "__main__":
    main()
