<script lang="ts">
  import { cn } from '$lib/utils';
  import StatCard from './StatCard.svelte';

  interface Stat {
    label: string;
    value: string | number;
    color?: 'default' | 'success' | 'warning' | 'error' | 'info';
  }

  interface Props {
    stats: Stat[];
    columns?: 2 | 3 | 4;
    class?: string;
  }

  let {
    stats,
    columns = 4,
    class: className,
  }: Props = $props();

  const gridClasses = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
  };
</script>

<div class={cn('grid gap-3', gridClasses[columns], className)}>
  {#each stats as stat}
    <StatCard label={stat.label} value={stat.value} color={stat.color} />
  {/each}
</div>
