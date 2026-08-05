<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import { STATUS_META } from '@mcat/shared-ui';
  import { normalizeRows, buildResultColumns } from '$lib/utils/resultTable';
  import DataTable from './DataTable.svelte';

  interface Props {
    run: Run;
    columns: string[];
    rows: Record<string, unknown>[];
    loading: boolean;
    error: string | null;
    onOpenScreenshot?: (path: string) => void;
    class?: string;
  }

  let { run, columns, rows, loading, error, onOpenScreenshot, class: className }: Props = $props();

  const displayRows = $derived(normalizeRows(rows));
  const tableColumns = $derived(buildResultColumns(columns, { statusType: 'transition', internal: ['previous_status'] }));
</script>

<div class={cn(className)}>
{#if loading}
  <p class="text-text-secondary text-base py-4">Loading...</p>
{:else if error}
  <p class="text-status-removed text-base py-4">{error}</p>
{:else if run.is_baseline}
  <div class="py-3 text-base">
    <p class="text-text-secondary mb-2">Baseline run — initial status of all URLs:</p>
    <div class="flex items-center gap-3">
      {#each STATUS_META as m (m.key)}
        {#if run.status_summary?.[m.summaryKey]}
          <span class={m.text}>{run.status_summary[m.summaryKey]} {m.label}</span>
        {/if}
      {/each}
    </div>
  </div>
{:else}
  <DataTable columns={tableColumns} rows={displayRows} emptyMessage="No changes detected" onScreenshotClick={onOpenScreenshot} />
{/if}
</div>
