<script lang="ts">
  import { cn } from '$lib/utils';
  import type { LogLevel } from '$types/console';
  import { Check, Warning, XCircle } from 'phosphor-svelte';

  interface Props {
    timestamp: Date;
    message: string;
    level: LogLevel;
    class?: string;
  }

  let { timestamp, message, level, class: className }: Props = $props();

  const levelColors: Record<LogLevel, string> = {
    debug: 'text-text-muted',
    info: 'text-text-body',
    warning: 'text-status-restricted',
    error: 'text-status-removed',
    success: 'text-status-live',
  };

  function formatTime(date: Date): string {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }
</script>

<div class={cn("flex gap-3 leading-7 text-base", levelColors[level], className)}>
  <span class="text-console-timestamp shrink-0">{formatTime(timestamp)}</span>
  {#if level === 'success'}
    <span class="shrink-0 flex items-center"><Check size={14} weight="bold" /></span>
  {:else if level === 'warning'}
    <span class="shrink-0 flex items-center"><Warning size={14} weight="bold" /></span>
  {:else if level === 'error'}
    <span class="shrink-0 flex items-center"><XCircle size={14} weight="bold" /></span>
  {/if}
  <span class="break-all">{message}</span>
</div>
