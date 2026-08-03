import { base } from '$app/paths';
import type { PolicyManifest } from '$lib/types/policies';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ fetch }) => {
  const res = await fetch(`${base}/policies/manifest.json`);
  const manifest = (await res.json()) as PolicyManifest;
  return { manifest };
};
