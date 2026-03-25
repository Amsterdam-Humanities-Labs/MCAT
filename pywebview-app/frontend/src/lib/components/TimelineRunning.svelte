<script lang="ts">
  import { formatTimestamp } from '$lib/utils/format';
  import { SpinnerGap } from 'phosphor-svelte';

  interface Props {
    timestamp: string;
    progressPercent: number;
  }

  let { timestamp, progressPercent }: Props = $props();
</script>

<div class="flex items-center gap-3 px-4 py-2.5 text-sm">
  <span class="inline-flex items-center justify-center w-5 h-5 shrink-0">
    <SpinnerGap size={14} class="animate-spin text-[#6B4C2A]" />
  </span>
  <span class="flex items-center gap-2">
    <span class="text-text-secondary">{formatTimestamp(timestamp)}</span>
    <span class="text-text-muted">·</span>
    <span class="text-text-hint">Running... {progressPercent}%</span>
  </span>
</div>
