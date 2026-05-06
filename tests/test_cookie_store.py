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


def test_separate_platforms(store):
    store.save_cookies("instagram", FAKE_COOKIES)
    store.save_cookies("facebook", [{"name": "c_user", "value": "111", "domain": ".facebook.com", "path": "/"}])
    assert len(store.load_cookies("instagram")) == 2
    assert len(store.load_cookies("facebook")) == 1
    store.delete_cookies("instagram")
    assert store.load_cookies("instagram") is None
    assert store.load_cookies("facebook") is not None
