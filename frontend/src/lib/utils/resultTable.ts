/**
 * Shared table prep for the run Results and Changes views — both render the same
 * mcat_* result rows, differing only in the status cell (a plain badge vs a
 * transition) and a couple of internal-only columns.
 */

export type ResultColumnType = 'text' | 'link' | 'status' | 'transition' | 'file';

export interface ResultColumn {
  key: string;
  header: string;
  type: ResultColumnType;
}

// Desired column order after the index + URL: these mcat columns, then anything else.
const MCAT_ORDER = ['mcat_status', 'mcat_screenshot', 'mcat_user', 'mcat_detail', 'mcat_error'];

function naCell(v: unknown): string {
  const s = v == null ? '' : String(v).trim();
  return s === '' || s.toUpperCase() === 'N/A' ? 'n/a' : s;
}

function mcatIndex(r: Record<string, unknown>): number {
  const n = Number(r.mcat_index);
  return Number.isFinite(n) ? n : Infinity;
}

/** Blank out N/A detail/error cells and order rows by mcat_index (results.csv is
 * written in completion order; rows without an index keep their order, last). */
export function normalizeRows(rows: Record<string, unknown>[]): Record<string, unknown>[] {
  return rows
    .map((r) => {
      const out = { ...r };
      if ('mcat_detail' in out) out.mcat_detail = naCell(out.mcat_detail);
      if ('mcat_error' in out) out.mcat_error = naCell(out.mcat_error);
      return out;
    })
    .sort((a, b) => mcatIndex(a) - mcatIndex(b));
}

/** Build DataTable columns: mcat_index (#) first, then the URL, then MCAT_ORDER,
 * then any remaining columns. `statusType` picks the mcat_status rendering and
 * `internal` hides columns used only for joins (e.g. previous_status). */
export function buildResultColumns(
  columns: string[],
  opts: { statusType: 'status' | 'transition'; internal?: string[] },
): ResultColumn[] {
  const visible = columns.filter((c) => !(opts.internal ?? []).includes(c));
  const urlCol = visible.find((c) => !c.startsWith('mcat_'));
  if (!urlCol) return visible.map((c) => ({ key: c, header: c, type: 'text' }));

  const head = ['mcat_index', urlCol, ...MCAT_ORDER].filter((c) => visible.includes(c));
  const rest = visible.filter((c) => !head.includes(c));

  return [...head, ...rest].map((col) => ({
    key: col,
    header:
      col === 'mcat_index' ? '#'
      : col === 'mcat_status' && opts.statusType === 'transition' ? 'change'
      : col,
    type:
      col === 'mcat_status' ? opts.statusType
      : col === urlCol ? 'link'
      : col === 'mcat_screenshot' ? 'file'
      : 'text',
  }));
}
