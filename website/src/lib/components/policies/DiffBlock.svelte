<script lang="ts">
  import { cn } from '@mcat/shared-ui';
  import type { DiffRow } from '$lib/types/policies';

  interface Props {
    row: DiffRow;
    side: 'a' | 'b';
    class?: string;
  }

  let { row, side, class: className }: Props = $props();

  const block = $derived(side === 'a' ? row.a : row.b);

  // Side a drops added words; side b drops removed words.
  const words = $derived(
    row.kind === 'changed' && row.words
      ? row.words.filter((w) => (side === 'a' ? !w.added : !w.removed))
      : null,
  );

  // Whole-block tint applies to dropped/new blocks only; edited blocks use
  // inline word marks.
  const filled = $derived(
    (row.kind === 'removed' && side === 'a') || (row.kind === 'added' && side === 'b'),
  );
</script>

{#if !block}
  <div class={className} aria-hidden="true"></div>
{:else}
  <div
    class={cn(
      'border-l-2 px-3 py-2 text-base',
      block.type === 'heading' && 'font-semibold',
      !filled && 'border-transparent text-text-body',
      filled &&
        side === 'a' &&
        'border-diff-removed-border bg-diff-removed-bg text-diff-removed-text line-through',
      filled && side === 'b' && 'border-diff-added-border bg-diff-added-bg text-diff-added-text',
      className,
    )}
  >
    {#if words}
      {#each words as word, i (i)}
        <span
          class={word.added ? 'bg-diff-added-mark' : word.removed ? 'bg-diff-removed-mark' : ''}
          >{word.value}</span
        >
      {/each}
    {:else}
      {block.text}
    {/if}
  </div>
{/if}
