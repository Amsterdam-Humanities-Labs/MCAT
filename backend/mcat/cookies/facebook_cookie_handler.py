"""
Facebook cookie consent modal handler.

Facebook uses div[role="button"] instead of <button> for cookie actions.

Maintainers: Update selectors here when Facebook changes their cookie modal.
Last updated: 2026-06-01
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

STRATEGIES = [
    (By.XPATH, ".//div[@role='button'][contains(text(), 'Decline optional cookies')]"),
    (By.XPATH, ".//div[@role='button'][contains(text(), 'Only allow essential cookies')]"),
    (By.XPATH, ".//div[@role='button'][contains(translate(., 'DECLINE', 'decline'), 'decline')]"),
]


def _find_cookie_dialog(driver: WebDriver, timeout: int) -> WebElement | None:
    try:
        dialogs = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[role="dialog"]'))
        )
        for dialog in dialogs:
            try:
                if "cookie" in dialog.text.lower():
                    return dialog
            except Exception:
                continue
    except TimeoutException:
        pass
    return None


def dismiss_facebook_cookies(driver: WebDriver, timeout: int = 3, wait_after: float = 1.0) -> bool:
    dialog = _find_cookie_dialog(driver, timeout)
    if not dialog:
        return True

    for by, selector in STRATEGIES:
        try:
            button = dialog.find_element(by, selector)
            if button.is_displayed():
                button.click()
                time.sleep(wait_after)
                return True
        except (NoSuchElementException, Exception):
            continue

    return False
