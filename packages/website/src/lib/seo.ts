export interface PageMeta {
  title?: string;
  description?: string;
  ogImage?: string;
}

// Site-wide defaults; any page-level PageMeta layers on top of these.
export const site = {
  name: 'MCAT',
  url: 'https://amsterdam-humanities-labs.github.io', // Pages origin; the /MCAT base path is added by page pathnames
  description: 'Track content-moderation status across platforms.',
  ogImage: '/og-default.png', // in static/
};
