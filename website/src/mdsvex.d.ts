declare module '*.md' {
  export const metadata: Record<string, unknown>;
  const component: import('svelte').Component;
  export default component;
}
