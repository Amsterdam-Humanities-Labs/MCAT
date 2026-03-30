<script lang="ts">
  import { cn } from '$lib/utils';
  import type { LogMessage } from '$types/console';
  import ConsoleHeader from './ConsoleHeader.svelte';
  import ConsoleBody from './ConsoleBody.svelte';

  interface Props {
    messages?: LogMessage[];
    class?: string;
  }

  let { messages = [], class: className }: Props = $props();

  let expanded = $state(true);

  const warningCount = $derived(
    messages.filter((m) => m.level === 'warning' || m.level === 'error').length
  );
</script>

<div class={cn("flex flex-col overflow-hidden", className)} class:h-[30vh]={expanded}>
  <ConsoleHeader
    {expanded}
    {warningCount}
    onToggle={() => (expanded = !expanded)}
  />
  {#if expanded}
    <div class="flex-1 overflow-y-auto">
      <ConsoleBody entries={messages} />
    </div>
  {/if}
</div>
