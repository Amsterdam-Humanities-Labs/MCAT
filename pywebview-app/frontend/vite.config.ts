import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  clearScreen: false,
  plugins: [svelte(), tailwindcss()],
  resolve: {
    alias: {
      $lib: path.resolve('./src/lib'),
      $types: path.resolve('./src/types'),
    },
  },
  server: {
    port: 5180,
    strictPort: false,
    hmr: true,  // Disable WebSocket HMR to avoid WebKit crash on Linux
  },
})
