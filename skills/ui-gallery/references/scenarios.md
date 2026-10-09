# Choosing scenarios

A gallery is useful when every frame answers a question a reviewer has. Derive the states from the
code, then keep the ones that matter for this review.

## Where states hide in code

- Status enums and union types (`'idle' | 'loading' | 'error'`), and every `switch` or ternary on them.
- Empty branches: `items.length === 0`, "No results", empty-state components.
- Error and offline branches: error boundaries, `isError`, toast and banner components, retry buttons.
- Loading: skeletons, spinners, disabled buttons while pending.
- Permissions and roles: admin versus member, read-only, locked features, trial or paid plans.
- Modes and toggles in global state: theme, compact or full, a global switch, feature flags.
- Overlays: dialogs, sheets, drawers, menus, popovers, confirmation steps, destructive actions.
- Onboarding: first run, empty account, setup wizards, permission prompts.
- Content stress: the longest realistic names, many items, very long translated strings, right-to-left
  text if supported, large numbers.
- Viewports: the phone, tablet and desktop widths the CSS actually distinguishes.

## What every gallery should contain

1. The main screen in its normal, populated state.
2. The same screen empty.
3. Loading, if it is visible for more than a moment in real use.
4. An error or offline state with its recovery action.
5. The longest realistic content (a long list, long names).
6. Each global mode the product has (one frame per mode).
7. The most important dialog or sheet, opened through steps.
8. The other main screens or tabs in their normal state.
9. First run or onboarding, if the product has one.
10. Any state the person asked about or the latest change touched.

Then go through every screen and add its remaining distinct states. Skip a state only when its frame
would look the same as another one. Group frames by screen or by topic, and order groups the way a
user meets them.

## Captions

Each caption has a short title naming the state and an optional note saying how to get there or
what to look at: "Paused: all apps go direct", "Long list: the Add button stays visible". Write
captions in the reviewer's language; the UI keeps its own language.
