<script lang="ts">
  import { cn } from '@mcat/shared-ui';
  import { base } from '$app/paths';
  import type { NavLink } from '$lib/nav';

  interface Props {
    links: NavLink[];
    currentPath: string;
    orientation?: 'horizontal' | 'vertical';
    class?: string;
  }

  let { links, currentPath, orientation = 'horizontal', class: className }: Props = $props();

  const path = $derived(currentPath.slice(base.length) || '/');
  const isActive = (href: string) =>
    href === '/' ? path === '/' : path.startsWith(href);
</script>

<nav class={className}>
  <ul
    class={cn(
      'flex list-none gap-3',
      orientation === 'horizontal' ? 'items-center' : 'flex-col items-start',
    )}
  >
    {#each links as { label, href }, i (href)}
      {#if i > 0 && orientation === 'horizontal'}
        <li aria-hidden="true" class="text-text-hint">|</li>
      {/if}
      <li>
        <a
          href={base + href}
          class={cn(
            'text-text-body hover:text-text-primary',
            isActive(href) && 'text-text-primary underline underline-offset-4',
          )}
        >
          {label}
        </a>
      </li>
    {/each}
  </ul>
</nav>
