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
  ];

  // Step 1 form
  const step1Form = new FormState({
    name: { value: '', rules: [rules.required('Project name is required')] },
    platform: { value: '', rules: [rules.selected('Please select a platform')] },
    location: { value: '', rules: [rules.required('Project location is required')] },
    csv_path: { value: '', rules: [rules.required('Source CSV is required')] },
  });

  // Step 2 form
  const step2Form = new FormState({
    url_column: { value: '', rules: [rules.selected('Please select the URL column')] },
  });

  const columnOptions = $derived(
    wizard.columns.map((col) => ({ value: col, label: col }))
  );

  async function handleCsvChange(path: string) {
    step1Form.setValue('csv_path', path);
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
      wizard.setUrlColumn(step2Form.getValue('url_column'));
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
  <div class="bg-bg-controls border border-border-mid rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-border-mid">
      <h2 class="text-lg font-semibold text-text-primary m-0">
        Create New Project
      </h2>
      <p class="text-sm text-text-muted mt-1">
        Step {wizard.step} of 2
      </p>
    </div>

    <!-- Step indicator -->
    <div class="px-6 py-3 bg-bg-primary/50 border-b border-border-mid">
      <div class="flex gap-2">
        <div
          class={cn(
            'flex-1 h-1 rounded-full transition-colors',
            wizard.step >= 1 ? 'bg-accent-brown' : 'bg-border-mid'
          )}
        ></div>
        <div
          class={cn(
            'flex-1 h-1 rounded-full transition-colors',
            wizard.step >= 2 ? 'bg-accent-brown' : 'bg-border-mid'
          )}
        ></div>
      </div>
    </div>

    <!-- Content -->
    <div class="p-6">
      {#if wizard.error}
        <div class="mb-4 p-3 bg-status-removed/10 border border-status-removed/30 rounded text-sm text-status-removed">
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

          <FormField label="Source CSV" required hint="CSV file containing URLs to analyze" error={step1Form.fields.csv_path.error}>
            <FilePickerInput
              value={step1Form.fields.csv_path.value}
              onchange={handleCsvChange}
              filters={[{ name: 'CSV', extensions: ['csv'] }]}
              placeholder="Select CSV file..."
              error={step1Form.fields.csv_path.error}
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
            error={step2Form.fields.url_column.error}
          >
            <Select
              options={columnOptions}
              value={step2Form.fields.url_column.value}
              onchange={(val) => step2Form.setValue('url_column', val)}
              placeholder="Select URL column..."
              disabled={wizard.columns.length === 0}
              error={step2Form.fields.url_column.error}
            />
          </FormField>
        </div>
      {/if}
    </div>

    <!-- Footer -->
    <div class="px-6 py-4 border-t border-border-mid flex justify-between">
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
