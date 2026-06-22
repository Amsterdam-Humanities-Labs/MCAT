// melt's Dialog/Select use the native Popover API. This polyfill self-gates
// (it patches only on WebKit that lacks it, e.g. Safari < 17, and no-ops where
// native), so a plain import is both correct and the simplest option.
import '@oddbird/popover-polyfill';
import './app.css';
import App from './App.svelte';
import { mount } from 'svelte';
import { setBackendUrl } from '$lib/api/client';

// Backend URL is passed via query param (pywebview sets this) or defaults to dev port
const params = new URLSearchParams(window.location.search);
const port = params.get('port') || '9876';
setBackendUrl(`http://127.0.0.1:${port}`);

const app = mount(App, {
  target: document.getElementById('app')!,
});

export default app;
