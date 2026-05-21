"""
Instagram cookie consent modal handler.

Maintainers: Update selectors here when Instagram changes their cookie modal.
Last updated: 2026-05-13
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time


STRATEGIES = [
    (By.XPATH, "//button[contains(text(), 'Decline optional cookies')]"),
    (By.XPATH, "//button[contains(text(), 'decline optional cookies')]"),
    (By.CSS_SELECTOR, 'button._a9_1'),
    (By.XPATH, "//button[contains(translate(., 'DECLINE', 'decline'), 'decline')]"),
]

JS_DISMISS = """
    let dialogs = document.querySelectorAll('div[role="dialog"]');
    for (let d of dialogs) {
        if (d.textContent.toLowerCase().includes('cookie')) {
            let buttons = d.querySelectorAll('button');
            for (let b of buttons) {
                if (b.textContent.toLowerCase().includes('decline')) {
                    b.click();
                    return true;
                }
            }
            if (buttons.length >= 2) {
                buttons[0].click();
                return true;
            }
        }
    }
    return false;
"""


def _find_cookie_dialog(driver: object, timeout: int) -> object | None:
    """Find the dialog element containing cookie consent text."""
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


def dismiss_instagram_cookies(driver: object, timeout: int = 3, wait_after: float = 1.0) -> bool:
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

    if driver.execute_script(JS_DISMISS):
        time.sleep(wait_after)
        return True

    return False
