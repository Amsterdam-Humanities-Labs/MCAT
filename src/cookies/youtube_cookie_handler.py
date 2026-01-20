"""
YouTube cookie consent modal handler.

Maintainers: Update selectors here when YouTube changes their cookie modal.
Last updated: 2026-01-14
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time


# Selector strategies (tried in order)
STRATEGIES = [
    # Strategy 1: Aria-label (most reliable)
    (By.CSS_SELECTOR, 'button[aria-label*="Reject the use of cookies"]'),

    # Strategy 2: Text content via XPath
    (By.XPATH, "//button[.//span[text()='Reject all']]"),

    # Strategy 3: CSS class chain
    (By.CSS_SELECTOR, '.eom-buttons ytd-button-renderer:first-child button'),

    # Strategy 4: Generic dialog button
    (By.CSS_SELECTOR, 'tp-yt-paper-dialog button[aria-label*="Reject"]'),
]

# JavaScript fallback
JS_DISMISS = """
    let buttons = document.querySelectorAll('.eom-buttons button, tp-yt-paper-dialog button');
    if (buttons.length >= 2) {
        buttons[0].click();
        return true;
    }
    return false;
"""

# Modal detection
MODAL_SELECTOR = (By.CSS_SELECTOR, 'tp-yt-paper-dialog[role="dialog"]')


def dismiss_youtube_cookies(driver, timeout: int = 3, wait_after: float = 1.0) -> bool:
    """
    Dismiss YouTube cookie consent modal.

    Args:
        driver: Selenium WebDriver instance
        timeout: Max seconds to wait for modal (default: 3)
        wait_after: Seconds to wait after clicking (default: 1.0)

    Returns:
        True if modal dismissed or not present, False if present but couldn't dismiss
    """
    try:
        # Check if modal exists
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(MODAL_SELECTOR)
        )

        # Try each strategy
        for by, selector in STRATEGIES:
            try:
                button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((by, selector))
                )
                button.click()
                time.sleep(wait_after)
                return True
            except (TimeoutException, NoSuchElementException):
                continue

        # Fallback: JavaScript
        if driver.execute_script(JS_DISMISS):
            time.sleep(wait_after)
            return True

        # Modal present but couldn't dismiss
        return False

    except TimeoutException:
        # No modal found
        return True
    except Exception as e:
        print(f"⚠️ Cookie modal error: {e}")
        return False
