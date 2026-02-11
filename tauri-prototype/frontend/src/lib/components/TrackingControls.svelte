<script lang="ts">
  import { trackingStore } from '$lib/stores/tracking.svelte';
  import { Button, Select } from '$lib/components';

  interface Props {
    class?: string;
  }

  let { class: className }: Props = $props();

  let selectedInterval = $state<number | null>(trackingStore.intervalMinutes);
  let isLoading = $state(false);

  const intervals = [
    { value: 30, label: 'Every 30 minutes' },
    { value: 60, label: 'Every hour' },
    { value: 360, label: 'Every 6 hours' },
    { value: 1440, label: 'Daily' },
  ];

  async function handleStart() {
    if (!selectedInterval) return;
    isLoading = true;
    try {
      await trackingStore.startTracking(selectedInterval);
    } finally {
      isLoading = false;
    }
  }

  async function handleStop() {
    isLoading = true;
    try {
      await trackingStore.stopTracking();
    } finally {
      isLoading = false;
    }
  }

  function formatTime(isoString: string | null): string {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
</script>

<div class={`tracking-controls bg-mcat-card border border-mcat-border rounded-lg p-4 ${className || ''}`}>
  <h3 class="text-sm font-medium mb-3">URL Tracking</h3>

  {#if !trackingStore.enabled}
    <div class="flex gap-2 items-center">
      <Select
        bind:value={selectedInterval}
        options={intervals}
        disabled={isLoading}
      />
      <Button
        variant="primary"
        size="sm"
        onclick={handleStart}
        disabled={isLoading}
      >
        Start Tracking
      </Button>
    </div>
  {:else}
    <div class="flex flex-col gap-3">
      <div class="text-sm text-mcat-text-muted space-y-1">
        <div>
          Checking every <span class="font-medium text-mcat-text">{trackingStore.intervalMinutes}</span> minutes
        </div>
        {#if trackingStore.nextCheck}
          <div>
            Next check: <span class="font-medium text-mcat-text">{formatTime(trackingStore.nextCheck)}</span>
          </div>
        {/if}
      </div>
      <Button
        variant="secondary"
        size="sm"
        onclick={handleStop}
        disabled={isLoading}
      >
        Stop Tracking
      </Button>
    </div>
  {/if}
</div>

<style>
  .tracking-controls :global(select) {
    max-width: 200px;
  }
</style>
