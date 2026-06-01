# MCAT

Moderation Content Analysis Tool — a desktop app for monitoring content moderation status across social platforms (YouTube, Instagram, Facebook, Twitter/X).

Built with pywebview (Python backend + Svelte 5 frontend).

## Prerequisites

- Node.js 20.19+ or 22.12+
- pnpm
- Python 3.10+
- Chrome/Chromium (for Selenium scrapers)

## Setup

```bash
pnpm install
cd backend && python3 -m venv --system-site-packages venv
venv/bin/pip install pywebview polars bottle
```

System packages needed: `selenium`, `pydispatch`, `chromedriver-autoinstaller`, `requests`, `pandas`, `beautifulsoup4`.

## Development

```bash
pnpm dev              # Start backend + Vite + pywebview window
pnpm dev:mock         # Same, with mock scraper (no real browser)
```

The backend starts on `127.0.0.1:9876` (fallback to next free port). Vite on `127.0.0.1:5180`. Open the URL `http://127.0.0.1:5180?port=<backend_port>` in a browser for development.

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
│   │   ├── api/       # HTTP handlers, router
│   │   ├── scrapers/  # Platform scrapers
│   │   ├── services/  # Project/run/processing/tracking services
│   │   ├── core/      # Batch processor, driver pool
│   │   ├── models/    # Data models
│   │   └── app.py     # Entry point
│   └── venv/          # Python virtual environment
└── tests/
    ├── mock_scraper.py        # Mock scraper for dev
    ├── fixtures/              # Test URLs and scenarios
    └── test_scrapers_live.py  # Live integration tests
```

## Scraping Approach

Each scraper uses a headless Chrome browser (via Selenium) to load the URL and inspect the rendered page for status signals. A pool of 3 browser instances processes URLs in parallel.

`driver.get()` blocks until page load completes (30s timeout). On timeout, the scraper checks whatever partial content rendered. After loading, detection signals are polled every 0.5s (up to 15s) instead of a fixed delay.

Detection uses `body.text` (visible text only, not `page_source`) to avoid false positives from JS template strings. Triage order:

1. **Negative signals**: removal/restriction evidence (text patterns, DOM elements)
2. **Positive signals**: evidence content is live (title element, meta tags)
3. **Login Required**: platform demands authentication, content status indeterminate
4. **Unknown**: no signal found, reported as-is rather than guessing

A page is never classified as "Live" until all negative checks pass. Both "Live" and "Removed" require affirmative evidence.

Cookie consent modals are dismissed automatically before detection. Each handler finds the consent dialog by its text content, then clicks the decline/reject button scoped within that dialog.

### Authentication

Some platforms (Instagram, Facebook, TikTok) may require login to view content. The app supports optional cookie-based authentication: the user logs in through a visible Chrome window, session cookies are captured and stored per-project in `<project>/cookies/<platform>.json`. No passwords are stored. Cookies are injected into the headless browser pool at scrape time. If cookies expire, the scraper reports "Login Required" and the user can re-authenticate. YouTube and Twitter work without login.

### YouTube

The page title is captured immediately after `driver.get()` returns, before YouTube redirects incognito browsers to its consent page. This initial title serves as a fallback Live signal when the SPA doesn't fully render.

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

| Status | Signal |
|--------|--------|
| Removed | Text: "this content isn't available", "this page isn't available", "this content has been removed", "the link you followed may be broken", "page not found" |
| Live | DOM: `div[role="article"]`; fallback: `og:title` meta tag present; fallback: page title matches `"... \| Facebook"` |
| Login Required | Login wall detected ("log in" + "create new account" in body text) with no other signal |
| Unknown | No signal found after timeout |

## Architecture

See `architecture.md` for diagrams covering the full data flow, API endpoints, SSE events, scraper detection strategies, and component tree.

## License

MCAT is licensed under the [European Union Public Licence v. 1.2](LICENSE) (EUPL-1.2).

Third-party bundled assets (fonts) carry their own licenses in [`LICENSES/`](LICENSES/).
