export interface CsvInfo {
  columns: string[];
  row_count: number;
}

export interface ImportPreview {
  total_in_file: number;
  new_urls: number;
  duplicates_skipped: number;
  sample_urls: string[];
}
