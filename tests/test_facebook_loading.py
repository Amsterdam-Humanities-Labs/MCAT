"""
Test script: observe Facebook page loading order and detection signals.

Usage:
  python tests/test_facebook_loading.py
"""

import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "mcat"))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException as SeleniumTimeout
import chromedriver_autoinstaller

POLL_INTERVAL = 0.3
MAX_POLL_TIME = 20.0
NUM_URLS = 10


def create_driver():
    chromedriver_autoinstaller.install()
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_argument("--window-size=1200,800")
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    return driver


def check_signals(driver):
    signals = {}

    try:
        signals["title"] = driver.title
    except Exception:
        signals["title"] = None

    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
        signals["body_text_len"] = len(body_text)
        body_lower = body_text.lower()
    except Exception:
        signals["body_text_len"] = 0
        body_lower = ""

    # Error/unavailable text
    error_phrases = [
        "this content isn't available",
        "this page isn't available",
        "content isn't available right now",
        "the link you followed may be broken",
        "page not found",
        "this content has been removed",
    ]
    matched = [p for p in error_phrases if p in body_lower]
    signals["error_text"] = matched[0] if matched else None

    # Login wall
    signals["has_login_wall"] = "log in" in body_lower or "create new account" in body_lower

    # Article element (post container)
    try:
        driver.find_element(By.CSS_SELECTOR, 'div[role="article"]')
        signals["has_article"] = True
    except Exception:
        signals["has_article"] = False

    # Moderation overlay (old selector)
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, '.xzueoph.x1k70j0n')
        texts = [el.text.strip() for el in elements if el.text.strip()]
        signals["moderation_overlay"] = texts[0][:80] if texts else None
    except Exception:
        signals["moderation_overlay"] = None

    # og:title
    try:
        meta = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
        content = meta.get_attribute("content")
        signals["og_title"] = content[:60] if content else None
    except Exception:
        signals["og_title"] = None

    # og:description
    try:
        meta = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:description"]')
        content = meta.get_attribute("content")
        signals["og_description"] = content[:60] if content else None
    except Exception:
        signals["og_description"] = None

    # Dialog elements (cookie consent, login prompts)
    try:
        dialogs = driver.find_elements(By.CSS_SELECTOR, 'div[role="dialog"]')
        dialog_texts = []
        for d in dialogs[:3]:
            t = d.text[:80].replace('\n', ' ').strip()
            if t:
                dialog_texts.append(t)
        signals["dialogs"] = dialog_texts if dialog_texts else None
    except Exception:
        signals["dialogs"] = None

    # Main content
    try:
        driver.find_element(By.CSS_SELECTOR, 'div[role="main"]')
        signals["has_main"] = True
    except Exception:
        signals["has_main"] = False

    # Current URL (redirects?)
    try:
        signals["current_url"] = driver.current_url[:80]
    except Exception:
        signals["current_url"] = None

    return signals


def test_url(driver, url, url_index):
    print(f"\n{'='*80}")
    print(f"URL {url_index}: {url}")
    print(f"{'='*80}")

    start = time.time()
    try:
        driver.get(url)
        elapsed = time.time() - start
        print(f"  driver.get() returned at {elapsed:.2f}s")
    except SeleniumTimeout:
        elapsed = time.time() - start
        print(f"  driver.get() TIMED OUT at {elapsed:.2f}s")

    first_seen = {}
    while (time.time() - start) < MAX_POLL_TIME:
        elapsed = time.time() - start
        signals = check_signals(driver)

        new_this_tick = []
        for key, val in signals.items():
            if key in first_seen:
                continue
            is_present = False
            if key == "title" and val and val not in ("Facebook", ""):
                is_present = True
            elif key == "body_text_len" and val and val > 50:
                is_present = True
            elif key == "error_text" and val:
                is_present = True
            elif key in ("has_login_wall", "has_article", "has_main") and val:
                is_present = True
            elif key in ("og_title", "og_description", "moderation_overlay") and val:
                is_present = True
            elif key == "dialogs" and val:
                is_present = True
            elif key == "current_url" and val and "login" in val.lower():
                is_present = True

            if is_present:
                first_seen[key] = (elapsed, val)
                new_this_tick.append(key)

        if new_this_tick:
            print(f"  [{elapsed:5.1f}s] NEW signals: {', '.join(new_this_tick)}")
            for k in new_this_tick:
                t, v = first_seen[k]
                display = v if not isinstance(v, str) or len(str(v)) < 80 else str(v)[:77] + "..."
                print(f"           {k} = {display}")

        time.sleep(POLL_INTERVAL)

    # Summary
    print(f"\n  SUMMARY (signals by appearance order):")
    for key, (t, val) in sorted(first_seen.items(), key=lambda x: x[1][0]):
        display = val if not isinstance(val, str) or len(str(val)) < 60 else str(val)[:57] + "..."
        print(f"    {t:5.1f}s  {key:25s} = {display}")

    # Body text
    try:
        body = driver.find_element(By.TAG_NAME, "body").text
        print(f"\n  BODY TEXT (first 300 chars):")
        for line in body[:300].split('\n'):
            if line.strip():
                print(f"    {line.strip()[:120]}")
    except Exception:
        pass


def main():
    csv_path = Path(__file__).resolve().parent / "fixtures" / "live" / "unverified" / \
        "facebook_sample_stopthesteal_2020.csv"

    urls = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            url = row.get('url', '').strip()
            if url:
                urls.append(url)

    # Also add a likely-removed URL (fake post ID)
    urls.insert(5, "https://www.facebook.com/permalink.php?story_fbid=999999999999999&id=100000000000000")

    print(f"URLs: {len(urls)} total, testing first {NUM_URLS}")
    print(f"Poll: {POLL_INTERVAL}s interval, {MAX_POLL_TIME}s max\n")

    driver = create_driver()

    try:
        for i, url in enumerate(urls[:NUM_URLS], 1):
            test_url(driver, url, i)
    finally:
        driver.quit()

    print("\n\nDone.")


if __name__ == "__main__":
    main()
