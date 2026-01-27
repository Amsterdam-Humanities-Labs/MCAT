<script lang="ts">
  import { save } from '@tauri-apps/plugin-dialog';
  import Dialog from '$lib/components/ui/Dialog.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import FormField from '$lib/components/form/FormField.svelte';
  import Select from '$lib/components/ui/Select.svelte';
  import CheckboxGroup from '$lib/components/form/CheckboxGroup.svelte';

  interface Props {
    open?: boolean;
    class?: string;
    onclose?: () => void;
  }

  let {
    open = $bindable(false),
    class: className,
    onclose,
  }: Props = $props();

  const formatOptions = [
    { value: 'csv', label: 'CSV (.csv)' },
    { value: 'json', label: 'JSON (.json)' },
    { value: 'xlsx', label: 'Excel (.xlsx)' },
  ];

  const statusFilterOptions = [
    { value: 'live', label: 'Live' },
    { value: 'removed', label: 'Removed' },
    { value: 'restricted', label: 'Restricted' },
    { value: 'error', label: 'Error' },
  ];

  let format = $state('csv');
  let statusFilters = $state<string[]>(['live', 'removed', 'restricted', 'error']);
  let loading = $state(false);

  async function handleExport() {
    loading = true;

    try {
      const extensions = {
        csv: ['csv'],
        json: ['json'],
        xlsx: ['xlsx'],
      };

      const path = await save({
        filters: [
          {
            name: formatOptions.find((f) => f.value === format)?.label ?? 'File',
            extensions: extensions[format as keyof typeof extensions],
          },
        ],
        defaultPath: `mcat-results.${format}`,
      });

      if (path) {
        // TODO: Call backend export API
        console.log('Export to:', path, 'format:', format, 'filters:', statusFilters);
        onclose?.();
      }
    } catch (e) {
      console.error('Export error:', e);
    } finally {
      loading = false;
    }
  }
</script>

<Dialog bind:open title="Export Results" {onclose} class={className}>
  <div class="space-y-4">
    <FormField label="Export Format">
      <Select
        options={formatOptions}
        bind:value={format}
      />
    </FormField>

    <FormField label="Include Statuses" hint="Select which result types to include">
      <CheckboxGroup
        options={statusFilterOptions}
        bind:selected={statusFilters}
        layout="horizontal"
      />
    </FormField>

    <div class="p-3 bg-mcat-bg rounded text-sm text-mcat-text-muted">
      <p class="m-0">
        Export will include all results matching the selected status filters.
        Original CSV columns that were preserved will also be included.
      </p>
    </div>
  </div>

  {#snippet actions()}
    <Button variant="secondary" onclick={onclose}>
      Cancel
    </Button>
    <Button
      variant="primary"
      onclick={handleExport}
      disabled={statusFilters.length === 0}
      {loading}
    >
      Export
    </Button>
  {/snippet}
</Dialog>
