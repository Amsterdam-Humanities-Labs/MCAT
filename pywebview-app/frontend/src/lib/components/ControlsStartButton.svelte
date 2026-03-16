<script lang="ts">
  interface Props {
    runState: 'idle' | 'running' | 'paused';
    onStart?: () => void;
    onPause?: () => void;
    onResume?: () => void;
    onCancel?: () => void;
  }

  let { runState, onStart, onPause, onResume, onCancel }: Props = $props();
</script>

<div class="flex items-center gap-2">
  {#if runState === 'idle'}
    <button
      class="px-5 py-1.5 rounded bg-accent-brown text-bg-primary font-semibold hover:opacity-90 transition-opacity cursor-pointer"
      onclick={onStart}
    >
      Start
    </button>
  {:else if runState === 'running'}
    <button
      class="px-4 py-1.5 rounded border border-accent-brown text-accent-brown font-semibold hover:bg-border-light transition-colors cursor-pointer"
      onclick={onPause}
    >
      Pause
    </button>
    <button
      class="px-4 py-1.5 rounded border border-status-removed text-status-removed font-semibold hover:bg-border-light transition-colors cursor-pointer"
      onclick={onCancel}
    >
      Cancel
    </button>
  {:else if runState === 'paused'}
    <button
      class="px-4 py-1.5 rounded bg-accent-brown text-bg-primary font-semibold hover:opacity-90 transition-opacity cursor-pointer"
      onclick={onResume}
    >
      Resume
    </button>
    <button
      class="px-4 py-1.5 rounded border border-status-removed text-status-removed font-semibold hover:bg-border-light transition-colors cursor-pointer"
      onclick={onCancel}
    >
      Cancel
    </button>
  {/if}
</div>
