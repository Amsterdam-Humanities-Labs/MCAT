import { metadata } from '$content/docs.md';
import type { PageMeta } from '$lib/seo';
import type { TocEntry } from '$lib/scrollSpy.svelte';
import type { PageLoad } from './$types';

export const load: PageLoad = () => {
  const m = metadata as {
    title?: string;
    description?: string;
    headings?: TocEntry[];
    toc?: boolean;
  };

  return {
    meta: { title: m.title, description: m.description } satisfies PageMeta,
    headings: m.headings ?? [],
    showToc: m.toc !== false,
  };
};
