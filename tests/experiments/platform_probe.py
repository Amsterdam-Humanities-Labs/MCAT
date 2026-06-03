"""Generalized consent-suppression probe.

For a platform: confirm the cookie modal shows (control), dismiss it via the
platform's existing handler, discover which cookies that set, then inject those
into a fresh headless pool and check the modal stays gone AFTER the per-request
localStorage wipe (the production isolation condition that a naive test hides).

The flow is generic; the per-platform parts are the dismiss handler (modal
detect + dismiss) and the profile (base_url). Add a platform by adding its
handler to ORACLES.

  backend/venv/bin/python tests/experiments/platform_probe.py <youtube|instagram|facebook>
"""
import sys
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from core.driver_manager import WebDriverPool  # noqa: E402
from config.platform_profiles import get_profile  # noqa: E402
from cookies.youtube_cookie_handler import dismiss_youtube_cookies, _find_consent_dialog  # noqa: E402
from cookies.instagram_cookie_handler import dismiss_instagram_cookies, _find_cookie_dialog as _find_ig  # noqa: E402
from cookies.facebook_cookie_handler import dismiss_facebook_cookies, _find_cookie_dialog as _find_fb  # noqa: E402

# platform -> (find_modal(driver, timeout) -> elem|None, dismiss(driver, timeout, wait_after) -> bool)
ORACLES = {
    "youtube": (_find_consent_dialog, dismiss_youtube_cookies),
    "instagram": (_find_ig, dismiss_instagram_cookies),
    "facebook": (_find_fb, dismiss_facebook_cookies),
}

SHOTS = Path(__file__).resolve().parent / "shots"
SHOTS.mkdir(exist_ok=True)


def modal_present(find, driver, timeout=8):
    return find(driver, timeout) is not None


def ls_keys(driver):
    try:
        return set(driver.execute_script("return Object.keys(window.localStorage)") or [])
    except Exception:
        return set()


def shot(driver, name):
    try:
        driver.set_window_size(1280, 1000)
        driver.save_screenshot(str(SHOTS / f"{name}.png"))
    except Exception:
        pass


def goto(driver, url):
    try:
        driver.get(url)
    except Exception as e:
        print(f"  get() raised {type(e).__name__}")


def main():
    platform = sys.argv[1] if len(sys.argv) > 1 else None
    if platform not in ORACLES:
        print("usage: platform_probe.py <youtube|instagram|facebook>")
        sys.exit(2)
    profile = get_profile(platform)
    assert profile is not None
    find, dismiss = ORACLES[platform]
    url = profile.base_url

    print(f"=== {platform} consent probe @ {url} ===")
    print("PART A — control + dismiss + capture")
    disc = WebDriverPool(pool_size=1, headless=True)
    d = disc.get_driver()
    d.set_page_load_timeout(25)
    goto(d, url)
    before = {c["name"]: c["value"] for c in d.get_cookies()}
    before_ls = ls_keys(d)
    control = modal_present(find, d)
    shot(d, f"{platform}_control")
    print(f"  control: modal present on fresh load? {control}")

    dismissed = dismiss(d)
    gone = not modal_present(find, d, timeout=4)
    after = d.get_cookies()
    new_ls = ls_keys(d) - before_ls
    changed = [c for c in after if before.get(c["name"]) != c["value"]]
    shot(d, f"{platform}_after_dismiss")
    print(f"  handler dismissed: {dismissed} | modal gone after dismiss? {gone}")
    print(f"  cookies set/changed by dismissal: {[c['name'] for c in changed]}")
    print(f"  localStorage keys added by dismissal: {sorted(new_ls) if new_ls else 'none'}")
    disc.cleanup()

    if not control:
        print("\nINCONCLUSIVE: modal never showed (geo? handler stale?). Cannot test suppression.")
        return
    if not changed:
        print("\nNo cookies changed on dismissal. Consent is likely NOT cookie-based here")
        print(f"(localStorage keys added: {sorted(new_ls) if new_ls else 'none'}). Keep the handler.")
        return

    print("\nPART B — inject dismissal cookies, test before and after the wipe")
    inj = WebDriverPool(pool_size=1, headless=True, cookies=changed, platform=platform)
    d2 = inj.get_driver()
    d2.set_page_load_timeout(25)
    goto(d2, url)
    injected = modal_present(find, d2)
    shot(d2, f"{platform}_injected")
    print(f"  [fresh inject]      modal present? {injected}")

    inj.return_driver(d2)  # wipe localStorage + reinject cookies
    d3 = inj.get_driver()
    d3.set_page_load_timeout(25)
    goto(d3, url)
    after_wipe = modal_present(find, d3)
    shot(d3, f"{platform}_after_wipe")
    print(f"  [after return wipe] modal present? {after_wipe}")
    inj.cleanup()

    print("\nVERDICT")
    if after_wipe:
        print(f"  FAIL: cookie injection does NOT survive the wipe for {platform}.")
        print(f"  Consent likely depends on localStorage (added: {sorted(new_ls) if new_ls else 'none'}). Keep its handler.")
    elif injected:
        print("  PARTIAL: suppressed after wipe but not on fresh inject. Inspect screenshots.")
    else:
        print(f"  PASS: cookie injection suppresses the {platform} modal even after the wipe.")
        print(f"  Candidate consent cookies for the profile: {[c['name'] for c in changed]}")


if __name__ == "__main__":
    main()
