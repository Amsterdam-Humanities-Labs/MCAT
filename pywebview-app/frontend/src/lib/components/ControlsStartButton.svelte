<script lang="ts">
  import { cn } from '$lib/utils';
  import Button from './Button.svelte';

  interface Props {
    runState: 'idle' | 'running' | 'paused';
    onStart?: () => void;
    onPause?: () => void;
    onResume?: () => void;
    class?: string;
  }

  let { runState, onStart, onPause, onResume, class: className }: Props = $props();
</script>

<div class={cn("flex items-center gap-2", className)}>
  {#if runState === 'idle'}
    <Button variant="primary" size="sm" onclick={onStart}>Start</Button>
  {:else if runState === 'running'}
    <Button variant="secondary" size="sm" onclick={onPause}>Pause</Button>
  {:else if runState === 'paused'}
    <Button variant="primary" size="sm" onclick={onResume}>Resume</Button>
  {/if}
</div>
