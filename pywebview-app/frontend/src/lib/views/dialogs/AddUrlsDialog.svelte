<script lang="ts">
  import { api } from '$lib/api/client';
  import { Dialog, Button, FilePickerInput, FormField } from '$lib/components';
  import type { ImportPreview } from '$types/csv';

  interface Props {
    open?: boolean;
    class?: string;
    onclose?: () => void;
    onimport?: (csvPath: string) => void;
  }

  let {
    open = $bindable(false),
    class: className,
    onclose,
    onimport,
  }: Props = $props();

  let csvPath = $state('');
  let preview = $state<ImportPreview | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);

  async function handleFileChange(path: string) {
    csvPath = path;
    if (!path) {
      preview = null;
      return;
    }

    loading = true;
    error = null;

    try {
      preview = await api.previewImport(path);
    } catch (e) {
      error = `Failed to preview CSV: ${e}`;
      preview = null;
    } finally {
      loading = false;
    }
  }

  function handleImport() {
    if (csvPath && preview && preview.new_urls > 0) {
      onimport?.(csvPath);
    }
  }

  function handleClose() {
    csvPath = '';
    preview = null;
    error = null;
    onclose?.();
  }

  const canImport = $derived(preview && preview.new_urls > 0 && !loading);
</script>

<Dialog bind:open title="Add URLs" onclose={handleClose} class={className}>
  <div class="space-y-4">
    <FormField label="CSV File" hint="Select a CSV file containing URLs to add">
      <FilePickerInput
        value={csvPath}
        onchange={handleFileChange}
        filters={[{ name: 'CSV', extensions: ['csv'] }]}
        placeholder="Select CSV file..."
        disabled={loading}
      />
    </FormField>

    {#if error}
      <div class="p-3 bg-status-removed/10 border border-status-removed/30 rounded text-base text-status-removed">
        {error}
      </div>
    {/if}

    {#if preview}
      <div class="p-4 bg-bg-primary rounded space-y-3">
        <h4 class="text-base font-medium text-text-body m-0">Import Preview</h4>

        <div class="grid grid-cols-3 gap-4">
          <div>
            <span class="block text-base text-text-secondary mb-1">Total in File</span>
            <span class="text-lg font-medium">{preview.total_in_file}</span>
          </div>
          <div>
            <span class="block text-base text-text-secondary mb-1">New URLs</span>
            <span class="text-lg font-medium text-status-live">{preview.new_urls}</span>
          </div>
          <div>
            <span class="block text-base text-text-secondary mb-1">Duplicates</span>
            <span class="text-lg font-medium text-text-secondary">{preview.duplicates_skipped}</span>
          </div>
        </div>

        {#if preview.new_urls === 0}
          <div class="p-2 bg-status-restricted/10 border border-status-restricted/30 rounded text-base text-status-restricted">
            All URLs in this file already exist in the project.
          </div>
        {:else if preview.sample_urls.length > 0}
          <div>
            <span class="block text-base text-text-secondary mb-2">Sample URLs to add:</span>
            <div class="space-y-1 max-h-32 overflow-auto">
              {#each preview.sample_urls.slice(0, 5) as url}
                <div class="text-base text-text-secondary font-mono truncate" title={url}>
                  {url}
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>

  {#snippet actions()}
    <Button variant="secondary" onclick={handleClose}>
      Cancel
    </Button>
    <Button
      variant="primary"
      onclick={handleImport}
      disabled={!canImport}
      {loading}
    >
      Import {preview?.new_urls ?? 0} URLs
    </Button>
  {/snippet}
</Dialog>
