<script lang="ts">
  import { page } from '$app/state';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { SelectGrid, SelectField, Link } from '@mcat/shared-ui';
  import H1 from '$components/H1.svelte';
  import P from '$components/P.svelte';
  import DiffPanes from '$components/policies/DiffPanes.svelte';
  import { loadPolicy } from '$lib/data/policies/client';
  import { getVersion } from '$lib/data/policies/hydrate';
  import { diffVersions } from '$lib/data/policies/diff';
  import type { PolicyDetail } from '$lib/types/policies';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  let detail = $state<PolicyDetail | null>(null);
  $effect(() => {
    const slug = data.slug;
    detail = null;
    loadPolicy(slug).then((loaded) => {
      if (data.slug === slug) detail = loaded;
    });
  });

  const versions = $derived(detail?.versions ?? []);
  const query = $derived(browser ? page.url.searchParams : new URLSearchParams());
  const dateA = $derived(query.get('a') ?? versions[0]?.date ?? '');
  const dateB = $derived(query.get('b') ?? versions.at(-1)?.date ?? '');

  const versionOptions = $derived(versions.map((v) => ({ value: v.date, label: v.label })));
  const labelOf = (date: string) => versions.find((v) => v.date === date)?.label ?? '';

  function setDate(which: 'a' | 'b', date: string) {
    const params = new URLSearchParams(page.url.searchParams);
    params.set(which, date);
    goto(`?${params}`, { replaceState: true, keepFocus: true, noScroll: true });
  }

  const rows = $derived.by(() =>
    detail && dateA && dateB
      ? diffVersions(getVersion(detail, dateA), getVersion(detail, dateB))
      : [],
  );
</script>

<Link href="/policies">← Compare a different policy</Link>
<H1 class="mt-2">{data.title}</H1>
<P class="mt-2 text-text-secondary">{data.platformLabel}</P>

<SelectGrid class="mt-6">
  <SelectField
    label="Compare from"
    options={versionOptions}
    value={dateA}
    placeholder="Select a version…"
    disabled={!versionOptions.length}
    onchange={(d) => setDate('a', d)}
  />
  <SelectField
    label="To"
    options={versionOptions}
    value={dateB}
    placeholder="Select a version…"
    disabled={!versionOptions.length}
    onchange={(d) => setDate('b', d)}
  />
</SelectGrid>

{#if rows.length}
  <DiffPanes {rows} labelA={labelOf(dateA)} labelB={labelOf(dateB)} class="mt-6" />
{:else if !detail}
  <P class="mt-6 text-text-secondary">Loading policy…</P>
{/if}
