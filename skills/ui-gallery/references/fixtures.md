# Fake backends

The fake replaces the transport so the app's own API layer, validation and caches run unchanged.
Install it before any app module loads: many clients capture `fetch` or create an instance at
import time.

## Contents

- Rules that apply to every fake
- fetch
- MSW (Mock Service Worker)
- axios
- GraphQL (Apollo, urql, Relay)
- Tauri invoke and events
- Electron preload bridge
- WebSocket and EventSource
- Storage, time and randomness
- Reusing the project's own fixtures

## Rules that apply to every fake

- **Scenario from the URL.** Read `new URLSearchParams(location.search)` once, one parameter per
  independent dimension, defaults giving the normal case. Document them in a comment at the top.
- **Same shapes as production.** Build fixtures from the project's types, zod schemas, OpenAPI
  spec or test factories. A fixture the app rejects is a bug in the fixture, not a state to show.
- **Fail loudly on unknown requests.** Log the method and URL with `console.error` and answer 501
  instead of passing the request to the network. Match by path on any host, so absolute API URLs
  are caught too.
- **In-memory state for mutations.** Keep a small mutable store so creating, toggling or deleting
  works inside a frame.
- **Small delay.** 40 to 100 ms lets loading states flash the way they do in real use; a scenario
  such as `delay=3000` can show the loading state itself.
- **Made-up data only.** No real names, emails, tokens, keys, server addresses or customer data.

## fetch

The template `assets/harness/fake-backend.ts` overrides `window.fetch` with a route table. Keep the
real `fetch` for the harness's own assets. Errors: return a `Response` with the real error status
and body; network failure: `throw new TypeError('Failed to fetch')`.

## MSW (Mock Service Worker)

If the project already has MSW handlers, reuse them: start the browser worker in the fake backend
with `worker.start({ onUnhandledRequest: 'error', quiet: true })` and await it before importing the
app (use a dynamic `import('@app/main.tsx')` after `await worker.start()`). The worker script
(`mockServiceWorker.js`) must be served from the harness root (`npx msw init <harness>/public`).
Select handlers per scenario with `worker.use(...)` based on the URL parameters. Without existing
handlers, a fetch override is simpler and needs no service worker.

## axios

axios in the browser uses XMLHttpRequest, not fetch. Either set a custom adapter on the app's axios
instance before it is used (export it from the app module and set `instance.defaults.adapter`), or
use MSW, which intercepts XHR as well.

## GraphQL (Apollo, urql, Relay)

Intercept the HTTP endpoint and answer by `operationName` from the request body:
`{ data: ... }` for success, `{ errors: [...] }` for GraphQL errors. Keep `__typename` fields in the
fixtures, or normalized caches drop the data.

## Tauri invoke and events

```ts
import { mockIPC } from '@tauri-apps/api/mocks';
mockIPC((cmd, args) => {
  switch (cmd) {
    case 'list_items': return state === 'empty' ? [] : items;
    case 'save_item': return save(args);
    default: throw new Error(`no fixture for ${cmd}`);
  }
});
```

If the app calls `window.__TAURI_INTERNALS__.invoke` directly or wraps it with validation, override
that object instead, so the app's validators see exactly what they see in production. Events from
`listen()` need `transformCallback` to store callbacks, and a helper to fire them for scenarios that
depend on native events (window focus, drag and drop). Plugin commands use names like
`plugin:dialog|open`.

## Electron preload bridge

Read the preload script and recreate the object it exposes:

```ts
(window as any).api = {
  getSettings: async () => fixtures.settings,
  onStatus: (cb: (s: Status) => void) => { cb(fixtures.status); return () => {}; },
};
```

Keep method names, argument order and return types identical to the preload file.

## WebSocket and EventSource

Replace the constructor with a small class that opens asynchronously, sends scripted messages for
the scenario, and records what the app sends. Real-time screens often need a "connected" and a
"disconnected" scenario.

## Storage, time and randomness

- Frames of one origin share `localStorage`, `sessionStorage` per tab, cookies and IndexedDB. If the
  app persists state, prefix keys per scenario (wrap `Storage.prototype.getItem/setItem` to add the
  query string as a prefix) or clear storage at boot.
- Pin `Date.now` and, where the app formats the current time, `new Date()` with a fixed value, so
  relative times are stable. Seed or replace `Math.random` and `crypto.randomUUID` if IDs appear on
  screen.
- If the person wants still frames, add a style rule in the harness:
  `*, *::before, *::after { animation: none !important; transition: none !important; }`.

## Reusing the project's own fixtures

Look before writing new data: `__fixtures__`, `test/fixtures`, factories (`fishery`, `@faker-js` with
a fixed seed), Storybook `args`, Playwright or Cypress mocks, seed scripts, OpenAPI examples. Import
them from the harness through the alias rather than copying them. When such a file imports a test
runner (`vitest`, `@jest/globals`) for `vi.fn()` or similar, add a harness alias that points that
import at a tiny shim exporting what the fixtures use.

Validators decide the format, not intuition: if the app checks that an avatar is a PNG data URL or
that an ID has 16 hex digits, the fixture must satisfy that check, or the frame shows the app's
error screen instead of the state you meant.
