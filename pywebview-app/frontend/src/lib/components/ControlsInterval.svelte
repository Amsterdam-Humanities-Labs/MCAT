<script lang="ts">
  import { Checkbox, Select, TimeSelector } from '$lib/components';

  interface Props {
    enabled: boolean;
    value: number;
    unit: 'minutes' | 'hours' | 'days';
    onToggle?: (enabled: boolean) => void;
    onChange?: (value: number, unit: 'minutes' | 'hours' | 'days') => void;
  }

  let { enabled, value, unit, onToggle, onChange }: Props = $props();

  const unitOptions = [
    { value: 'minutes', label: 'minutes' },
    { value: 'hours', label: 'hours' },
    { value: 'days', label: 'days' },
  ];

  const minValues: Record<string, number> = {
    minutes: 5,
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

<div class="flex items-center gap-2">
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
