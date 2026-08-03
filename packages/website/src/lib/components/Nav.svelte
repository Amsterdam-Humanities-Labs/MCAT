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
  <ul class={cn('flex list-none gap-6', orientation === 'vertical' && 'flex-col gap-3')}>
    {#each links as { label, href } (href)}
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
