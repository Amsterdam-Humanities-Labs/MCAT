<script lang="ts">
  import { cn } from '$lib/utils';
  import { Checkbox, Select, TimeSelector } from '$lib/components';

  interface Props {
    enabled: boolean;
    value: number;
    unit: 'minutes' | 'hours' | 'days';
    onToggle?: (enabled: boolean) => void;
    onChange?: (value: number, unit: 'minutes' | 'hours' | 'days') => void;
    class?: string;
  }

  let { enabled, value, unit, onToggle, onChange, class: className }: Props = $props();

  const unitOptions = [
    { value: 'seconds', label: 'seconds' },
    { value: 'minutes', label: 'minutes' },
    { value: 'hours', label: 'hours' },
    { value: 'days', label: 'days' },
  ];

  const minValues: Record<string, number> = {
    seconds: 5,
    minutes: 1,
    hours: 1,
    days: 1,
  };

  const currentMin = $derived(minValues[unit] ?? 1);

  function handleUnitChange(newUnit: string) {
    const typedUnit = newUnit as 'minutes' | 'hours' | 'days';
    const newMin = minValues[typedUnit] ?? 1;
    const clamped = Math.max(newMin, value);
    onChange?.(clamped, typedUnit);
  }
</script>

<div class={cn("flex items-center gap-2", className)}>
  <Checkbox
    checked={enabled}
    label="Repeat every"
    size="sm"
    onchange={(checked) => onToggle?.(checked)}
  />
  <TimeSelector
    {value}
    min={currentMin}
    disabled={!enabled}
    onchange={(v) => onChange?.(v, unit)}
  />
  <Select
    options={unitOptions}
    value={unit}
    disabled={!enabled}
    onchange={handleUnitChange}
  />
</div>
