import { diffArrays, diffWords } from 'diff';
import type { Block, DiffRow, WordPart } from '../../types/policies';

// Paragraph-matched diff: aligns whole blocks, then word-diffs changed blocks.

const key = (b: Block) => b.text.replace(/\s+/g, ' ').trim();

const wordCount = (s: string) => (s.trim() ? s.trim().split(/\s+/).length : 0);

function wordDiff(a: string, b: string): WordPart[] {
  return diffWords(a, b).map((p) => ({
    value: p.value,
    added: p.added || undefined,
    removed: p.removed || undefined,
  }));
}

export function diffVersions(a: Block[], b: Block[]): DiffRow[] {
  const parts = diffArrays(a.map(key), b.map(key));

  // Re-attach the actual blocks to each part.
  type Seg = { type: 'equal' | 'removed' | 'added'; blocks: Block[] };
  const segs: Seg[] = [];
  let ai = 0;
  let bi = 0;
  for (const p of parts) {
    const n = p.value.length;
    if (!p.added && !p.removed) {
      segs.push({ type: 'equal', blocks: a.slice(ai, ai + n) });
      ai += n;
      bi += n;
    } else if (p.removed) {
      segs.push({ type: 'removed', blocks: a.slice(ai, ai + n) });
      ai += n;
    } else {
      segs.push({ type: 'added', blocks: b.slice(bi, bi + n) });
      bi += n;
    }
  }

  const rows: DiffRow[] = [];
  for (let s = 0; s < segs.length; s++) {
    const seg = segs[s];
    if (seg.type === 'equal') {
      for (const blk of seg.blocks) rows.push({ kind: 'equal', a: blk, b: blk });
    } else if (seg.type === 'removed') {
      const nextSeg = segs[s + 1];
      // A removed run immediately followed by an added run = an edit → pair them.
      if (nextSeg?.type === 'added') {
        const rem = seg.blocks;
        const add = nextSeg.blocks;
        const paired = Math.min(rem.length, add.length);
        for (let k = 0; k < paired; k++) {
          rows.push({ kind: 'changed', a: rem[k], b: add[k], words: wordDiff(rem[k].text, add[k].text) });
        }
        for (let k = paired; k < rem.length; k++) rows.push({ kind: 'removed', a: rem[k] });
        for (let k = paired; k < add.length; k++) rows.push({ kind: 'added', b: add[k] });
        s++; // consumed nextSeg
      } else {
        for (const blk of seg.blocks) rows.push({ kind: 'removed', a: blk });
      }
    } else {
      for (const blk of seg.blocks) rows.push({ kind: 'added', b: blk });
    }
  }
  return rows;
}

export function countWords(rows: DiffRow[]): { added: number; removed: number } {
  let added = 0;
  let removed = 0;
  for (const r of rows) {
    if (r.kind === 'added') added += wordCount(r.b!.text);
    else if (r.kind === 'removed') removed += wordCount(r.a!.text);
    else if (r.kind === 'changed' && r.words) {
      for (const w of r.words) {
        if (w.added) added += wordCount(w.value);
        if (w.removed) removed += wordCount(w.value);
      }
    }
  }
  return { added, removed };
}
