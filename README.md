# MCAT

![MCAT — tracking content-moderation status across platforms](static/mcat_preview.jpg)

**MCAT (Moderation Content Analysis Tool)** is a desktop app for researchers studying platform content moderation. Given a list of post/video URLs, it checks whether each is still **live**, **restricted**, **moderated**, or **unavailable** by loading it in a real browser and inspecting the rendered page — and it can **re-check on a schedule** to capture *when* a piece of content's status changes over time.

It targets **YouTube, Instagram, Facebook, and X (Twitter)**, runs locally as a native window, and writes results to a plain CSV alongside per-URL screenshots, so findings stay auditable and easy to analyze. Nothing leaves your machine except the page loads themselves.

Built with pywebview — a Python backend, a Svelte 5 frontend, and a zendriver-driven Chrome for scraping.

## Contents

- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Development](#development)
- [Testing](#testing)
- [Building & installing](#building--installing)
  - [Linux (AppImage)](#linux-appimage)
  - [macOS (.app)](#macos-app)
- [Usage](#usage)
  - [Input & output](#input--output)
  - [Content states](#content-states)
  - [Set up browser (authentication)](#set-up-browser-authentication)
  - [Monitoring over time (tracking)](#monitoring-over-time-tracking)
- [Scraping strategies](#scraping-strategies)
  - [General approach](#general-approach)
  - [YouTube](#youtube)
  - [Instagram](#instagram)
  - [Facebook](#facebook)
  - [X (Twitter)](#x-twitter)
- [License](#license)

## Project structure

```
MCAT/                              # pnpm workspace monorepo
└── packages/
    ├── app/                       # the desktop app (Svelte + Python)
    │   ├── frontend/          # Svelte 5 UI (Vite)
    │   │   └── src/           # lib (components, stores, api), types
    │   ├── backend/           # Python backend
    │   │   ├── mcat/          # api, scrapers, services, core, models, app.py
    │   │   └── pyproject.toml # Dependencies (single source of truth)
    │   ├── tests/             # pytest suite, mock scraper, fixtures
    │   └── build/             # Linux AppImage / macOS packaging config
    ├── website/                   # SvelteKit site — docs, policy diffing, downloads
    │   └── src/               # routes, lib (components, data, types), content
    └── shared-ui/                 # @mcat/shared-ui — Svelte primitives + theme
```

## Prerequisites

- Node.js 20.19+ or 22.12+
- pnpm
- Python 3.10+
- Google Chrome or Chromium (driven by zendriver over the Chrome DevTools Protocol)
- Linux only: system WebKitGTK + PyGObject for pywebview's GTK backend (Fedora: `webkit2gtk4.1`, `gtk3`, `python3-gobject`)

## Setup

```bash
pnpm install
cd packages/app/backend && python3 -m venv --system-site-packages venv
venv/bin/pip install ".[dev]"
```

Dependencies are declared in `packages/app/backend/pyproject.toml` (`zendriver`, `pywebview`; `pyinstaller` + `pyright` under the `dev` extra) — that's the single source of truth, so there's no separate list to install by hand. On macOS, pywebview pulls its native WebKit backend (`pyobjc-*`) automatically. On Linux it uses the **system** WebKitGTK/PyGObject, which is why the venv is created with `--system-site-packages`.

## Development

```bash
pnpm dev:app          # Start backend + Vite + pywebview window
pnpm dev:app:mock     # Same, with a mock scraper (no real browser)
```

The backend starts on `127.0.0.1:9876` (fallback to next free port); Vite on `127.0.0.1:5180`. `pnpm dev` runs `app.py`, which spawns Vite itself in dev mode and hot-reloads the frontend. To inspect the UI in a normal browser, open `http://127.0.0.1:5180?port=<backend_port>`.

## Testing

```bash
pnpm test          # Python suite via pytest (needs packages/app/backend/venv set up)
```

Covers `csv_handler` (I/O + delimiter handling), each platform's `_detect_status` detection branches (offline, via fake tabs), the scraping harness — batch orchestration and the per-URL flow: cancel / pause / retry / timeout, no browser — and the cookie store. CI runs it on every push and PR (`.github/workflows/test.yml`). The verified-URL fixtures under `packages/app/tests/fixtures/live/verified/` are ground truth for an optional live (networked) detection check.

## Building & installing

### Linux (AppImage)

```bash
pnpm build:linux          # → packages/app/build/MCAT-x86_64.AppImage
```

### macOS (`.app`)

```bash
pnpm build                                                                    # frontend
cd packages/app/backend && venv/bin/python -m PyInstaller --clean mcat.spec   # → dist/MCAT.app
xattr -dr com.apple.quarantine dist/MCAT.app                                  # unsigned; clear Gatekeeper
mv dist/MCAT.app /Applications
```

Store projects outside the app (e.g. `~/Documents`) — updating the app deletes anything beside it.

## Usage

### Input & output

**Input** is a CSV with at least one column of URLs. A header row is required, but the URL column can be named anything — it's auto-detected and confirmed in the project wizard. Any other columns (titles, IDs, dates) are optional and passed through to the output untouched. The smallest valid file is:

```
url
https://youtube.com/watch?v=...
https://instagram.com/p/...
https://x.com/user/status/...
```

**Output** is written incrementally to `results.csv` in the run folder: the original columns plus `mcat_status`, `mcat_detail`, `mcat_screenshot`, `mcat_timestamp`, `mcat_error`, and `mcat_user`. When screenshots are enabled, they're saved under `screenshots/<status>/`.

### Content states

Every checked URL gets one `mcat_status`; the specific reason (age-restricted, geo-blocked, removed by uploader, suspended account, …) is recorded separately in `mcat_detail` rather than spawning its own state.

| State | Meaning | Platforms |
|---|---|---|
| **Live** | Loads and is publicly viewable | all |
| **Restricted** | Present but access-gated — age-restricted, geo-blocked, or private | YouTube, X |
| **Moderated** | Taken down by platform enforcement — suspended account or terminated channel | YouTube, X |
| **Unavailable** | Gone — deleted by the uploader, 404, or expired | all |
| **Login Required** | An auth wall blocked the check; the content itself may still be live | Instagram |
| **Unknown** | Loaded but nothing matched — left for a human to judge from the screenshot | all |
| **Error** | The check itself failed — no load, timeout, or crash | all |

### Set up browser (authentication)

**Set up browser** opens a visible Chrome window so you can dismiss the cookie-consent modal and, where needed, log in; the resulting cookies are stored per-project in `<project>/cookies/<platform>.json` and injected into the tab pool at run start. No passwords are stored — only cookies, and the activity log prints cookie *names*, never values — so use a dedicated / throwaway account, never your real one. Instagram and Facebook may need a login (when their session cookies expire the scraper reports `Login Required` or an undecided `Unknown`, so re-run it); YouTube needs no login but should be run once to capture its `SOCS` consent cookie (~13-month life), especially in the EU where an un-set-up project is redirected to the consent page; and X should be run **logged in**, since logged out it throttles even live tweets to a generic page that misreads as `Unavailable`.

### Monitoring over time (tracking)

Enable **tracking** to re-run the checks automatically on an interval (minutes / hours / days). Each scheduled run re-checks the project's URLs, so you can capture when content gets taken down or restricted *after* the initial check — the core "moderation over time" use case. The next-check time is shown in the UI; tracking stops when you disable it or close the project.

## Scraping strategies

### General approach

Each scraper drives a Chrome tab via **zendriver** (Chrome DevTools Protocol — no chromedriver) to load the URL and inspect the rendered page. A single Chrome process hosts a pool of tabs (default 3, via `max_zendriver_tabs`); URLs run concurrently with async I/O, `tab.get()` awaits load (30s timeout), and every tab/CDP call is wrapped in a per-operation timeout so one wedged page can't stall the batch. Signals are polled every 0.5s (up to 15s) rather than on a fixed delay.

Detection reads `body.innerText` (visible text, not raw HTML — avoids false positives from JS template strings) in a fixed order: **negative signals first** (evidence the content is gone, moderated, or restricted — a takedown notice must never be overridden by a "looks-live" signal), then **positive signals** (the rendered post, `og:title`, the SPA title), then a **login wall**, then **Unknown**.

**Which signal is trusted first flips by platform — always the one that can't be faked:**

- **YouTube / Instagram / Facebook — negatives first.** A taken-down page *replaces* the post with a removal notice (platform chrome a live post never contains), while their positives leak onto dead pages — so the negative is the trustworthy signal.
- **X (Twitter) — positives first.** Its gone-phrases (`suspended account`, `nothing to see here`) are ordinary tweet text users post, but X renders a tweet card *only* when the post is genuinely live — so the card is the one signal user text can't fake.

The principle: **`Live` and every negative state require their own affirmative evidence — never a guess.** A page is called `Live` only when all negative checks fail *and* a positive is found; otherwise the result is `Unknown`, left for a human to judge from the screenshot. Consent modals are never dismissed in-scraper — the cookie captured during **Set up browser** is injected into every tab so the modal never renders.

### YouTube

Captures the page title immediately after load — before YouTube redirects an un-set-up (incognito) browser to its consent page — as a fallback `Live` signal. Negatives first: visible text is matched for removal, age/geo/private, and channel-termination markers; `Live` needs the rendered video-title element (or a `"<Title> - YouTube"` page title).

### Instagram

Works without login — Instagram shows post previews to anonymous visitors (auth gives a fuller view). Negatives first via the page title and an error SVG; `Live` is confirmed by the `og:title` post caption (or the logged-in article DOM). A bare login wall with no other signal is the one case that returns `Login Required`.

### Facebook

The coarsest of the four — in practice it only distinguishes `Live` from `Unavailable`. Posts are partially visible logged-out: unavailable pages load fast (~0.7s) with a clear error, live pages render slowly (~4–9s). There's deliberately no login-wall branch (every anonymous page embeds a login form, so there's no reliable per-post signal), so an undecided page returns `Unknown`.

### X (Twitter)

Positive-first: X renders a tweet card only when the post is genuinely live, so a rendered card is conclusive `Live`, checked before any negative phrase. Run logged in — logged out, X throttles even live tweets to a generic "nothing to see here" page indistinguishable from a real takedown.

## License

MCAT is licensed under the [European Union Public Licence v. 1.2](LICENSE) (EUPL-1.2).

Third-party bundled assets (fonts) carry their own licenses in [`LICENSES/`](LICENSES/).
