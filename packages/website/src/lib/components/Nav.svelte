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
  const isActive = (href: string) => (href === '/' ? path === '/' : path.startsWith(href));
</script>

<nav class={className}>
  <ul
    class={cn(
      'flex list-none',
      orientation === 'vertical'
        ? 'flex-col items-start gap-3'
        : 'w-full flex-wrap items-center justify-center gap-x-6 gap-y-2',
    )}
  >
    {#each links as { label, href } (href)}
      <li>
        <a
          href={base + href}
          class={cn(
            'inline-block border-b-4 border-transparent pb-[2.5px] text-lg text-text-body hover:border-accent-primary hover:text-text-primary',
            isActive(href) && 'border-accent-primary text-text-primary',
          )}
        >
          {label}
        </a>
      </li>
    {/each}
  </ul>
</nav>
