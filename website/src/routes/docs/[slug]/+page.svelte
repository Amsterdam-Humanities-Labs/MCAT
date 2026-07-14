<script lang="ts">
  import { docs } from '$lib/docs';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  const Content = $derived(docs[data.slug].default);
</script>

<Content />
