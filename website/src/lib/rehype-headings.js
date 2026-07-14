// Collects the page's h2/h3 headings (after rehype-slug has assigned ids) into
// frontmatter as `headings`, so it surfaces on the compiled module's `metadata`.
// Markdown headings are top-level nodes, so a flat scan of the root is enough.

/**
 * @typedef {Object} HastNode
 * @property {string} type
 * @property {string} [value]
 * @property {string} [tagName]
 * @property {Record<string, unknown>} [properties]
 * @property {HastNode[]} [children]
 */

/**
 * @param {HastNode} node
 * @returns {string}
 */
function textOf(node) {
  if (node.type === 'text') return node.value ?? '';
  if (node.children) return node.children.map(textOf).join('');
  return '';
}

export function rehypeHeadings() {
  /**
   * @param {HastNode} tree
   * @param {{ data: Record<string, unknown> }} file
   */
  return (tree, file) => {
    const headings = [];
    for (const node of tree.children ?? []) {
      if (
        node.type === 'element' &&
        node.tagName &&
        /^h[2-3]$/.test(node.tagName) &&
        node.properties?.id
      ) {
        headings.push({
          depth: Number(node.tagName[1]),
          text: textOf(node),
          id: String(node.properties.id),
        });
      }
    }
    file.data.fm = { ...(file.data.fm ?? {}), headings };
  };
}
