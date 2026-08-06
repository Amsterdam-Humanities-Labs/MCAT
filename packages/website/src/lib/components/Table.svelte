<script lang="ts">
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();
</script>

<div class="w-full overflow-x-auto">
  <table class="w-full text-left">
    {@render children()}
  </table>
</div>
