"""Run the hardened FB _detect_status against a random sample of the unverified
dataset (anonymous). No ground-truth labels, so it records the verdict + key
signals + a screenshot per URL named with the verdict, for eyeball review.

  backend/venv/bin/python tests/experiments/fb_sample_test.py [N]
"""
import sys
import csv
import random
import time
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from selenium.webdriver.common.by import By  # noqa: E402
from core.driver_manager import WebDriverPool  # noqa: E402
from scrapers.facebook_scraper import FacebookScraper  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "fixtures/live/unverified/facebook_sample_stopthesteal_2020.csv"
SHOTS = Path(__file__).resolve().parent / "shots" / "fb_sample"
SHOTS.mkdir(parents=True, exist_ok=True)

N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
rows = [r for r in csv.DictReader(DATA.open()) if r.get("url")]
random.seed(42)
sample = random.sample(rows, min(N, len(rows)))
print(f"sampling {len(sample)} of {len(rows)} urls (anonymous)\n")


def main():
    pool = WebDriverPool(pool_size=1, headless=True)  # incognito, no account
    scraper = FacebookScraper(pool)
    counts: dict[str, int] = {}
    try:
        for i, row in enumerate(sample):
            url = row["url"]
            d = pool.get_driver()
            d.set_page_load_timeout(30)
            try:
                d.get(url)
            except Exception:
                pass
            scraper._dismiss_consent(d)
            time.sleep(6)

            article = len(d.find_elements(By.CSS_SELECTOR, 'div[role="article"]'))
            pass_field = len(d.find_elements(By.CSS_SELECTOR, 'input[name="pass"]'))
            try:
                ogt = d.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]').get_attribute("content")
            except Exception:
                ogt = None
            verdict = scraper._detect_status(d, "")
            status = verdict[0] if verdict else "Unknown"
            counts[status] = counts.get(status, 0) + 1

            slug = url.rstrip("/").split("/")[-1][:12]
            d.save_screenshot(str(SHOTS / f"{i:02d}_{status}_{slug}.png"))
            pool.return_driver(d)

            print(f"{i:02d} {status:14} article={article:<2} pass={pass_field} "
                  f"og={(ogt or '')[:32]!r:34} {url}")
        print("\nDistribution:", counts)
    finally:
        pool.cleanup()


if __name__ == "__main__":
    main()
