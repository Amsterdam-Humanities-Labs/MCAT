<script lang="ts">
  import { formatDuration } from '$lib/utils/format';

  interface Props {
    enabled: boolean;
    nextCheck: string | null;
    isRunning: boolean;
  }

  let { enabled, nextCheck, isRunning }: Props = $props();

  let now = $state(Date.now());

  $effect(() => {
    if (!enabled || !nextCheck || isRunning) return;
    const id = setInterval(() => { now = Date.now(); }, 30_000);
    return () => clearInterval(id);
  });

  const remainingSeconds = $derived.by(() => {
    if (!nextCheck) return 0;
    const diff = (new Date(nextCheck).getTime() - now) / 1000;
    return Math.max(0, Math.round(diff));
  });

  const label = $derived.by(() => {
    if (!enabled) return '';
    if (isRunning) return 'Repeating';
    if (remainingSeconds > 0) return `Next run in ${formatDuration(remainingSeconds)}`;
    return '';
  });
</script>

{#if label}
  <span class="text-text-hint text-sm">{label}</span>
{/if}
