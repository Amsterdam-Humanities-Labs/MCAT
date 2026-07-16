<script lang="ts">
  import { SelectField, cn } from '@mcat/shared-ui';
  import type { PolicyManifest } from '$lib/types/policies';

  interface Props {
    manifest: PolicyManifest;
    platform: string;
    policySlug: string;
    versions: { date: string; label: string }[];
    dateA: string;
    dateB: string;
    loading?: boolean;
    class?: string;
    onPlatform: (id: string) => void;
    onPolicy: (slug: string) => void;
    onDateA: (date: string) => void;
    onDateB: (date: string) => void;
  }

  let {
    manifest,
    platform,
    policySlug,
    versions,
    dateA,
    dateB,
    loading = false,
    class: className,
    onPlatform,
    onPolicy,
    onDateA,
    onDateB,
  }: Props = $props();

  const platformOptions = $derived(manifest.map((g) => ({ value: g.id, label: g.label })));

  const policyOptions = $derived(
    (manifest.find((g) => g.id === platform)?.policies ?? []).map((p) => ({
      value: p.slug,
      label: `${p.title} · ${p.versionCount} versions`,
    })),
  );

  const versionOptions = $derived(versions.map((v) => ({ value: v.date, label: v.label })));
  const versionPlaceholder = $derived(loading ? 'Loading…' : 'Select a version…');
</script>

<div class={cn('grid gap-4 md:grid-cols-2', className)}>
  <SelectField
    label="Platform"
    options={platformOptions}
    value={platform}
    placeholder="Select a platform…"
    onchange={onPlatform}
  />
  <SelectField
    label="Policy"
    options={policyOptions}
    value={policySlug}
    placeholder="Select a policy…"
    disabled={!platform}
    onchange={onPolicy}
  />
  <SelectField
    label="Compare from"
    options={versionOptions}
    value={dateA}
    placeholder={versionPlaceholder}
    disabled={!versionOptions.length}
    onchange={onDateA}
  />
  <SelectField
    label="To"
    options={versionOptions}
    value={dateB}
    placeholder={versionPlaceholder}
    disabled={!versionOptions.length}
    onchange={onDateB}
  />
</div>
