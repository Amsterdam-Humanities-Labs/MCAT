"""Generalized store-level flow check, driven by the platform profile.

Verifies cookie_store + the job_builder auth_user rule for any platform:
- a jar WITHOUT the login cookie loads and reads as anonymous (consent-only),
- a jar WITH the login cookie reads as logged in with the right mcat_user.
No browser, no network.

  backend/venv/bin/python tests/experiments/flow_check.py <platform>
"""
import sys
import tempfile
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from cookies.cookie_store import CookieStore  # noqa: E402
from config.platform_profiles import get_profile  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")


def cookie(name, value="x"):
    return {"name": name, "value": value, "path": "/", "secure": True}


def auth_user_of(info):
    # mirrors services/job_builder.py
    if info and info["username"]:
        return info["username"]
    if info and info.get("logged_in"):
        return "logged-in"
    return "anonymous"


def main():
    platform = sys.argv[1] if len(sys.argv) > 1 else None
    profile = get_profile(platform)
    if not platform or not profile:
        print("usage: flow_check.py <platform>")
        sys.exit(2)

    print(f"=== {platform} store flow ===")
    marker = "consent_marker"

    with tempfile.TemporaryDirectory() as tmp:
        store = CookieStore(Path(tmp))

        print("no-login jar (consent-only):")
        store.save_cookies(platform, [cookie(marker)], username="")
        info = store.get_cookie_info(platform)
        check("loads", store.load_cookies(platform) is not None)
        check("logged_in is False", bool(info) and info.get("logged_in") is False)
        check('auth_user is "anonymous"', auth_user_of(info) == "anonymous")

        if not profile.login_cookie:
            print(f"  ({platform} has no login cookie; login case N/A)")
        else:
            print("login jar:")
            jar = [cookie(marker)]
            uname = ""
            if profile.username_cookie == profile.login_cookie:
                jar.append(cookie(profile.login_cookie, "1042"))  # one cookie is both (FB c_user)
                uname = "1042"
            else:
                jar.append(cookie(profile.login_cookie, "sess"))
                if profile.username_cookie:
                    jar.append(cookie(profile.username_cookie, "1042"))
                    uname = "1042"
            store.save_cookies(platform, jar, username=uname)
            info = store.get_cookie_info(platform)
            expected = uname or "logged-in"
            check("loads", store.load_cookies(platform) is not None)
            check("logged_in is True", bool(info) and info.get("logged_in") is True)
            check(f'auth_user is "{expected}"', auth_user_of(info) == expected)

    print("RESULT:", "ALL PASS" if ok else "FAILURES ABOVE")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
