"""Unit tests for cookies.cookie_diff — consent/login classification and the
baseline-vs-final diff that powers the consent indicator (offline)."""
from cookies.cookie_diff import (
    classify_cookie_names,
    changed_cookie_names,
    consent_login_events,
)


def _c(name, value):
    return {"name": name, "value": value}


# --- classify_cookie_names ---

def test_classify_splits_by_profile_sets():
    consent, login, other = classify_cookie_names(
        "youtube", ["SOCS", "LOGIN_INFO", "VISITOR_INFO", "CONSENT"]
    )
    assert consent == ["SOCS", "CONSENT"]
    assert login == ["LOGIN_INFO"]
    assert other == 1  # VISITOR_INFO is neither


def test_classify_dedups_and_ignores_blanks():
    consent, login, other = classify_cookie_names("youtube", ["SOCS", "SOCS", ""])
    assert consent == ["SOCS"] and login == [] and other == 0


def test_classify_unknown_platform_is_all_other():
    consent, login, other = classify_cookie_names("nope", ["a", "b"])
    assert consent == [] and login == [] and other == 2


# --- changed_cookie_names ---

def test_changed_detects_appeared_and_value_change_only():
    baseline = [_c("SOCS", "default"), _c("guest_id", "g")]
    final = [_c("SOCS", "consented"), _c("guest_id", "g"), _c("auth_token", "t")]
    changed = changed_cookie_names(baseline, final)
    assert "SOCS" in changed          # value changed
    assert "auth_token" in changed    # appeared
    assert "guest_id" not in changed  # unchanged


# --- consent_login_events ---

def test_consent_event_on_value_change():
    # YouTube auto-sets SOCS on load; dismissing the banner rewrites it.
    baseline = [_c("SOCS", "default")]
    final = [_c("SOCS", "consented")]
    assert consent_login_events(baseline, final, "youtube") == (True, False)


def test_no_event_when_auto_set_tokens_unchanged():
    # The headline bug: X drops guest_id/gt on load; doing nothing must NOT
    # read as consent.
    jar = [_c("guest_id", "g"), _c("gt", "t"), _c("personalization_id", "p")]
    assert consent_login_events(jar, jar, "twitter") == (False, False)


def test_login_event_when_login_cookie_appears():
    baseline = [_c("datr", "d")]            # datr is an IG consent cookie (unchanged)
    final = [_c("datr", "d"), _c("sessionid", "s")]
    assert consent_login_events(baseline, final, "instagram") == (False, True)
