export interface CsvInfo {
  columns: string[];
  rowCount: number;
}

export interface ImportPreview {
  totalInFile: number;
  newUrls: number;
  duplicatesSkipped: number;
  sampleUrls: string[];
}
