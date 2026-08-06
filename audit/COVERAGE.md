# MCAT Backend Audit — Coverage

Round 1 complete. Every backend module under `packages/app/backend/` has been
reviewed by each applicable lens, and every finding it produced has been ruled
on by a verifier. See [FINDINGS.md](FINDINGS.md).

`Sec` = security-auditor · `Leak` = leak-auditor · `Str` = structure-auditor.
`n/a` = the lens has no purchase on that module (no I/O, no state, no lifecycle).

Status: **done** everywhere. Findings column lists the ids raised from that
module (surviving ids only; rejected ones are in the FINDINGS.md audit trail).

---

## Threat-category verdicts

Each in-scope category from the audit brief, marked explicitly.

| Category | Verdict | Evidence |
| --- | --- | --- |
| **localhost-exposure** (DNS rebinding / CORS / CSRF) | **PRESENT** | MCAT-001 (substring `Origin` match, reflected), MCAT-002 (no CSRF token, no `Content-Type` check → simple-request POST executes), MCAT-008 (no `Host` validation) |
| **cookie-confidentiality** | **PRESENT** | MCAT-003 (plaintext jar in a user-chosen, syncable, git-trackable dir; 0644 write window; swallowed `chmod` `OSError`; no `cookies/` ignore rule). Verified negative: no session-secret cookie **value** reaches any log, SSE event, API response, or CSV — `cookie_diff` and `_log_capture_summary` handle names only, `browser_manager` logs a count only (MCAT-013 rejected on this basis) |
| **ssrf** | **PRESENT** | MCAT-010 (`normalize_url` passes any explicit scheme to `tab.get` → `file://`, other loopback ports, `169.254.169.254`). Verified negative: `/process/start`'s `urls` field is **not** an injection vector — it only filters rows already in `urls.csv` |
| **browser-hardening** | **ABSENT as a finding** | `sandbox=False` → `--no-sandbox` is real and unconditional, but exploitation needs a separate unpatched renderer CVE, so it fails the threat-model gate (MCAT-005 rejected). Tracked as non-security hardening: nothing here requires `--no-sandbox`; zendriver only needs it under root. Incidental: `--disable-features=MediaRouter` is appended *after* zendriver's site-isolation disable, and last-switch-wins means site isolation stays **enabled** — a fragile accident (see FINDINGS round-2 notes) |
| **cdp-exposure** | **ABSENT** | Mechanism verified (unauthenticated loopback CDP, `--remote-allow-origins=*`) but no privilege boundary is crossed: the port is randomized, `/json/*` sends no ACAO so a web page cannot learn the target GUID, and any local process that could attach can read the jar file directly (MCAT-012 rejected) |
| **js-bridge** | **ABSENT** | `webview.create_window` (`app.py:112-119`) passes **no `js_api`**, and `expose()` is never called anywhere, so `window._js_api is None` and `window._functions` is empty. The only dispatchable names in pywebview 6.2.1's `js_bridge_call` (`pywebviewMoveWindow`, `pywebviewEventHandler`, `pywebviewAsyncCallback`, `pywebviewState*`) reach no filesystem or process surface. No page but the app's own SPA loads in the WKWebView, and `DataTable.svelte:83` gates rendered links behind an `http(s)`-only `isUrl()`, so a `javascript:` CSV cell renders as inert text |
| **path-traversal** | **PRESENT** | MCAT-004 (YouTube/Facebook `_extract_id` → screenshot write to an arbitrary absolute path), MCAT-006 (unvalidated `run_id` in `/run/results`), MCAT-007 (unvalidated `name`/`location` in `create_project`), MCAT-011 (prefix-not-containment in `open_external`). Verified clean: `_serve_static` correctly uses `resolve()` + `is_relative_to`, and `urlparse` does not percent-decode so `%2e%2e` stays literal |
| **csv-injection** | **PRESENT** | MCAT-009 (no neutralization of leading `=+-@`/tab/CR in `append_row`, `save_csv`, `_write_changes_csv`), via both passthrough source cells and page-derived `mcat_detail` |

Leak and structure areas from the brief, same convention:

