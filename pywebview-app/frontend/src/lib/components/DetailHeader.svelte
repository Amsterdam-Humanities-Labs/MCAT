<script lang="ts">
  import { cn } from '$lib/utils';
  import type { Run } from '$types/project';
  import { formatDuration } from '$lib/utils/format';
  import Button from './Button.svelte';

  interface Props {
    run: Run;
    runNumber: number;
    onOpenFolder?: () => void;
    class?: string;
  }

  let { run, runNumber, onOpenFolder, class: className }: Props = $props();

  const statusLabel = $derived.by(() => {
    if (run.status === 'abandoned') return 'Abandoned';
    if (run.status === 'in_progress') return 'Running';
    const duration = formatDuration(run.duration_seconds);
    return duration ? `Completed in ${duration}` : 'Completed';
  });
</script>

<div class={cn("flex items-center justify-between py-2.5 text-sm", className)}>
  <span class="text-text-secondary">#{runNumber} {statusLabel}</span>

  {#if onOpenFolder}
    <Button variant="secondary" size="sm" onclick={onOpenFolder}>
      Run Folder
    </Button>
  {/if}
</div>
