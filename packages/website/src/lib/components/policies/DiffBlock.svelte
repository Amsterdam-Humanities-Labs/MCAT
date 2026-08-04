<script lang="ts">
  import { cn } from '@mcat/shared-ui';
  import type { DiffRow, WordPart } from '$lib/types/policies';

  interface Props {
    row: DiffRow;
    side: 'a' | 'b';
    class?: string;
  }

  let { row, side, class: className }: Props = $props();

  const block = $derived(side === 'a' ? row.a : row.b);

  const parts = $derived.by((): WordPart[] | null => {
    if (!block) return null;
    if (row.kind === 'equal') return [{ value: block.text }];
    if (row.kind === 'changed' && row.words) {
      return row.words.filter((w) => (side === 'a' ? !w.added : !w.removed));
    }
    return [{ value: block.text, added: row.kind === 'added', removed: row.kind === 'removed' }];
  });
</script>

{#if !parts}
  <div class={className} aria-hidden="true"></div>
{:else}
  <div
    class={cn(
      'px-3 py-2 text-base text-text-body',
      block?.type === 'heading' && 'font-medium',
      className,
    )}
  >
    {#each parts as part, i (i)}
      <span
        class={part.added
          ? 'bg-diff-added-mark text-diff-added-text'
          : part.removed
            ? 'bg-diff-removed-mark text-diff-removed-text'
            : ''}>{part.value}</span
      >
    {/each}
  </div>
{/if}
