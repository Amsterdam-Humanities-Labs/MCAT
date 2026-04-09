<script lang="ts">
  import { cn } from '$lib/utils';
  import { Tooltip } from 'melt/builders';

  interface Props {
    text: string;
    class?: string;
    children?: import('svelte').Snippet;
  }

  let {
    text,
    class: className,
    children,
  }: Props = $props();

  const tooltip = new Tooltip({
    openDelay: 200,
    closeDelay: 0,
  });
</script>

<span {...tooltip.trigger} class={cn('inline-block', className)}>
  {@render children?.()}
</span>

<div
  {...tooltip.content}
  class={cn(
    'z-50 px-2 py-1 text-base',
    'bg-bg-controls border border-border-mid rounded shadow-lg text-text-body'
  )}
>
  <div {...tooltip.arrow}></div>
  {text}
</div>
