<script lang="ts">
  import { cn } from '$lib/utils';
  import { Button } from '$lib/components';

  interface Props {
    class?: string;
    onnewproject?: () => void;
    onopenproject?: () => void;
  }

  let {
    class: className,
    onnewproject,
    onopenproject,
  }: Props = $props();
</script>

<div class={cn('flex items-center justify-center h-screen bg-bg-timeline', className)}>
  <div class="bg-bg-controls border border-border-mid rounded p-8 max-w-md w-full text-center">
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-text-primary mb-2">Welcome to MCAT</h2>
      <p class="text-text-muted text-sm">
        Moderation Content Analysis Tool<br />
        Create a new project or open an existing one to get started.
      </p>
    </div>

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
