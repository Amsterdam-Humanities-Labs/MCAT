"""Interpret a Set up browser session's cookies against a platform profile.

Two pure, offline-testable helpers, shared by the activity-log summary and the
consent indicator:

- ``classify_cookie_names`` splits names into consent / login / other per the
  profile's reporting sets.
- ``consent_login_events`` diffs the post-load baseline jar against the final
  jar and reports whether a consent / login cookie *appeared or changed value* —
  i.e. the user actually acted, as opposed to the site auto-setting its tokens
  on page load (e.g. X's ``guest_id``, an initial ``SOCS``). Keying on change,
  not presence, is what keeps "Consent saved" honest across platforms.
"""
from config.platform_profiles import get_profile


def classify_cookie_names(platform: str, names: list[str]) -> tuple[list[str], list[str], int]:
    """Split cookie names into (consent, login, other_count) per the profile's
    reporting sets. Order-preserving and de-duplicated."""
    profile = get_profile(platform)
    consent_names = set(profile.consent_cookies) if profile else set()
    login_names = set(profile.login_cookies) if profile else set()
    seen = list(dict.fromkeys(n for n in names if n))
    consent = [n for n in seen if n in consent_names]
    login = [n for n in seen if n in login_names]
    other = len(seen) - len(consent) - len(login)
    return consent, login, other


def changed_cookie_names(baseline: list[dict], final: list[dict]) -> list[str]:
    """Names in ``final`` that were absent from ``baseline`` or whose value
    changed — the cookies this session actually wrote, not ones already set when
    the window settled."""
    base = {c["name"]: c.get("value") for c in baseline if c.get("name")}
    return [
        c["name"] for c in final
        if c.get("name") and (c["name"] not in base or base[c["name"]] != c.get("value"))
    ]


def consent_login_events(baseline: list[dict], final: list[dict], platform: str) -> tuple[bool, bool]:
    """(consent_event, login_event): did a consent / login cookie appear or
    change value between the post-load baseline and the final jar?"""
    consent, login, _ = classify_cookie_names(platform, changed_cookie_names(baseline, final))
    return bool(consent), bool(login)
