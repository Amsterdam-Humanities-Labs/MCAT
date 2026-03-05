# MCAT UI Redesign — Stage 1 Implementation Plan

## Context

MCAT is a Tauri desktop app for batch URL status checking (YouTube/Instagram). The current UI uses a dark-themed, card-based layout with a combined.csv results table, a tracking history dropdown, and a console. We're replacing it with a timeline-centric, Noctua-themed interface focused on change detection.

Stage 1 covers the **collapsed (non-expanded) view only** — toolbar, controls, progress, timeline, and console. The expanded detail panel, pinned URL tracks, and screenshot viewer are deferred to Stage 2.

Reference wireframe: `mcat-v9 1.jpg` (collapsed view — Stage 1 target). The expanded view wireframe (`mcat-v9 -expanded 1.jpg`) is reference for Stage 2.

---

## Design System

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `bg-primary` | `#FAF6F0` | Main background, console body |
| `bg-timeline` | `#F3EDE4` | Timeline band background (subtle darker) |
| `bg-controls` | `#F5EDE0` | Controls strip, console header |
| `bg-toolbar` | `#EDE5D8` | Top toolbar |
| `border-light` | `#E4DAC9` | Timeline band borders |
| `border-mid` | `#D9CBAE` | General dividers |
| `border-input` | `#C4AD8A` | Input borders, timeline axis |
| `text-primary` | `#1A1209` | Headings, primary labels |
| `text-body` | `#2A1E0E` | Body text, console entries |
| `text-secondary` | `#6B5540` | Timestamps, metadata |
| `text-muted` | `#B0997A` | Disabled/quiet states |
| `text-hint` | `#7A6548` | Hints, tertiary info |
| `accent-brown` | `#6B4C2A` | Buttons, active dots |
| `accent-gold` | `#C9A96E` | Branding accent (sparingly) |
| `status-live` | `#4E8A4E` | Live status |
| `status-removed` | `#B54040` | Removed status |
| `status-restricted` | `#B8832F` | Restricted/warning status |
| `status-error` | `#7A6548` | Error status |
| `link-blue` | `#2B5C8A` | URL links (Stage 2) |

### Typography

All text minimum **16px**. No exceptions.

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Project name | 18px | 700 | `text-primary` |
| Body/labels | 16px | 400 | `text-body` |
| Buttons | 16px | 600 | cream on brown |
| Section headers (RUNS) | 16px | 700, letter-spacing 0.5px | `text-secondary` |
| Timeline run labels | 16px | 600 for active, 400 for inactive | `text-primary` / `text-hint` |
| Console monospace | 16px | 400 | `text-body` or status colors |

### Icons

Use **Phosphor-style outline SVG icons** throughout. No emoji anywhere in the UI (console glyphs like checkmark, warning, x-mark are fine as text characters in monospace).

Stage 1 icons needed: folder (open), close/X, chevron up/down (console expand/collapse).

### Layout

Viewport: 1440px wide. Full-width, no cards. Tauri handles window chrome — no custom title bar or window controls.

---

## Codebase Changes Overview

Target: `tauri-prototype/frontend/src/`

```
KEEP AS-IS
  App.svelte, main.ts
  lib/views/StartScreen.svelte
  lib/views/ProjectWizard.svelte
  lib/views/dialogs/*
  lib/api/client.ts
  lib/stores/app.svelte.ts, wizard.svelte.ts, dialogs.svelte.ts
  lib/utils.ts, lib/utils/*

MODIFY
  lib/views/ProjectView.svelte          <- gut and rewire to new layout
  lib/api/sse.ts                        <- remove results/tracking listeners, update project event
  lib/stores/project.svelte.ts          <- add enriched run metadata types, derived helpers
  lib/stores/processing.svelte.ts       <- keep SSE logic, expose runState enum
  lib/stores/console.svelte.ts          <- keep, no changes
  lib/stores/polling.svelte.ts          <- adapt interval to value+unit
  types/project.ts                      <- add new run fields, tracking config
  types/processing.ts                   <- add run state enum

KEEP (for future use)
  lib/components/DataTable.svelte       <- will reuse in Stage 2 All Results tab

REMOVE (after migration complete)
  lib/components/StatCard.svelte
  lib/components/StatsGrid.svelte
  lib/components/TrackingHistory.svelte
  lib/components/TrackingControls.svelte
  lib/stores/results.svelte.ts
  lib/stores/tracking.svelte.ts
  types/results.ts

CREATE (new files below)
```

---

## New Files — All flat in `lib/components/`

```
lib/components/SvgIcon.svelte                <- NEW
lib/components/Toolbar.svelte                <- NEW
lib/components/ToolbarBadge.svelte           <- NEW
lib/components/Controls.svelte               <- NEW
lib/components/ControlsStartButton.svelte    <- NEW
lib/components/ControlsInterval.svelte       <- NEW
lib/components/ControlsHint.svelte           <- NEW
lib/components/ProgressSection.svelte        <- NEW
lib/components/ProgressBar.svelte            <- NEW (replaces SegmentedProgress)
lib/components/ProgressLegend.svelte         <- NEW
lib/components/Timeline.svelte               <- NEW
lib/components/TimelineAxis.svelte           <- NEW
lib/components/TimelineDot.svelte            <- NEW
lib/components/TimelineLabel.svelte          <- NEW
lib/components/TimelineRunning.svelte        <- NEW
lib/components/ConsolePanel.svelte           <- MODIFY (restyle + split)
lib/components/ConsoleHeader.svelte          <- NEW
lib/components/ConsoleBody.svelte            <- NEW
lib/components/ConsoleEntry.svelte           <- NEW
lib/theme.ts                                 <- NEW
lib/utils/format.ts                          <- NEW
```

---

## Component Definitions

### Shared

