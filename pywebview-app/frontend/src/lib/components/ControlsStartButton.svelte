<script lang="ts">
  import Button from './Button.svelte';

  interface Props {
    runState: 'idle' | 'running' | 'paused';
    onStart?: () => void;
    onPause?: () => void;
    onResume?: () => void;
  }

  let { runState, onStart, onPause, onResume }: Props = $props();
</script>

<div class="flex items-center gap-2">
  {#if runState === 'idle'}
    <Button variant="primary" size="sm" onclick={onStart}>Start</Button>
  {:else if runState === 'running'}
    <Button variant="secondary" size="sm" onclick={onPause}>Pause</Button>
  {:else if runState === 'paused'}
    <Button variant="primary" size="sm" onclick={onResume}>Resume</Button>
  {/if}
</div>
