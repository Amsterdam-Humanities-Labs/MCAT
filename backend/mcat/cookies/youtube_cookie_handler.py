"""
YouTube cookie consent modal handler.

Maintainers: Update selectors here when YouTube changes their cookie modal.
Last updated: 2026-05-20
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

CONSENT_KEYWORDS = ("cookie", "consent", "before you continue")

STRATEGIES = [
    (By.CSS_SELECTOR, 'button[aria-label*="Reject the use of cookies"]'),
    (By.XPATH, ".//button[.//span[text()='Reject all']]"),
    (By.CSS_SELECTOR, '.eom-buttons ytd-button-renderer:first-child button'),
    (By.CSS_SELECTOR, 'button[aria-label*="Reject"]'),
]


def _find_consent_dialog(driver: object, timeout: int) -> object | None:
    """Find the cookie consent dialog by checking dialog text content."""
    try:
        dialogs = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'tp-yt-paper-dialog[role="dialog"], div[role="dialog"]')
            )
        )
        for dialog in dialogs:
            try:
                text = dialog.text.lower()
                if any(kw in text for kw in CONSENT_KEYWORDS):
                    return dialog
            except Exception:
                continue
    except TimeoutException:
        pass
    return None


def dismiss_youtube_cookies(driver: object, timeout: int = 3, wait_after: float = 1.0) -> bool:
    dialog = _find_consent_dialog(driver, timeout)
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
