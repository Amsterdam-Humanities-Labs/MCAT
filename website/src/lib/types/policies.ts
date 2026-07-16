export type Platform = string; // 'x' | 'youtube' | 'facebook' | … (open for now)

export interface BlockContent {
  type: 'heading' | 'paragraph';
  depth?: number; // heading level 1–6
  text: string;
}

// A block in a hydrated version: content + a positional id for keying.
export interface Block extends BlockContent {
  id: string;
}

// ── manifest.json — index of every policy; carries no version lists or text ──
export interface PolicyIndexEntry {
  slug: string; // '<platform>/<policy>', e.g. 'x/community-guidelines'
  title: string;
  platform: Platform;
  versionCount: number;
  firstDate: string;
  lastDate: string;
}

export interface PlatformGroup {
  id: Platform;
  label: string; // 'X', 'YouTube'
  policies: PolicyIndexEntry[];
}

export type PolicyManifest = PlatformGroup[];

// ── <platform>/<policy>.json — one file per policy, lazy-loaded ──────────
// Blocks live in a dictionary (array index = block id); each version is an
// ordered list of ids.
export interface VersionRef {
  date: string; // raw sortable stamp: 'YYYY-MM-DD' or 'YYYY-MM-DDTHH-MM-SSZ'
  label: string; // human display, e.g. '2022-10-11'
  refs: number[]; // indices into PolicyDetail.blocks
}

export interface ChangeStat {
  date: string;
  label: string;
  added: number; // words added vs the previous version
  removed: number;
}

export interface PolicyDetail {
  slug: string;
  title: string;
  platform: Platform;
  blocks: BlockContent[]; // the dictionary; index is the id
  versions: VersionRef[];
  changes: ChangeStat[];
}

// ── Diff ────────────────────────────────────────────────────────────────
export type DiffKind = 'equal' | 'added' | 'removed' | 'changed';

export interface WordPart {
  value: string;
  added?: boolean;
  removed?: boolean;
}

export interface DiffRow {
  kind: DiffKind;
  a?: Block; // present unless kind === 'added'
  b?: Block; // present unless kind === 'removed'
  words?: WordPart[]; // inline word diff, present when kind === 'changed'
}
