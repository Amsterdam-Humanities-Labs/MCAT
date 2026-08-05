/**
 * Single source of truth for the content-status taxonomy: label, colors, badge
 * classes, progress ordering, and the summary-count key — everything the status
 * surfaces (badges, progress bar/legend, console, timeline) need.
 *
 * Class strings are written out literally (not interpolated) so Tailwind's
 * content scan generates them. The color values live once, in theme.css;
 * inline-style consumers use `var(--color-status-*)`.
 */

export type StatusKey =
  | 'live'
  | 'restricted'
  | 'moderated'
  | 'unavailable'
  | 'login_required'
  | 'unknown'
  | 'error';

/** Fields on the app's RunStatusSummary that count each status. */
export type StatusSummaryKey =
  | 'live'
  | 'unavailable'
  | 'moderated'
  | 'restricted'
  | 'login_required'
  | 'unknown'
  | 'errors';

export interface StatusMeta {
  key: StatusKey;
  label: string;
  /** Field in RunStatusSummary that counts this status. */
  summaryKey: StatusSummaryKey;
  /** `bg-status-*` — progress segments and legend dots. */
  bg: string;
  /** `text-status-*` — colored status text. */
  text: string;
  /** Badge background + text + border classes. */
  badge: string;
}

const NEUTRAL_BADGE = 'bg-bg-controls text-text-secondary border-border-light';

// Canonical order: progress-bar segments and timeline severity (live → worst).
export const STATUS_META: StatusMeta[] = [
  { key: 'live', label: 'Live', summaryKey: 'live',
    bg: 'bg-status-live', text: 'text-status-live',
    badge: 'bg-badge-live-bg text-badge-live-text border-badge-live-border' },
  { key: 'restricted', label: 'Restricted', summaryKey: 'restricted',
    bg: 'bg-status-restricted', text: 'text-status-restricted',
    badge: 'bg-badge-restricted-bg text-badge-restricted-text border-badge-restricted-border' },
  { key: 'moderated', label: 'Moderated', summaryKey: 'moderated',
    bg: 'bg-status-moderated', text: 'text-status-moderated',
    badge: 'bg-badge-moderated-bg text-badge-moderated-text border-badge-moderated-border' },
  { key: 'unavailable', label: 'Unavailable', summaryKey: 'unavailable',
    bg: 'bg-status-unavailable', text: 'text-status-unavailable',
    badge: 'bg-badge-unavailable-bg text-badge-unavailable-text border-badge-unavailable-border' },
  { key: 'login_required', label: 'Login Required', summaryKey: 'login_required',
    bg: 'bg-status-login', text: 'text-status-login',
    badge: 'bg-badge-login-bg text-badge-login-text border-badge-login-border' },
  { key: 'unknown', label: 'Unknown', summaryKey: 'unknown',
    bg: 'bg-status-unknown', text: 'text-status-unknown',
    badge: 'bg-badge-unknown-bg text-badge-unknown-text border-badge-unknown-border' },
  { key: 'error', label: 'Error', summaryKey: 'errors',
    bg: 'bg-status-error', text: 'text-status-error',
    badge: 'bg-badge-error-bg text-badge-error-text border-badge-error-border' },
];

// Legacy mcat_status values (collapsed by the taxonomy) → their canonical status,
// so results recorded before the change still render with the right color/label.
const LEGACY: Record<string, StatusKey> = {
  removed: 'unavailable',
  private: 'restricted',
  'age-restricted': 'restricted',
  'geo-blocked': 'restricted',
};

// Resolve any mcat_status string or summary key to its meta: canonical key,
// label ("login required"), summary key ("errors"), and legacy aliases.
const BY_STRING = new Map<string, StatusMeta>();
for (const m of STATUS_META) {
  BY_STRING.set(m.key, m);
  BY_STRING.set(m.label.toLowerCase(), m);
  BY_STRING.set(m.summaryKey, m);
}
for (const [alias, key] of Object.entries(LEGACY)) {
  BY_STRING.set(alias, STATUS_META.find((m) => m.key === key)!);
}

export function statusMeta(status: string): StatusMeta | undefined {
  return BY_STRING.get(status.trim().toLowerCase());
}

/** Badge classes for a status string, falling back to neutral for unknowns. */
export function statusBadge(status: string): string {
  return statusMeta(status)?.badge ?? NEUTRAL_BADGE;
}

/** Display label, falling back to a title-cased version of the raw string. */
export function statusLabel(status: string): string {
  return statusMeta(status)?.label ?? status.charAt(0).toUpperCase() + status.slice(1);
}

/** Canonical severity order (live=0 … error=6); 99 for unrecognized. */
export function statusOrder(status: string): number {
  const meta = statusMeta(status);
  return meta ? STATUS_META.indexOf(meta) : 99;
}
