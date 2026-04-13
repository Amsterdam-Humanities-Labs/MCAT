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
    debug: 'text-text-secondary',
    info: 'text-text-body',
    warning: 'text-status-restricted',
    error: 'text-status-removed',
    success: 'text-status-live',
  };

  const statusColors: Record<string, string> = {
    live: 'text-status-live',
    removed: 'text-status-removed',
    restricted: 'text-status-restricted',
    private: 'text-status-restricted',
    error: 'text-status-error',
  };

  function formatTime(date: Date): string {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }

  // Parse "[N/M] url → Status" pattern
  const parsed = $derived.by(() => {
    const match = message.match(/^(.+→\s*)(\w[\w-]*)$/);
    if (!match) return null;
    const status = match[2].toLowerCase();
    if (!statusColors[status]) return null;
    return { prefix: match[1], status: match[2], colorClass: statusColors[status] };
  });
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
  {#if parsed}
    <span class="break-all">{parsed.prefix}<span class={parsed.colorClass}>{parsed.status}</span></span>
  {:else}
    <span class="break-all">{message}</span>
  {/if}
</div>
