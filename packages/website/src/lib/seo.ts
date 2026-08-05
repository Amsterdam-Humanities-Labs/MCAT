export interface PageMeta {
  title?: string;
  description?: string;
  ogImage?: string;
}

// Site-wide defaults; any page-level PageMeta layers on top of these.
export const site = {
  name: 'MCAT',
  url: 'https://amsterdam-humanities-labs.github.io', // Pages origin
  basePath: '/MCAT', // Pages project subpath; keep in sync with BASE_PATH in svelte.config
  description: 'Track content-moderation status across platforms.',
  ogImage: '/mcat_og.jpg', // in static/
  ogImageAlt: 'MCAT — the Moderation Content Analysis Tool',
  ogImageWidth: 1200,
  ogImageHeight: 630,
  locale: 'en_US',
};
