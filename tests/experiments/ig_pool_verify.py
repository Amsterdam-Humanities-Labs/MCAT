"""End-to-end: does the REAL WebDriverPool (with the fixed UA) now render the
main IG post image? Uses the production pool + the project's login cookies.

  backend/venv/bin/python tests/experiments/ig_pool_verify.py
"""
import sys
import json
import time
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from core.driver_manager import WebDriverPool  # noqa: E402

SHOTS = Path(__file__).resolve().parent / "shots"
SHOTS.mkdir(exist_ok=True)
JAR = Path("/home/m/Documents/projects/2025/mcat_projects/Instagram/cookies/instagram.json")
COOKIES = json.loads(JAR.read_text())["cookies"]
POST = "https://www.instagram.com/p/CH8faiynhTP/"

pool = WebDriverPool(pool_size=1, headless=True, cookies=COOKIES, platform="instagram")
try:
    d = pool.get_driver()
    d.set_page_load_timeout(30)
    print("pool UA:", d.execute_script("return navigator.userAgent"))
    d.get(POST)
    time.sleep(8)
    d.save_screenshot(str(SHOTS / "ig_pool_fixed.png"))
    print("shot: ig_pool_fixed.png")
finally:
    pool.cleanup()
