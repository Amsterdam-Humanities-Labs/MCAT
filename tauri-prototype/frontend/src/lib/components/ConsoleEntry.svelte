<script lang="ts">
  import type { LogLevel } from '$types/console';

  interface Props {
    timestamp: Date;
    message: string;
    level: LogLevel;
  }

  let { timestamp, message, level }: Props = $props();

  const levelColors: Record<LogLevel, string> = {
    debug: 'text-text-muted',
    info: 'text-text-body',
    warning: 'text-status-restricted',
    error: 'text-status-removed',
    success: 'text-status-live',
  };

  const levelGlyphs: Record<LogLevel, string> = {
    debug: '...',
    info: '·',
    warning: '⚠',
    error: '✗',
    success: '✓',
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

<div class="flex gap-3 leading-7 {levelColors[level]}">
  <span class="text-console-timestamp shrink-0">[{formatTime(timestamp)}]</span>
  <span class="shrink-0">{levelGlyphs[level]}</span>
  <span class="break-all">{message}</span>
</div>
