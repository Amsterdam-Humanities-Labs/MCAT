<script lang="ts">
  import { cn } from '../utils';
  import type { NavLink } from './types';

  interface Props {
    links: NavLink[];
    currentPath: string;
    orientation?: 'horizontal' | 'vertical';
    class?: string;
  }

  let { links, currentPath, orientation = 'horizontal', class: className }: Props = $props();

  const isActive = (href: string) =>
    href === '/' ? currentPath === '/' : currentPath.startsWith(href);
</script>

<nav class={className}>
  <ul class={cn('flex list-none gap-6', orientation === 'vertical' && 'flex-col gap-3')}>
    {#each links as { label, href } (href)}
      <li>
        <a
          {href}
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
