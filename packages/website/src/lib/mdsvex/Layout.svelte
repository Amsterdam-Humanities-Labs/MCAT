<script module>
  // mdsvex custom components: these named exports replace the matching markdown
  // elements, so all rendered doc content flows through our components.
  export { default as h1 } from '$components/H1.svelte';
  export { default as h2 } from '$components/H2.svelte';
  export { default as h3 } from '$components/H3.svelte';
  export { default as p } from '$components/P.svelte';
  export { default as ul } from '$components/Ul.svelte';
  export { default as ol } from '$components/Ol.svelte';
  export { default as li } from '$components/Li.svelte';
  export { Link as a } from '@mcat/shared-ui';
</script>

<script>
  let { children } = $props();
</script>

<article class="flex flex-col gap-4 [&_h2]:pt-6 [&_h3]:pt-4">
  {@render children()}
</article>
