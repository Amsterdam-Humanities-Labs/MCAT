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

## Architecture

See `architecture.md` for diagrams covering the full data flow, API endpoints, SSE events, scraper detection strategies, and component tree.
