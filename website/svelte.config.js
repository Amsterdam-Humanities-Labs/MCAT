import { fileURLToPath } from 'node:url';
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { mdsvex } from 'mdsvex';
import rehypeSlug from 'rehype-slug';
import { rehypeHeadings } from './src/lib/rehype-headings.js';

// Absolute path: mdsvex both reads this file and injects it as an import into
// every .md, so a relative path can't satisfy both from nested content files.
const mdsvexLayout = fileURLToPath(new URL('./src/lib/mdsvex/Layout.svelte', import.meta.url));

/** @type {import('@sveltejs/kit').Config} */
const config = {
  extensions: ['.svelte', '.md'],
  preprocess: [
    vitePreprocess(),
    mdsvex({
      extensions: ['.md'],
      // Maps markdown elements (h1, p, a, …) to our components.
      layout: { _: mdsvexLayout },
      // rehype-slug gives every heading an id; rehypeHeadings collects them into metadata.
      rehypePlugins: [rehypeSlug, rehypeHeadings],
    }),
  ],
  kit: {
    adapter: adapter(),
    alias: {
      $components: 'src/lib/components',
      $content: 'src/content',
    },
  },
};

export default config;