**`SvgIcon`** — Central icon registry. Renders inline SVG by name. All icons route through this, no raw `<svg>` elsewhere.

Props: `name: 'folder' | 'close' | 'chevron-up' | 'chevron-down' | 'x'`, `size`, `color`

**`lib/theme.ts`** — Design tokens as exported constants. Colors, spacing values. Imported by components needing raw values. CSS custom properties in a global stylesheet cover the rest.

**`lib/utils/format.ts`** — `statusColor(status)`, `formatDuration(seconds)`, `formatTimestamp(iso)`. Shared across timeline, progress, console.

### Toolbar group

**`Toolbar`** — 48px bar. Project identity + actions.

Props: `projectName`, `platform`, `urlCount`, `onOpenFolder`, `onClose`

Children: `ToolbarBadge`, two `SvgIcon` button areas.

**`ToolbarBadge`** — Brown pill, cream text. Pure presentational.

Props: `platform`

### Controls group

**`Controls`** — 56px strip. Layout shell composing children. No logic beyond layout.

Props: `runState`, `intervalValue`, `intervalUnit`, `lastRunDuration`, callbacks

**`ControlsStartButton`** — Swaps Start (filled) <-> Pause+Cancel (outlines) based on run state. Reuse existing `Button` with style variants where possible.

Props: `runState: 'idle' | 'running' | 'paused'`, `onStart`, `onPause`, `onCancel`

**`ControlsInterval`** — Checkbox + number input + unit dropdown. Reuse existing `Checkbox`, `Input`, `Select`.

Props: `enabled`, `value`, `unit`, `onToggle`, `onChange`

**`ControlsHint`** — "Last run took ~Xm" or nothing.

Props: `durationSeconds: number | null`

### Progress group

**`ProgressSection`** — Wrapper for bar + legend. Hides when no data.

Props: `total`, `checked`, `statusCounts: { live, removed, restricted, error }`

**`ProgressBar`** — 6px segmented bar. Replaces existing `SegmentedProgress`.

Props: `total`, `statusCounts`

**`ProgressLegend`** — Row of colored dot + count + label pairs.

Props: `statusCounts`

### Timeline group

**`Timeline`** — The `#F3EDE4` band. Owns horizontal scroll, uniform dot positioning, auto-scroll to latest. Most complex component but delegates rendering to children.

Props: `runs: Run[]`, `currentRun: ActiveRun | null`, `selectedRunId: string | null`, `onRunClick: (id) => void`

Positioning: uniform spacing, min 200px gap between dots. Total width = max(viewport, numRuns * gap). `overflow-x: auto`. Time-proportional spacing is deferred — uniform is simpler and matches the wireframes.

**`TimelineAxis`** — SVG line + arrowhead. Pure decoration.

Props: `width: number`

**`TimelineDot`** — Circle on axis + click target. Size/color from run data. Selection ring when active. Delegates text below to `TimelineLabel`.

Props: `run: Run`, `isSelected: boolean`, `onClick: () => void`

Dot rules: baseline -> brown 7px; has changes -> brown 7px; no changes -> muted 5px.

**`TimelineLabel`** — Text below a dot. Varies by run type:
- Baseline -> timestamp, "Initial", url count, status breakdown
- Has changes -> timestamp, "N changes", colored transition lines
- No changes -> timestamp, "No changes" (muted)

Props: `run: Run`

**`TimelineRunning`** — Dashed circle + "Running... X%". Right end of axis. Separate from `TimelineDot` because it doesn't map to a completed run.

Props: `timestamp: string`, `progressPercent: number`

### Console group

**`ConsolePanel`** — MODIFY existing. Shell managing expanded/collapsed. Renders header always, body conditionally.

Props: `entries`, `expanded`, `onToggle`, `warningCount`

**`ConsoleHeader`** — 36px bar. Label + warning count + chevron via `SvgIcon`.

Props: `expanded`, `warningCount`, `onToggle`

**`ConsoleBody`** — Scrollable log container. Auto-scrolls on new entries.

Props: `entries`

**`ConsoleEntry`** — Single monospace line. Timestamp (muted) + message (colored by level). No truncation.

Props: `timestamp`, `message`, `level: 'info' | 'success' | 'warning' | 'error'`

---

## Updated barrel export

```ts
// lib/components/index.ts — add to existing exports

export { default as SvgIcon } from './SvgIcon.svelte'

export { default as Toolbar } from './Toolbar.svelte'
export { default as ToolbarBadge } from './ToolbarBadge.svelte'

export { default as Controls } from './Controls.svelte'
export { default as ControlsStartButton } from './ControlsStartButton.svelte'
export { default as ControlsInterval } from './ControlsInterval.svelte'
export { default as ControlsHint } from './ControlsHint.svelte'

export { default as ProgressSection } from './ProgressSection.svelte'
export { default as ProgressBar } from './ProgressBar.svelte'
export { default as ProgressLegend } from './ProgressLegend.svelte'

export { default as Timeline } from './Timeline.svelte'
export { default as TimelineAxis } from './TimelineAxis.svelte'
export { default as TimelineDot } from './TimelineDot.svelte'
export { default as TimelineLabel } from './TimelineLabel.svelte'
export { default as TimelineRunning } from './TimelineRunning.svelte'

export { default as ConsolePanel } from './ConsolePanel.svelte'
export { default as ConsoleHeader } from './ConsoleHeader.svelte'
export { default as ConsoleBody } from './ConsoleBody.svelte'
export { default as ConsoleEntry } from './ConsoleEntry.svelte'
```

---

## Type Changes

