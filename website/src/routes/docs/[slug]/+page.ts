import { error } from '@sveltejs/kit';
import { docs } from '$lib/docs';
import type { PageMeta } from '$lib/seo';
import type { TocEntry } from '$lib/scrollSpy.svelte';
import type { EntryGenerator, PageLoad } from './$types';

export const entries: EntryGenerator = () =>
  Object.keys(docs).map((slug) => ({ slug }));

export const load: PageLoad = ({ params }) => {
  const doc = docs[params.slug];
  if (!doc) throw error(404, 'Doc not found');

  const m = doc.metadata as {
    title?: string;
    description?: string;
    headings?: TocEntry[];
    toc?: boolean;
  };

  return {
    slug: params.slug,
    meta: { title: m.title, description: m.description } satisfies PageMeta,
    headings: m.headings ?? [],
    showToc: m.toc !== false,
  };
};
