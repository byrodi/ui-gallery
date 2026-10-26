# ui-gallery

Agent skill that shows every state of an app's UI on one page as live iframes of the real code over a fake backend.

Each frame is the real front-end code, clickable, fed by a fake backend in its own scenario.

It suits a design review, a check after a redesign, or a question like "what does this screen look
like when it is empty, offline or full of long names?". It works for web UIs (React, Vue, Svelte,
Solid, Angular, Next.js, plain HTML) and web-view desktop apps (Tauri, Electron). It is the
Storybook idea applied to whole screens, without adding a framework to the project.

## How it works

1. The agent reads the app: stack, entry point, where the UI gets its data, the real viewport size,
   existing stories, mocks and fixtures.
2. It lists every distinct state from the code (empty, loading, error, offline, modes, dialogs,
   first run, long content) and groups them.
3. It builds a harness outside the repository that imports the app's real code after a fake
   transport (fetch, MSW, axios, GraphQL, Tauri `invoke`, an Electron preload bridge).
4. A URL parameter picks the scenario; optional steps click through to dialogs and sheets.
5. The agent fills `assets/scenarios.template.json`, then `scripts/make_gallery.py` writes
   `gallery.html`: a numbered contents panel with group descriptions and preview cards with state
   notes, open/reload actions and status badges. Frames fit automatically; there are no zoom controls.
6. The agent checks that every frame rendered and opens the page in your browser.

The project's own files stay untouched unless you ask to keep the gallery.

## Usage

The skill loads when you ask to see or review an interface across states, for example "show me all
the screens of the app on one page" or "покажи все состояния интерфейса". To call it explicitly in
Claude Code:

```text
/ui-gallery:ui-gallery
```

## Install

Claude Code (remove or rename an existing `~/.claude/skills/ui-gallery` first):

```sh
git clone https://github.com/byrodi/ui-gallery ~/IdeaProjects/skills/ui-gallery
ln -s ~/IdeaProjects/skills/ui-gallery ~/.claude/skills/ui-gallery
```

Or through the [byrodi marketplace](https://github.com/byrodi/skills): `claude plugin marketplace add byrodi/skills`, then `claude plugin install ui-gallery@byrodi`.

Codex:

```sh
ln -s ~/IdeaProjects/skills/ui-gallery/skills/ui-gallery ~/.agents/skills/ui-gallery
```

Update with `git pull` in the clone. The browser check uses a chrome-devtools MCP server when one is available. The gallery script needs only Python 3.

## Contents

| Path | What it is |
|---|---|
| `skills/ui-gallery/SKILL.md` | The workflow the agent follows |
| `skills/ui-gallery/references/` | Harness per stack, fake backends per transport, how to choose scenarios |
| `skills/ui-gallery/assets/harness/` | Vite harness template: `index.html`, `boot.ts`, `fake-backend.ts`, `steps.ts`, `vite.config.mjs` |
| `skills/ui-gallery/assets/serve.sh` | Rebuilds the harness, writes the page and starts or stops the preview by its PID file |
| `skills/ui-gallery/assets/scenarios.template.json` | Ready scenario list to copy and fill; the generator supplies the layout and numbering |
| `skills/ui-gallery/scripts/make_gallery.py` | Writes the gallery page from a scenario list |
| `skills/ui-gallery/scripts/check_frames.js` | Browser check that every frame rendered |

## License

MIT
