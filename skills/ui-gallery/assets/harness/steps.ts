/*
 * Scripted steps for a gallery frame: ?do=click:Settings,fill:Email=ann@example.com,wait:300
 * runs them in order after the first render. Steps match visible text, accessible names and roles,
 * never CSS classes, so they survive a restyle. Adapt the "ready" selector below to the app.
 *
 *   click:<text>          click the first enabled button, link, tab, switch, menu item or summary
 *                         whose visible text or aria-label equals <text> (inside an open dialog first)
 *   clickstart:<text>     the same, matching the start of the text (rows with extra text)
 *   fill:<label>=<value>  type into the field whose label, aria-label or placeholder is <label>
 *   key:<key>             press a key on the focused element (Escape, Enter, ArrowDown)
 *   scroll:bottom         scroll every scrollable area and open dialog to the bottom
 *   wait:<ms>             pause
 * When done, document.body.dataset.steps is "done", or "failed: <step>" on the first failure.
 */
export {};

const steps = (new URLSearchParams(location.search).get('do') ?? '').split(',').filter(Boolean);
const sleep = (ms: number): Promise<void> => new Promise((r) => setTimeout(r, ms));

async function find<T>(pick: () => T | null | undefined, ms = 4000): Promise<T> {
  const end = performance.now() + ms;
  for (;;) {
    const found = pick();
    if (found) return found;
    if (performance.now() > end) throw new Error('not found');
    await sleep(50);
  }
}

const scope = (): ParentNode => document.querySelector('dialog[open], [role=dialog]') ?? document;
const accessibleName = (el: Element): string => (el.getAttribute('aria-label') ?? el.textContent ?? '').replace(/\s+/g, ' ').trim();
const clickables = (): HTMLElement[] =>
  [...scope().querySelectorAll<HTMLElement>('button, a[href], [role=button], [role=tab], [role=switch], [role=menuitem], [role=radio], summary')]
    .filter((el) => !(el as HTMLButtonElement).disabled && el.getAttribute('aria-disabled') !== 'true');

function field(label: string): HTMLInputElement | HTMLTextAreaElement | null {
  const all = [...scope().querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('input, textarea')];
  return (
    all.find((el) => el.getAttribute('aria-label') === label || el.placeholder === label) ??
    all.find((el) => el.labels && [...el.labels].some((l) => accessibleName(l) === label)) ??
    null
  );
}

function type(el: HTMLInputElement | HTMLTextAreaElement, value: string): void {
  el.focus();
  // Use the native setter so React, Vue and others see the change as user input.
  const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, 'value')?.set?.call(el, value);
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
}

async function run(step: string): Promise<void> {
  const i = step.indexOf(':');
  const verb = i < 0 ? step : step.slice(0, i);
  const arg = i < 0 ? '' : step.slice(i + 1);
  switch (verb) {
    case 'click':
      (await find(() => clickables().find((el) => accessibleName(el) === arg))).click();
      break;
    case 'clickstart':
      (await find(() => clickables().find((el) => accessibleName(el).startsWith(arg)))).click();
      break;
    case 'fill': {
      const j = arg.indexOf('=');
      type(await find(() => field(arg.slice(0, j))), arg.slice(j + 1));
      break;
    }
    case 'key':
      (document.activeElement ?? document.body).dispatchEvent(new KeyboardEvent('keydown', { key: arg, bubbles: true }));
      break;
    case 'scroll':
      for (const el of document.querySelectorAll<HTMLElement>('*')) {
        if (el.scrollHeight > el.clientHeight + 1 && getComputedStyle(el).overflowY !== 'visible') el.scrollTop = el.scrollHeight;
      }
      window.scrollTo(0, document.body.scrollHeight);
      break;
    case 'wait':
      await sleep(Number(arg));
      break;
    default:
      throw new Error(`unknown step ${verb}`);
  }
  await sleep(250);
}

void (async () => {
  if (steps.length === 0) {
    document.body.dataset.steps = 'done';
    return;
  }
  // Wait for the first real render. Replace the selector with something the app always draws.
  await find(() => document.querySelector('main, nav, [role=main], button'), 8000).catch(() => undefined);
  await sleep(300);
  for (const step of steps) {
    try {
      await run(step);
    } catch {
      document.body.dataset.steps = `failed: ${step}`;
      return;
    }
  }
  document.body.dataset.steps = 'done';
})();
