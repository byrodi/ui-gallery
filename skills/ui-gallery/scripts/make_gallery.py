#!/usr/bin/env python3
"""Write a one-page gallery of live UI states from a scenario list.

Usage:
    python3 make_gallery.py scenarios.json --out <served-root>/gallery.html

The scenario file is JSON:

    {
      "title": "Tunnelet: interface states",
      "lead": "Real app code over a fake backend. Every frame is clickable; the data is made up.",
      "lang": "en",
      "frame": {"width": 380, "height": 687},
      "max_width": 480,
      "groups": [
        {
          "title": "Apps",
          "scenarios": [
            {"title": "Chosen apps", "note": "the normal case", "url": "/?do=apps"},
            {"title": "Whole Mac", "url": "/?whole=1&do=apps"},
            {"title": "Desktop layout", "url": "/?state=full", "width": 1280, "height": 800}
          ]
        }
      ]
    }

- "url" is relative to the gallery page (same origin), or absolute.
- "frame" is the default viewport of every frame; a scenario may set its own "width" and "height".
- A frame wider than "max_width" (default 480 CSS pixels) is rendered at its real size and scaled
  down to fit, so the layout is the real one; its "open" link shows it at full size.
- A flat "scenarios" list may replace "groups".
- Frames load lazily once the page holds more than 16 of them ("lazy": true or false overrides).
  Lazy frames load as they scroll into view; check_frames.js scrolls through the page first.

The page has jump links to every group, a zoom control (remembered per browser) and a status badge
per frame: "ok" once the frame rendered (and its steps finished), "steps failed", or "blank". The
badges need the frames on the gallery's own origin. No external dependencies.
"""

import argparse
import html
import json
import sys
from pathlib import Path

PAGE = """<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{ color-scheme: light; --bg: #eef0f3; --text: #1f2328; --muted: #59636e; --line: #d1d9e0; --card: #fff; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 24px; background: var(--bg); color: var(--text);
         font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  header {{ max-width: 960px; margin-bottom: 24px; }}
  h1 {{ font-size: 20px; margin: 0 0 6px; }}
  h2 {{ font-size: 15px; margin: 28px 0 12px; color: var(--muted); font-weight: 600; }}
  p.lead {{ margin: 0; color: var(--muted); }}
  .grid {{ display: flex; flex-wrap: wrap; gap: 28px; align-items: flex-start; }}
  figure {{ margin: 0; }}
  figcaption {{ display: flex; justify-content: space-between; gap: 12px; align-items: baseline; margin-bottom: 8px;
                min-height: 2.9em; /* frames in a row line up whether or not a caption has a note */ }}
  figcaption b {{ display: block; }}
  figcaption span {{ display: block; color: var(--muted); font-size: 12.5px; }}
  figcaption nav {{ white-space: nowrap; font-size: 12.5px; }}
  figcaption a, figcaption button {{ color: var(--muted); background: none; border: 0; padding: 0 0 0 8px;
         font: inherit; cursor: pointer; text-decoration: underline; }}
  .frame {{ overflow: hidden; border-radius: 14px; background: var(--card);
           box-shadow: 0 1px 2px rgb(0 0 0 / 8%), 0 8px 24px rgb(0 0 0 / 10%); }}
  .frame iframe {{ border: 0; display: block; transform-origin: 0 0; background: var(--card); }}
  .bar {{ position: sticky; top: 0; z-index: 1; display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: center;
         margin: 0 -24px 8px; padding: 10px 24px; background: rgb(238 240 243 / 92%); backdrop-filter: blur(6px);
         border-bottom: 1px solid var(--line); font-size: 13px; }}
  .bar a {{ color: var(--text); }}
  .bar .zoom {{ margin-left: auto; display: flex; gap: 4px; }}
  .bar .zoom button {{ font: inherit; border: 1px solid var(--line); background: var(--card); border-radius: 6px;
         padding: 2px 8px; cursor: pointer; }}
  .bar .zoom button[aria-pressed="true"] {{ border-color: var(--text); font-weight: 600; }}
  .badge {{ display: inline-block; margin-left: 6px; padding: 0 6px; border-radius: 9px; font-size: 11px;
           font-weight: 600; vertical-align: 1px; color: var(--muted); background: #e3e6ea; }}
  .badge[data-state="ok"] {{ color: #1a7f37; background: #dafbe1; }}
  .badge[data-state="failed"], .badge[data-state="blank"] {{ color: #cf222e; background: #ffebe9; }}
</style>
</head>
<body>
<header>
<h1>{title}</h1>
{lead}
</header>
<div class="bar">{nav}<span class="zoom" role="group" aria-label="{zoom_label}"><button type="button" data-zoom="1">100%</button><button type="button" data-zoom="0.75">75%</button><button type="button" data-zoom="0.5">50%</button></span></div>
{sections}
<script>
  const words = {words_json};
  let zoom = 1;
  try {{ zoom = Number(localStorage.getItem('ui-gallery-zoom')) || 1; }} catch {{}}
  function applyZoom() {{
    for (const box of document.querySelectorAll('.frame')) {{
      const f = box.firstElementChild, w = +box.dataset.w, h = +box.dataset.h, s = +box.dataset.s * zoom;
      box.style.width = Math.round(w * s) + 'px';
      box.style.height = Math.round(h * s) + 'px';
      f.style.transform = 'scale(' + s + ')';
    }}
    for (const b of document.querySelectorAll('[data-zoom]')) b.setAttribute('aria-pressed', String(+b.dataset.zoom === zoom));
  }}
  document.addEventListener('click', (e) => {{
    const z = e.target.closest('button[data-zoom]');
    if (z) {{
      zoom = +z.dataset.zoom;
      try {{ localStorage.setItem('ui-gallery-zoom', String(zoom)); }} catch {{}}
      applyZoom();
    }}
    const b = e.target.closest('button[data-reload]');
    if (b) {{
      const f = document.getElementById(b.dataset.reload);
      f.dataset.since = String(Date.now());
      f.src = f.src;
    }}
  }});
  // Status badges: a same-origin frame is "ok" once it rendered and its steps (if any) are done.
  function status(f) {{
    let doc;
    try {{ doc = f.contentDocument; }} catch {{ return 'unknown'; }}
    if (!doc || !doc.body) return 'loading';
    const steps = doc.body.dataset.steps;
    if (steps && steps.startsWith('failed')) return 'failed';
    const rendered = doc.body.querySelectorAll('*').length > 5 && (doc.body.innerText || '').trim().length > 0;
    if (rendered && (steps === undefined || steps === 'done')) return 'ok';
    const since = Number(f.dataset.since || 0);
    return since && Date.now() - since > 12000 ? 'blank' : 'loading';
  }}
  function tick() {{
    for (const f of document.querySelectorAll('.frame iframe')) {{
      const badge = document.querySelector('.badge[data-for="' + f.id + '"]');
      const st = status(f);
      if (badge.dataset.state !== st) {{ badge.dataset.state = st; badge.textContent = words[st] || st; }}
    }}
  }}
  for (const f of document.querySelectorAll('.frame iframe')) {{
    f.addEventListener('load', () => {{ f.dataset.since = String(Date.now()); }});
  }}
  applyZoom();
  setInterval(tick, 700);
</script>
</body>
</html>
"""

