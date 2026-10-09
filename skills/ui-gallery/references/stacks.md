# Harness per stack

Read only the section for the stack you found. In every case the harness imports the app's real
code and installs the fake backend before it; it never edits the app.

## Contents

- Vite apps: React, Vue, Svelte, Solid, Preact
- Tauri and Electron (web-view desktop apps)
- Next.js
- Angular
- Create React App, webpack and other bundlers
- Plain HTML and JavaScript
- Server-rendered pages (Rails, Django, Laravel, Spring, PHP)
- Projects with Storybook, Ladle or React Cosmos
- Out of scope

## Vite apps: React, Vue, Svelte, Solid, Preact

The template in `assets/harness/` is written for this case.

1. Copy the template to a scratch directory. Symlink `node_modules` to the app's own
   `node_modules`, so the harness uses the same React or Vue version and plugins as the app.
2. In `vite.config.mjs` set `APP` to the frontend directory, use the app's framework plugin, and copy
   its `resolve.alias` entries (also the ones that come from `tsconfig` paths through a plugin),
   `define`, and `css` options. If the app's config is simple, import it instead:
   `import base from '<app>/vite.config.ts'` and spread its plugins and resolve options.
3. In `index.html` use the same mount element as the app (`#root`, `#app`).
4. In `boot.ts` import the fake backend, then the app's entry (`@app/main.tsx`, `@app/main.ts`), then
   the steps. If the entry renders with providers that need runtime config (`window.__CONFIG__`,
   an env variable), set them in the fake backend file first.
5. Build and preview: `vite build --config vite.config.mjs --outDir dist` then `vite preview` on a
   fixed port. Write `gallery.html` into `dist/` after the build, because the build empties it.

If the entry reads `import.meta.env.VITE_*`, pass the same variables when building the harness, or
add them to `define`.

## Tauri and Electron (web-view desktop apps)

The renderer is a normal web app; only its bridge to the native side changes.

- **Tauri 2**: the front end calls `invoke()` from `@tauri-apps/api/core`, which goes through
  `window.__TAURI_INTERNALS__`. Either use `mockIPC((cmd, args) => ...)` from
  `@tauri-apps/api/mocks` in the fake backend, or define `window.__TAURI_INTERNALS__ = { invoke,
  transformCallback, ... }` yourself before the app loads. Events (`listen`) need
  `transformCallback` and a stored callback map if the app subscribes to native events.
- **Tauri 1**: `window.__TAURI_IPC__` and `@tauri-apps/api/tauri` `invoke`; `mockIPC` exists there too.
- **Electron**: the renderer usually calls an API that a preload script exposes with
  `contextBridge.exposeInMainWorld('api', {...})`. Read the preload file and define the same object
  on `window` in the fake backend, with the same method names and return shapes.
- Size each frame like the app's window: `tauri.conf.json` `app.windows[].width/height`, or the
  Electron `BrowserWindow` options. Subtract the native title bar if the content area is smaller.
- Native menus, tray items and notifications do not exist in the browser; leave them out and say so.

## Next.js

The App Router renders on the server, so importing pages into a Vite harness rarely works. Options,
in order of preference:

1. **Client-side mocking in `next dev`**: start MSW's browser worker (or a fetch override) from a
   client component that loads only when an environment flag such as `NEXT_PUBLIC_GALLERY=1` is
   set, and pass the scenario in the URL (`?state=empty`). Server components that fetch on the
   server need their data source mocked on the server instead (MSW `setupServer` in
   `instrumentation.ts`, or a fixture-backed API base URL pointing at a tiny local fixture server).
2. **Client components only**: if the screens are mostly client components, a Vite harness can
   import them with `next/navigation`, `next/link` and `next/image` aliased to small stubs.
3. **A fixture API server**: run the app normally against a local server that answers from fixtures
   by scenario, selected through a cookie or header set per frame URL.

Keep any gallery flag out of production builds and say where it lives.

## Angular

Add a gallery configuration instead of a separate Vite harness:

- an `HttpInterceptor` provided only in a `gallery` environment, answering from fixtures by the
  scenario in `location.search`;
- `ng serve --configuration gallery` or `ng build --configuration gallery` plus a static server.

This changes the repository (an environment file and a configuration entry), so do it in a scratch
copy or a branch unless the person asked to keep the gallery.

## Create React App, webpack and other bundlers

A Vite harness usually still works: point the alias at `src`, add the same JSX and CSS handling,
and stub CRA's `process.env.REACT_APP_*` through `define`. If the code depends on webpack-only
features (`require.context`, custom loaders), add the fake backend as an extra entry in a copy of
the webpack config instead.

## Plain HTML and JavaScript

Serve the app's files with any static server and load the fake backend first: copy `index.html` into
the harness with one extra `<script src="fake-backend.js"></script>` before the app's scripts, or
inject it with a small server rule. Relative asset paths must still resolve, so serve the app
directory and put the harness page next to it in the scratch copy.

## Server-rendered pages (Rails, Django, Laravel, Spring, PHP)

The state lives on the server, so the fake goes there:

- run the app locally against a throwaway database seeded per scenario, and give each scenario its
  own account or record so frames do not share state; or
- add a development-only route or middleware that renders a page from a fixture, if the framework
  makes that easy (Rails view previews, Django test client data, Spring profiles).

Frame URLs then point at real local routes. Never seed from production data.

## Projects with Storybook, Ladle or React Cosmos

Reuse what exists. Each story or fixture has an iframe URL:

- Storybook: `iframe.html?id=<story-id>&viewMode=story` on the Storybook server or static build
  (`storybook build`).
- Ladle: `/?story=<story-id>&mode=preview`.
- React Cosmos: the renderer URL with the fixture path.

Pick whole-screen stories for the gallery and write only `scenarios.json`. Add missing states as new
stories only if the person wants them kept.

## Out of scope

SwiftUI, AppKit, UIKit, Android views and Flutter on mobile or desktop do not render in a browser.
Say so, and suggest the platform's own tool: Xcode previews or snapshot tests, Android Studio
Compose previews or Paparazzi, Flutter golden tests. Flutter web builds work like any web app.
