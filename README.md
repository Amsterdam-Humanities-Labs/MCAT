# MCAT

Moderation Content Analysis Tool — a desktop app for monitoring content moderation status across social platforms (YouTube, Instagram, Facebook).

Built with pywebview: a Python backend, a Svelte 5 frontend, and a zendriver-driven Chrome for scraping.

## Prerequisites

- Node.js 20.19+ or 22.12+
- pnpm
- Python 3.10+
- Google Chrome or Chromium (driven by zendriver over the Chrome DevTools Protocol)
- Linux only: system WebKitGTK + PyGObject for pywebview's GTK backend (Fedora: `webkit2gtk4.1`, `gtk3`, `python3-gobject`)

## Setup

```bash
pnpm install
cd backend && python3 -m venv --system-site-packages venv
venv/bin/pip install ".[dev]"
```

Dependencies are declared in `backend/pyproject.toml` (`zendriver`, `pywebview`; `pyinstaller` + `pyright` under the `dev` extra) — that's the single source of truth, so there's no separate list to install by hand. On macOS, pywebview pulls its native WebKit backend (`pyobjc-*`) automatically. On Linux it uses the **system** WebKitGTK/PyGObject, which is why the venv is created with `--system-site-packages`.

## Development

```bash
pnpm dev              # Start backend + Vite + pywebview window
pnpm dev:mock         # Same, with mock scraper (no real browser)
```

The backend starts on `127.0.0.1:9876` (fallback to next free port). Vite on `127.0.0.1:5180`. Open `http://127.0.0.1:5180?port=<backend_port>` in a browser for development. (`pnpm dev` runs `app.py`, which spawns Vite itself in dev mode.)

## Project Structure

```
MCAT/
├── frontend/          # Svelte 5 UI (Vite)
│   ├── src/
│   │   ├── lib/       # Components, stores, api
│   │   ├── types/     # Shared TypeScript types
│   │   └── themes/    # Color themes
│   └── public/fonts/  # Custom fonts
├── backend/           # Python backend
│   ├── mcat/
│   │   ├── api/       # HTTP handlers, router (also serves the built SPA)
│   │   ├── scrapers/  # Platform scrapers (detection only)
│   │   ├── services/  # Project/run/processing/tracking/login services
│   │   ├── core/      # Batch processor, zendriver browser session
│   │   ├── models/    # Data models
│   │   └── app.py     # Entry point
│   ├── pyproject.toml # Dependencies (single source of truth)
│   └── venv/          # Python virtual environment
└── tests/
    ├── mock_scraper.py          # Mock scraper for dev
    ├── mock_scraper_factory.py  # Wires the mock into the batch pipeline
    ├── fixtures/                # Test URLs and scenarios
    └── test_cookie_store.py     # Cookie store round-trip test
```

## Scraping Approach

Each scraper drives a Chrome tab via **zendriver** (Chrome DevTools Protocol — no chromedriver) to load the URL and inspect the rendered page for status signals. A single Chrome process hosts a pool of tabs (default 3, configurable via `max_zendriver_tabs`); URLs are processed concurrently across the pool with async I/O, and the whole session is torn down with one `browser.stop()` per run.

`tab.get()` awaits page load (30s timeout). On timeout, the scraper inspects whatever partial content rendered. After loading, detection signals are polled every 0.5s (up to 15s) instead of using a fixed delay. Every tab/CDP call is wrapped in a per-operation timeout so a single wedged page can't stall the batch.

Detection uses `body.innerText` (visible text only, not raw HTML) to avoid false positives from JS template strings. Triage order:

1. **Negative signals**: removal/restriction evidence (text patterns, DOM elements)
2. **Positive signals**: evidence content is live (title element, meta tags)
3. **Login Required**: platform demands authentication, content status indeterminate
4. **Unknown**: no signal found, reported as-is rather than guessing

A page is never classified as "Live" until all negative checks pass. Both "Live" and "Removed" require affirmative evidence.

When screenshots are enabled, a Live post additionally waits for its main image to paint before capture, so the screenshot shows the post rather than a loading skeleton.

Cookie consent modals are never dismissed in-scraper. Running **Set up browser** once captures the platform's consent cookie into the per-project jar; it is injected into every tab when the browser session starts, so the modal simply never renders during scraping.

