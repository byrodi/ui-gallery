---
name: ui-gallery
description: Builds a one-page live gallery of an application's UI states - every important screen and state (normal, empty, loading, error, offline, long content, dialogs, modes, first run) shown side by side as live, clickable iframes of the real UI code running over a fake backend - and opens it in the browser for review. Use it whenever someone wants to see, review, evaluate or compare an interface across states or scenarios, after a UI change or redesign, or before asking for design feedback, even if they never say "gallery" - for example "show me all the screens", "all scenarios on one page", "I want to evaluate the interface", "storybook-like page", "покажи все состояния", "все сценарии на одной странице", "витрина экранов", "хочу оценить интерфейс". Works for web UIs (React, Vue, Svelte, Solid, Angular, Next.js, plain HTML) and web-view desktop apps (Tauri, Electron). Not for a single screenshot, a visual-regression CI setup, a design mockup with no code behind it, or native UIs that do not render in a browser.
---

# UI gallery

A UI gallery is one web page that shows the real interface in many states at once. Each state is a
live iframe of the application's own front-end code, fed by a fake backend that a URL parameter puts
into a scenario. A reviewer sees every state side by side, clicks inside any of them, and judges
the design in minutes instead of paging through screenshots. Storybook, React Cosmos and Ladle use
the same idea per component; this skill does it for whole screens, with no new framework in the
project.

The parts:

1. **Harness**: a small build that imports the app's real entry point, after a fake transport is
   installed, so production components, validators and state logic all run unchanged.
2. **Fake backend**: replaces the app's boundary to the outside world (HTTP, IPC, a preload bridge,
   websockets) and answers from fixtures picked by URL parameters, for example `?state=paused`.
3. **Steps** (optional): `?do=` actions that click by visible text or accessible name to reach states
   that need interaction, such as an open dialog.
4. **Gallery page**: `scripts/make_gallery.py` turns a scenario list into `gallery.html`, a grid of
   captioned iframes at the app's real viewport size.

## Workflow

### 1. Read the app first

Find, from the code rather than by guessing:

- the stack, the bundler and the front-end entry point (`main.tsx`, `main.ts`, `index.html`, an
  Angular `main.ts`, a Next.js `app/` tree);
- the boundary where the UI gets data: a fetch or axios client and its base URL, React Query or SWR
  fetchers, a GraphQL client, Tauri `invoke`, an Electron preload API on `window`, websockets,
  `localStorage`;
- what already exists to reuse: Storybook stories, MSW handlers, test fixtures and factories,
  OpenAPI or zod schemas, demo data;
- the real viewport: a desktop window size (Tauri `tauri.conf.json`, Electron `BrowserWindow`), the
  mobile breakpoints, or the layout the product is designed for;
- gates that would block rendering: auth redirects, a first-run or onboarding gate, feature flags,
  locale detection, a service worker.

If the project has Storybook, Ladle or React Cosmos with stories that cover whole screens, skip the
harness and point the gallery at their iframe URLs (Storybook: `iframe.html?id=<story-id>&viewMode=story`).

Read [references/stacks.md](references/stacks.md) for the stack you found.

### 2. Choose the scenarios

List the states from the code itself: status enums, union types, error branches, empty branches,
loading flags, dialogs, sheets and menus, modes and toggles, roles and permissions, first run, long
or translated text. [references/scenarios.md](references/scenarios.md) has a checklist.

Cover every distinct state the person would want to judge, not a sample: people use the gallery to
see all scenarios at once. A small app has about 10 to 20 states, a larger one 30 to 60. Group them
by screen or by topic in the order a user meets them. Always include the main happy path, an empty
state, an error or offline state, and the longest realistic content. Leave out states that look the
same as another frame, and say which areas you left out. If the main task of the app is unclear, ask
one question; otherwise decide and say what you chose.

### 3. Build the harness without touching the app

Put the harness outside the repository by default (the session scratchpad or a temp directory), so
the project's tree and git status stay clean. The harness imports the app's source through an alias
and adds nothing to it. Build it in the repository only when the person wants the gallery kept; then
use a clearly named directory (for example `fixtures/` or `app/gallery/`), a script or make target
to start it, and gitignored build output.

Start from `assets/harness/`: `index.html`, `boot.ts`, `fake-backend.ts`, `steps.ts` and a
`vite.config.mjs` template, plus `assets/serve.sh`.
`boot.ts` installs the fake transport first, then imports the real entry, then the step runner. Copy
the app's own bundler settings that matter (framework plugin, path aliases from `tsconfig`, `define`
and env variables, CSS preprocessors) instead of inventing new ones.

### 4. Fake the backend at the boundary

Replace the transport, not the components: the real API layer, its validation and its caches then
run exactly as in production, and a fixture that does not match the real schema shows up as an
error in the frame instead of a false picture. [references/fixtures.md](references/fixtures.md)
covers fetch, MSW, axios, GraphQL, Tauri, Electron and websockets.

- One URL parameter per independent dimension (`state=`, `items=none|few|long`, `role=`, `fail=`),
  each with a default that gives the normal case, documented in a comment at the top of the file.
