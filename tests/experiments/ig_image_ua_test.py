"""Isolate it: the visible run differed from headless in 3 ways (headless,
spoofed Windows UA, no anti-automation flags). This runs HEADLESS but otherwise
identical to the working visible config (real UA + anti-automation flags). If the
main image paints here, headless is NOT the blocker and the fix is cheap.

  backend/venv/bin/python tests/experiments/ig_image_ua_test.py
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


def make_opts(headless: bool, spoof_ua: bool, anti_automation: bool) -> Options:
    o = Options()
    if headless:
        o.add_argument("--headless=new")
    o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage")
    if anti_automation:
        o.add_argument("--disable-blink-features=AutomationControlled")
        o.add_experimental_option("excludeSwitches", ["enable-automation"])
        o.add_experimental_option("useAutomationExtension", False)
    if spoof_ua:
        o.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    o.add_argument("--window-size=1000,1200")
    return o


def run(label, **kw):
    driver = webdriver.Chrome(service=Service(chromedriver_autoinstaller.install()), options=make_opts(**kw))
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
        big = driver.execute_script(
            "return [...document.querySelectorAll('img')].filter(i=>i.naturalWidth>200).length"
        )
        driver.save_screenshot(str(SHOTS / f"ig_ua_{label}.png"))
        print(f"  [{label}] big images loaded: {big}")
    finally:
        driver.quit()


# headless, but real UA + anti-automation (like the working visible run)
print("A. headless + real UA + anti-automation:")
run("A_real_anti", headless=True, spoof_ua=False, anti_automation=True)
# headless, real UA, no anti-automation -> isolate the UA alone
print("B. headless + real UA, no anti-automation:")
run("B_real_noanti", headless=True, spoof_ua=False, anti_automation=False)
# headless, spoofed UA + anti-automation -> isolate the spoof alone
print("C. headless + spoofed UA + anti-automation:")
run("C_spoof_anti", headless=True, spoof_ua=True, anti_automation=True)