| Area | Verdict | Evidence |
| --- | --- | --- |
| Tab/CDP close vs detach on the 50-nav recycle | **PRESENT (low)** | MCAT-017. The target itself *does* go away (`Target.closeTarget` is sent and `_handle_target_update` removes it). `_nav_counts` id-reuse: **absent** — `_recycle` opens the replacement before popping `id(old)`, so a fresh object can never alias a live key |
| asyncio loop teardown per batch | **PARTLY PRESENT** | MCAT-014 (library-global `Browser` retention + never-popped event `mapper`), MCAT-016. The `call_soon_threadsafe` race is defended (RuntimeError caught, `_stopped` short-circuits `release_tab`). Cross-loop primitives: **absent** — `_tabs`/`_rate_lock` are per-run and bind lazily inside the run's own loop |
| SSE subscriber / event fan-out accumulation | **ABSENT** | `unsubscribe` is in a `finally` so it runs for *any* exception; SSE threads are daemons; the frontend closes the old `EventSource` before reconnecting, so a reload is reaped within one or two 15s heartbeats. The unbounded-`Queue` observation is technically right (`put_nowait` never raises, so `publish`'s `dead_queues` branch is dead code) but no path here produces a stalled reader |
| Chrome process growth | **PRESENT** | MCAT-015 (backend + Chrome survive window close), MCAT-019 (Set-up-browser hang latch), MCAT-016 (orphan on the abnormal teardown path). The normal per-run path is clean |
| `threading.Timer` accumulation | **ABSENT for doubling; PRESENT as the inverse** | `_schedule_next_check` cancels before re-arming and the two chains mutually collapse. The real defect is MCAT-020: the 5s busy-retry is cancelled microseconds after it is armed, so a skipped tick waits a full interval |
| Progress queue growth | **ABSENT** | `ProgressQueue` is bounded at 20 with drop-oldest; `BatchProcessor.progress_queue` is only written when `progress_callback` is `None`, which `start_processing` always sets — dead in production, and the processor is rebuilt per run |
| Threading ↔ asyncio seam | **PRESENT** | MCAT-027 (check-then-act), MCAT-029 (split critical section), MCAT-021 (unbounded await). Cross-loop calls are largely sound — `cancel_processing` correctly snapshots `_loop`/`_session` into locals first |
| Pause / cancel correctness | **PRESENT** | MCAT-028 (`cancel_flag.clear()` erases an in-flight cancel), MCAT-031. **Absent as defects:** pause holding a tab is correct by design (the pool *is* the concurrency gate), and a paused run cancels promptly because `cancel_processing` sets `resume_event` before `cancel_flag` is polled. Note `ProcessingService._pause_event` is write-only dead state |
| Error handling / partial failure | **PRESENT** | MCAT-023 (row misalignment), MCAT-026 (swallowed writes → COMPLETED with zero results), MCAT-030 (both callbacks fire), MCAT-024, MCAT-033 |
| The two-dict router | **PRESENT (low)** | MCAT-033. Missing-key handling is actually *good* in most handlers (`.get` + `raise ValueError` → clean 400). Lambda-wrapping is **not** a defect — a signature adapter for the one no-arg handler, consistent with `GET_ROUTES` |
| Blast radius of a wedged tab | **PRESENT** | MCAT-021. `release_tab`'s "always re-pools exactly one tab" invariant was **verified to hold on every exception path**; the only loss vector is a hang inside `_recycle → _open_tab → _inject_cookies`. Everything in the scraper hot path is individually bounded; worst case per URL is ~260s, so a wedged page costs one pool slot for a bounded time and the batch still finishes |

---

## Entry point & HTTP server

| Module | LOC | Sec | Leak | Str | Findings |
| --- | --- | --- | --- | --- | --- |
| `mcat/app.py` | 136 | done | done | done | MCAT-015 |
| `mcat/server.py` | 204 | done | done | done | MCAT-001, MCAT-002, MCAT-008, MCAT-033 |

## API layer

| Module | LOC | Sec | Leak | Str | Findings |
| --- | --- | --- | --- | --- | --- |
| `mcat/api/router.py` | 35 | done | n/a | done | MCAT-002 (route surface) |
| `mcat/api/context.py` | 134 | done | done | done | MCAT-031 (via `set_project`) |
| `mcat/api/serializers.py` | 39 | done | done | done | MCAT-018 |
| `mcat/api/handlers/auth.py` | 57 | done | done | done | MCAT-002 (logout), MCAT-019 (gate) |
| `mcat/api/handlers/csv.py` | 42 | done | n/a | done | MCAT-001 (arbitrary-path read) |
| `mcat/api/handlers/dialog.py` | 126 | done | n/a | done | MCAT-011 |
| `mcat/api/handlers/health.py` | 13 | done | n/a | n/a | — |
| `mcat/api/handlers/processing.py` | 110 | done | done | done | MCAT-022 |
| `mcat/api/handlers/project.py` | 142 | done | done | done | MCAT-007 |
| `mcat/api/handlers/run.py` | 78 | done | done | done | MCAT-006 |
| `mcat/api/handlers/tracking.py` | 51 | done | done | done | MCAT-002 (0-interval) |

## Services

| Module | LOC | Sec | Leak | Str | Findings |
| --- | --- | --- | --- | --- | --- |
| `mcat/services/processing_service.py` | 325 | done | done | done | MCAT-015, MCAT-027, MCAT-029, MCAT-030, MCAT-031, MCAT-035 |
| `mcat/services/tracking_service.py` | 215 | done | done | done | MCAT-020, MCAT-024 |
| `mcat/services/login_service.py` | 171 | done | done | done | MCAT-019 |
| `mcat/services/run_service.py` | 193 | done | done | done | MCAT-030, MCAT-032 |
| `mcat/services/project_service.py` | 166 | done | done | done | MCAT-007 |
| `mcat/services/progress_queue.py` | 84 | done | done | done | — (bounded at 20, drop-oldest) |
| `mcat/services/job_builder.py` | 51 | done | n/a | done | — |
| `mcat/services/processing_validator.py` | 46 | done | n/a | done | MCAT-023 (blank-column guard too weak) |

## Core

| Module | LOC | Sec | Leak | Str | Findings |
| --- | --- | --- | --- | --- | --- |
| `mcat/core/browser_manager.py` | 264 | done | done | done | MCAT-010, MCAT-014, MCAT-016, MCAT-017, MCAT-021 |
| `mcat/core/batch_processor.py` | 262 | done | done | done | MCAT-009, MCAT-023, MCAT-028 |

## Scrapers

| Module | LOC | Sec | Leak | Str | Findings |
| --- | --- | --- | --- | --- | --- |
| `mcat/scrapers/base_scraper.py` | 313 | done | done | done | MCAT-004 (sink), MCAT-010 (sink) |
| `mcat/scrapers/youtube_scraper.py` | 99 | done | done | done | MCAT-004, MCAT-009 (`Restricted` innerText) |
| `mcat/scrapers/facebook_scraper.py` | 90 | done | done | done | MCAT-004 |
| `mcat/scrapers/instagram_scraper.py` | 94 | done | done | done | — (`_extract_id` splits on `/`; title sink gated) |
| `mcat/scrapers/twitter_scraper.py` | 54 | done | done | done | — (`_extract_id` splits on `/`; returns fixed strings) |

## Cookies

| Module | LOC | Sec | Leak | Str | Findings |
| --- | --- | --- | --- | --- | --- |
| `mcat/cookies/cookie_store.py` | 128 | done | n/a | done | MCAT-003 |
| `mcat/cookies/cookie_diff.py` | 45 | done | n/a | done | — (pure, names only, never values) |

## Models

| Module | LOC | Sec | Leak | Str | Findings |
| --- | --- | --- | --- | --- | --- |
| `mcat/models/project_models.py` | 225 | done | done | done | MCAT-002 (`interval_seconds`), MCAT-018 |
| `mcat/models/project_state.py` | 92 | done | done | done | MCAT-006 (path sink) |
| `mcat/models/processing_models.py` | 88 | done | n/a | done | — |
| `mcat/models/file_models.py` | 74 | done | n/a | done | — |
| `mcat/models/import_result.py` | 56 | done | n/a | done | — |
| `mcat/models/types.py` | 67 | n/a | n/a | done | — |
| `mcat/models/__init__.py` | 24 | n/a | n/a | n/a | re-exports |

## Config, events, utils

| Module | LOC | Sec | Leak | Str | Findings |
| --- | --- | --- | --- | --- | --- |
| `mcat/config/settings.py` | 19 | done | done | done | — (`max_zendriver_tabs: 3` bounds MCAT-021's deadlock) |
| `mcat/config/platform_profiles.py` | 83 | done | n/a | done | — (frozen dataclasses; cookie **names** only, documented reporting-only) |
| `mcat/events/event_bus.py` | 42 | done | done | done | — (`dead_queues` branch is dead code; no reachable growth) |
| `mcat/utils/csv_handler.py` | 141 | done | done | done | MCAT-009, MCAT-010, MCAT-023, MCAT-024, MCAT-026 |

## Build hooks

| Module | LOC | Sec | Leak | Str | Findings |
| --- | --- | --- | --- | --- | --- |
| `hooks/hook-webview.py` | 35 | done | n/a | n/a | — (build-time PyInstaller collection; no runtime surface) |
| `hooks/hook-zendriver.py` | 10 | done | n/a | n/a | — (build-time PyInstaller collection; no runtime surface) |

## Empty / trivial

`n/a` on all lenses — empty or re-export only:
`mcat/api/__init__.py`, `mcat/api/handlers/__init__.py`,
`mcat/config/__init__.py`, `mcat/cookies/__init__.py`,
`mcat/core/__init__.py`, `mcat/events/__init__.py`,
`mcat/scrapers/__init__.py`, `mcat/services/__init__.py`,
`mcat/utils/__init__.py`

---

## Cross-cutting seams

| Seam | Sec | Leak | Str | Outcome |
| --- | --- | --- | --- | --- |
| Browser session lifecycle | done | done | done | MCAT-014, MCAT-016, MCAT-017, MCAT-021 |
| Cookie store → job → CDP injection | done | n/a | done | MCAT-003, MCAT-021. Injection itself is sound: `cookie_to_dict`/`to_cookie_param` round-trip cleanly and `from_json` coerces (MCAT-034 rejected) |
| Threading ↔ asyncio boundary | done | done | done | MCAT-021, MCAT-027, MCAT-028, MCAT-029, MCAT-035 |
| SSE fan-out | done | done | done | No leak; MCAT-018 is payload growth only |
| Untrusted URL path | done | n/a | done | MCAT-004, MCAT-009, MCAT-010, MCAT-023 |

---

## Beyond the backend

Read to resolve specific claims, not audited in their own right:

- **Frontend** — `main.ts`, `lib/api/{client,sse}.ts`, `lib/stores/{project,processing}.svelte.ts`,
  `lib/views/ProjectView.svelte`, `lib/components/{DataTable,Controls,ControlsStartButton,ControlsInterval,DetailResults,DetailChanges,DetailPanel}.svelte`,
  `types/{processing,project}.ts`, `App.svelte`, `packages/shared-ui/src/Link.svelte`.
  Decisive for MCAT-022 (`IDLE_STATES` includes `'cancelled'`), MCAT-031 and
  MCAT-033 (client renders `data.error` for any non-ok status), and for rejecting
  MCAT-036 and MCAT-037.
- **Vendored zendriver 0.15.3** — `core/{browser,connection,tab,util,config}.py`,
  `cdp/network.py`. Decisive for MCAT-014, MCAT-016, MCAT-017, MCAT-019,
  MCAT-021, and for rejecting MCAT-034.
- **pywebview 6.2.1** — `util.py` (`js_bridge_call`), `js/api.js`, `window.py`.
  Decisive for the js-bridge ABSENT verdict.
- **Stdlib 3.14** — `asyncio/{locks,base_events,runners}.py`, `http/server.py`.
  Decisive for MCAT-016 and MCAT-033.
- **Repo** — root and backend `.gitignore` (neither covers `cookies/`), `mcat.spec`.
</content>
