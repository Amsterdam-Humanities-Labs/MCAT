import type { PolicyDetail } from '../../types/policies';

const cache = new Map<string, Promise<PolicyDetail>>();

// Fetches one policy's data, cached per slug. Pass SvelteKit's `fetch` when
// calling from a load.
export function loadPolicy(slug: string, fetcher: typeof fetch = fetch): Promise<PolicyDetail> {
  let pending = cache.get(slug);
  if (!pending) {
    pending = fetcher(`/policies/${slug}.json`).then((res) => {
      if (!res.ok) throw new Error(`Failed to load policy "${slug}": ${res.status}`);
      return res.json() as Promise<PolicyDetail>;
    });
    cache.set(slug, pending);
  }
  return pending;
}
