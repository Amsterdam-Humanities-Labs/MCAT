<script lang="ts">
  import { formatTimestamp } from '$lib/utils/format';
  import { SpinnerGap } from 'phosphor-svelte';

  interface Props {
    timestamp: string;
    progressPercent: number;
  }

  let { timestamp, progressPercent }: Props = $props();
</script>

<div class="flex flex-col items-center">
  <span class="inline-flex items-center justify-center w-6 h-6">
    <SpinnerGap size={18} class="animate-spin text-[#6B4C2A]" />
  </span>
  <div class="flex flex-col items-center text-center gap-0.5 mt-3">
    <span class="text-text-secondary text-[14px]">{formatTimestamp(timestamp)}</span>
    <span class="text-text-hint">Running... {progressPercent}%</span>
  </div>
</div>
