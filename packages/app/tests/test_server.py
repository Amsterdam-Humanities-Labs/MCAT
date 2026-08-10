"""Request-level guards on MCATHandler: Host, Origin, and the API token.

The handler is exercised without a socket — a subclass captures the response
instead of writing it — so these are pure request-shape assertions.
"""
import json
import pytest

import server
from server import MCATHandler


TOKEN = "test-token"
HOST = "127.0.0.1:9876"
ORIGIN = "http://127.0.0.1:9876"


class _Headers(dict):
    """Case-insensitive header lookup, like http.client's message object."""

    def get(self, key, default=""):
        for k, v in self.items():
            if k.lower() == key.lower():
                return v
        return default


class _Handler(MCATHandler):
    """MCATHandler with the socket plumbing replaced by capture."""

    def __init__(self, path, method="GET", headers=None, body=None):
        self.path = path
        self.command = method
        self.headers = _Headers(headers or {})
        self._body = (body or b"")
        self.status = None
        self.sent_headers = {}
        self.written = b""

    # --- captured plumbing ---
    def send_response(self, code, message=None):
        self.status = code

    def send_header(self, key, value):
        self.sent_headers[key] = value

    def end_headers(self):
        pass

    @property
    def wfile(self):
        handler = self

        class _W:
            def write(self, data):
                handler.written += data

            def flush(self):
                pass

        return _W()

    @property
    def rfile(self):
        handler = self

        class _R:
            def read(self, n):
                return handler._body[:n]

        return _R()

    def json_body(self):
        return json.loads(self.written.decode()) if self.written else None


@pytest.fixture(autouse=True)
def _configure():
    MCATHandler.allowed_hosts = {HOST, "localhost:9876"}
    MCATHandler.allowed_origins = {ORIGIN, "http://localhost:9876"}
    MCATHandler.auth_token = TOKEN
    MCATHandler.static_dir = None
    yield
    MCATHandler.allowed_hosts = set()
    MCATHandler.allowed_origins = set()
    MCATHandler.auth_token = ""
    MCATHandler.static_dir = None


def _post(path="/project/close", headers=None, body=b"{}"):
    base = {"Host": HOST, "Content-Type": "application/json",
            server.AUTH_HEADER: TOKEN, "Content-Length": str(len(body))}
    base.update(headers or {})
    h = _Handler(path, "POST", base, body)
    h.do_POST()
    return h


def _get(path="/health", headers=None):
    base = {"Host": HOST, server.AUTH_HEADER: TOKEN}
    base.update(headers or {})
    h = _Handler(path, "GET", base)
    h.do_GET()
    return h


# --- Host (DNS rebinding) ---

def test_foreign_host_is_rejected():
    """A rebound page is same-origin, so CORS never runs; Host is the guard."""
    assert _get(headers={"Host": "rebind.attacker.tld:9876"}).status == 421
    assert _post(headers={"Host": "rebind.attacker.tld:9876"}).status == 421


def test_allowed_host_passes():
    assert _get().status == 200


# --- Origin (CORS) ---

def test_substring_origin_gets_no_cors_header():
    """localhost.attacker.tld contains 'localhost' but is not an allowed origin."""
    h = _get(headers={"Origin": "http://localhost.attacker.tld"})
    assert "Access-Control-Allow-Origin" not in h.sent_headers


def test_allowed_origin_is_echoed():
    h = _get(headers={"Origin": ORIGIN})
    assert h.sent_headers["Access-Control-Allow-Origin"] == ORIGIN


# --- Token (CSRF) ---

def test_post_without_token_is_refused():
    h = _post(headers={server.AUTH_HEADER: ""})
    assert h.status == 403
    assert h.json_body()["error"] == "Forbidden"


def test_get_without_token_is_refused():
    assert _get(headers={server.AUTH_HEADER: ""}).status == 403


def test_sse_reads_the_token_from_the_query_string():
    """EventSource cannot set headers."""
    assert _get(path="/events?token=wrong", headers={server.AUTH_HEADER: ""}).status == 403


def test_preflight_is_not_token_gated():
    """A preflight carries no custom headers; gating it would break every POST."""
    h = _Handler("/project/close", "OPTIONS", {"Host": HOST, "Origin": ORIGIN})
    h.do_OPTIONS()
    assert h.status == 200
    assert server.AUTH_HEADER in h.sent_headers["Access-Control-Allow-Headers"]


# --- Static serving (production: the SPA is served from this same origin) ---

@pytest.fixture
def dist(tmp_path):
    """A stand-in built frontend, wired up the way app.py does in production."""
    (tmp_path / "index.html").write_text("<!doctype html><title>MCAT</title>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "index-abc123.js").write_text("export default 1;")
    MCATHandler.static_dir = tmp_path
    return tmp_path


def test_spa_page_is_served_without_a_token(dist):
    """The initial page load cannot carry a token; gating it ships a blank window."""
    h = _get(path="/", headers={server.AUTH_HEADER: ""})
    assert h.status == 200
    assert b"MCAT" in h.written


def test_spa_assets_are_served_without_a_token(dist):
    h = _get(path="/assets/index-abc123.js", headers={server.AUTH_HEADER: ""})
    assert h.status == 200
    assert b"export default" in h.written


def test_unknown_path_falls_back_to_index_without_a_token(dist):
    """SPA routing: unknown GETs return index.html rather than 404."""
    h = _get(path="/nope", headers={server.AUTH_HEADER: ""})
    assert h.status == 200
    assert b"MCAT" in h.written


def test_api_routes_stay_gated_when_static_is_served(dist):
    """The static branch must not become an escape hatch around the token."""
    assert _get(path="/health", headers={server.AUTH_HEADER: ""}).status == 403


def test_static_serving_still_honours_the_host_check(dist):
    h = _get(path="/", headers={server.AUTH_HEADER: "", "Host": "rebind.attacker.tld:9876"})
    assert h.status == 421


# --- Content-Type ---

def test_non_json_content_type_is_refused():
    """text/plain is what lets a page POST here without a preflight."""
    assert _post(headers={"Content-Type": "text/plain"}).status == 415


def test_json_content_type_with_charset_is_accepted():
    h = _post(headers={"Content-Type": "application/json; charset=utf-8"})
    assert h.status != 415
