import './app.css';
import App from './App.svelte';
import { mount } from 'svelte';
import { setBackendUrl } from '$lib/api/client';

// melt's Dialog uses the native Popover API, which older WebKit lacks
// (Safari < 17 / macOS Ventura). Load the polyfill only when it's actually
// missing, so modern webviews (Linux, Windows, current macOS) never fetch or
// run it — capability-gated, not OS-gated.
if (!('showPopover' in HTMLElement.prototype)) {
  await import('@oddbird/popover-polyfill');
}

// Backend URL is passed via query param (pywebview sets this) or defaults to dev port
const params = new URLSearchParams(window.location.search);
const port = params.get('port') || '9876';
setBackendUrl(`http://127.0.0.1:${port}`);

const app = mount(App, {
  target: document.getElementById('app')!,
});

export default app;
