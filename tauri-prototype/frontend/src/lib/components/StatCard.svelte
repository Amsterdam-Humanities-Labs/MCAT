<script lang="ts">
  import { cn } from '$lib/utils';

  interface Props {
    label: string;
    value: string | number;
    color?: 'default' | 'success' | 'warning' | 'error' | 'info';
    class?: string;
  }

  let {
    label,
    value,
    color = 'default',
    class: className,
  }: Props = $props();

  const colorClasses = {
    default: 'text-mcat-text',
    success: 'text-status-live',
    warning: 'text-status-restricted',
    error: 'text-status-error',
    info: 'text-mcat-orange',
  };
</script>

<div class={cn('bg-mcat-bg p-3 rounded', className)}>
  <span class="block text-xs text-mcat-text-muted mb-1">{label}</span>
  <span class={cn('text-sm font-medium', colorClasses[color])}>{value}</span>
</div>
