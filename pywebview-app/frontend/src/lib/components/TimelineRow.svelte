<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import { formatTimestamp } from '$lib/utils/format';
  import { CaretUp, CaretDown } from 'phosphor-svelte';
  import TransitionBadge from './TransitionBadge.svelte';
  import StatusBadge from './StatusBadge.svelte';

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
    isAbandoned || isNoChange ? 'text-text-secondary' : 'text-text-secondary'
  );

  const TRANSITIONS = [
    { key: 'removed_to_live', from: 'removed', to: 'live' },
    { key: 'restricted_to_live', from: 'restricted', to: 'live' },
    { key: 'live_to_restricted', from: 'live', to: 'restricted' },
    { key: 'live_to_private', from: 'live', to: 'private' },
    { key: 'restricted_to_removed', from: 'restricted', to: 'removed' },
    { key: 'live_to_removed', from: 'live', to: 'removed' },
  ];

  const summary = $derived(run.changes_summary || {});
  const timestamp = $derived(formatTimestamp(run.started_at));
</script>

<button
  type="button"
  class={cn("w-full flex items-center gap-3 px-4 py-2.5 text-left cursor-ns-resize hover:bg-interactive-hover transition-colors text-base bg-bg-primary", isSelected ? 'shadow-[0_-4px_8px_-2px_rgba(0,0,0,0.25)] hover:bg-interactive-row' : 'border-b border-solid border-border-light', className)}
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
    <span class="text-text-secondary">Abandoned</span>
  {:else if run.is_baseline}
    <span class="text-text-primary shrink-0">Baseline</span>
    {#if run.status_summary}
      <span class="flex items-center gap-1.5">
        {#if run.status_summary.live > 0}
          <StatusBadge status="live" count={run.status_summary.live} />
        {/if}
        {#if run.status_summary.restricted > 0}
          <StatusBadge status="restricted" count={run.status_summary.restricted} />
        {/if}
        {#if run.status_summary.removed > 0}
          <StatusBadge status="removed" count={run.status_summary.removed} />
        {/if}
      </span>
    {/if}
  {:else}
    {#if run.changes_count > 0}
      <span class="text-text-primary font-bold shrink-0">{run.changes_count} changes</span>
    {:else}
      <span class="text-text-primary shrink-0">No changes</span>
    {/if}

    <span class="flex items-center gap-1.5">
      {#each TRANSITIONS as t}
        {#if summary[t.key]}
          <TransitionBadge from={t.from} to={t.to} count={summary[t.key]} />
        {/if}
      {/each}
    </span>
  {/if}

  <span class="ml-auto text-text-secondary shrink-0">
    {#if isSelected}
      <CaretUp size={14} weight="bold" />
    {:else}
      <CaretDown size={14} weight="bold" />
    {/if}
  </span>
</button>
