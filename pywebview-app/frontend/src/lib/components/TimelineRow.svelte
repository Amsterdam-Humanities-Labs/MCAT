<script lang="ts">
  import type { Run } from '$types/project';
  import { formatTimestamp } from '$lib/utils/format';
  import { colors } from '$lib/theme';

  interface Props {
    run: Run;
    index: number;
    isSelected: boolean;
    onClick?: () => void;
  }

  let { run, index, isSelected, onClick }: Props = $props();

  const isAbandoned = $derived(run.status === 'abandoned');
  const isNoChange = $derived(!run.is_baseline && run.changes_count === 0 && !isAbandoned);
  const dotSize = $derived(isAbandoned || isNoChange ? 'text-[7px]' : 'text-[10px]');
  const dotColor = $derived(
    isAbandoned ? 'text-[#D9CBAE] opacity-50' : isNoChange ? 'text-[#C4AD8A]' : 'text-[#6B4C2A]'
  );

  function parseTransitions(summary: Record<string, number>): Array<{ label: string; color: string }> {
    const result: Array<{ label: string; count: number; color: string }> = [];
    for (const [key, count] of Object.entries(summary)) {
      const parts = key.split('_to_');
      if (parts.length === 2) {
        const from = shortName(parts[0]);
        const to = shortName(parts[1]);
        result.push({ label: `${count} ${from} \u2192 ${to}`, count, color: transitionColor(parts[1]) });
      }
    }
    result.sort((a, b) => b.count - a.count);
    return result;
  }

  function shortName(s: string): string {
    const map: Record<string, string> = { live: 'Live', removed: 'Removed', restricted: 'Rst', error: 'Error', private: 'Private' };
    return map[s] || s.charAt(0).toUpperCase() + s.slice(1);
  }

  function transitionColor(toStatus: string): string {
    switch (toStatus) {
      case 'removed': return colors.status.removed;
      case 'live': return colors.status.live;
      case 'restricted': case 'private': return colors.status.restricted;
      default: return colors.text.hint;
    }
  }

  const transitions = $derived(parseTransitions(run.changes_summary || {}));
  const visibleTransitions = $derived(transitions.slice(0, 3));
  const extraCount = $derived(transitions.length - visibleTransitions.length);
  const timestamp = $derived(formatTimestamp(run.started_at));
</script>

<button
  type="button"
  class="w-full flex items-center gap-3 px-4 py-2.5 text-left cursor-pointer bg-transparent border-none border-b border-border-light hover:bg-hover transition-colors text-sm"
  class:bg-bg-primary={isSelected}
  onclick={onClick}
>
  <!-- Dot -->
  <span class="relative inline-flex items-center justify-center w-5 h-5 shrink-0">
    {#if isSelected}
      <span class="absolute inset-0 rounded-full border-2 border-[#6B4C2A]/35"></span>
    {/if}
    <span class="{dotSize} {dotColor} leading-none">&#x25CF;</span>
  </span>

  <!-- Content -->
  <span class="flex items-center gap-2 flex-wrap min-w-0">
    <span class="text-text-secondary shrink-0">{timestamp}</span>

    {#if isAbandoned}
      <span class="text-text-muted">·</span>
      <span class="text-text-muted">Incomplete</span>
    {:else if run.is_baseline}
      <span class="text-text-muted">·</span>
      <span class="font-semibold text-text-primary">Baseline</span>
      <span class="text-text-muted">·</span>
      <span class="text-text-secondary">{run.total_checked.toLocaleString()} URLs</span>
      {#if run.status_summary}
        {#if run.status_summary.live > 0}
          <span class="text-text-muted">·</span>
          <span style="color: {colors.status.live}">{run.status_summary.live} Live</span>
        {/if}
        {#if run.status_summary.removed > 0}
          <span class="text-text-muted">·</span>
          <span style="color: {colors.status.removed}">{run.status_summary.removed} Removed</span>
        {/if}
        {#if run.status_summary.restricted > 0}
          <span class="text-text-muted">·</span>
          <span style="color: {colors.status.restricted}">{run.status_summary.restricted} Restricted</span>
        {/if}
      {/if}
    {:else if run.changes_count > 0}
      <span class="text-text-muted">·</span>
      <span class="font-semibold text-text-primary">{run.changes_count} changes</span>
      {#each visibleTransitions as t}
        <span class="text-text-muted">·</span>
        <span style="color: {t.color}">{t.label}</span>
      {/each}
      {#if extraCount > 0}
        <span class="text-text-muted">·</span>
        <span class="text-text-muted">+{extraCount} more</span>
      {/if}
    {:else}
      <span class="text-text-muted">·</span>
      <span class="text-text-muted">No changes</span>
    {/if}
  </span>
</button>
