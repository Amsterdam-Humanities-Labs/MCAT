<script lang="ts">
  import type { Run } from '$types/project';
  import { formatTimestamp, formatDuration } from '$lib/utils/format';
  import { FolderOpen } from 'phosphor-svelte';

  interface Props {
    run: Run;
    runNumber: number;
    onOpenFolder?: () => void;
  }

  let { run, runNumber, onOpenFolder }: Props = $props();
</script>

<div class="flex items-center justify-between py-3">
  <div class="flex items-center gap-4 text-sm">
    <span class="text-lg font-bold text-text-primary">Run #{runNumber}</span>
    <span class="text-text-secondary">{formatTimestamp(run.started_at)}</span>
    {#if run.duration_seconds > 0}
      <span class="text-text-secondary">{formatDuration(run.duration_seconds)}</span>
    {/if}
    {#if run.total_checked > 0}
      <span class="text-text-secondary">{run.total_checked.toLocaleString()} checked</span>
    {/if}
  </div>

  {#if onOpenFolder}
    <button
      type="button"
      class="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary cursor-pointer bg-transparent border-none"
      onclick={onOpenFolder}
    >
      <FolderOpen size={16} />
      <span>Open run folder</span>
    </button>
  {/if}
</div>
