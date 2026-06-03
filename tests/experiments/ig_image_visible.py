"""Does the main IG post image render in a VISIBLE (non-headless) browser?

Mirrors LoginService's visible driver (no headless, anti-automation flags, real
UA), injects the project's login cookies, loads the post, waits, and reports how
many real images painted. Pops a Chrome window briefly, then closes it.

  DISPLAY=:0 backend/venv/bin/python tests/experiments/ig_image_visible.py
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

opts = Options()  # visible: NO --headless
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)
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
    info = driver.execute_script(
        "const imgs=[...document.querySelectorAll('img')];"
        "const big=imgs.filter(i=>i.naturalWidth>200);"
        "return {total:imgs.length, big:big.length, hosts:[...new Set(big.map(i=>{try{return new URL(i.currentSrc||i.src).host}catch(e){return ''}}))].slice(0,4)};"
    )
    driver.save_screenshot(str(SHOTS / "ig_visible.png"))
    print("visible browser ->", info, "| shot: ig_visible.png")
finally:
    driver.quit()
