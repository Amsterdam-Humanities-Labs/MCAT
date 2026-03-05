<script lang="ts">
  import type { Run } from '$types/project';
  import { formatTimestamp } from '$lib/utils/format';
  import { colors } from '$lib/theme';

  interface Props {
    run: Run;
  }

  let { run }: Props = $props();

  const timestamp = $derived(formatTimestamp(run.startedAt));

  // Parse changes_summary keys like "live_to_removed" into display format
  function parseTransitions(summary: Record<string, number>): Array<{ label: string; count: number; color: string }> {
    const result: Array<{ label: string; count: number; color: string }> = [];
    for (const [key, count] of Object.entries(summary)) {
      const parts = key.split('_to_');
      if (parts.length === 2) {
        const from = capitalize(parts[0]);
        const to = capitalize(parts[1]);
        result.push({
          label: `${count} ${from} \u2192 ${to}`,
          count,
          color: getTransitionColor(parts[1]),
        });
      }
    }
    return result.sort((a, b) => b.count - a.count);
  }

  function capitalize(s: string): string {
    // "age-restricted" -> "Rst" etc. Keep short.
    const shortMap: Record<string, string> = {
      'live': 'Live',
      'removed': 'Removed',
      'restricted': 'Rst',
      'error': 'Error',
      'private': 'Private',
    };
    return shortMap[s] || s.charAt(0).toUpperCase() + s.slice(1);
  }

  function getTransitionColor(toStatus: string): string {
    switch (toStatus) {
      case 'removed': return colors.status.removed;
      case 'live': return colors.status.live;
      case 'restricted':
      case 'private': return colors.status.restricted;
      default: return colors.text.hint;
    }
  }

  const transitions = $derived(parseTransitions(run.changesSummary || {}));
</script>

<div class="flex flex-col items-center text-center gap-0.5 mt-3 min-w-[120px]">
  <span class="text-text-secondary text-[14px]">{timestamp}</span>

  {#if run.isBaseline}
    <span class="font-semibold text-text-primary">Initial</span>
    <span class="text-text-secondary">{run.totalChecked.toLocaleString()} URLs</span>
    {#if run.statusSummary}
      <div class="flex flex-col gap-0 text-[14px]">
        {#if run.statusSummary.live > 0}
          <span style="color: {colors.status.live}">{run.statusSummary.live} Live</span>
        {/if}
        {#if run.statusSummary.removed > 0}
          <span style="color: {colors.status.removed}">{run.statusSummary.removed} Removed</span>
        {/if}
        {#if run.statusSummary.restricted > 0}
          <span style="color: {colors.status.restricted}">{run.statusSummary.restricted} Restricted</span>
        {/if}
      </div>
    {/if}
  {:else if run.changesCount > 0}
    <span class="font-semibold text-text-primary">{run.changesCount} changes</span>
    <div class="flex flex-col gap-0 text-[14px]">
      {#each transitions as t}
        <span style="color: {t.color}">{t.label}</span>
      {/each}
    </div>
  {:else}
    <span class="text-text-muted">No changes</span>
  {/if}
</div>
