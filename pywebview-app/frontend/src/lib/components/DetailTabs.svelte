<script lang="ts">
  interface Props {
    activeTab: 'changes' | 'results';
    onchange?: (tab: 'changes' | 'results') => void;
  }

  let { activeTab, onchange }: Props = $props();

  const tabs = [
    { id: 'changes' as const, label: 'Changes' },
    { id: 'results' as const, label: 'All Results' },
  ];
</script>

<div class="flex gap-4 border-b border-border-light">
  {#each tabs as tab}
    <button
      type="button"
      class="pb-2 text-sm cursor-pointer bg-transparent border-none border-b-2 transition-colors"
      class:border-accent-brown={activeTab === tab.id}
      class:text-text-primary={activeTab === tab.id}
      class:font-semibold={activeTab === tab.id}
      class:border-transparent={activeTab !== tab.id}
      class:text-text-muted={activeTab !== tab.id}
      onclick={() => onchange?.(tab.id)}
    >
      {tab.label}
    </button>
  {/each}
</div>
