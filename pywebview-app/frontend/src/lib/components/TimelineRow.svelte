<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import { formatTimestamp } from '$lib/utils/format';
  import { colors } from '$lib/theme';
  import { CaretUp, CaretDown } from 'phosphor-svelte';

  interface Props {
    run: Run;
    index: number;
    isSelected: boolean;
    onClick?: () => void;
    class?: string;
  }

  let { run, index, isSelected, onClick, class: className }: Props = $props();

  const isAbandoned = $derived(run.status === 'abandoned');
  const isNoChange = $derived(!run.is_baseline && run.changes_count === 0 && !isAbandoned);
  const dotSize = $derived(isAbandoned || isNoChange ? 'text-[7px]' : 'text-[10px]');
  const dotColor = $derived(
    isAbandoned ? 'text-text-muted opacity-50' : isNoChange ? 'text-text-muted' : 'text-text-secondary'
  );

  const TRANSITION_COLUMNS = [
    { key: 'removed_to_live', label: 'Removed → Live', color: colors.status.live },
    { key: 'restricted_to_live', label: 'Restricted → Live', color: colors.status.live },
    { key: 'live_to_restricted', label: 'Live → Restricted', color: colors.status.restricted },
    { key: 'live_to_private', label: 'Live → Private', color: colors.status.restricted },
    { key: 'restricted_to_removed', label: 'Restricted → Removed', color: colors.status.removed },
    { key: 'live_to_removed', label: 'Live → Removed', color: colors.status.removed },
  ];

  const summary = $derived(run.changes_summary || {});
  const timestamp = $derived(formatTimestamp(run.started_at));
</script>

<button
  type="button"
  class={cn("w-full flex items-center gap-1 px-4 py-2.5 text-left cursor-ns-resize hover:bg-interactive-hover transition-colors text-sm", isSelected ? 'bg-bg-detail' : 'border-b border-solid border-border-light', className)}
  onclick={onClick}
>
  <!-- Dot -->
  <span class="relative inline-flex items-center justify-center w-5 h-5 shrink-0">
    {#if isSelected}
      <span class="absolute inset-0 rounded-full border-2 border-timeline-selection"></span>
    {/if}
    <span class="{dotSize} {dotColor} leading-none">&#x25CF;</span>
  </span>

  <!-- Date -->
  <span class="text-text-secondary shrink-0">{timestamp}</span>

  {#if isAbandoned}
    <span class="text-text-muted">Abandoned</span>
  {:else if run.is_baseline}
    <span class="text-text-primary shrink-0">Baseline</span>
    {#if run.status_summary}
      {#if run.status_summary.live > 0}
        <span style="color: {colors.status.live}">{run.status_summary.live} Live</span>
      {/if}
      {#if run.status_summary.restricted > 0}
        <span style="color: {colors.status.restricted}">{run.status_summary.restricted} Restricted</span>
      {/if}
      {#if run.status_summary.removed > 0}
        <span style="color: {colors.status.removed}">{run.status_summary.removed} Removed</span>
      {/if}
    {/if}
  {:else}
    <span class="text-text-primary shrink-0">{run.changes_count > 0 ? `${run.changes_count} changes` : 'No changes'}</span>

    <span class="flex items-center gap-3">
      {#each TRANSITION_COLUMNS as col}
        {#if summary[col.key]}
          <span style="color: {col.color}">{summary[col.key]} {col.label}</span>
        {/if}
      {/each}
    </span>
  {/if}

  <span class="ml-auto text-text-muted shrink-0">
    {#if isSelected}
      <CaretUp size={14} weight="bold" />
    {:else}
      <CaretDown size={14} weight="bold" />
    {/if}
  </span>
</button>