### Authentication

The **Set up browser** action opens a visible Chrome window on the platform so the user can dismiss the cookie consent modal and, where needed, log in. Whatever cookies result (consent cookies, plus session cookies if the user logged in) are captured and stored per-project in `<project>/cookies/<platform>.json`, then injected into the tab pool when a run's browser session starts. No passwords are stored. Cookies are captured live during the session (so login cookies are available immediately) and when the window is closed.

Instagram and Facebook may need login to view content; if their session cookies expire the scraper reports "Login Required" (Instagram) or an undecided "Unknown" (Facebook) and the user re-runs Set up browser. YouTube needs no login but shows a consent modal: running Set up browser once captures its `SOCS` consent cookie (~13-month lifetime) so the modal never renders during scraping. This is recommended in the EU, where an un-set-up YouTube project gets redirected to the consent page and detection degrades.

### YouTube

The page title is captured immediately after `tab.get()` returns, before YouTube redirects incognito browsers to its consent page. This initial title serves as a fallback Live signal when the SPA doesn't fully render. Running Set up browser injects the consent cookie and prevents the redirect entirely.

| Status | Signal |
|--------|--------|
| Removed | Text: "video unavailable", "this video isn't available", "removed by the user", "account has been terminated" |
| Age-restricted | Text: "age-restricted", "sign in to confirm your age" |
| Geo-blocked | Text: "not available in your country" |
| Private | Text: "private video" |
| Restricted | DOM: elements with `warning` or `restricted` in class name |
| Live | DOM: `h1.ytd-watch-metadata` via `innerText` (handles hashtag-only titles); fallback: page title matches `"<Title> - YouTube"` |
| Unknown | No signal found after timeout |

### Instagram

Works without login (Instagram shows post previews to anonymous visitors). With authentication, the scraper gets a full view of the content.

| Status | Signal |
|--------|--------|
| Removed | Page title contains "isn't available"; error SVG `svg[aria-label="error"]`; text: "post isn't available", "sorry, this page isn't available", "page not found" |
| Live | Meta tag `og:title` contains `" on Instagram:"`; fallback: `article[role="presentation"]` (logged-in view) |
| Login Required | Login wall detected ("log in" + "sign up" in body text) with no other signal |
| Unknown | No signal found after timeout |

### Facebook

Posts are partially visible without login. Removed posts load fast (~0.7s) with a clear error message; live posts take longer (~4-9s) as the SPA renders.

There is deliberately no login-wall branch: every anonymous page embeds a login form, so there is no reliable per-post login signal. An undecided page returns Unknown for a human to judge from the screenshot.

| Status | Signal |
|--------|--------|
| Removed | Text: "this content isn't available", "this page isn't available", "this content has been removed", "the link you followed may be broken", "page not found" |
| Live | DOM: `div[role="article"]`; fallback: `og:title` meta or page title `"... \| Facebook"`, but only when they carry real content (generic "Facebook" / "Log in to Facebook" titles are ignored) |
| Unknown | No signal found after timeout |

## Building

**Linux** (AppImage):

```bash
pnpm build:linux      # → build/MCAT-x86_64.AppImage
```

See [`build/README.md`](build/README.md) for details.

**macOS** (`.app`):

```bash
pnpm build            # build the frontend first
cd backend && venv/bin/python -m PyInstaller --clean mcat.spec   # → backend/dist/MCAT.app
```

The GitHub Actions workflow (`.github/workflows/build-macos.yml`) builds both arm64 (Apple Silicon, on `macos-26`) and x86_64 (Intel, on `macos-15-intel`) bundles on pushes to `build`. The bundles are unsigned, so first launch needs a Gatekeeper override: `xattr -dr com.apple.quarantine MCAT.app`.

At runtime the app serves the built SPA from its own backend so the UI and API share one origin — required on macOS, where a `file://` page is blocked from reaching the `http://` backend.

## License

MCAT is licensed under the [European Union Public Licence v. 1.2](LICENSE) (EUPL-1.2).

Third-party bundled assets (fonts) carry their own licenses in [`LICENSES/`](LICENSES/).
