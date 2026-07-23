<script lang="ts">
  import { goto } from '$app/navigation';
  import { SelectGrid, SelectField } from '@mcat/shared-ui';
  import H1 from '$components/H1.svelte';
  import P from '$components/P.svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  let platform = $state('');

  const platformOptions = $derived(data.manifest.map((g) => ({ value: g.id, label: g.label })));
  const policyOptions = $derived(
    (data.manifest.find((g) => g.id === platform)?.policies ?? []).map((p) => ({
      value: p.slug,
      label: `${p.title} · ${p.versionCount} versions`,
    })),
  );

  function selectPolicy(slug: string) {
    if (slug) goto(`/policies/${slug}`);
  }
</script>

<H1>Policies</H1>
<P class="mt-3">Compare how a platform's policy changed between two dates.</P>

<SelectGrid class="mt-6">
  <SelectField
    label="Platform"
    options={platformOptions}
    value={platform}
    placeholder="Select a platform…"
    onchange={(id) => (platform = id)}
  />
  <SelectField
    label="Policy"
    options={policyOptions}
    value=""
    disabled={!platform}
    placeholder="Select a policy…"
    onchange={selectPolicy}
  />
</SelectGrid>
