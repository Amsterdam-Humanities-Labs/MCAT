import { site } from '$lib/seo';
import { base } from '$app/paths';

export const prerender = true;

export function GET() {
  const body = `User-agent: *
Allow: /

Sitemap: ${site.url}${base}/sitemap.xml
`;

  return new Response(body, { headers: { 'Content-Type': 'text/plain' } });
}
