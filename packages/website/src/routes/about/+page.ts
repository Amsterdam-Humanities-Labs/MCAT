import { metadata } from '$content/about.md';
import type { PageMeta } from '$lib/seo';
import type { PageLoad } from './$types';

export const load: PageLoad = () => {
  const m = metadata as { title?: string; description?: string };
  return {
    meta: { title: m.title, description: m.description } satisfies PageMeta,
  };
};
