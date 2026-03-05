<script lang="ts">
  interface Props {
    enabled: boolean;
    value: number;
    unit: 'minutes' | 'hours' | 'days';
    onToggle?: (enabled: boolean) => void;
    onChange?: (value: number, unit: 'minutes' | 'hours' | 'days') => void;
  }

  let { enabled, value, unit, onToggle, onChange }: Props = $props();

  function handleValueChange(e: Event) {
    const v = parseInt((e.target as HTMLInputElement).value) || 1;
    onChange?.(v, unit);
  }

  function handleUnitChange(e: Event) {
    const u = (e.target as HTMLSelectElement).value as 'minutes' | 'hours' | 'days';
    onChange?.(value, u);
  }
</script>

<div class="flex items-center gap-2">
  <label class="flex items-center gap-2 cursor-pointer select-none">
    <input
      type="checkbox"
      checked={enabled}
      onchange={() => onToggle?.(!enabled)}
      class="w-4 h-4 accent-accent-brown cursor-pointer"
    />
    <span class="text-text-body">Repeat every</span>
  </label>
  <input
    type="number"
    min="1"
    {value}
    disabled={!enabled}
    onchange={handleValueChange}
    class="w-16 px-2 py-1 rounded border border-border-input bg-bg-primary text-text-body text-center disabled:opacity-50 disabled:cursor-not-allowed"
  />
  <select
    value={unit}
    disabled={!enabled}
    onchange={handleUnitChange}
    class="px-2 py-1 rounded border border-border-input bg-bg-primary text-text-body disabled:opacity-50 disabled:cursor-not-allowed"
  >
    <option value="minutes">minutes</option>
    <option value="hours">hours</option>
    <option value="days">days</option>
  </select>
</div>
