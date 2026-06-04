"""Characterize Facebook's Live vs Removed pages against the verified set, to
design a better _detect_status. Uses the Fb123 login jar + the real pool, and
prints the raw signals plus the CURRENT scraper verdict for each labeled URL.

  backend/venv/bin/python tests/experiments/fb_detect_probe.py
"""
import sys
import json
import csv
import time
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from selenium.webdriver.common.by import By  # noqa: E402
from core.driver_manager import WebDriverPool  # noqa: E402
from scrapers.facebook_scraper import FacebookScraper  # noqa: E402

SHOTS = Path(__file__).resolve().parent / "shots"
SHOTS.mkdir(exist_ok=True)
JAR = Path("/home/m/Documents/projects/2025/mcat_projects/Fb123/cookies/facebook.json")
VERIFIED = Path(__file__).resolve().parents[1] / "fixtures/live/verified/facebook_verified_urls.csv"
COOKIES = json.loads(JAR.read_text())["cookies"]
ROWS = list(csv.DictReader(VERIFIED.open()))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "login"  # login | anon
    if mode == "anon":
        pool = WebDriverPool(pool_size=1, headless=True)  # incognito, no cookies
    else:
        pool = WebDriverPool(pool_size=1, headless=True, cookies=COOKIES, platform="facebook")
    print(f"### MODE: {mode} ###")
    scraper = FacebookScraper(pool)  # only for REMOVAL_PHRASES + _detect_status
    try:
        for row in ROWS:
            url, expected = row["url"], row["status"]
            d = pool.get_driver()
            d.set_page_load_timeout(30)
            try:
                d.get(url)
            except Exception as e:
                print(f"  get raised {type(e).__name__}")
            if mode == "anon":
                scraper._dismiss_consent(d)  # clear the cookie modal first
            time.sleep(6)

            def meta(prop):
                try:
                    return d.find_element(By.CSS_SELECTOR, f'meta[property="{prop}"]').get_attribute("content")
                except Exception:
                    return None

            title = d.title
            og_title = meta("og:title")
            og_desc = meta("og:description")
            article = len(d.find_elements(By.CSS_SELECTOR, 'div[role="article"]'))
            try:
                body = d.find_element(By.TAG_NAME, "body").text.lower()
            except Exception:
                body = ""
            removal_hit = next((p for p in scraper.REMOVAL_PHRASES if p in body), None)
            login_hit = ("log in" in body and "create new account" in body)
            current = scraper._detect_status(d, "")

            slug = url.rstrip("/").split("/")[-1][:14]
            d.save_screenshot(str(SHOTS / f"fb_{expected.lower()}_{slug}.png"))
            pool.return_driver(d)

            print(f"\n=== EXPECTED: {expected}  |  {url}")
            print(f"  title        : {title!r}")
            print(f"  og:title     : {og_title!r}")
            print(f"  og:desc      : {(og_desc or '')[:90]!r}")
            print(f"  div[article] : {article}")
            print(f"  removal hit  : {removal_hit!r}")
            print(f"  login wall   : {login_hit}")
            print(f"  body[:140]   : {body[:140]!r}")
            print(f"  >>> CURRENT _detect_status: {current}")
    finally:
        pool.cleanup()


if __name__ == "__main__":
    main()
