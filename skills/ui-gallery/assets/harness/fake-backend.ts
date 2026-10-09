/*
 * Fake backend for the gallery: answers the app's HTTP calls from fixtures chosen by URL parameters.
 * Document every parameter here; each has a default that gives the normal case.
 *   state=ok|empty|error|offline   (default ok)
 *   items=few|long|none            (default few)
 *   delay=<ms>                     answer delay (default 60)
 * Made-up data only. An unmatched request fails loudly instead of reaching the network.
 */
export {};

type Json = unknown;
type Handler = (req: { url: URL; method: string; body: Json; match: RegExpMatchArray }) => Json | Response;

const q = new URLSearchParams(location.search);
const state = q.get('state') ?? 'ok';
const delay = Number(q.get('delay') ?? 60);

// Pin time so relative dates ("2 hours ago") do not change between loads.
const now = new Date('2026-01-15T10:00:00Z').getTime();
Date.now = () => now;

// In-memory state so clicks and forms work inside a frame.
const db = {
  items: q.get('items') === 'none' ? [] : [{ id: '1', name: 'First item' }, { id: '2', name: 'Second item' }],
};

const routes: Array<[string, RegExp, Handler]> = [
  ['GET', /\/api\/items$/, () => (state === 'error' ? new Response('{"error":"boom"}', { status: 500 }) : db.items)],
  ['POST', /\/api\/items$/, ({ body }) => {
    const item = { id: String(db.items.length + 1), ...(body as object) };
    db.items.push(item as never);
    return item;
  }],
];

const realFetch = window.fetch.bind(window);
window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  const req = new Request(input, init);
  const url = new URL(req.url, location.href);
  // Let the harness load its own assets.
  if (url.origin === location.origin && !url.pathname.startsWith('/api/')) return realFetch(input, init);
  await new Promise((r) => setTimeout(r, delay));
  if (state === 'offline') throw new TypeError('Failed to fetch');
  for (const [method, pattern, handle] of routes) {
    const match = url.pathname.match(pattern);
    if (req.method === method && match) {
      const text = req.method === 'GET' || req.method === 'HEAD' ? '' : await req.text();
      const out = handle({ url, method: req.method, body: text ? JSON.parse(text) : null, match });
      return out instanceof Response ? out : new Response(JSON.stringify(out), { headers: { 'content-type': 'application/json' } });
    }
  }
  console.error('gallery: no fixture for', req.method, url.href);
  return new Response('{"error":"no fixture"}', { status: 501 });
};
