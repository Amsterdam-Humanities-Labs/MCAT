import { site } from '$lib/seo';
import { base } from '$app/paths';

export const prerender = true;

// Every page on the site. Add new top-level routes here.
const routes = ['/', '/download', '/docs', '/policies', '/about'];

export function GET() {
  const urls = routes
    .map((r) => `  <url><loc>${site.url}${base}${r}</loc></url>`)
    .join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`;

  return new Response(xml, { headers: { 'Content-Type': 'application/xml' } });
}