```ts
// types/project.ts — ADD to existing types

interface RunStatusSummary {
  live: number
  removed: number
  restricted: number
  error: number
}

interface RunChangesSummary {
  [transition: string]: number  // e.g. "live_to_removed": 3
}

// MODIFY existing Run interface
interface Run {
  id: string
  started_at: string
  completed_at: string
  duration_seconds: number
  status: 'completed' | 'running' | 'failed' | 'cancelled'
  is_baseline: boolean
  screenshots_enabled: boolean
  total_checked: number
  changes_count: number
  changes_summary: RunChangesSummary
  status_summary: RunStatusSummary
}

// MODIFY existing TrackingConfig
interface TrackingConfig {
  enabled: boolean
  interval_value: number
  interval_unit: 'minutes' | 'hours' | 'days'
  last_run: string | null
  next_run_at: string | null
}
```

---

## Store Changes

**`project.svelte.ts`** — MODIFY. Add derived: `sortedRuns`, `latestRun`, `baselineRun`.

**`processing.svelte.ts`** — MODIFY. Expose `runState: 'idle' | 'running' | 'paused'`.

**`polling.svelte.ts`** — MODIFY. `interval_value` + `interval_unit` replacing `interval_minutes`.

**`results.svelte.ts`** — REMOVE after migration.

**`tracking.svelte.ts`** — REMOVE after migration.

---

## Backend Changes

**`mcat/models/project_models.py`** — Add `is_baseline`, `duration_seconds`, `changes_count`, `changes_summary`, `status_summary` to `RunConfig`. Update `TrackingConfig` to `interval_value` + `interval_unit`. Provide defaults in `from_dict` so existing `project.json` files without these fields load without error.

**`mcat/services/run_service.py`** — On completion: diff vs previous run, write `changes.csv`, populate new metadata, update `project.json`.

**`mcat/services/processing_service.py`** — Remove `TRACK-` prefix. All runs use timestamp IDs. Keep `run_type` field on the model for now (no behavioral difference, just metadata).

**`mcat/models/file_models.py`** — Add `ChangesRow`: `url`, `previous_status`, `new_status`, `info`, `timestamp`.

**`mcat/services/csv_service.py`** — Add `write_changes_csv()` and `read_changes_csv()`.

**Backend API routes** — Update `/tracking/start` to accept `interval_value` + `interval_unit` instead of `interval_minutes`. Deprecate `/results/combined` (remove in Step 9). Ensure the `project` SSE event includes the enriched run metadata (new fields in `runs[]`).

---

## SSE Changes (`lib/api/sse.ts`)

The SSE handler requires coordinated updates as stores are added/removed:

**Step 7 (with backend changes):**
- Update the `project` event listener: the project payload will now include enriched run data (`status_summary`, `changes_summary`, etc.). The existing `projectStore.setProject(data.project)` call handles this automatically as long as `types/project.ts` is updated.
- Tracking state now lives in the project data (part of `project.json`), so tracking SSE events should update project state instead of the old tracking store.

**Step 9 (cleanup):**
- Remove `import { resultsStore }` and `import { trackingStore }`.
- Remove the `results` event listener entirely.
- Remove `tracking.started`, `tracking.stopped`, `tracking.run_completed`, `tracking.changes_detected` listeners.
- Move any console logging from tracking listeners (e.g. "Detected N status changes") into the `project` event handler or a new `run.completed` SSE event from the backend.
- Remove the `resultsStore.load()` call from the `project` event listener.

---

## ProjectView.svelte Rewire

```svelte
<div class="processing-view">
  <Toolbar {projectName} {platform} {urlCount} {onOpenFolder} {onClose} />
  <Controls {runState} {intervalValue} {intervalUnit} {lastRunDuration} ... />
  <ProgressSection {total} {checked} {statusCounts} />
  <Timeline {runs} {currentRun} {selectedRunId} {onRunClick} />
  <ConsolePanel {entries} {expanded} {onToggle} {warningCount} />
</div>
```

~50 lines. Pulls from stores, passes props down.

---

## Implementation Steps

Each step produces a testable state. Work top-down through the layout.

### Step 1: Theme & Global Styles

**What:** Replace the existing dark theme with the Noctua palette. Set up CSS custom properties for all design tokens listed above. Set `font-family: Inter, system-ui, sans-serif` and base `font-size: 16px`. Create `lib/theme.ts` and `lib/utils/format.ts`.

**Test:** Open the app. Background should be warm cream `#FAF6F0`. All text should render in Inter at 16px minimum. No dark theme remnants.

---

### Step 2: Backend — project.json Metadata & API Routes

**What:** Update the backend to write enriched metadata to `project.json` and serve it through updated APIs.

**Model changes (`project_models.py`):**
- Add to `RunConfig`: `is_baseline: bool`, `duration_seconds: float`, `changes_count: int`, `changes_summary: dict`, `status_summary: dict`. All default to zero/empty in `from_dict` for backward compatibility with existing project files.
- Update `TrackingConfig`: replace `interval_minutes: int` with `interval_value: int` + `interval_unit: str` (default `"minutes"`). In `from_dict`, if `interval_minutes` exists but `interval_value` does not, migrate: set `interval_value = interval_minutes`, `interval_unit = "minutes"`.

**Run service changes (`run_service.py`):**
- On `complete_run`: compute `duration_seconds` from `started_at`/`completed_at`. Set `is_baseline = True` if this is the first completed run. Compute `status_summary` from the run's `results.csv`. Diff against previous completed run to get `changes_count` and `changes_summary`.
- Remove the `TRACK-` prefix from `generate_run_id`. All runs use plain timestamp IDs. Keep `run_type` field on the model as metadata (no behavioral difference).

**API route changes:**
- Update `/tracking/start` to accept `{ interval_value, interval_unit }` instead of `{ interval_minutes }`.
- Ensure the `project` SSE event payload includes the full enriched run data.

**Test:** Complete a run. Read `project.json` — new fields are present and correct. Open an old project with no new fields — loads without error, fields default to zero/empty. Tracking API accepts value+unit.

---

