interface DocModule {
  default: import('svelte').Component;
  metadata: Record<string, unknown>;
}

// Eagerly bundle every doc so both the loader (metadata) and the page (component)
// can look one up by slug.
const modules = import.meta.glob<DocModule>('/src/content/docs/*.md', { eager: true });

export const docs: Record<string, DocModule> = {};
for (const [path, mod] of Object.entries(modules)) {
  const slug = path.split('/').pop()!.replace(/\.md$/, '');
  docs[slug] = mod;
}
