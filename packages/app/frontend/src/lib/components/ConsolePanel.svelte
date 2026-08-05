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

<div class={cn("relative z-10 flex flex-col overflow-hidden bg-bg-log shadow-[0_-4px_8px_-2px_rgba(0,0,0,0.2)]", className)} class:h-[30vh]={expanded}>
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
