// Gallery harness: serves the app's real source through Vite with a fake backend.
//   APP=/path/to/frontend ./node_modules/.bin/vite build --config vite.config.mjs --outDir dist --emptyOutDir
//   ./node_modules/.bin/vite preview --config vite.config.mjs --outDir dist --port 5198 --strictPort
// node_modules is a symlink to the app's own node_modules, so versions match the app.
// Copy what matters from the app's vite config: the framework plugin, resolve.alias, define, css.
import react from '@vitejs/plugin-react'; // or @vitejs/plugin-vue, @sveltejs/vite-plugin-svelte, ...
import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const app = process.env.APP ?? '/absolute/path/to/the/frontend';

export default defineConfig({
  root: here,
  plugins: [react()],
  clearScreen: false,
  resolve: {
    alias: {
      '@app': path.join(app, 'src'),
      // Repeat the app's own aliases, for example: '@': path.join(app, 'src'),
    },
  },
  // Repeat the app's define and env handling if its code reads import.meta.env or globals.
  server: { port: 5199, strictPort: true, fs: { allow: [here, app] } },
});