- Made-up labels and data only. Never copy real accounts, keys, tokens or personal data into
  fixtures.
- Pin what makes frames differ between loads: the current date (`Date.now`), random IDs, and
  animations if the person wants still frames.
- Give mutations a believable answer and keep the state in memory, so toggles and forms work when
  clicked.
- Frames of one origin share `localStorage`, cookies and IndexedDB. If the app stores state there,
  give each scenario its own namespace (for example by wrapping `Storage` with a key prefix taken
  from the scenario), or every frame shows the last writer's state.

### 5. Reach interactive states with steps

For a dialog, a sheet, a filled form or a scrolled list, add `?do=step|step` (or repeat `do=`) and
run the steps from `steps.ts` after the first render. Steps are separated by `|`, because visible
texts often contain commas. Match visible text, accessible names and roles, never CSS class names, so
the steps survive a restyle. Set the runner's "ready" selector to something that appears only after
the data has loaded; a loading screen that already has `<main>` would start the steps too early. The
runner sets `document.body.dataset.steps` to `done` or `failed: <step>`, which the check in step 7
reads.

### 6. Build, serve and generate the page

Serve a production build of the harness (`vite build` then `vite preview`, or the stack's
equivalent) on a fixed free port. Development servers often run effects twice (React StrictMode) or
inject overlays, and that can show states the real app never shows. Use the dev server only while
iterating on fixtures.

Write the scenario list as JSON and generate the page into the served root, so the gallery and the
frames share one origin (the check in step 7 and the page's own status badges need that):

```sh
python3 scripts/make_gallery.py scenarios.json --out <served-root>/gallery.html
```

Copy `make_gallery.py`, `scenarios.json` and `assets/serve.sh` into the harness, so the gallery can
be rebuilt and restarted without this skill. `serve.sh` builds, writes the page, starts the preview
in the background with a PID file and prints the URL; `serve.sh stop` stops exactly that process.

The JSON format is in the docstring of `scripts/make_gallery.py`. Write the title, the lead and the
captions in the reviewer's language, and keep the UI itself in its own language. Say in the lead
that the data is made up and that every frame is clickable. Set the frame size to the app's real
viewport; wide frames are scaled down automatically and keep an "open" link to full size. The page
has jump links to every group, a zoom control, a status badge on each frame (rendered, steps failed,
blank) and lazy loading once it holds more than 16 frames.

### 7. Check every frame

Before showing the page, open it in a browser you control (with the chrome-devtools skill if it is
available) and run `scripts/check_frames.js` through `evaluate_script`. It lists every frame with
its rendered text, the step status and any blank or failed frame. Fix blank frames, failed steps and
console errors, then check again. Also read a few frames' text yourself to confirm each shows the
state its caption promises, not just something. Take a screenshot of the gallery if the person
cannot open a browser; the chrome-devtools server saves files only inside its workspace root, so
save there and move the file.

### 8. Hand it over

Open the page in the person's default browser (`open` on macOS, `xdg-open` on Linux, `start` on
Windows), give the URL, list the groups in a few words, and say that the server keeps running in
the background and how to stop it (`serve.sh stop`). Mention anything you knowingly left out. Offer
to keep the gallery in the repository if it lives in a temporary directory.

Stop servers only by their PID or port (`kill $(cat <pidfile>)`, `lsof -t -iTCP:<port> -sTCP:LISTEN`).
Never use `pkill -f` on a command line: other galleries and other sessions run the same
`vite preview` command, and a pattern match kills theirs too.

## Pitfalls

- **Wrong viewport.** A phone-shaped or fixed-size desktop window rendered at full browser width
  shows a layout the product never has. Size frames from the app's configuration.
- **Mocking components instead of the boundary.** Hand-made props skip the real data flow and its
  validation; the gallery then shows states that cannot occur.
- **Auth and first-run gates.** Fake a signed-in session and a completed onboarding by default, and
  make the gate itself one explicit scenario.
- **Absolute API URLs.** A fake that only matches relative paths lets requests to
  `https://api.example.com` escape to the network. Match by path on any host, and fail loudly on an
  unmatched request instead of passing it through.
- **Frame-blocking headers.** `X-Frame-Options` or a CSP `frame-ancestors` rule from the app's server
  blocks iframes. The harness serves its own build, so do not copy those headers into it.
- **Service workers and caches.** Disable registration in the harness, or frames show stale builds.
- **Many frames.** Each frame boots the whole app. Use the production build, keep lazy loading on for
  large pages, and prefer one well-grouped page over several small ones.
- **Test-only imports in fixtures.** Reusing the app's test fixtures is good, but a fixture file that
  imports `vitest` or `jest` fails in the browser; alias that import to a small shim.

## Done when

- Every frame renders the intended state, the check reports no blank or failed frame, and the steps
  status is `done` where steps are used.
- The real front-end code runs unchanged; the repository has no new or modified files unless the
  person asked to keep the gallery.
- Captions name each state in the reviewer's language, and the page says the data is fake.
- The page is open in the person's browser and they have the URL and the way to stop the server.
