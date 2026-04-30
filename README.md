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

Each scraper uses a headless Chrome browser (via Selenium) to load the URL and inspect the rendered page for status signals. No platform APIs or authentication required. A pool of 3 browser instances processes URLs in parallel.

`driver.get()` blocks until page load completes (30s timeout). On timeout, the scraper checks whatever partial content rendered. After loading, detection signals are polled every 0.5s (up to 15s) instead of a fixed delay.

Detection uses `body.text` (visible text only, not `page_source`) to avoid false positives from JS template strings. Triage order:

1. **Negative signals**: removal/restriction evidence (text patterns, DOM elements)
2. **Positive signals**: evidence content is live (title element, article container)
3. **Unknown**: no signal found, reported as-is rather than guessing

A page is never classified as "Live" until all negative checks pass. Both "Live" and "Removed" require affirmative evidence.

### YouTube

Detected statuses:

| Status | Signal |
|--------|--------|
| Removed | Text: "video unavailable", "this video isn't available", "removed by the user", "account has been terminated" |
| Age-restricted | Text: "age-restricted", "sign in to confirm your age" |
| Geo-blocked | Text: "not available in your country" |
| Private | Text: "private video" |
| Restricted | DOM: elements with `warning` or `restricted` in class name |
| Live | DOM: `h1.ytd-watch-metadata` with text; fallback: page title matches `"<Title> - YouTube"` |
| Unknown | No signal found after timeout |

## Architecture

See `architecture.md` for diagrams covering the full data flow, API endpoints, SSE events, scraper detection strategies, and component tree.

## License

MCAT is licensed under the [European Union Public Licence v. 1.2](LICENSE) (EUPL-1.2).

Third-party bundled assets (fonts) carry their own licenses in [`LICENSES/`](LICENSES/).
