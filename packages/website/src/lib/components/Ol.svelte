<script lang="ts">
  let { children } = $props();
</script>

<ol class="list-decimal space-y-2 pl-6">
  {@render children()}
</ol>
