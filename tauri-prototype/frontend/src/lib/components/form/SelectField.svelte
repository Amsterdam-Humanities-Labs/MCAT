<script lang="ts">
  import FormField from './FormField.svelte';
  import Select from '../ui/Select.svelte';

  interface Option {
    value: string;
    label: string;
    disabled?: boolean;
  }

  interface Props {
    label?: string;
    options: Option[];
    value?: string;
    placeholder?: string;
    disabled?: boolean;
    required?: boolean;
    error?: string;
    hint?: string;
    class?: string;
    onchange?: (value: string) => void;
  }

  let {
    label,
    options,
    value = $bindable(),
    placeholder,
    disabled = false,
    required = false,
    error,
    hint,
    class: className,
    onchange,
  }: Props = $props();
</script>

<FormField {label} {required} {error} {hint} class={className}>
  <Select
    {options}
    bind:value
    {placeholder}
    {disabled}
    {onchange}
  />
</FormField>
