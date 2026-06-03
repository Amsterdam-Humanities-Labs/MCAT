"""Why is the MAIN IG post image black while thumbnails load? Try the levers.

Loads one IG post with the project's login cookies under three configs and
reports whether the main <article img> actually has pixels:
  1. current  : old --headless, --disable-gpu, --disable-images  (pool today)
  2. images-on : old --headless, --disable-gpu, images enabled
  3. best      : --headless=new, GPU kept, images enabled, scroll-into-view

  backend/venv/bin/python tests/experiments/ig_image_probe.py
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
DRIVER_PATH = chromedriver_autoinstaller.install()
COOKIES = json.loads(JAR.read_text())["cookies"]


def make_options(disable_images: bool, new_headless: bool, keep_gpu: bool) -> Options:
    o = Options()
    o.add_argument("--headless=new" if new_headless else "--headless")
    o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage")
    if not keep_gpu:
        o.add_argument("--disable-gpu")
    if disable_images:
        o.add_argument("--disable-images")
    o.add_argument("--ignore-certificate-errors")
    o.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    o.add_argument("--window-size=800,1200")
    return o


def run(opts: Options, label: str, scroll: bool):
    driver = webdriver.Chrome(service=Service(DRIVER_PATH), options=opts)
    driver.set_page_load_timeout(30)
    try:
        driver.get("https://www.instagram.com")
        for c in COOKIES:
            try:
                driver.add_cookie(c)
            except Exception:
                pass
        try:
            driver.get(POST)
        except Exception as e:
            print(f"  get raised {type(e).__name__}")
        time.sleep(4)
        if scroll:
            driver.execute_script("const i=document.querySelector('article img'); if(i) i.scrollIntoView({block:'center'});")
            time.sleep(4)
        else:
            time.sleep(4)
        info = driver.execute_script(
            "const i=document.querySelector('article img');"
            "return i ? {found:true, nw:i.naturalWidth, src:(i.currentSrc||i.src||'').slice(0,70)} : {found:false};"
        )
        driver.save_screenshot(str(SHOTS / f"ig_main_{label}.png"))
        print(f"  [{label}] main article img -> {info}")
    finally:
        driver.quit()


print("1. current (disable-images, old headless, no gpu):")
run(make_options(True, False, False), "current", scroll=False)
print("2. images-on (old headless, no gpu):")
run(make_options(False, False, False), "imageson", scroll=False)
print("3. best (new headless, gpu kept, scroll):")
run(make_options(False, True, True), "best", scroll=True)
