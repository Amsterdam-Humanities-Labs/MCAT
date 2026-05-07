"""
Manual test: Instagram login flow.

Opens a visible Chrome window for you to log in. After login,
captures cookies and saves them to a temp folder.

Usage:
    python tests/test_login_flow.py
"""

import sys
import time
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "mcat"))

from cookies.cookie_store import CookieStore
from services.login_service import LoginService


def main():
    tmp = Path(tempfile.mkdtemp(prefix="mcat_login_test_"))
    print(f"Cookie store: {tmp}")

    store = CookieStore(tmp)
    service = LoginService(store)

    print("\nOpening Instagram login window...")
    result = service.start_login("instagram")
    if not result["success"]:
        print(f"Failed: {result['error']}")
        return

    print("Please log in to Instagram in the browser window.")
    print("Polling for login status...\n")

    while True:
        status = service.check_login()
        if status.get("logged_in"):
            print(f"Login detected! Username: {status.get('username', '?')}")
            break
        print("  Not logged in yet...")
        time.sleep(2)

    print("\nCapturing cookies...")
    result = service.complete_login()

    if result["success"]:
        print(f"Saved {result['cookie_count']} cookies for user: {result['username']}")
        info = store.get_cookie_info("instagram")
        print(f"Cookie info: {info}")

        # Verify round-trip
        cookies = store.load_cookies("instagram")
        print(f"Loaded back {len(cookies)} cookies from disk")
        print(f"\nCookie file: {tmp / 'cookies' / 'instagram.json'}")
    else:
        print(f"Failed: {result.get('error')}")


if __name__ == "__main__":
    main()
