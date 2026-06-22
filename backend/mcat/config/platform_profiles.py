"""Per-platform auth/cookie facts in one place.

Each platform declares its setup URL, which cookie marks a logged-in session,
and which cookie carries the account id. The capture / inject / expiry machinery
is generic and reads these profiles, so adding a platform is one entry here (plus
an injection probe to confirm cookie auth actually works headless for it).

No consent cookies are ever shipped as default *values*: when a project has no
cookies, the user is asked to Set up browser, which captures consent (and
optional login) into the per-project jar. The consent_cookies / login_cookies
*names* below are reporting-only — they label what a setup session captured in
the activity log and drive no capture/inject/expiry logic.

This lives in `config` because `core`, `cookies`, and `services` all consume it
and all already depend on `config`, so there is no new cross-package coupling.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformProfile:
    platform: str
    # Base URL used both to open the Set up browser window and as the domain to
    # navigate to before injecting cookies.
    base_url: str
    # Whether the Set up browser flow is wired and verified for this platform.
    supports_setup: bool = True
    # Cookie whose presence/validity marks a logged-in session. Drives expiry
    # detection (cookie_store) and login auto-detect (login_service). None means
    # the platform is not gated on login (e.g. YouTube: a consent-only jar must
    # still load, so this stays None until the per-cookie load-gate fix lands).
    login_cookie: str | None = None
    # Cookie whose value is the account id shown to the user and recorded in
    # the mcat_user column. None means no readable id (e.g. Google/YouTube).
    username_cookie: str | None = None
    # Reporting-only cookie-name sets, used purely to label what a Set up
    # browser session captured in the activity log (consent vs login vs other).
    # They never drive capture, injection, or expiry — the full jar is always
    # captured regardless — so a stale or missing name only makes the log
    # message slightly less precise (the cookie falls into the "other" bucket)
    # and never changes behaviour. Keep the two sets disjoint.
    consent_cookies: tuple[str, ...] = ()
    login_cookies: tuple[str, ...] = ()


PROFILES: dict[str, PlatformProfile] = {
    "instagram": PlatformProfile(
        "instagram", "https://www.instagram.com",
        login_cookie="sessionid", username_cookie="ds_user_id",
        consent_cookies=("mid", "ig_did", "datr"),
        login_cookies=("sessionid", "ds_user_id", "csrftoken", "rur"),
    ),
    "facebook": PlatformProfile(
        "facebook", "https://www.facebook.com",
        login_cookie="c_user", username_cookie="c_user",
        consent_cookies=("datr", "sb"),
        login_cookies=("c_user", "xs", "fr"),
    ),
    "youtube": PlatformProfile(
        "youtube", "https://www.youtube.com",
        # No readable account id cookie, so username_cookie stays None and an
        # authenticated run is recorded as "logged-in". A consent-only jar (no
        # LOGIN_INFO) still loads because a missing login cookie is not expired.
        login_cookie="LOGIN_INFO",
        consent_cookies=("SOCS", "CONSENT"),
        login_cookies=("LOGIN_INFO", "SID", "HSID", "SSID", "APISID", "SAPISID",
                       "__Secure-1PSID", "__Secure-3PSID"),
    ),
    "twitter": PlatformProfile(
        "twitter", "https://x.com",
        login_cookie="auth_token", username_cookie="twid",
        consent_cookies=("guest_id", "personalization_id", "gt"),
        login_cookies=("auth_token", "ct0", "twid"),
    ),
}


def get_profile(platform: str | None) -> PlatformProfile | None:
    if not platform:
        return None
    return PROFILES.get(platform)
