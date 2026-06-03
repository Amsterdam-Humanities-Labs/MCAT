"""Confirm a COMPLETE Windows Chrome UA (with the Chrome/Safari token) renders
the main image headless. If yes, the fix keeps the Windows disguise; the current
UA just lacks the Chrome version token.

  backend/venv/bin/python tests/experiments/ig_image_fullua.py
"""
import sys
import json
import time
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

import chromedriver_autoinstaller  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402
from selenium.webdriver.chrome.service import Service  # noqa: E402

SHOTS = Path(__file__).resolve().parent / "shots"
SHOTS.mkdir(exist_ok=True)
JAR = Path("/home/m/Documents/projects/2025/mcat_projects/Instagram/cookies/instagram.json")
POST = "https://www.instagram.com/p/CH8faiynhTP/"
COOKIES = json.loads(JAR.read_text())["cookies"]
FULL_WIN_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)
opts.add_argument(f"--user-agent={FULL_WIN_UA}")
opts.add_argument("--window-size=1000,1200")

driver = webdriver.Chrome(service=Service(chromedriver_autoinstaller.install()), options=opts)
driver.set_page_load_timeout(30)
try:
    driver.get("https://www.instagram.com")
    for c in COOKIES:
        try:
            driver.add_cookie(c)
        except Exception:
            pass
    driver.get(POST)
    time.sleep(8)
    driver.save_screenshot(str(SHOTS / "ig_fullua.png"))
    print("complete Windows UA, headless -> shot: ig_fullua.png")
finally:
    driver.quit()
