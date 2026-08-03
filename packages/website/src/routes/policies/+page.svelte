<script lang="ts">
  import { page } from '$app/state';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { SelectGrid, SelectField } from '@mcat/shared-ui';
  import H1 from '$components/H1.svelte';
  import P from '$components/P.svelte';
  import DiffPanes from '$components/policies/DiffPanes.svelte';
  import { loadPolicy } from '$lib/data/policies/client';
  import { getVersion } from '$lib/data/policies/hydrate';
  import { diffVersions } from '$lib/data/policies/diff';
  import type { PolicyDetail } from '$lib/types/policies';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  // The query string drives the comparison; prerender sees an empty one.
  const query = $derived(browser ? page.url.searchParams : new URLSearchParams());
  const slug = $derived(query.get('policy') ?? '');

  // Platform mirrors the chosen policy; before one is picked it's a local filter.
  let platformFilter = $state('');
  const platform = $derived(slug ? slug.split('/')[0] : platformFilter);

  let detail = $state<PolicyDetail | null>(null);
  $effect(() => {
    const s = slug;
    detail = null;
    if (!s) return;
    loadPolicy(s).then((loaded) => {
      if (slug === s) detail = loaded;
    });
  });

  const versions = $derived(detail?.versions ?? []);
  const dateA = $derived(query.get('a') || versions[0]?.date || '');
  const dateB = $derived(query.get('b') || versions.at(-1)?.date || '');

  const platformOptions = $derived(data.manifest.map((g) => ({ value: g.id, label: g.label })));
  const policyOptions = $derived(
    (data.manifest.find((g) => g.id === platform)?.policies ?? []).map((p) => ({
      value: p.slug,
      label: `${p.title} · ${p.versionCount} versions`,
    })),
  );
  const versionOptions = $derived(versions.map((v) => ({ value: v.date, label: v.label })));
  const labelOf = (date: string) => versions.find((v) => v.date === date)?.label ?? '';

  function updateUrl(next: URLSearchParams) {
    goto(next.size ? `?${next}` : '?', { replaceState: true, keepFocus: true, noScroll: true });
  }

  function selectPlatform(id: string) {
    platformFilter = id;
    if (slug) updateUrl(new URLSearchParams());
  }

  function selectPolicy(next: string) {
    const params = new URLSearchParams();
    if (next) params.set('policy', next);
    updateUrl(params);
  }

  function setDate(which: 'a' | 'b', date: string) {
    const params = new URLSearchParams(query);
    params.set(which, date);
    updateUrl(params);
  }

  const rows = $derived.by(() =>
    detail && dateA && dateB
      ? diffVersions(getVersion(detail, dateA), getVersion(detail, dateB))
      : [],
  );
</script>

<H1>Policies</H1>
<P class="mt-3">Compare how a platform's policy changed between two dates.</P>

<SelectGrid class="mt-6">
  <SelectField
    label="Platform"
    options={platformOptions}
    value={platform}
    placeholder="Select a platform…"
    onchange={selectPlatform}
  />
  <SelectField
    label="Policy"
    options={policyOptions}
    value={slug}
    disabled={!platform}
    placeholder="Select a policy…"
    onchange={selectPolicy}
  />
</SelectGrid>

{#if detail}
  <SelectGrid class="mt-6">
    <SelectField
      label="Compare from"
      options={versionOptions}
      value={dateA}
      disabled={!versionOptions.length}
      onchange={(d) => setDate('a', d)}
    />
    <SelectField
      label="To"
      options={versionOptions}
      value={dateB}
      disabled={!versionOptions.length}
      onchange={(d) => setDate('b', d)}
    />
  </SelectGrid>
{/if}

{#if rows.length}
  <DiffPanes {rows} labelA={labelOf(dateA)} labelB={labelOf(dateB)} class="mt-6" />
{:else if slug && !detail}
  <P class="mt-6 text-text-secondary">Loading policy…</P>
{/if}
