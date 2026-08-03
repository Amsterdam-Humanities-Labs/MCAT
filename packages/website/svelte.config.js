import { fileURLToPath } from 'node:url';
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { mdsvex } from 'mdsvex';
import rehypeSlug from 'rehype-slug';
import { headingsScanner } from './src/lib/utils/headings-scanner.js';

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
      // rehype-slug gives every heading an id; headingsScanner collects them into metadata.
      rehypePlugins: [rehypeSlug, headingsScanner],
    }),
  ],
  kit: {
    adapter: adapter(),
    paths: {
      base: process.env.BASE_PATH ?? '',
    },
    alias: {
      $components: 'src/lib/components',
      $content: 'src/content',
    },
  },
};

export default config;
