import type { PageMeta } from '$lib/seo';
import type { PageLoad } from './$types';

export const load: PageLoad = () => ({
  meta: {
    title: 'Policies — MCAT',
    description: 'Compare how platform moderation policies changed between two dates.',
  } satisfies PageMeta,
});
