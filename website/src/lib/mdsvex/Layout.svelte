<script module>
  // mdsvex custom components: these named exports replace the matching markdown
  // elements, so all rendered doc content flows through our components.
  export { H1 as h1, H2 as h2, H3 as h3, P as p } from '@mcat/ui/website';
  export { Link as a } from '@mcat/ui';
</script>

<script>
  let { children } = $props();
</script>

<article class="flex flex-col gap-4">
  {@render children()}
</article>
