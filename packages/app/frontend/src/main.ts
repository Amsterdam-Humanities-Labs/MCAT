// melt's Dialog/Select use the native Popover API. This polyfill self-gates
// (it patches only on WebKit that lacks it, e.g. Safari < 17, and no-ops where
// native), so a plain import is both correct and the simplest option.
import '@oddbird/popover-polyfill';
import './app.css';
import App from './App.svelte';
import { mount } from 'svelte';
import { setBackendUrl, setAuthToken } from '$lib/api/client';

// Backend URL is passed via query param (pywebview sets this) or defaults to dev port
const params = new URLSearchParams(window.location.search);
const port = params.get('port') || '9876';
setBackendUrl(`http://127.0.0.1:${port}`);

// The URL is the only copy the backend hands over, so mirror it into
// sessionStorage: a reload or navigation that drops the query string would
// otherwise leave every API call unauthenticated.
//
// sessionStorage, not localStorage: the backend mints a new token per launch,
// and a per-window lifetime matches that. localStorage would persist a stale
// token across launches.
//
// The URL wins when both are present, so a fresh launch is never shadowed by a
// leftover value from an earlier session in the same window.
const TOKEN_KEY = 'mcat_token';
const urlToken = params.get('token') || '';
if (urlToken) {
  sessionStorage.setItem(TOKEN_KEY, urlToken);
}
setAuthToken(urlToken || sessionStorage.getItem(TOKEN_KEY) || '');

const app = mount(App, {
  target: document.getElementById('app')!,
});

export default app;
