import { error } from '@sveltejs/kit';
import type { PageMeta } from '$lib/seo';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, parent }) => {
  const { manifest } = await parent();
  const slug = `${params.platform}/${params.policy}`;
  const group = manifest.find((g) => g.id === params.platform);
  const policy = group?.policies.find((p) => p.slug === slug);
  if (!group || !policy) throw error(404, 'Policy not found');

  return {
    slug,
    title: policy.title,
    platformLabel: group.label,
    meta: {
      title: `${policy.title} — ${group.label} — MCAT`,
      description: `Compare versions of ${group.label}'s ${policy.title}.`,
    } satisfies PageMeta,
  };
};
