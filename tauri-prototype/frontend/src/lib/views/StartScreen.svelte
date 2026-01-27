<script lang="ts">
  import { cn } from '$lib/utils';
  import Button from '$lib/components/ui/Button.svelte';

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

<div class={cn('flex items-center justify-center min-h-[60vh]', className)}>
  <div class="bg-mcat-card border border-mcat-border rounded-lg p-8 max-w-md w-full text-center">
    <div class="mb-6">
      <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-mcat-orange/10 flex items-center justify-center">
        <svg class="w-8 h-8 text-mcat-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h2 class="text-xl font-semibold text-white mb-2">Welcome to MCAT</h2>
      <p class="text-mcat-text-muted text-sm">
        Moderation Content Analysis Tool<br />
        Create a new project or open an existing one to get started.
      </p>
    </div>

    <div class="flex flex-col gap-3">
      <Button variant="primary" size="lg" class="w-full" onclick={onnewproject}>
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        New Project
      </Button>
      <Button variant="secondary" size="lg" class="w-full" onclick={onopenproject}>
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
        </svg>
        Open Project
      </Button>
    </div>
  </div>
</div>
