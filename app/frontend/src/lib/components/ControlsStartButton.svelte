<script lang="ts">
  import { cn } from '$lib/utils';
  import { Button } from '@mcat/shared-ui';

  interface Props {
    runState: 'idle' | 'running' | 'paused';
    onStart?: () => void;
    onPause?: () => void;
    onResume?: () => void;
    onAbandon?: () => void;
    class?: string;
  }

  let { runState, onStart, onPause, onResume, onAbandon, class: className }: Props = $props();
</script>

<div class={cn("flex items-center gap-2", className)}>
  {#if runState === 'idle'}
    <Button variant="primary" size="sm" onclick={onStart}>Start</Button>
  {:else if runState === 'running'}
    <Button variant="secondary" size="sm" onclick={onPause}>Pause</Button>
    <Button variant="danger" size="sm" onclick={onAbandon}>Abandon</Button>
  {:else if runState === 'paused'}
    <Button variant="primary" size="sm" onclick={onResume}>Resume</Button>
    <Button variant="danger" size="sm" onclick={onAbandon}>Abandon</Button>
  {/if}
</div>
