<script lang="ts">
  import type { LogMessage } from '$types/console';
  import ConsoleHeader from './ConsoleHeader.svelte';
  import ConsoleBody from './ConsoleBody.svelte';

  interface Props {
    messages?: LogMessage[];
  }

  let { messages = [] }: Props = $props();

  let expanded = $state(true);

  const warningCount = $derived(
    messages.filter((m) => m.level === 'warning' || m.level === 'error').length
  );
</script>

<div class="flex flex-col">
  <ConsoleHeader
    {expanded}
    {warningCount}
    onToggle={() => (expanded = !expanded)}
  />
  {#if expanded}
    <ConsoleBody entries={messages} />
  {/if}
</div>
