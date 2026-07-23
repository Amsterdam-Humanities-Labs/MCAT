import { readFileSync } from 'node:fs';
import type { PolicyManifest } from '$lib/types/policies';
import type { EntryGenerator } from './$types';

export const entries: EntryGenerator = () => {
  try {
    const manifest: PolicyManifest = JSON.parse(
      readFileSync('static/policies/manifest.json', 'utf8'),
    );
    return manifest.flatMap((g) =>
      g.policies.map((p) => {
        const [platform, policy] = p.slug.split('/');
        return { platform, policy };
      }),
    );
  } catch {
    return [];
  }
};
