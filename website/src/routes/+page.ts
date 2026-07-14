import { metadata } from '$content/home.md';
import type { PageMeta } from '$lib/seo';

interface HomeContent extends PageMeta {
  headline: string;
  tagline: string;
}

export const load = () => {
  const { headline, tagline, ...meta } = metadata as unknown as HomeContent;
  return { headline, tagline, meta: meta as PageMeta };
};
