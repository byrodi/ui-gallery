// Paste this function into evaluate_script (chrome-devtools) on the open gallery page.
// It needs the gallery and the frames on one origin. It scrolls once so lazy frames load,
// waits for them, and returns one row per frame plus a list of problems.
async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  window.scrollTo(0, document.body.scrollHeight);
  await sleep(300);
  window.scrollTo(0, 0);
  const frames = [...document.querySelectorAll('iframe')];
  const deadline = Date.now() + 8000;
  const read = (f) => {
    let doc;
    try {
      doc = f.contentDocument;
    } catch {
      return { error: 'cross-origin frame: serve the gallery from the same origin' };
    }
    if (!doc || !doc.body) return { pending: true };
    const steps = doc.body.dataset.steps ?? null;
    const text = (doc.body.innerText || '').replace(/\s+/g, ' ').trim();
    const nodes = doc.body.querySelectorAll('*').length;
    return { steps, text: text.slice(0, 80), nodes, pending: steps === null && nodes < 5 };
  };
  let rows;
  for (;;) {
    rows = frames.map((f) => ({ title: f.title, url: f.getAttribute('src'), ...read(f) }));
    const waiting = rows.some((r) => r.pending || (r.steps !== null && r.steps !== 'done' && !String(r.steps).startsWith('failed')));
    if (!waiting || Date.now() > deadline) break;
    await sleep(250);
  }
  const problems = rows
    .filter((r) => r.error || r.pending || !r.text || (r.steps && r.steps !== 'done'))
    .map((r) => `${r.title}: ${r.error ?? (r.steps && r.steps !== 'done' ? `steps ${r.steps}` : 'blank or still loading')}`);
  return { frames: rows.length, problems, rows };
}
