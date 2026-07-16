<script lang="ts">
  import H1 from '$components/H1.svelte';
  import P from '$components/P.svelte';
  import PolicyGate from '$components/policies/PolicyGate.svelte';
  import DiffPanes from '$components/policies/DiffPanes.svelte';
  import { loadPolicy } from '$lib/data/policies/client';
  import { getVersion } from '$lib/data/policies/hydrate';
  import { diffVersions } from '$lib/data/policies/diff';
  import type { PolicyDetail } from '$lib/types/policies';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  let platform = $state('');
  let policySlug = $state('');
  let detail = $state<PolicyDetail | null>(null);
  let loading = $state(false);
  let dateA = $state('');
  let dateB = $state('');

  function reset() {
    detail = null;
    dateA = '';
    dateB = '';
  }

  function selectPlatform(id: string) {
    platform = id;
    policySlug = '';
    reset();
  }

  async function selectPolicy(slug: string) {
    policySlug = slug;
    reset();
    if (!slug) return;

    loading = true;
    try {
      const loaded = await loadPolicy(slug);
      if (policySlug !== slug) return; // selection moved on while loading
      detail = loaded;
      dateA = loaded.versions[0]?.date ?? '';
      dateB = loaded.versions.at(-1)?.date ?? '';
    } finally {
      loading = false;
    }
  }

  const versions = $derived(
    detail?.versions.map((v) => ({ date: v.date, label: v.label })) ?? [],
  );
  const labelOf = (date: string) => detail?.versions.find((v) => v.date === date)?.label ?? '';

  const rows = $derived.by(() =>
    detail && dateA && dateB
      ? diffVersions(getVersion(detail, dateA), getVersion(detail, dateB))
      : [],
  );
</script>

<H1>Policies</H1>
<P class="mt-3">Compare how a platform's policy changed between two dates.</P>

<PolicyGate
  manifest={data.manifest}
  {platform}
  {policySlug}
  {versions}
  {dateA}
  {dateB}
  {loading}
  onPlatform={selectPlatform}
  onPolicy={selectPolicy}
  onDateA={(d) => (dateA = d)}
  onDateB={(d) => (dateB = d)}
  class="mt-6"
/>

{#if rows.length}
  <DiffPanes {rows} labelA={labelOf(dateA)} labelB={labelOf(dateB)} class="mt-6" />
{:else if loading}
  <P class="mt-6 text-text-secondary">Loading policy…</P>
{/if}
