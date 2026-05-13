"""
Test Instagram cookie consent dismissal.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "mcat"))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller

from cookies.instagram_cookie_handler import dismiss_instagram_cookies


def create_driver():
    chromedriver_autoinstaller.install()
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_argument("--window-size=1200,800")
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    return driver


def main():
    driver = create_driver()
    try:
        url = "https://www.instagram.com/p/CH9GrAbn7fE/"
        print(f"Loading: {url}")
        driver.get(url)
        time.sleep(2)

        # Check if cookie dialog is present before dismissal
        dialogs = driver.find_elements(By.CSS_SELECTOR, 'div[role="dialog"]')
        cookie_dialogs = [d for d in dialogs if "cookie" in d.text.lower()]
        print(f"Cookie dialogs before: {len(cookie_dialogs)}")

        # Dismiss
        result = dismiss_instagram_cookies(driver, timeout=3)
        print(f"Dismiss result: {result}")

        time.sleep(1)

        # Check if cookie dialog is gone
        dialogs = driver.find_elements(By.CSS_SELECTOR, 'div[role="dialog"]')
        cookie_dialogs = [d for d in dialogs if "cookie" in d.text.lower()]
        print(f"Cookie dialogs after: {len(cookie_dialogs)}")

        if result and len(cookie_dialogs) == 0:
            print("PASSED: Cookie modal dismissed")
        elif result and len(cookie_dialogs) > 0:
            print("PARTIAL: Dismiss returned True but dialog still visible")
        else:
            print("FAILED: Could not dismiss cookie modal")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
