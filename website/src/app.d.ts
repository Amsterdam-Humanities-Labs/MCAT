declare global {
  namespace App {
    interface PageData {
      meta?: import('./lib/seo').PageMeta;
      headings?: import('@mcat/ui/website').TocEntry[];
      showToc?: boolean;
    }
  }
}

export {};
