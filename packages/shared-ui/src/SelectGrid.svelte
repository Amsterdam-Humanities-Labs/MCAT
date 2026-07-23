<script lang="ts">
  import type { Snippet } from 'svelte';
  import { cn } from './utils';

  interface Props {
    class?: string;
    children: Snippet;
  }

  let { class: className, children }: Props = $props();
</script>

<div class={cn('grid grid-cols-1 gap-4 md:grid-cols-2', className)}>
  {@render children()}
</div>
