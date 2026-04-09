<script lang="ts">
  import { cn } from '$lib/utils';
  import { formatTimestamp } from '$lib/utils/format';
  import { SpinnerGap } from 'phosphor-svelte';

  interface Props {
    timestamp: string;
    progressPercent: number;
    class?: string;
  }

  let { timestamp, progressPercent, class: className }: Props = $props();
</script>

<div class={cn("flex items-center gap-3 px-4 py-2.5 text-base border-b border-border-light", className)}>
  <span class="inline-flex items-center justify-center w-5 h-5 shrink-0">
    <SpinnerGap size={14} class="animate-spin text-timeline-dot" />
  </span>
  <span class="flex items-center gap-2">
    <span class="text-text-secondary">{formatTimestamp(timestamp)}</span>
    <span class="text-text-muted">·</span>
    <span class="text-text-hint">Running... {progressPercent}%</span>
  </span>
</div>
