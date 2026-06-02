"""Diagnostic: does the YouTube consent modal actually appear in the app's
headless pool config, and if so where? The suppression probe came back
inconclusive because the modal never rendered on a fresh load. This captures
the visual + URL truth so we know whether the modal is even a problem here.

Read-only. Headless. Run:
  backend/venv/bin/python tests/experiments/yt_consent_diag.py
"""
import sys
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from core.driver_manager import WebDriverPool  # noqa: E402
from cookies.youtube_cookie_handler import _find_consent_dialog  # noqa: E402

SHOTS = Path(__file__).resolve().parent / "shots"
SHOTS.mkdir(exist_ok=True)

SURFACES = [
    ("homepage", "https://www.youtube.com/"),
    ("watch", "https://www.youtube.com/watch?v=XvMcfOtR538"),
]


def short(v, n=70):
    return v if v is None or len(v) <= n else v[:n] + "..."


def inspect(driver, label, url):
    print(f"\n--- {label}: {url}")
    try:
        driver.get(url)
    except Exception as e:
        print(f"  get() raised {type(e).__name__}, continuing")

    print(f"  landed url : {driver.current_url}")
    try:
        print(f"  title      : {short(driver.title)}")
    except Exception:
        pass

    cookies = {c['name']: c['value'] for c in driver.get_cookies()}
    print(f"  cookie names: {sorted(cookies)}")
    if 'SOCS' in cookies:
        print(f"  SOCS       : {short(cookies['SOCS'])}")
    else:
        print("  SOCS       : (absent)")

    # production consent detector
    modal = _find_consent_dialog(driver, timeout=6) is not None
    # broader sweep: any dialog/consent host at all
    any_dialog = driver.execute_script(
        "return document.querySelectorAll('tp-yt-paper-dialog,[role=dialog]').length"
    )
    consent_host = "consent" in driver.current_url
    body_text = ""
    try:
        body_text = driver.execute_script("return document.body.innerText || ''")[:200].replace("\n", " ")
    except Exception:
        pass
    print(f"  _find_consent_dialog: {modal} | dialog elements on page: {any_dialog} | on consent host: {consent_host}")
    print(f"  body[:200] : {body_text!r}")

    try:
        driver.set_window_size(1280, 1000)
    except Exception:
        pass
    shot = SHOTS / f"{label}.png"
    try:
        driver.save_screenshot(str(shot))
        print(f"  screenshot : {shot}")
    except Exception as e:
        print(f"  screenshot failed: {e}")


def main():
    print("Fresh no-cookie headless pool (current YouTube prod config: incognito + pool UA)")
    pool = WebDriverPool(pool_size=1, headless=True)
    d = pool.get_driver()
    d.set_page_load_timeout(25)
    for label, url in SURFACES:
        inspect(d, label, url)
    pool.cleanup()
    print("\nDone. Inspect the screenshots in tests/experiments/shots/.")


if __name__ == "__main__":
    main()
