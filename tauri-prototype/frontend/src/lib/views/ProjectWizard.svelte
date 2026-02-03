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
    CheckboxGroup,
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
  ];

  // Step 1 form
  const step1Form = new FormState({
    name: { value: '', rules: [rules.required('Project name is required')] },
    platform: { value: '', rules: [rules.selected('Please select a platform')] },
    location: { value: '', rules: [rules.required('Project location is required')] },
    csvPath: { value: '', rules: [rules.required('Source CSV is required')] },
  });

  // Step 2 form
  const step2Form = new FormState({
    urlColumn: { value: '', rules: [rules.selected('Please select the URL column')] },
  });

  const columnOptions = $derived(
    wizard.columns.map((col) => ({ value: col, label: col }))
  );

  async function handleCsvChange(path: string) {
    step1Form.setValue('csvPath', path);
    if (path) {
      await wizard.loadCsvColumns(path);
    }
  }

  function handleBack() {
    wizard.setStep(1);
  }

  function handleNext() {
    step1Form.touchAll();

    if (step1Form.valid) {
      // Sync to wizard store
      wizard.setName(step1Form.getValue('name'));
      wizard.setPlatform(step1Form.getValue('platform') as Platform);
      wizard.setLocation(step1Form.getValue('location'));
      wizard.setStep(2);
    }
  }

  function handleCreate() {
    step2Form.touchAll();

    if (step1Form.valid && step2Form.valid) {
      wizard.setUrlColumn(step2Form.getValue('urlColumn'));
      oncomplete?.(wizard.getCreateData());
    }
  }

  function handleCancel() {
    wizard.reset();
    step1Form.reset();
    step2Form.reset();
    oncancel?.();
  }
</script>

<div class={cn('max-w-lg mx-auto', className)}>
  <div class="bg-mcat-card border border-mcat-border rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-mcat-border">
      <h2 class="text-lg font-semibold text-white m-0">
        Create New Project
      </h2>
      <p class="text-sm text-mcat-text-muted mt-1">
        Step {wizard.step} of 2
      </p>
    </div>

    <!-- Step indicator -->
    <div class="px-6 py-3 bg-mcat-bg/50 border-b border-mcat-border">
      <div class="flex gap-2">
        <div
          class={cn(
            'flex-1 h-1 rounded-full transition-colors',
            wizard.step >= 1 ? 'bg-mcat-orange' : 'bg-mcat-border'
          )}
        ></div>
        <div
          class={cn(
            'flex-1 h-1 rounded-full transition-colors',
            wizard.step >= 2 ? 'bg-mcat-orange' : 'bg-mcat-border'
          )}
        ></div>
      </div>
    </div>

    <!-- Content -->
    <div class="p-6">
      {#if wizard.error}
        <div class="mb-4 p-3 bg-mcat-error-bg border border-mcat-error/30 rounded text-sm text-mcat-error">
          {wizard.error}
        </div>
      {/if}

      {#if wizard.step === 1}
        <!-- Step 1: Basic Info -->
        <div class="space-y-4">
          <FormField label="Project Name" required error={step1Form.fields.name.error}>
            <Input
              value={step1Form.fields.name.value}
              oninput={(e) => step1Form.setValue('name', (e.target as HTMLInputElement).value)}
              placeholder="My Research Project"
              error={step1Form.fields.name.error}
            />
          </FormField>

          <FormField label="Platform" required error={step1Form.fields.platform.error}>
            <Select
              options={platformOptions}
              value={step1Form.fields.platform.value}
              onchange={(val) => step1Form.setValue('platform', val)}
              placeholder="Select platform..."
              error={step1Form.fields.platform.error}
            />
          </FormField>

          <FormField label="Project Location" required hint="Where project files will be stored" error={step1Form.fields.location.error}>
            <FolderPickerInput
              value={step1Form.fields.location.value}
              onchange={(path) => step1Form.setValue('location', path)}
              placeholder="Select folder..."
              error={step1Form.fields.location.error}
            />
          </FormField>

          <FormField label="Source CSV" required hint="CSV file containing URLs to analyze" error={step1Form.fields.csvPath.error}>
            <FilePickerInput
              value={step1Form.fields.csvPath.value}
              onchange={handleCsvChange}
              filters={[{ name: 'CSV', extensions: ['csv'] }]}
              placeholder="Select CSV file..."
              error={step1Form.fields.csvPath.error}
            />
          </FormField>
        </div>
      {:else}
        <!-- Step 2: Column Configuration -->
        <div class="space-y-4">
          <FormField
            label="URL Column"
            required
            hint="Column containing the URLs to analyze"
            error={step2Form.fields.urlColumn.error}
          >
            <Select
              options={columnOptions}
              value={step2Form.fields.urlColumn.value}
              onchange={(val) => step2Form.setValue('urlColumn', val)}
              placeholder="Select URL column..."
              disabled={wizard.columns.length === 0}
              error={step2Form.fields.urlColumn.error}
            />
          </FormField>

          {#if wizard.columns.length > 0}
            {@const availableColumns = columnOptions.filter((o) => o.value !== step2Form.fields.urlColumn.value)}
            {@const allSelected = availableColumns.length > 0 && wizard.preserveColumns.length === availableColumns.length}
            <FormField
              label="Preserve Columns"
              hint="Additional columns to keep in results (optional)"
            >
              {#if availableColumns.length > 0}
                <button
                  type="button"
                  class="text-xs text-mcat-orange hover:text-mcat-orange/80 mb-2"
                  onclick={() => {
                    if (allSelected) {
                      wizard.setPreserveColumns([]);
                    } else {
                      wizard.setPreserveColumns(availableColumns.map(c => c.value));
                    }
                  }}
                >
                  {allSelected ? 'Deselect All' : 'Select All'}
                </button>
              {/if}
              <CheckboxGroup
                options={availableColumns}
                selected={wizard.preserveColumns}
                onchange={(selected) => wizard.setPreserveColumns(selected)}
                layout="vertical"
              />
            </FormField>
          {/if}
        </div>
      {/if}
    </div>

    <!-- Footer -->
    <div class="px-6 py-4 border-t border-mcat-border flex justify-between">
      <Button variant="ghost" onclick={handleCancel}>
        Cancel
      </Button>

      <div class="flex gap-2">
        {#if wizard.step === 2}
          <Button variant="secondary" onclick={handleBack}>
            Back
          </Button>
        {/if}

        {#if wizard.step === 1}
          <Button
            variant="primary"
            onclick={handleNext}
            disabled={!step1Form.valid}
          >
            Next
          </Button>
        {:else}
          <Button
            variant="primary"
            onclick={handleCreate}
            loading={wizard.loading}
            disabled={!step2Form.valid}
          >
            Create Project
          </Button>
        {/if}
      </div>
    </div>
  </div>
</div>
