<script lang="ts">
  import { cn } from '$lib/utils';
  import { Button } from '$lib/components';

  interface Props {
    class?: string;
    onnewproject?: () => unknown;
    onopenproject?: () => unknown;
  }

  let {
    class: className,
    onnewproject,
    onopenproject,
  }: Props = $props();
</script>

<div class={cn('flex items-center justify-center h-screen bg-bg-controls', className)}>
  <div class="bg-bg-toolbar border border-border-mid rounded p-8 max-w-md w-full text-center">
    <div class="flex flex-col gap-3">
      <Button variant="primary" size="lg" class="w-full" onclick={onnewproject}>
        New Project
      </Button>
      <Button variant="secondary" size="lg" class="w-full" onclick={onopenproject}>
        Open Project
      </Button>
    </div>
  </div>
</div>
