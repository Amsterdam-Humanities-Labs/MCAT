"""
Test script: observe Instagram page loading order and detection signals.

Usage:
  python tests/test_instagram_loading.py
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
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-images")
    opts.add_argument("--incognito")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
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

    # Error text patterns
    error_phrases = [
        "sorry, this page isn't available",
        "this page isn't available",
        "page not found",
        "post isn't available",
        "content isn't available",
        "isn't available",
        "not available",
        "restricted",
    ]
    matched = [p for p in error_phrases if p in body_lower]
    signals["error_text"] = matched[0] if matched else None

    # Login wall
    signals["has_login_wall"] = "log in" in body_lower and "sign up" in body_lower

    # Error SVG
    try:
        driver.find_element(By.CSS_SELECTOR, 'svg[aria-label="error"]')
        signals["has_error_svg"] = True
    except Exception:
        signals["has_error_svg"] = False

    # Article element (positive Live signal)
    try:
        driver.find_element(By.CSS_SELECTOR, 'article[role="presentation"]')
        signals["has_article"] = True
    except Exception:
        signals["has_article"] = False

    # Main content area
    try:
        driver.find_element(By.CSS_SELECTOR, 'main[role="main"]')
        signals["has_main"] = True
    except Exception:
        signals["has_main"] = False

    # og:title meta tag
    try:
        meta = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
        content = meta.get_attribute("content")
        signals["og_title"] = content[:60] if content else None
    except Exception:
        signals["og_title"] = None

    # og:description meta tag
    try:
        meta = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:description"]')
        content = meta.get_attribute("content")
        signals["og_description"] = content[:60] if content else None
    except Exception:
        signals["og_description"] = None

    # Image elements (posts have images)
    try:
        imgs = driver.find_elements(By.CSS_SELECTOR, 'article img, div[role="button"] img')
        signals["post_images"] = len(imgs) if imgs else 0
    except Exception:
        signals["post_images"] = 0

    # Video elements
    try:
        vids = driver.find_elements(By.CSS_SELECTOR, 'article video, video')
        signals["videos"] = len(vids) if vids else 0
    except Exception:
        signals["videos"] = 0

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
            if key == "title" and val and val not in ("Instagram", ""):
                is_present = True
            elif key == "body_text_len" and val and val > 50:
                is_present = True
            elif key == "error_text" and val:
                is_present = True
            elif key in ("has_login_wall", "has_error_svg", "has_article", "has_main") and val:
                is_present = True
            elif key in ("og_title", "og_description") and val:
                is_present = True
            elif key == "post_images" and val > 0:
                is_present = True
            elif key == "videos" and val > 0:
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

    # Body text snippet
    try:
        body = driver.find_element(By.TAG_NAME, "body").text
        print(f"\n  BODY TEXT (first 300 chars):")
        for line in body[:300].split('\n'):
            if line.strip():
                print(f"    {line.strip()[:100]}")
    except Exception:
        pass


def main():
    csv_path = Path(__file__).resolve().parent / "fixtures" / "live" / "unverified" / \
        "instagram_sample_us_elections_2020.csv"

    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        sys.exit(1)

    urls = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            url = row.get('url', '').strip()
            if url:
                urls.append(url)

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
