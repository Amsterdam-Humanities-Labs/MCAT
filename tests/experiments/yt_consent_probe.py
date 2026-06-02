"""Throwaway probe: can a captured YouTube consent cookie suppress the consent
modal AFTER a localStorage wipe (the production per-request isolation condition)?

The "after a wipe" part is the whole point: return_driver() clears localStorage on
every request, so if YouTube mirrors consent into localStorage, a naive test would
show the modal gone (suppressed by leftover localStorage, not the cookie) and lie.
Part 2 exercises the real pool return cycle to avoid that false positive.

Read-only. Headless. No app state is touched.
Run: backend/venv/bin/python tests/experiments/yt_consent_probe.py
"""
import sys
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from core.driver_manager import WebDriverPool  # noqa: E402
from cookies.youtube_cookie_handler import dismiss_youtube_cookies, _find_consent_dialog  # noqa: E402

WATCH_A = "https://www.youtube.com/watch?v=XvMcfOtR538"
WATCH_B = "https://www.youtube.com/watch?v=8Rv6LjSN7G4"
WATCH_C = "https://www.youtube.com/watch?v=n2peg8jxYH8"

# Cookies "Reject all" is known to write for Google/YouTube consent.
CONSENT_NAMES = {"SOCS", "CONSENT"}


def modal_present(driver, timeout=8):
    return _find_consent_dialog(driver, timeout) is not None


def ls_keys(driver):
    try:
        return set(driver.execute_script("return Object.keys(window.localStorage)") or [])
    except Exception:
        return set()


def goto(driver, url):
    try:
        driver.get(url)
    except Exception as e:
        print(f"  (navigation to {url} raised {type(e).__name__}, continuing to detection)")


def short(v, n=60):
    return v if len(v) <= n else v[:n] + "..."


def main():
    print("=" * 70)
    print("PART 1 — discover what 'Reject all' writes (no-cookie pool = current prod)")
    print("=" * 70)

    disc = WebDriverPool(pool_size=1, headless=True)
    d = disc.get_driver()
    d.set_page_load_timeout(25)

    goto(d, WATCH_A)
    before = {c["name"]: c["value"] for c in d.get_cookies()}
    before_ls = ls_keys(d)
    modal_before = modal_present(d)
    print(f"modal present on fresh headless load? {modal_before}")
    print(f"cookies before dismissal: {len(before)} | localStorage keys: {len(before_ls)}")

    dismissed = dismiss_youtube_cookies(d)
    modal_after_dismiss = modal_present(d, timeout=4)
    print(f"handler reported dismissal: {dismissed} | modal still present after: {modal_after_dismiss}")

    after = d.get_cookies()
    after_ls = ls_keys(d)
    changed = [c for c in after if before.get(c["name"]) != c["value"]]
    new_ls = after_ls - before_ls

    print(f"\ncookies new/changed by dismissal: {len(changed)}")
    for c in sorted(changed, key=lambda c: c["name"]):
        flag = "  <-- consent" if c["name"] in CONSENT_NAMES else ""
        print(f"  {c['name']:24} dom={c.get('domain'):20} "
              f"exp={c.get('expiry')} secure={c.get('secure')} "
              f"httpOnly={c.get('httpOnly')} sameSite={c.get('sameSite')}{flag}")
        print(f"      value={short(c['value'])}")
    print(f"\nlocalStorage keys ADDED by dismissal: {sorted(new_ls) if new_ls else 'none'}")

    candidates = [c for c in changed if c["name"] in CONSENT_NAMES]
    used_fallback = False
    if not candidates:
        used_fallback = True
        candidates = changed
        print("\n!! no SOCS/CONSENT cookie changed — falling back to the full changed set")
    print(f"\ninjection candidates: {[c['name'] for c in candidates]}")

    disc.cleanup()

    if not candidates:
        print("\nNo cookies to test. Aborting.")
        return

    print()
    print("=" * 70)
    print("PART 2 — inject candidate cookie(s), then test BEFORE and AFTER a wipe")
    print("=" * 70)

    inj = WebDriverPool(pool_size=1, headless=True, cookies=candidates, platform="youtube")
    d2 = inj.get_driver()
    d2.set_page_load_timeout(25)
    goto(d2, WATCH_B)
    modal_injected = modal_present(d2)
    print(f"[fresh inject]      modal present at {WATCH_B[-11:]}? {modal_injected}")

    # Exercise the real isolation cycle: return (wipe localStorage + reinject cookies)
    # then reuse the same driver for a second request.
    inj.return_driver(d2)
    d3 = inj.get_driver()
    d3.set_page_load_timeout(25)
    after_wipe_ls = ls_keys(d3)
    goto(d3, WATCH_C)
    modal_after_wipe = modal_present(d3)
    print(f"[after return wipe] localStorage keys carried over: {len(after_wipe_ls)}")
    print(f"[after return wipe] modal present at {WATCH_C[-11:]}? {modal_after_wipe}")

    inj.cleanup()

    print()
    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    if not modal_before:
        print("INCONCLUSIVE: modal never showed on the fresh load (geo? cached?).")
        print("Nothing to suppress, so suppression can't be confirmed from here.")
    elif modal_after_wipe:
        print("FAIL: cookie injection does NOT survive the localStorage wipe.")
        print("Consent depends on localStorage, which isolation erases. YouTube keeps its handler.")
    elif modal_injected:
        print("PARTIAL: suppressed on fresh inject but modal returned... (unexpected; inspect).")
    else:
        scope = "full changed set" if used_fallback else "SOCS/CONSENT only"
        print(f"PASS: injecting [{scope}] suppresses the modal even after a localStorage wipe.")
        print("Cookie injection is viable for YouTube; the live handler can become fallback-only.")
        print("\nBake these as the default consent cookie(s):")
        for c in candidates:
            print(f"  {c['name']} (domain={c.get('domain')}, value={short(c['value'], 80)})")


if __name__ == "__main__":
    main()
