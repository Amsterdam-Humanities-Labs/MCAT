<script lang="ts">
  import { Link } from '@mcat/shared-ui';

  const year = new Date().getFullYear();
</script>

<footer class="relative border-t border-border-light bg-bg-toolbar">
  <div
    class="mx-auto flex max-w-5xl flex-wrap items-center justify-center gap-x-4 gap-y-1 px-4 py-2 text-text-secondary"
  >
    <Link href="https://www.digitalmethods.net/">DMI {year}</Link>
    <Link href="https://github.com/Amsterdam-Humanities-Labs/MCAT">GitHub</Link>
    <Link href="https://eupl.eu/1.2/en/">License</Link>
  </div>
</footer>
