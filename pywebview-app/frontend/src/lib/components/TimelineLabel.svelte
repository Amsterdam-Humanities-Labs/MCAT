<script lang="ts">
  import type { Run } from '$types/project';
  import { formatTimestamp } from '$lib/utils/format';
  import { colors } from '$lib/theme';

  interface Props {
    run: Run;
  }

  let { run }: Props = $props();

  const timestamp = $derived(formatTimestamp(run.started_at));

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

  const transitions = $derived(parseTransitions(run.changes_summary || {}));
</script>

<div class="flex flex-col items-center text-center gap-0.5 mt-3 min-w-[120px]">
  <span class="text-text-secondary text-[14px]">{timestamp}</span>

  {#if run.status === 'abandoned'}
    <span class="text-text-muted">Incomplete</span>
  {:else if run.is_baseline}
    <span class="font-semibold text-text-primary">Baseline</span>
    <span class="text-text-secondary">{run.total_checked.toLocaleString()} URLs</span>
    {#if run.status_summary}
      <div class="flex flex-col gap-0 text-[14px]">
        {#if run.status_summary.live > 0}
          <span style="color: {colors.status.live}">{run.status_summary.live} Live</span>
        {/if}
        {#if run.status_summary.removed > 0}
          <span style="color: {colors.status.removed}">{run.status_summary.removed} Removed</span>
        {/if}
        {#if run.status_summary.restricted > 0}
          <span style="color: {colors.status.restricted}">{run.status_summary.restricted} Restricted</span>
        {/if}
      </div>
    {/if}
  {:else if run.changes_count > 0}
    <span class="font-semibold text-text-primary">{run.changes_count} changes</span>
    <div class="flex flex-col gap-0 text-[14px]">
      {#each transitions as t}
        <span style="color: {t.color}">{t.label}</span>
      {/each}
    </div>
  {:else}
    <span class="text-text-muted">No changes</span>
  {/if}
</div>
