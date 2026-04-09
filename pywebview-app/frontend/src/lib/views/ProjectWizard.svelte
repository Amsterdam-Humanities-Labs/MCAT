<script lang="ts">
  import { cn } from '$lib/utils';
  import { FormState, rules } from '$lib/utils/form.svelte';
  import {
    Button,
    Input,
    Select,
    FormField,
    FilePickerInput,
    FolderPickerInput,
  } from '$lib/components';
  import type { Platform } from '$types/project';
  import type { wizardStore as WizardStoreType } from '$lib/stores/wizard.svelte';

  interface Props {
    wizard: typeof WizardStoreType;
    class?: string;
    oncancel?: () => void;
    oncomplete?: (data: ReturnType<typeof WizardStoreType.getCreateData>) => void;
  }

  let {
    wizard,
    class: className,
    oncancel,
    oncomplete,
  }: Props = $props();

  const platformOptions = [
    { value: 'youtube', label: 'YouTube' },
    { value: 'instagram', label: 'Instagram' },
    { value: 'facebook', label: 'Facebook' },
    { value: 'twitter', label: 'Twitter / X' },
  ];

  const form = new FormState({
    name: { value: '', rules: [rules.required('Project name is required')] },
    platform: { value: '', rules: [rules.selected('Please select a platform')] },
    location: { value: '', rules: [rules.required('Project location is required')] },
    csv_path: { value: '', rules: [rules.required('Source CSV is required')] },
    url_column: { value: '', rules: [rules.selected('Please select the URL column')] },
  });

  const columnOptions = $derived(
    wizard.columns.map((col) => ({ value: col, label: col }))
  );

  async function handleCsvChange(path: string) {
    form.setValue('csv_path', path);
    if (path) {
      await wizard.loadCsvColumns(path);
    }
  }

  function handleCreate() {
    form.touchAll();

    if (form.valid) {
      wizard.setName(form.getValue('name'));
      wizard.setPlatform(form.getValue('platform') as Platform);
      wizard.setLocation(form.getValue('location'));
      wizard.setUrlColumn(form.getValue('url_column'));
      oncomplete?.(wizard.getCreateData());
    }
  }

  function handleCancel() {
    wizard.reset();
    form.reset();
    oncancel?.();
  }
</script>

<div class={cn('h-screen flex items-center justify-center bg-bg-timeline', className)}>
<div class="max-w-lg w-full">
  <div class="bg-bg-controls border border-border-mid rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-border-mid">
      <h2 class="text-lg font-semibold text-text-primary m-0">
        Create New Project
      </h2>
    </div>

    <!-- Content -->
    <div class="p-6">
      {#if wizard.error}
        <div class="mb-4 p-3 bg-status-removed/10 border border-status-removed/30 rounded text-base text-status-removed">
          {wizard.error}
        </div>
      {/if}

      <div class="space-y-4">
        <FormField label="Project Name" required error={form.fields.name.error}>
          <Input
            value={form.fields.name.value}
            oninput={(e) => form.setValue('name', (e.target as HTMLInputElement).value)}
            placeholder="My Research Project"
            error={form.fields.name.error}
          />
        </FormField>

        <FormField label="Platform" required error={form.fields.platform.error}>
          <Select
            options={platformOptions}
            value={form.fields.platform.value}
            onchange={(val) => form.setValue('platform', val)}
            placeholder="Select platform..."
            error={form.fields.platform.error}
          />
        </FormField>

        <FormField label="Project Location" required hint="Where project files will be stored" error={form.fields.location.error}>
          <FolderPickerInput
            value={form.fields.location.value}
            onchange={(path) => form.setValue('location', path)}
            placeholder="Select folder..."
            error={form.fields.location.error}
          />
        </FormField>

        <FormField label="Source CSV" required hint="CSV file containing URLs to analyze" error={form.fields.csv_path.error}>
          <FilePickerInput
            value={form.fields.csv_path.value}
            onchange={handleCsvChange}
            filters={[{ name: 'CSV', extensions: ['csv'] }]}
            placeholder="Select CSV file..."
            error={form.fields.csv_path.error}
          />
        </FormField>

        {#if wizard.columns.length > 0}
          <FormField
            label="URL Column"
            required
            hint="Column containing the URLs to analyze"
            error={form.fields.url_column.error}
          >
            <Select
              options={columnOptions}
              value={form.fields.url_column.value}
              onchange={(val) => form.setValue('url_column', val)}
              placeholder="Select URL column..."
              error={form.fields.url_column.error}
            />
          </FormField>
        {/if}
      </div>
    </div>

    <!-- Footer -->
    <div class="px-6 py-4 border-t border-border-mid flex justify-between">
      <Button variant="secondary" onclick={handleCancel}>
        Cancel
      </Button>

      <Button
        variant="primary"
        onclick={handleCreate}
        loading={wizard.loading}
        disabled={!form.valid}
      >
        Create Project
      </Button>
    </div>
  </div>
</div>
</div>
