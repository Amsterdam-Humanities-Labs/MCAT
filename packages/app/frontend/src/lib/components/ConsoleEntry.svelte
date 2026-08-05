<script lang="ts">
  import { cn } from '$lib/utils';
  import { statusMeta } from '@mcat/shared-ui';
  import type { LogLevel } from '$types/console';

  interface Props {
    timestamp: Date;
    message: string;
    level: LogLevel;
    class?: string;
  }

  let { timestamp, message, level, class: className }: Props = $props();

  const messageColors: Record<LogLevel, string> = {
    debug: 'text-text-secondary',
    info: 'text-text-body',
    warning: 'text-status-restricted',
    error: 'text-status-restricted',
    success: 'text-text-body',
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
    const colorClass = statusMeta(match[2])?.text;
    if (!colorClass) return null;
    return { prefix: match[1], status: match[2], colorClass };
  });
</script>

<div class={cn("flex gap-3 leading-7 text-base", messageColors[level], className)}>
  <span class="text-console-timestamp shrink-0">{formatTime(timestamp)}</span>
  {#if parsed}
    <span class="break-all text-text-body">{parsed.prefix}<span class={parsed.colorClass}>{parsed.status}</span></span>
  {:else}
    <span class="break-all">{message}</span>
  {/if}
</div>
