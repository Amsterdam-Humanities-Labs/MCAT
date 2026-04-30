"""
Test script: observe YouTube page loading order.

For each URL, polls every 0.3s and logs which detection-relevant signals
are present at each tick. This tells us the order elements appear in,
and how long each takes — so we can design a reliable "page is ready" signal.

Usage:
  python tests/test_youtube_loading.py              # normal mode
  python tests/test_youtube_loading.py --eager       # eager page load strategy
  python tests/test_youtube_loading.py --throttle    # throttled network
  python tests/test_youtube_loading.py --eager --throttle  # both
"""

import argparse
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "mcat"))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException as SeleniumTimeout
import chromedriver_autoinstaller

from cookies.youtube_cookie_handler import dismiss_youtube_cookies

POLL_INTERVAL = 0.3
MAX_POLL_TIME = 30.0
NUM_URLS = 6


def create_driver(eager=False):
    chromedriver_autoinstaller.install()
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-images")
    opts.add_argument("--incognito")
    opts.add_argument("--mute-audio")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)

    if eager:
        opts.page_load_strategy = 'eager'

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

    removal_phrases = [
        'video unavailable', 'this video is not available',
        "this video isn't available", "video isn't available anymore",
        'removed by the user', 'account has been terminated'
    ]
    signals["has_removal_text"] = any(p in body_lower for p in removal_phrases)

    signals["has_age_restricted"] = (
        'age-restricted' in body_lower or 'sign in to confirm your age' in body_lower
    )

    try:
        title_el = driver.find_element(By.CSS_SELECTOR, 'h1.ytd-watch-metadata, h1.title')
        signals["h1_title"] = title_el.text.strip()[:60] if title_el.text.strip() else None
    except Exception:
        signals["h1_title"] = None

    try:
        driver.find_element(By.CSS_SELECTOR, '#movie_player, ytd-player')
        signals["has_player"] = True
    except Exception:
        signals["has_player"] = False

    try:
        driver.find_element(By.CSS_SELECTOR, '#error-page, yt-player-error-message-renderer')
        signals["has_error_el"] = True
    except Exception:
        signals["has_error_el"] = False

    try:
        driver.find_element(By.CSS_SELECTOR, 'ytd-watch-metadata')
        signals["has_watch_metadata"] = True
    except Exception:
        signals["has_watch_metadata"] = False

    try:
        driver.find_element(By.CSS_SELECTOR, '#above-the-fold, #owner')
        signals["has_secondary_info"] = True
    except Exception:
        signals["has_secondary_info"] = False

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
        print(f"  driver.get() TIMED OUT at {elapsed:.2f}s (page still loading, will poll)")

    dismiss_youtube_cookies(driver, timeout=2)
    after_cookies = time.time() - start
    print(f"  cookie handler done at {after_cookies:.2f}s")

    first_seen = {}
    while (time.time() - start) < MAX_POLL_TIME:
        elapsed = time.time() - start
        signals = check_signals(driver)

        new_this_tick = []
        for key, val in signals.items():
            if key in first_seen:
                continue
            is_present = False
            if key == "title" and val and val != "YouTube" and len(val) > 0:
                is_present = True
            elif key == "body_text_len" and val and val > 100:
                is_present = True
            elif key == "h1_title" and val:
                is_present = True
            elif key in ("has_removal_text", "has_age_restricted", "has_player",
                         "has_error_el", "has_watch_metadata", "has_secondary_info") and val:
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

    final_title = ""
    try:
        final_title = driver.title
    except Exception:
        pass

    body_lower = ""
    try:
        body_lower = driver.find_element(By.TAG_NAME, "body").text.lower()
    except Exception:
        pass

    if any(p in body_lower for p in ['video unavailable', 'this video is not available',
                                      "this video isn't available", "video isn't available anymore",
                                      'removed by the user', 'account has been terminated']):
        conclusion = "Removed"
    elif 'h1_title' in first_seen:
        conclusion = "Live (h1 present)"
    elif final_title and final_title != "YouTube" and " - YouTube" in final_title:
        conclusion = "Live (title-based, no h1)"
    else:
        conclusion = "Unknown"

    print(f"    -> Final page title: {final_title}")
    print(f"    -> Final conclusion: {conclusion}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eager", action="store_true", help="Use eager page load strategy")
    parser.add_argument("--throttle", action="store_true", help="Throttle network via CDP")
    args = parser.parse_args()

    csv_path = Path(__file__).resolve().parent / "fixtures" / \
        "Sample - YouTube - YouTube search results for StopTheSteal sorted by date - Nov 2020.csv"

    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        sys.exit(1)

    urls = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            video_id = row.get('videoId', '')
            if video_id:
                urls.append(f"https://www.youtube.com/watch?v={video_id}")

    print(f"URLs: {len(urls)} total, testing first {NUM_URLS}")
    print(f"Mode: {'eager' if args.eager else 'normal'} page load, "
          f"{'throttled' if args.throttle else 'unthrottled'} network")
    print(f"Poll: {POLL_INTERVAL}s interval, {MAX_POLL_TIME}s max\n")

    driver = create_driver(eager=args.eager)

    if args.throttle:
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
            "offline": False,
            "latency": 150,
            "downloadThroughput": 300 * 1024,
            "uploadThroughput": 75 * 1024,
        })
        print("Throttle: 300KB/s down, 75KB/s up, 150ms latency")

    try:
        for i, url in enumerate(urls[:NUM_URLS], 1):
            test_url(driver, url, i)
    finally:
        driver.quit()

    print("\n\nDone.")


if __name__ == "__main__":
    main()
