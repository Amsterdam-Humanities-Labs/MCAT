import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "mcat"))

import pytest
from cookies.cookie_store import CookieStore

FAKE_COOKIES = [
    {"name": "sessionid", "value": "abc123", "domain": ".instagram.com", "path": "/"},
    {"name": "csrftoken", "value": "xyz789", "domain": ".instagram.com", "path": "/"},
]


@pytest.fixture
def store(tmp_path):
    return CookieStore(tmp_path)


def test_save_and_load(store):
    store.save_cookies("instagram", FAKE_COOKIES)
    loaded = store.load_cookies("instagram")
    assert loaded == FAKE_COOKIES


def test_load_missing_returns_none(store):
    assert store.load_cookies("instagram") is None


def test_has_cookies(store):
    assert not store.has_cookies("instagram")
    store.save_cookies("instagram", FAKE_COOKIES)
    assert store.has_cookies("instagram")


def test_delete(store):
    store.save_cookies("instagram", FAKE_COOKIES)
    assert store.delete_cookies("instagram")
    assert not store.has_cookies("instagram")
    assert not store.delete_cookies("instagram")


def test_get_cookie_info(store):
    assert store.get_cookie_info("instagram") is None
    store.save_cookies("instagram", FAKE_COOKIES)
    info = store.get_cookie_info("instagram")
    assert info["platform"] == "instagram"
    assert info["cookie_count"] == 2
    assert "captured_at" in info


def test_consent_captured_round_trips(store):
    store.save_cookies("instagram", FAKE_COOKIES, consent_captured=True)
    assert store.get_cookie_info("instagram")["consent_captured"] is True
    store.save_cookies("instagram", FAKE_COOKIES)  # default
    assert store.get_cookie_info("instagram")["consent_captured"] is False


def test_jar_without_field_defaults_consent_false(store, tmp_path):
    # No recorded consent event -> treated as not captured (and the jar still
    # loads; only the consent flag is absent).
    path = tmp_path / "cookies" / "instagram.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "platform": "instagram", "username": "", "captured_at": "2025-01-01T00:00:00",
        "cookies": FAKE_COOKIES,
    }))
    assert store.get_cookie_info("instagram")["consent_captured"] is False


def test_get_auth_info_shape(store):
    empty = store.get_auth_info("instagram")
    assert empty == {"has_cookies": False, "username": "", "logged_in": False,
                     "captured_at": None, "consent_captured": False}
    store.save_cookies("instagram", FAKE_COOKIES, username="jane", consent_captured=True)
    info = store.get_auth_info("instagram")
    assert info["has_cookies"] is True
    assert info["username"] == "jane"
    assert info["consent_captured"] is True


def test_separate_platforms(store):
    store.save_cookies("instagram", FAKE_COOKIES)
    store.save_cookies("facebook", [{"name": "c_user", "value": "111", "domain": ".facebook.com", "path": "/"}])
    assert len(store.load_cookies("instagram")) == 2
    assert len(store.load_cookies("facebook")) == 1
    store.delete_cookies("instagram")
    assert store.load_cookies("instagram") is None
    assert store.load_cookies("facebook") is not None
