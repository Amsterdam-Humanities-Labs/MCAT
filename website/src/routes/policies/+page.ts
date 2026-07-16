import type { PolicyManifest } from '$lib/types/policies';
import type { PageMeta } from '$lib/seo';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
  const res = await fetch('/policies/manifest.json');
  const manifest = (await res.json()) as PolicyManifest;

  return {
    manifest,
    meta: {
      title: 'Policies — MCAT',
      description: 'Compare how platform moderation policies changed between two dates.',
    } satisfies PageMeta,
  };
};