FIGURE = """<figure>
<figcaption><div><b>{title}</b><span class="badge" data-for="{fid}" data-state="loading">{loading}</span>{note}</div><nav><a href="{url}" target="_blank" rel="noopener">{open}</a><button type="button" data-reload="{fid}">{reload}</button></nav></figcaption>
<div class="frame" data-w="{w}" data-h="{h}" data-s="{scale}" style="width:{box_w}px;height:{box_h}px"><iframe id="{fid}" title="{title}" src="{url}" width="{w}" height="{h}" style="width:{w}px;height:{h}px;transform:scale({scale})"{lazy}></iframe></div>
</figure>"""

WORDS = {
    "ru": {"open": "открыть", "reload": "обновить", "zoom": "Масштаб", "groups": "Группы",
           "loading": "загрузка", "ok": "готово", "failed": "шаги не прошли", "blank": "пусто", "unknown": "?"},
    "en": {"open": "open", "reload": "reload", "zoom": "Zoom", "groups": "Groups",
           "loading": "loading", "ok": "ok", "failed": "steps failed", "blank": "blank", "unknown": "?"},
}


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def render(spec: dict) -> str:
    lang = spec.get("lang", "en")
    words = WORDS.get(lang.split("-")[0], WORDS["en"])
    frame = spec.get("frame", {})
    dw, dh = int(frame.get("width", 390)), int(frame.get("height", 844))
    max_w = int(spec.get("max_width", 480))
    groups = spec.get("groups") or [{"title": "", "scenarios": spec.get("scenarios", [])}]
    total = sum(len(g.get("scenarios", [])) for g in groups)
    if total == 0:
        raise ValueError("the scenario file has no scenarios")
    lazy = ' loading="lazy"' if spec.get("lazy", total > 16) else ""
    sections, nav, n = [], [], 0
    for gi, g in enumerate(groups, 1):
        figs = []
        for s in g.get("scenarios", []):
            if "url" not in s or "title" not in s:
                raise ValueError(f"scenario needs title and url: {s}")
            n += 1
            w, h = int(s.get("width", dw)), int(s.get("height", dh))
            scale = min(1.0, max_w / w)
            note = f"<span>{esc(s['note'])}</span>" if s.get("note") else ""
            figs.append(FIGURE.format(
                title=esc(s["title"]), note=note, url=esc(s["url"]), fid=f"f{n}",
                w=w, h=h, scale=f"{scale:.4f}", box_w=round(w * scale), box_h=round(h * scale),
                lazy=lazy, open=esc(words["open"]), reload=esc(words["reload"]), loading=esc(words["loading"]),
            ))
        head = f"<h2 id=\"g{gi}\">{esc(g['title'])}</h2>\n" if g.get("title") else ""
        if g.get("title"):
            nav.append(f'<a href="#g{gi}">{esc(g["title"])} ({len(figs)})</a>')
        sections.append(f"<section>\n{head}<div class=\"grid\">\n" + "\n".join(figs) + "\n</div>\n</section>")
    lead = f'<p class="lead">{esc(spec["lead"])}</p>' if spec.get("lead") else ""
    return PAGE.format(
        lang=esc(lang), title=esc(spec.get("title", "UI gallery")), lead=lead, sections="\n".join(sections),
        nav=" ".join(nav), zoom_label=esc(words["zoom"]),
        words_json=json.dumps({k: words[k] for k in ("loading", "ok", "failed", "blank", "unknown")}, ensure_ascii=False),
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scenarios", type=Path, help="scenario JSON file")
    ap.add_argument("--out", type=Path, required=True, help="gallery HTML to write, inside the served root")
    args = ap.parse_args()
    try:
        spec = json.loads(args.scenarios.read_text(encoding="utf-8"))
        page = render(spec)
    except (OSError, ValueError) as e:
        print(f"make_gallery: {e}", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")
    count = page.count("<iframe ")
    print(f"wrote {args.out} with {count} frames")
    return 0


if __name__ == "__main__":
    sys.exit(main())
