<script lang="ts">
  import { cn } from '$lib/utils';
  import { Progress } from 'melt/builders';

  interface Props {
    value?: number;
    max?: number;
    class?: string;
  }

  let {
    value = 0,
    max = 100,
    class: className,
  }: Props = $props();

  const progress = new Progress({
    value: () => value,
    max: () => max,
  });
</script>

<div
  {...progress.root}
  class={cn('w-full h-2 bg-progress-track rounded-full overflow-hidden', className)}
>
  <div
    {...progress.progress}
    class="h-full bg-accent-brown transition-all duration-300 ease-out"
    style="width: {max > 0 ? (value / max) * 100 : 0}%"
  ></div>
</div>
