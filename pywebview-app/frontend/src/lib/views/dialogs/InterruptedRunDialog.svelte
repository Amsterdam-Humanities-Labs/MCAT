<script lang="ts">
  import { Dialog, Button } from '$lib/components';
  import { Warning } from 'phosphor-svelte';

  interface InterruptedRun {
    run_id: string;
    processed: number;
    total: number;
    remaining: number;
  }

  interface Props {
    open?: boolean;
    run?: InterruptedRun | null;
    class?: string;
    onresume?: () => void;
    onabandon?: () => void;
    onclose?: () => void;
  }

  let {
    open = $bindable(false),
    run,
    class: className,
    onresume,
    onabandon,
    onclose,
  }: Props = $props();

  function handleResume() {
    onresume?.();
  }

  function handleAbandon() {
    onabandon?.();
    onclose?.();
  }
</script>

<Dialog bind:open title="Interrupted Run Detected" {onclose} class={className}>
  <div class="space-y-4">
    <div class="flex items-center gap-3 p-3 bg-status-restricted/10 border border-status-restricted/30 rounded">
      <Warning size={20} class="text-status-restricted flex-shrink-0" />
      <p class="text-sm text-status-restricted">
        A previous processing run was interrupted. Would you like to resume or start fresh?
      </p>
    </div>

    {#if run}
      <div class="grid grid-cols-2 gap-3 p-4 bg-bg-primary rounded">
        <div>
          <span class="block text-xs text-text-muted mb-1">Run ID</span>
          <span class="font-mono text-sm">{run.run_id}</span>
        </div>
        <div>
          <span class="block text-xs text-text-muted mb-1">Progress</span>
          <span class="text-sm">{run.processed} / {run.total}</span>
        </div>
        <div>
          <span class="block text-xs text-text-muted mb-1">Remaining</span>
          <span class="text-sm">{run.remaining} URLs</span>
        </div>
        <div>
          <span class="block text-xs text-text-muted mb-1">Completion</span>
          <span class="text-sm">{Math.round((run.processed / run.total) * 100)}%</span>
        </div>
      </div>
    {/if}
  </div>

  {#snippet actions()}
    <Button variant="secondary" onclick={handleAbandon}>
      Start New
    </Button>
    <Button variant="primary" onclick={handleResume}>
      Resume Run
    </Button>
  {/snippet}
</Dialog>
