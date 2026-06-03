"""Generalized login probe: does an injected login jar keep the production pool
logged in, and survive the per-request wipe (fix #2)?

Uses the real WebDriverPool (production driver options + _inject_cookies +
return_driver wipe). The per-platform "are we logged in" check is a small JS
oracle; the screenshots are the ground truth.

  backend/venv/bin/python tests/experiments/login_probe.py <platform> <project_path>
"""
import sys
import json
import time
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from core.driver_manager import WebDriverPool  # noqa: E402
from config.platform_profiles import get_profile  # noqa: E402

SHOTS = Path(__file__).resolve().parent / "shots"
SHOTS.mkdir(exist_ok=True)

# logged-in when this JS returns truthy
ORACLE_JS = {
    "youtube": "try { return (window.ytcfg && ytcfg.get) ? !!ytcfg.get('LOGGED_IN') : false } catch (e) { return false }",
    "instagram": "return !document.querySelector('input[name=\"password\"]')",   # no login form => logged in
    "facebook": "return !document.querySelector('input[name=\"pass\"]')",
}


def main():
    if len(sys.argv) < 3:
        print("usage: login_probe.py <platform> <project_path>")
        sys.exit(2)
    platform, project = sys.argv[1], sys.argv[2]
    profile = get_profile(platform)
    if not profile or platform not in ORACLE_JS:
        print(f"unsupported platform: {platform}")
        sys.exit(2)

    jar_file = Path(project) / "cookies" / f"{platform}.json"
    if not jar_file.exists():
        print(f"no jar at {jar_file}")
        sys.exit(2)
    cookies = json.loads(jar_file.read_text())["cookies"]
    has_login = any(c["name"] == profile.login_cookie for c in cookies)
    print(f"login cookie '{profile.login_cookie}' present: {has_login}")
    if not has_login:
        print("This jar has no login cookie (consent-only). Set up browser AND sign in first.")
        return

    js = ORACLE_JS[platform]
    pool = WebDriverPool(pool_size=1, headless=True, cookies=cookies, platform=platform)
    try:
        d = pool.get_driver()
        d.set_page_load_timeout(30)
        d.get(profile.base_url)
        time.sleep(6)
        fresh = bool(d.execute_script(js))
        d.save_screenshot(str(SHOTS / f"login_{platform}_fresh.png"))
        print(f"  [fresh inject]      logged in? {fresh}")

        pool.return_driver(d)  # wipe localStorage + reinject cookies
        d2 = pool.get_driver()
        d2.set_page_load_timeout(30)
        d2.get(profile.base_url)
        time.sleep(6)
        after = bool(d2.execute_script(js))
        d2.save_screenshot(str(SHOTS / f"login_{platform}_after_wipe.png"))
        print(f"  [after return wipe] logged in? {after}")

        print("VERDICT:", "PASS (login survives headless + wipe)" if fresh and after
              else "PARTIAL (fresh only)" if fresh else "FAIL")
    finally:
        pool.cleanup()


if __name__ == "__main__":
    main()
