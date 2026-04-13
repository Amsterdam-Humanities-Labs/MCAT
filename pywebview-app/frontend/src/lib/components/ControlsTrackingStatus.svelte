<script lang="ts">
  import { cn } from '$lib/utils';
  import { Circle } from 'phosphor-svelte';

  interface Props {
    enabled: boolean;
    nextCheck: string | null;
    isRunning: boolean;
    runNumber: number;
    class?: string;
  }

  let { enabled, nextCheck, isRunning, runNumber, class: className }: Props = $props();

  let now = $state(Date.now());

  $effect(() => {
    if (!enabled || !nextCheck || isRunning) return;
    now = Date.now();
    const remaining = nextCheck ? (new Date(nextCheck).getTime() - now) / 1000 : 0;
    const tick = remaining > 86400 ? 60_000 : 1000;
    const id = setInterval(() => { now = Date.now(); }, tick);
    return () => clearInterval(id);
  });

  const remainingSeconds = $derived.by(() => {
    if (!nextCheck) return 0;
    const diff = (new Date(nextCheck).getTime() - now) / 1000;
    return Math.max(0, Math.floor(diff));
  });

  function formatCountdown(totalSeconds: number): string {
    const d = Math.floor(totalSeconds / 86400);
    const h = Math.floor((totalSeconds % 86400) / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    const mm = String(m).padStart(2, '0');
    const ss = String(s).padStart(2, '0');
    if (d > 0) return `${d}d ${h}h ${mm}m`;
    if (h > 0) return `${h}:${mm}:${ss}`;
    return `${mm}:${ss}`;
  }

  const label = $derived.by(() => {
    if (!enabled) return '';
    if (isRunning) return `Run ${runNumber} in progress`;
    if (remainingSeconds > 0) return `Next run in ${formatCountdown(remainingSeconds)}`;
    return '';
  });

  const showDot = $derived(enabled && !isRunning && remainingSeconds > 0);
</script>

{#if label}
  <span class={cn("flex items-center gap-2 text-text-hint text-base", className)}>
    {#if showDot}
      <span class="animate-pulse text-status-live">
        <Circle size={12} weight="fill" />
      </span>
    {/if}
    {label}
  </span>
{/if}
