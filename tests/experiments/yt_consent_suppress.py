"""Suppression test with a positive control, using the homepage (reliable repro).

A: fresh no-cookie driver -> homepage -> CONFIRM modal (positive control) ->
   click Reject all -> capture the resulting SOCS cookie (the value to bake).
B: fresh pool injected with that SOCS -> homepage -> modal? -> return_driver
   (wipes localStorage + reinjects SOCS, the production isolation cycle) ->
   homepage again -> modal? The post-wipe check is the real question.

Read-only. Headless. Run:
  backend/venv/bin/python tests/experiments/yt_consent_suppress.py
"""
import sys
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from core.driver_manager import WebDriverPool  # noqa: E402
from cookies.youtube_cookie_handler import dismiss_youtube_cookies, _find_consent_dialog  # noqa: E402

HOME = "https://www.youtube.com/"
SHOTS = Path(__file__).resolve().parent / "shots"
SHOTS.mkdir(exist_ok=True)


def modal_present(driver, timeout=8):
    return _find_consent_dialog(driver, timeout) is not None


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


def short(v, n=90):
    return v if v is None or len(v) <= n else v[:n] + "..."


def main():
    print("PART A — confirm modal (control) and capture the Reject-all SOCS")
    p0 = WebDriverPool(pool_size=1, headless=True)
    d = p0.get_driver()
    d.set_page_load_timeout(25)
    d.get(HOME)
    control = modal_present(d)
    shot(d, "supp_control")
    print(f"  control: modal present on fresh homepage? {control}")

    clicked = dismiss_youtube_cookies(d)
    gone = not modal_present(d, timeout=4)
    shot(d, "supp_after_reject")
    socs = next((c for c in d.get_cookies() if c["name"] == "SOCS"), None)
    print(f"  clicked Reject all: {clicked} | modal gone after click? {gone}")
    print(f"  captured SOCS: {short(socs['value']) if socs else '(none!)'}")
    p0.cleanup()

    if not control:
        print("\nINCONCLUSIVE: control modal didn't show; cannot test suppression.")
        return
    if not socs:
        print("\nABORT: no SOCS captured after Reject all.")
        return

    print("\nPART B — inject SOCS, test before and after the isolation wipe")
    p1 = WebDriverPool(pool_size=1, headless=True, cookies=[socs], platform="youtube")
    d2 = p1.get_driver()
    d2.set_page_load_timeout(25)
    d2.get(HOME)
    injected = modal_present(d2)
    shot(d2, "supp_injected")
    print(f"  [fresh inject]      modal present? {injected}")

    p1.return_driver(d2)  # wipe localStorage + reinject SOCS
    d3 = p1.get_driver()
    d3.set_page_load_timeout(25)
    d3.get(HOME)
    carried = ls_keys(d3)
    after_wipe = modal_present(d3)
    shot(d3, "supp_after_wipe")
    print(f"  [after return wipe] localStorage keys carried: {len(carried)} | modal present? {after_wipe}")
    p1.cleanup()

    print("\nVERDICT")
    if after_wipe:
        print("  FAIL: cookie alone does not survive the localStorage wipe -> keep the handler.")
    elif injected:
        print("  PARTIAL: suppressed after wipe but not on fresh inject -> inspect screenshots.")
    else:
        print("  PASS: SOCS injection suppresses the modal even after the isolation wipe.")
        print(f"  Bake SOCS (domain={socs.get('domain')}, secure={socs.get('secure')}):")
        print(f"    {socs['value']}")


if __name__ == "__main__":
    main()
