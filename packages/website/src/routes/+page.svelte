<script lang="ts">
  import { Button } from '@mcat/shared-ui';
  import { base } from '$app/paths';
  import H1 from '$components/H1.svelte';
  import P from '$components/P.svelte';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();
</script>

<section class="flex flex-col gap-8">
  <img
    src="{base}/mcat_preview.jpg"
    alt="MCAT desktop app"
    class="w-full rounded border border-border-light shadow-[0_0_30px_0_rgba(0,0,0,0.2)]"
  />

  <div class="flex flex-col gap-5">
    <H1>{data.headline}</H1>
    <P>{data.tagline}</P>
    <div class="flex flex-wrap gap-3">
      <Button href="{base}/download" variant="primary">Download</Button>
      <Button href="{base}/docs" variant="secondary">Documentation</Button>
    </div>
  </div>
</section>
