<script lang="ts">
  import { Panel } from '@mcat/shared-ui';
  import DiffBlock from './DiffBlock.svelte';
  import type { DiffRow } from '$lib/types/policies';

  interface Props {
    rows: DiffRow[];
    labelA: string;
    labelB: string;
    class?: string;
  }

  let { rows, labelA, labelB, class: className }: Props = $props();
</script>

<Panel bodyClass="p-0" class={className}>
  <!-- One grid for both columns: each row's old/new cells share a grid row.
       Collapses to a single column on mobile. -->
  <div class="grid grid-cols-1 md:grid-cols-2 md:gap-x-4">
    <div class="hidden border-b border-border-light px-3 py-2 text-base text-text-secondary md:block">
      {labelA}
    </div>
    <div class="hidden border-b border-border-light px-3 py-2 text-base text-text-secondary md:block">
      {labelB}
    </div>

    {#each rows as row, i (i)}
      <DiffBlock {row} side="a" class={row.kind === 'equal' ? 'hidden md:block' : undefined} />
      <DiffBlock {row} side="b" />
    {/each}
  </div>
</Panel>
