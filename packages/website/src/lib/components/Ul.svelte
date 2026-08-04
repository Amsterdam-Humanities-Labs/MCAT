<script lang="ts">
  let { children } = $props();
</script>

<ul class="flex flex-col gap-2">
  {@render children()}
</ul>
