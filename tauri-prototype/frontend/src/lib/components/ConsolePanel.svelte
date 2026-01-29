<script lang="ts">
  import { cn } from '$lib/utils';
  import type { LogLevel, LogSource } from '$lib/stores/console.svelte';

  interface LogMessage {
    id: number;
    text: string;
    level: LogLevel;
    source: LogSource;
    timestamp: Date;
  }

  interface Props {
    messages?: LogMessage[];
    maxHeight?: string;
    class?: string;
  }

  let {
    messages = [],
    maxHeight = '300px',
    class: className,
  }: Props = $props();

  let containerEl: HTMLDivElement | undefined = $state();
  let autoScroll = $state(true);

  const levelClasses: Record<LogLevel, string> = {
    debug: 'text-mcat-text-muted',
    info: 'text-log-info',
    warning: 'text-log-warning',
    error: 'text-log-error',
    success: 'text-log-success',
  };

  const levelIcons: Record<LogLevel, string> = {
    debug: '⋯',
    info: '•',
    warning: '⚠',
    error: '✕',
    success: '✓',
  };

  const sourceLabels: Record<LogSource, string> = {
    app: 'APP',
    backend: 'API',
    processing: 'PROC',
  };

  function formatTime(date: Date): string {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }

  function handleScroll() {
    if (!containerEl) return;
    const { scrollTop, scrollHeight, clientHeight } = containerEl;
    autoScroll = scrollHeight - scrollTop - clientHeight < 50;
  }

  $effect(() => {
    if (autoScroll && containerEl && messages.length > 0) {
      containerEl.scrollTop = containerEl.scrollHeight;
    }
  });
</script>

<div class={cn('flex flex-col bg-console-bg rounded-lg border border-mcat-border', className)}>
  <!-- Header -->
  <div class="flex items-center px-3 py-2 border-b border-mcat-border">
    <span class="text-sm font-medium text-mcat-text-muted">Console</span>
  </div>

  <!-- Messages -->
  <div
    bind:this={containerEl}
    onscroll={handleScroll}
    class="overflow-auto font-mono text-xs p-3 space-y-1"
    style="max-height: {maxHeight}"
  >
    {#if messages.length === 0}
      <div class="text-mcat-text-muted italic">No messages yet...</div>
    {:else}
      {#each messages as msg (msg.id)}
        <div class={cn('flex gap-2', levelClasses[msg.level])}>
          <span class="text-mcat-text-muted shrink-0">[{formatTime(msg.timestamp)}]</span>
          <span class="text-mcat-text-muted shrink-0 w-10">[{sourceLabels[msg.source]}]</span>
          <span class="shrink-0">{levelIcons[msg.level]}</span>
          <span class="break-all">{msg.text}</span>
        </div>
      {/each}
    {/if}
  </div>
</div>