### Step 3: Backend — changes.csv Generation

**What:** After each run completes, the backend diffs the current results against the previous run and writes a `changes.csv` file.

Format: `url,previous_status,new_status,info,timestamp`

Only written for non-baseline runs. If no changes detected, write an empty file (headers only) and set `changes_count: 0` in project.json.

This is part of Stage 1 because the diff logic also produces the `changes_count` and `changes_summary` fields that the timeline needs. The CSV itself won't be read by the frontend until Stage 2 (detail panel), but writing it now is free and keeps the backend complete.

**Test:** Run a check. Inspect the run folder — `changes.csv` exists with correct diff data. `project.json` has matching `changes_count` and `changes_summary`.

---

### Step 4: Toolbar

**What:** Replace the current header bar (MCAT branding, backend status, etc.) with a single toolbar strip. Create `SvgIcon.svelte`, `Toolbar.svelte`, and `ToolbarBadge.svelte`.

Layout (left to right): Project name (18px bold) -> Platform badge pill (brown `#6B4C2A` bg, cream text, rounded) -> URL count -> [spacer] -> Folder icon + "Folder" label -> vertical divider -> "Close" label.

The folder icon is an SVG outline path via `SvgIcon`. Clicking it calls the existing "open project folder" command. Close calls the existing close project command.

**Remove:** The "MCAT" branding text, "Moderation Content Analysis Tool" subtitle, backend connection status indicator. Tauri shows the app name in the OS title bar already.

**Test:** Toolbar renders at 48px height with `#EDE5D8` background. Project name, badge, URL count visible on the left. Folder and Close on the right. Clicking Folder opens the project directory. Clicking Close returns to project list.

---

### Step 5: Processing Controls Strip

**What:** Replace the current processing card with a flat controls strip below the toolbar. Create `Controls.svelte`, `ControlsStartButton.svelte`, `ControlsInterval.svelte`, `ControlsHint.svelte`.

Layout: `[Start]` button (brown fill, cream text) -> checkbox + "Repeat every" label -> number input -> unit dropdown (minutes/hours/days) -> "Last run took ~Xm" hint text.

The Start button is the only button in idle state. When a run is in progress, Start is replaced by `[Pause]` (outline border) + `[Cancel]` (outline border, red-ish text) in the same position.

**Hint text:** Reads the last completed run's `duration_seconds` from the project's run list and displays it as "Last run took ~Xm". Hidden if no completed runs exist yet.

**Test:** Controls strip renders at 56px height with `#F5EDE0` background. Start button triggers a run. Checkbox enables/disables repeat. Number + unit inputs are functional. During a run, Start swaps to Pause + Cancel. When run ends or is cancelled, Start returns.

---

### Step 6: Progress Bar

**What:** Keep the existing segmented progress bar but restyle it. Create `ProgressSection.svelte`, `ProgressBar.svelte`, `ProgressLegend.svelte`.

Bar: 6px height, rounded ends, track color `#E8DCC8`. Segments colored by status: green `#4E8A4E` (Live), red `#B54040` (Removed), orange `#B8832F` (Restricted).

Below the bar: "650 / 1,000 (65%)" text + status legend with colored dots. All at 16px.

The progress bar + legend sits between the controls strip and the timeline, separated by a `#D9CBAE` divider. Progress updates in real time via the existing SSE connection.

**Test:** Start a run. Bar fills proportionally as URLs are checked. Status counts update in real time. Colors match the palette. When run completes, bar shows 100% with final breakdown.

---

### Step 7: Console Panel

**What:** Restyle the existing console. Refactor into `ConsolePanel.svelte` (modify), `ConsoleHeader.svelte`, `ConsoleBody.svelte`, `ConsoleEntry.svelte`.

Console has two states: expanded (shows log entries, takes remaining vertical space) and collapsed (just a 36px header bar).

Header: `#F5EDE0` background, "Console" label (16px bold), warning count in `#A0522D` if any, chevron icon (outline via `SvgIcon`) on the right to toggle expand/collapse.

Log entries: 16px monospace, 28px line height. Timestamp in `#9A8468`, message in `#2A1E0E` (normal), `#4E8A4E` (success), `#B8832F` (warning), `#B54040` (error). Full URL IDs — no truncation, the console is full width.

Console should auto-scroll to latest entry during a run.

**Test:** Console renders with warm cream styling. Collapse/expand toggle works. During a run, log entries stream in with correct colors. URLs are not truncated. Auto-scrolls to bottom.

---

### Step 8: Timeline Band

**What:** This is the main new component. Replace the old Results table and Tracking History dropdown with a horizontal timeline. Create `Timeline.svelte`, `TimelineAxis.svelte`, `TimelineDot.svelte`, `TimelineLabel.svelte`, `TimelineRunning.svelte`.

The timeline sits in a band with `#F3EDE4` background. The band contains a horizontal axis line with an arrow at the right end.

Each completed run is a dot on the axis. Data comes from `project.json` -> `runs[]` array (via the project store) — no CSV reads needed.

**Run dot rendering rules:**
- Baseline run (first): solid brown `#6B4C2A` dot, 7px radius. Below it: timestamp, "Initial", URL count, status breakdown (Live/Removed/Restricted counts in status colors).
- Run with changes: solid brown dot, 7px radius. Below: timestamp, "N changes", then transition summary lines (e.g., "3 Live -> Removed" in red, "2 Removed -> Live" in green).
- Run with no changes: smaller muted dot (`#C4AD8A`, 5px radius). Below: timestamp, "No changes" in muted text.
- Currently running: dashed circle outline, brown. Below: timestamp, "Running... X%".

All text below dots is 16px. Timestamps on one line ("Feb 12, 14:30"), summaries below.

**Spacing:** Uniform spacing between dots (not time-proportional). Min 200px gap. Total width = max(viewport, numRuns * gap). Time-proportional layout is deferred — uniform is simpler and matches the wireframes.

