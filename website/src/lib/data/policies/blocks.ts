import type { Block } from '../../types/policies';

// Splits policy markdown into heading/paragraph blocks. Handles ATX (`###`)
// and Setext (underlined with `===` / `---`) headings.

function djb2(s: string): string {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36);
}

function makeBlock(
  type: Block['type'],
  text: string,
  depth: number | undefined,
  index: number,
): Block {
  return { id: `${index}-${djb2(text)}`, type, depth, text };
}

export function splitBlocks(md: string): Block[] {
  const lines = md.replace(/\r\n/g, '\n').split('\n');
  const blocks: Block[] = [];
  let para: string[] = [];

  const flushParagraph = () => {
    if (!para.length) return;
    const text = para.join(' ').replace(/\s+/g, ' ').trim();
    if (text) blocks.push(makeBlock('paragraph', text, undefined, blocks.length));
    para = [];
  };

  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    const next = (lines[i + 1] ?? '').trim();

    if (trimmed === '') {
      flushParagraph();
      continue;
    }

    // Setext heading: a text line underlined by === (h1) or --- (h2)
    if (para.length === 0 && /^=+$/.test(next)) {
      blocks.push(makeBlock('heading', trimmed, 1, blocks.length));
      i++;
      continue;
    }
    if (para.length === 0 && /^-{2,}$/.test(next)) {
      blocks.push(makeBlock('heading', trimmed, 2, blocks.length));
      i++;
      continue;
    }

    // ATX heading: #{1,6} text
    const atx = /^(#{1,6})\s+(.*)$/.exec(trimmed);
    if (atx) {
      flushParagraph();
      blocks.push(makeBlock('heading', atx[2].trim(), atx[1].length, blocks.length));
      continue;
    }

    // Standalone rule / stray underline not consumed above → ignore
    if (/^(-{2,}|=+|\*{3,}|_{3,})$/.test(trimmed)) {
      flushParagraph();
      continue;
    }

    para.push(trimmed);
  }
  flushParagraph();
  return blocks;
}
