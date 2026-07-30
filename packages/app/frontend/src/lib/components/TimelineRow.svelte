<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import { formatTimestamp } from '$lib/utils/format';
  import { statusOrder, STATUS_META } from '$lib/status';
  import { CaretUp, CaretDown, CheckCircleIcon, CircleDashedIcon } from 'phosphor-svelte';
  import TransitionBadge from './TransitionBadge.svelte';
  import StatusBadge from './StatusBadge.svelte';

  interface Props {
    run: Run;
    isSelected: boolean;
    onClick?: () => void;
    class?: string;
  }

  let { run, isSelected, onClick, class: className }: Props = $props();

  const isAbandoned = $derived(run.status === 'abandoned');
  const dotColor = 'text-text-secondary';

  const summary = $derived(run.changes_summary || {});
  const timestamp = $derived(formatTimestamp(run.started_at));

  // Derive transitions from summary keys like "live_to_removed"
  const transitions = $derived.by(() => {
    const entries = Object.entries(summary)
      .map(([key, count]) => {
        const [from, to] = key.split('_to_');
        return { key, from, to, count: count as number };
      })
      .filter((t) => t.from && t.to && t.count > 0);

    entries.sort((a, b) => {
      const aToLive = a.to === 'live' ? 0 : 1;
      const bToLive = b.to === 'live' ? 0 : 1;
      if (aToLive !== bToLive) return aToLive - bToLive;
      const aWeight = statusOrder(a.to) - statusOrder(a.from);
      const bWeight = statusOrder(b.to) - statusOrder(b.from);
      return aWeight - bWeight;
    });

    return entries;
  });
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
    {#if isAbandoned}
      <CircleDashedIcon size={16} class={dotColor} />
    {:else}
      <CheckCircleIcon size={16}  class={dotColor} />
    {/if}
  </span>

  <!-- Date -->
  <span class="text-text-secondary shrink-0">{timestamp}</span>

  {#if isAbandoned}
    <span class="text-text-secondary">Abandoned</span>
  {:else if run.is_baseline}
    <span class="text-text-primary shrink-0">Baseline</span>
    {#if run.status_summary}
      <span class="flex items-center gap-1.5">
        {#each STATUS_META as m (m.key)}
          {#if run.status_summary[m.summaryKey] > 0}
            <StatusBadge status={m.key} count={run.status_summary[m.summaryKey]} />
          {/if}
        {/each}
      </span>
    {/if}
  {:else}
    {#if run.changes_count > 0}
      <span class="text-text-primary font-semibold shrink-0">{run.changes_count} changes</span>
    {:else}
      <span class="text-text-primary shrink-0">No changes</span>
    {/if}

    <span class="flex items-center gap-1.5">
      {#each transitions as t (t.key)}
        <TransitionBadge from={t.from} to={t.to} count={t.count} />
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