**Scrolling:** If more runs than fit horizontally, the timeline scrolls horizontally. Most recent run should be visible by default (scroll to right end).

**Test:** Open a project with multiple completed runs. Timeline renders with correct dots, labels, and colors. Baseline shows full breakdown. Subsequent runs show change summaries. No-change runs are visually muted. During a run, a dashed dot appears at the right. Timeline scrolls if there are many runs.

---

### Step 9: SSE & Store Wiring

**What:** Update `sse.ts` and stores to reflect the new data flow. This connects all the new frontend components to live data.

**`sse.ts` changes:**
- Remove `import { resultsStore }` and `import { trackingStore }`.
- Remove the `results` event listener.
- Remove `tracking.started`, `tracking.stopped`, `tracking.run_completed`, `tracking.changes_detected` event listeners.
- Remove the `resultsStore.load()` call from the `project` event listener.
- Tracking state is now part of the project data (in `project.json`), so the `project` SSE event already carries it. No separate tracking listeners needed.
- Add a `run.completed` event listener that logs to console (e.g., "Run completed: N changes detected") — replaces the old `tracking.changes_detected` logging.

**`project.svelte.ts` changes:**
- Add derived getters: `sortedRuns` (by `started_at`), `latestRun` (most recent completed), `baselineRun` (first completed, `is_baseline === true`).

**`processing.svelte.ts` changes:**
- Expose `runState: 'idle' | 'running' | 'paused'` derived from existing `isIdle`/`isProcessing`/`isPaused`.
- Remove `StatusCounts` import from `types/results` — define locally or move to `types/processing.ts`.

**`polling.svelte.ts` changes:**
- Update tracking API calls to use `interval_value` + `interval_unit`.

**Test:** Start a run. SSE events flow through to progress bar, timeline running dot, and console. Run completes — new dot appears on timeline with correct summary. No console errors about missing stores or events.

---

### Step 10: Remove Old Components & Code

**What:** Remove the components and code that are no longer needed.

**Frontend removals:**
- Components: `StatCard.svelte`, `StatsGrid.svelte`, `TrackingHistory.svelte`, `TrackingControls.svelte`, `SegmentedProgress.svelte`.
- Stores: `results.svelte.ts`, `tracking.svelte.ts`.
- Types: `types/results.ts`.
- Remove old dark theme CSS variables.
- Remove barrel exports for deleted components from `lib/components/index.ts`.
- Remove `combinedCsvPath` from the `Project` type if no longer used.

**Backend removals:**
- Remove `generate_combined_csv()` from `run_service.py`.
- Remove `/results/combined` API endpoint.
- Remove any combined.csv generation calls from run completion flow.

**Test:** Full flow works end to end: open project -> controls + timeline + console visible -> start run -> progress updates -> run completes -> new dot appears on timeline with correct summary -> console shows logs. No old UI elements visible. No dead imports or unused code.

---

## Stage 1 Dependency Graph

```
Step 1 (Theme)
  |-> Step 4 (Toolbar)
  |-> Step 5 (Controls)
  |-> Step 6 (Progress Bar)
  +-> Step 7 (Console)

Step 2 (project.json + API) ---> Step 8 (Timeline)
Step 3 (changes.csv)        ---> (frontend reads in Stage 2, write now)

Step 9 (SSE + Store Wiring) --- depends on Steps 2, 4-8

Step 10 (Cleanup) --- after all others
```

Steps 1-3 have no frontend/backend cross-dependencies and can be done in parallel.
Steps 4-7 depend on Step 1 (theme) but are independent of each other.
Step 8 depends on Step 2 (needs enriched project.json data).
Step 9 wires everything together.
Step 10 is last.

**Recommended order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10**

