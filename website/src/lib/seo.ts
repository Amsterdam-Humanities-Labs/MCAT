export interface PageMeta {
  title?: string;
  description?: string;
  ogImage?: string;
}

// Site-wide defaults; any page-level PageMeta layers on top of these.
export const site = {
  name: 'MCAT',
  url: 'https://mcat.example', // TODO: real domain
  description: 'Track content-moderation status across platforms.',
  ogImage: '/og-default.png', // in static/
};

// Merge a page's metadata over the site defaults into final <Seo> values.
export function resolveSeo(meta: PageMeta | undefined, pathname: string) {
  const ogImage = meta?.ogImage ?? site.ogImage;
  return {
    title: meta?.title ?? site.name,
    description: meta?.description ?? site.description,
    canonical: site.url + pathname,
    ogImage: ogImage.startsWith('http') ? ogImage : site.url + ogImage,
    siteName: site.name,
  };
}