(Steps 2+3 can overlap with 4-7 since they're backend vs frontend work.)

---

## Stage 2 — Expanded View

Stage 2 builds on the completed Stage 1 timeline. It adds interactivity: clicking a run dot expands a detail panel showing changes and full results, URLs can be pinned to track across runs, and screenshots can be previewed.

Reference wireframe: `mcat-v9 -expanded 1.jpg`

---

## Stage 2 Design Elements

### Detail Panel Layout

The detail panel appears **between the timeline band and the console** when a run dot is clicked. It pushes the console down (no overlay/modal). Clicking the same dot again or clicking a different dot toggles/switches the panel.

Panel structure (top to bottom):
1. **Header row:** "Run #N" (bold) + date/time + duration + "N checked" + [spacer] + folder icon "Open run file" link (right-aligned)
2. **Tab bar:** "Changes" tab (default active) | "All Results" tab. Underline-style tabs, `accent-brown` for active, `text-muted` for inactive.
3. **Tab content area:** scrollable, max-height before console takes over.

### Pinned URL Tracks Layout

Pinned tracks appear as **parallel horizontal lines in the timeline band**, below the "RUNS" axis and above the detail panel. Each track is labeled with a shortened URL on the left.

Each track has dots at the same x-positions as the run dots above. Dot color = status color at that run. When status changes between runs, the connecting line segment changes to the new status color + the dot gets a larger radius to draw attention.

Label: "PINNED" section header above the tracks (same style as "RUNS").

### Screenshot Viewer

Inline preview — not a separate window. When the screenshot icon on a URL row is clicked, a preview panel expands below that row (or to the side). Shows the screenshot image at a reasonable size with the run timestamp. Clicking again or clicking another screenshot closes/swaps it.

Screenshots are stored at `runs/<run_id>/screenshots/<video_id>_<timestamp>.png`. The backend needs an endpoint to serve/resolve screenshot paths.

---

## Stage 2 Codebase Changes Overview

```
MODIFY
  lib/views/ProjectView.svelte          <- add detail panel slot, selection state
  lib/components/Timeline.svelte        <- add selectedRunId highlight, pinned tracks section
  lib/components/TimelineDot.svelte     <- add selection ring style
  lib/components/DataTable.svelte       <- restyle for Noctua theme, add pin/screenshot action columns
  lib/api/client.ts                     <- add run detail + screenshot endpoints
  lib/api/sse.ts                        <- no changes expected
  lib/stores/project.svelte.ts          <- add selectedRunId, pinnedUrls state
  types/project.ts                      <- add changes types

CREATE
  lib/components/DetailPanel.svelte           <- NEW
  lib/components/DetailHeader.svelte          <- NEW
  lib/components/DetailTabs.svelte            <- NEW
  lib/components/DetailChanges.svelte         <- NEW
  lib/components/DetailChangeGroup.svelte     <- NEW
  lib/components/DetailUrl.svelte             <- NEW
  lib/components/TimelinePinned.svelte        <- NEW
  lib/components/TimelinePinnedTrack.svelte   <- NEW
  lib/components/TimelinePinnedDot.svelte     <- NEW
  lib/components/ScreenshotPreview.svelte     <- NEW
```

---

## Stage 2 Type Changes

```ts
// types/project.ts — ADD

interface ChangeRow {
  url: string
  previous_status: string
  new_status: string
  info: string
  timestamp: string
}

interface ChangeGroup {
  transition: string        // e.g. "Live -> Removed"
  previous_status: string
  new_status: string
  count: number
  urls: ChangeRow[]
}

interface RunDetail {
  run: Run
  changes: ChangeGroup[]    // grouped and sorted by transition type
  results: ResultRow[]      // full results.csv rows (lazy-loaded)
}

interface PinnedUrl {
  url: string
  history: Array<{          // one entry per completed run, in order
    run_id: string
    status: string
  }>
}
```

---

## Stage 2 Store Changes

**`project.svelte.ts`** — MODIFY.
- Add `selectedRunId: string | null` — set when a timeline dot is clicked, cleared when clicked again.
- Add `pinnedUrls: PinnedUrl[]` — persisted to `project.json` so pins survive app restarts.
- Add `async loadRunDetail(runId: string): RunDetail` — fetches changes + results for a run.
- Add `togglePin(url: string)` — adds/removes a URL from pinned list, persists to `project.json`.

**`types/project.ts`** — Add `pinned_urls: string[]` to the `Project` interface (just the URL strings; history is computed from run data).

---

## Stage 2 Backend Changes

**New API endpoints:**
- `GET /run/<run_id>/changes` — reads `runs/<run_id>/changes.csv`, groups by transition type, returns `ChangeGroup[]`. The grouping logic: collect all rows, group by `(previous_status, new_status)`, sort groups by count descending.
- `GET /run/<run_id>/results` — reads `runs/<run_id>/results.csv`, returns all rows. (Replaces the old `/results/run` endpoint with a cleaner path.)
- `GET /run/<run_id>/screenshot/<filename>` — serves a screenshot file from `runs/<run_id>/screenshots/`. Returns the image bytes with correct content-type.
- `GET /url/<url_encoded>/history` — for a given URL, looks up its status in each completed run's `results.csv` and returns the history array. Used by pinned track rendering.

**`project_models.py`** — Add `pinned_urls: List[str]` to `ProjectConfig`. Default empty list. Persisted in `project.json`.

**`project_state.py`** — Add `get_screenshot_path(run_id, filename)` helper.

---

## Stage 2 Component Definitions

### Detail Panel group

**`DetailPanel`** — Outer container. Manages which tab is active. Fetches run detail data on mount (or when `runId` changes).

Props: `runId: string`, `onClose: () => void`

State: `activeTab: 'changes' | 'results'`, `detail: RunDetail | null`, `loading: boolean`

**`DetailHeader`** — Single row with run metadata + "Open run file" action.

Props: `run: Run`, `onOpenFolder: () => void`

Renders: "Run #N" (bold, computed as index in sorted runs + 1) + formatted date + duration + "N checked" + folder icon link.

**`DetailTabs`** — Tab bar with two options. Underline style.

Props: `activeTab`, `onTabChange`, `changesCount: number`, `resultsCount: number`

Renders: "Changes (N)" | "All Results (N)" with counts in parentheses.

**`DetailChanges`** — Changes tab content. Groups transitions and renders them.

Props: `changes: ChangeGroup[]`

Renders: List of `DetailChangeGroup` components. If no changes, shows "No changes from previous run" in muted text.

**`DetailChangeGroup`** — Single transition group with header + URL list.

Props: `group: ChangeGroup`, `onPin: (url) => void`, `onScreenshot: (url, runId) => void`, `pinnedUrls: string[]`

Renders: Colored square (status color of `new_status`) + "Previous -> New (N)" header. Below: list of `DetailUrl` rows.

Color rules for the square: `status-removed` red for any transition ending in Removed. `status-live` green for any transition ending in Live. `status-restricted` orange for transitions ending in Restricted/Private/Age-restricted/Geo-blocked.

**`DetailUrl`** — Single URL row in a change group or results table.

Props: `url: string`, `isPinned: boolean`, `hasScreenshot: boolean`, `onPin: () => void`, `onScreenshot: () => void`

Renders: URL as clickable link (`link-blue` color, opens in browser) + [spacer] + pin icon (toggle, filled if pinned) + screenshot icon (if screenshot exists for this URL in this run). Icons via `SvgIcon`.

New icons needed for Stage 2: `pin` (outline + filled variant), `screenshot`/`image` icon, `external-link`.

### Results tab

The "All Results" tab reuses the existing `DataTable.svelte` component, restyled to Noctua theme.

**`DataTable` modifications:**
- Restyle: cream background, `border-light` borders, `text-body` text, `text-secondary` headers. Status column uses Noctua status colors.
- Add action column (rightmost): pin icon + screenshot icon per row. Same behavior as in `DetailUrl`.
- URL column renders as `link-blue` clickable link.

### Pinned tracks group

**`TimelinePinned`** — Section within the timeline band, below the runs axis. Renders "PINNED" header + list of tracks.

Props: `pinnedUrls: PinnedUrl[]`, `runs: Run[]`, `dotPositions: number[]` (x-positions from parent Timeline, shared with run dots for alignment)

**`TimelinePinnedTrack`** — Single horizontal track for one pinned URL.

Props: `pinnedUrl: PinnedUrl`, `dotPositions: number[]`, `onUnpin: () => void`

Renders: URL label on the left (truncated to video ID or last path segment, full URL in tooltip) + horizontal line + status dots at each run position.

Line segments between dots are colored by the status at the left dot. When status changes, the line color changes at the transition point.

**`TimelinePinnedDot`** — Single dot on a pinned track.

Props: `status: string`, `hasChanged: boolean` (compared to previous dot)

Renders: Circle colored by status. If `hasChanged`, radius is 6px + status label text appears below. If unchanged, radius is 4px, no label.

### Screenshot preview

**`ScreenshotPreview`** — Inline image preview panel.

Props: `src: string` (image URL from backend), `runTimestamp: string`, `onClose: () => void`

Renders: Image (max-width 600px, aspect-ratio preserved) + timestamp caption + close button. Appears below the URL row that triggered it, within the detail panel scroll area.

The image is loaded from the backend via `/run/<run_id>/screenshot/<filename>`. The frontend constructs this URL from the run ID and the screenshot filename stored in the results data.

---

## Stage 2 Updated Barrel Export

```ts
// lib/components/index.ts — add to Stage 1 exports

export { default as DetailPanel } from './DetailPanel.svelte'
export { default as DetailHeader } from './DetailHeader.svelte'
export { default as DetailTabs } from './DetailTabs.svelte'
export { default as DetailChanges } from './DetailChanges.svelte'
export { default as DetailChangeGroup } from './DetailChangeGroup.svelte'
export { default as DetailUrl } from './DetailUrl.svelte'

export { default as TimelinePinned } from './TimelinePinned.svelte'
export { default as TimelinePinnedTrack } from './TimelinePinnedTrack.svelte'
export { default as TimelinePinnedDot } from './TimelinePinnedDot.svelte'

export { default as ScreenshotPreview } from './ScreenshotPreview.svelte'
```

---

## Stage 2 Implementation Steps

### Step 11: Backend — Run Detail & Screenshot APIs

**What:** Add the API endpoints that Stage 2 frontend components need.

**New endpoints:**
- `GET /run/<run_id>/changes` — reads `changes.csv` from the run folder, groups rows by `(previous_status, new_status)` transition, returns `{ changes: ChangeGroup[] }`. Each group sorted by count descending, URLs within each group sorted alphabetically.
- `GET /run/<run_id>/results` — reads `results.csv`, returns `{ results: ResultRow[], total: number }`.
- `GET /run/<run_id>/screenshot/<filename>` — serves the image file from `runs/<run_id>/screenshots/`. Returns 404 if not found. Content-type from file extension.
- `GET /url/history` (POST with `{ url: string }`) — iterates all completed runs, reads each `results.csv`, finds the URL's status in each. Returns `{ history: [{ run_id, status }] }` ordered by run date.

**Model additions:**
- Add `pinned_urls: List[str]` to `ProjectConfig` with empty default.
- Add `POST /project/pin` with `{ url: string }` — toggles a URL in/out of the pinned list, saves `project.json`.

**Test:** Call `/run/<id>/changes` — returns grouped change data matching `changes.csv`. Call `/run/<id>/screenshot/<file>` — returns the image. Call `/url/history` — returns status across runs. Pin a URL — `project.json` updates.

---

### Step 12: Detail Panel — Structure & Header

**What:** Create `DetailPanel.svelte`, `DetailHeader.svelte`, `DetailTabs.svelte`. Wire the panel into `ProjectView.svelte`.

**Interaction:** Clicking a timeline dot sets `selectedRunId` in the project store. If a run is already selected and the same dot is clicked, deselect (close panel). If a different dot is clicked, switch to that run.

`ProjectView` layout becomes:
```svelte
<Toolbar ... />
<Controls ... />
<ProgressSection ... />
<Timeline ... {selectedRunId} {onRunClick} />
{#if selectedRunId}
  <DetailPanel runId={selectedRunId} onClose={deselectRun} />
{/if}
<ConsolePanel ... />
```

`DetailPanel` fetches run detail on mount / when `runId` changes. Shows a loading skeleton while fetching. Renders header + tabs + content area.

**Timeline dot selection:** `TimelineDot` gets a selection ring — 2px `accent-brown` outline with 3px gap (use box-shadow or a second SVG circle). Selected dot is visually distinct from hover.

**Test:** Click a timeline dot — detail panel slides in between timeline and console. Header shows correct run info. Click same dot — panel closes. Click different dot — panel switches. "Open run file" opens the run folder.

---

### Step 13: Changes Tab

**What:** Create `DetailChanges.svelte`, `DetailChangeGroup.svelte`, `DetailUrl.svelte`.

The Changes tab is the default active tab. It shows change groups from the run's `changes.csv`, fetched via `/run/<run_id>/changes`.

**Layout per group:**
- Header: colored square (16x16, colored by `new_status`) + "Live -> Removed" text (16px, bold) + "(3)" count in parentheses
- Below: indented list of URL rows, one per changed URL

**URL row layout:** URL text (clickable, `link-blue`, opens in browser) + [spacer] + pin icon (outline, toggles on click) + screenshot icon (if screenshot exists, otherwise hidden). Both icons 20x20, `text-hint` color, `accent-brown` on hover.

**For baseline runs:** The Changes tab shows "This is the baseline run — no previous run to compare against." in muted text. The tab label still shows "Changes (0)".

**Test:** Click a run with changes. Changes tab shows grouped transitions with correct colors. URLs are clickable. Pin icon toggles. Click baseline run — shows baseline message.

---

### Step 14: All Results Tab

**What:** Restyle `DataTable.svelte` for Noctua theme. Wire it into the "All Results" tab of the detail panel.

**DataTable restyling:**
- Background: `bg-primary`. Header row: `bg-controls` with `text-secondary` column headers.
- Borders: `border-light`. Row hover: subtle `bg-timeline`.
- Status column: colored text using Noctua status colors.
- URL column: `link-blue`, clickable to open in browser.
- Add rightmost action column: pin icon + screenshot icon per row (same as Changes tab).

**Tab content:** Fetches via `/run/<run_id>/results`. Shows all result rows for that run. Paginate or virtual-scroll if > 100 rows (use existing `maxRows` prop as starting point, but consider raising the limit or adding "Load more").

**Test:** Click "All Results" tab. Table renders with all URLs from that run. Columns: URL, Status, Info, Timestamp, actions. Noctua styling applied. Pin/screenshot icons work.

---

### Step 15: Pinned URL Tracks

**What:** Create `TimelinePinned.svelte`, `TimelinePinnedTrack.svelte`, `TimelinePinnedDot.svelte`. Integrate into `Timeline.svelte`.

**Data flow:** When a URL is pinned (via pin icon in detail panel), it's added to `projectStore.pinnedUrls`. The backend persists this to `project.json`. The `Timeline` component receives the pinned URLs list and fetches their history via `/url/history`.

**Timeline layout update:**
```
[RUNS section header]
[--- run axis with dots ---]
[PINNED section header]     <- only shown if pinnedUrls.length > 0
[track 1: watch?v=ABC...]
[track 2: watch?v=DEF...]
```

The PINNED section sits below the RUNS axis within the same `bg-timeline` band. It shares the same horizontal scroll container so pinned dots align vertically with run dots.

**Track rendering:**
- Left label: shortened URL (video ID for YouTube, shortcode for Instagram). Full URL in tooltip.
- Horizontal line spanning all run positions.
- Dots at each run position, colored by status at that run.
- Line segments between dots colored by the left dot's status.
- When status changes between two adjacent runs: the dot at the new run gets a larger radius (6px vs 4px) and the new status label appears below it.

**Unpin:** Clicking the pin icon on a pinned track's label removes it. Or unpin from within the detail panel.

**Performance:** Pin history is fetched once per pin action and cached in the store. When a new run completes, refresh all pinned URL histories.

**Test:** Pin a URL from the detail panel. A new track appears in the timeline with correct status dots. Status changes show enlarged dots with labels. Unpin — track disappears. Close and reopen the project — pins persist.

---

### Step 16: Screenshot Preview

**What:** Create `ScreenshotPreview.svelte`. Add screenshot viewing to `DetailUrl` and `DataTable` action columns.

**Interaction:** Clicking the screenshot icon on a URL row expands an inline preview below that row. Clicking again (or clicking a different screenshot) closes/swaps it. Only one preview open at a time within the detail panel.

**Preview layout:**
- Image: max-width 600px, natural aspect ratio, `border-light` border, slight shadow.
- Caption: run timestamp + URL below the image, `text-secondary`.
- Close button (X icon) in top-right corner of the preview.

**Image loading:** The frontend requests `GET /run/<run_id>/screenshot/<filename>`. The filename is derived from the `screenshot_path` field in the results data. If no screenshot exists for a URL in that run, the screenshot icon is hidden.

**New SvgIcon additions:** `image` (for screenshot button), `pin` (outline), `pin-filled` (active pin), `external-link` (URL open).

**Test:** Click screenshot icon on a URL with a screenshot. Preview expands inline showing the correct image. Click another URL's screenshot — preview swaps. Click X — preview closes. URLs without screenshots don't show the icon.

---

### Step 17: Polish & Edge Cases

**What:** Handle edge cases and polish interactions across all Stage 2 components.

**Edge cases to handle:**
- Detail panel open during a running run: show partial results in "All Results", show "Run in progress..." in Changes tab.
- Pinning a URL that doesn't exist in older runs: show empty/missing dots at those positions (hollow circle or gap).
- Large number of pinned URLs: cap at ~10 pinned tracks. Show "N pinned, showing first 10" if exceeded. Or allow vertical scroll within the pinned section.
- Screenshot files missing (deleted externally): show placeholder "Screenshot not found" instead of broken image.
- Run with 0 results (abandoned early): detail panel shows empty state message.
- Switching between runs rapidly: cancel pending API requests when `runId` changes.

**Performance:**
- Lazy-load "All Results" tab content — only fetch when tab is activated, not on panel open.
- Cache fetched run details in a Map so re-selecting a run doesn't re-fetch.
- Virtual scrolling for results tables with > 500 rows.

**Test:** Cover each edge case manually. Verify no console errors, no broken layouts, no stale data.

---

## Stage 2 Dependency Graph

```
Step 11 (Backend APIs)
  |-> Step 12 (Detail Panel structure)
  |     |-> Step 13 (Changes tab)
  |     +-> Step 14 (Results tab)
  |-> Step 15 (Pinned tracks)
  +-> Step 16 (Screenshots)

Step 17 (Polish) --- after all others
```

Steps 13 and 14 depend on 12 (panel must exist). Steps 13-16 all depend on 11 (backend APIs). Steps 15 and 16 are independent of 13/14 and can be done in parallel.

**Recommended order: 11 -> 12 -> 13 -> 14 -> 15 -> 16 -> 17**
