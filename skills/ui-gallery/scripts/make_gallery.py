#!/usr/bin/env python3
"""Write a one-page gallery of live UI states from a scenario list.

Usage:
    python3 make_gallery.py scenarios.json --out <served-root>/gallery.html

Copy assets/scenarios.template.json and fill its titles, descriptions, notes and URLs.
The JSON accepts title, lead, lang (en or ru), frame {width, height}, max_width
(default 480), and groups [{title, description, scenarios: [{title, note, url}]}].
A flat scenarios list can replace groups. Scenario width and height override frame.
URLs may be relative or absolute; same-origin frames support render status checks.
Viewports keep their real dimensions and fit automatically inside the gallery.
Frames load lazily above 16 scenarios; lazy: true or false overrides that default.
The generated page has no external dependencies or manual zoom controls.
"""

import argparse
import html
import json
import sys
from pathlib import Path
from string import Template

PAGE = Template("""<!doctype html>
<html lang="$lang">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<style>
  :root { color-scheme: light; --bg: #fcfafb; --card: #fff; --text: #29242a;
    --muted: #74616c; --line: #eee4e9; --rose: #a94460; --rose-soft: #fcecf0;
    --plum: #715385; --plum-soft: #f2edf8; }
  * { box-sizing: border-box; }
  html { scrollbar-gutter: stable; }
  body { margin: 0; background: var(--bg); color: var(--text);
    font: 14px/1.55 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  .wrap { max-width: 1680px; margin-inline: auto; padding: 40px clamp(16px, 3vw, 48px) 80px; }
  h1, h2, h3, p { margin: 0; overflow-wrap: anywhere; }
  a, button { -webkit-tap-highlight-color: transparent; }
  :where(a, button):focus-visible { outline: 3px solid var(--rose); outline-offset: 4px; }
  .eyebrow { color: var(--rose); font-size: 12px; font-weight: 650; letter-spacing: .12em;
    text-transform: uppercase; margin-bottom: 12px; }
  h1 { font-size: clamp(28px, 3vw, 42px); line-height: 1.15; letter-spacing: -.035em; }
  .lead { max-width: 80ch; margin-top: 14px; color: var(--muted); font-size: 15px; }
  .summary { display: flex; flex-wrap: wrap; gap: 8px 24px; color: var(--plum); margin-top: 20px; }
  .contents { margin-block: 32px 48px; padding: 24px; border: 1px solid var(--line);
    border-radius: 20px; background: var(--card); }
  .contents h2 { font-size: 15px; margin-bottom: 16px; }
  .contents-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px 24px; padding: 0; margin: 0; list-style: none; }
  .contents-list li { min-width: 0; }
  .contents-list a { display: grid; grid-template-columns: 36px minmax(0, 1fr); gap: 12px;
    padding: 12px; border: 1px solid transparent; border-radius: 12px;
    text-decoration: none; color: var(--text); min-height: 44px; }
  .contents-list a:hover { background: var(--rose-soft); border-color: var(--line); }
  .number { display: inline-flex; justify-content: center; align-items: center; width: 36px;
    height: 36px; border-radius: 10px; background: var(--rose-soft); color: var(--rose);
    font-variant-numeric: tabular-nums; font-weight: 650; flex-shrink: 0; }
  .contents-title { display: block; font-weight: 600; overflow-wrap: anywhere; }
  .contents-note { display: block; margin-top: 3px; color: var(--muted); overflow-wrap: anywhere; }
  .count { display: block; margin-top: 6px; color: var(--plum); font-size: 12px; }
  section { scroll-margin-top: 24px; margin-top: 48px; }
  .section-head { display: flex; gap: 16px; align-items: flex-start; margin-bottom: 24px; }
  .section-head .number { background: var(--plum-soft); color: var(--plum); }
  .section-head h2 { font-size: 23px; line-height: 1.3; letter-spacing: -.025em; }
  .section-head p { color: var(--muted); max-width: 90ch; margin-top: 6px; }
  .grid { display: flex; flex-wrap: wrap; align-items: flex-start; gap: 24px; }
  figure { margin: 0; min-width: 0; max-width: 100%; width: var(--preview-width);
    background: var(--card); border: 1px solid var(--line); border-radius: 18px;
    overflow: hidden; box-shadow: 0 8px 35px rgb(118 52 77 / 4%); }
  figcaption { padding: 18px; }
  .caption-top { display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
  .scenario-number { color: var(--plum); font-size: 12px; font-weight: 650; font-variant-numeric: tabular-nums; }
  h3 { font-size: 16px; line-height: 1.4; }
  .note { margin-top: 6px; color: var(--muted); font-size: 13px; }
  .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
  .actions a, .actions button { font: inherit; font-size: 12px; font-weight: 600;
    min-height: 36px; padding: 7px 12px; border: 1px solid #a88c9a; border-radius: 9px;
    color: var(--rose); background: var(--card); cursor: pointer; text-decoration: none; }
  .actions a:hover, .actions button:hover { background: var(--rose-soft); }
  .badge { display: inline-block; padding: 3px 9px; border-radius: 20px; font-size: 11px;
    color: var(--muted); background: #faf8f9; min-width: 110px; text-align: center; }
  .badge[data-state="ok"] { color: #267348; background: #edf7f0; }
  .badge[data-state="failed"], .badge[data-state="blank"] { color: #a8324b; background: var(--rose-soft); }
  .frame { overflow: hidden; background: var(--card); border-top: 1px solid var(--line); }
  .frame iframe { border: 0; display: block; transform-origin: 0 0; background: var(--card); }
  @media (max-width: 700px) {
    .wrap { padding-top: 24px; }
    .contents { padding: 16px; margin-block: 24px 32px; }
    .contents-list { grid-template-columns: minmax(0, 1fr); gap: 4px; }
    .contents-list a { padding: 10px 0; }
    .section-head h2 { font-size: 20px; }
  }
</style>
</head>
<body>
<main class="wrap">
<header><p class="eyebrow">UI gallery</p><h1>$title</h1>$lead
<p class="summary"><span>$group_summary</span><span>$scenario_summary</span></p></header>
<nav class="contents" aria-labelledby="contents-title"><h2 id="contents-title">$contents_label</h2>
<ol class="contents-list">$nav</ol></nav>
$sections
</main>
<script>
  const words = $words_json;
  // Fit the preview, not the app viewport: desktop layouts keep their breakpoints.
  function fit(box) {
    const iframe = box.firstElementChild;
    const width = Number(box.dataset.w), height = Number(box.dataset.h);
    const scale = Math.min(1, box.parentElement.clientWidth / width);
    box.style.width = width * scale + 'px';
    box.style.height = height * scale + 'px';
    iframe.style.transform = 'scale(' + scale + ')';
  }
  const observer = new ResizeObserver((entries) => {
    for (const entry of entries) fit(entry.target.querySelector('.frame'));
  });
  for (const figure of document.querySelectorAll('figure')) {
    fit(figure.querySelector('.frame'));
    observer.observe(figure);
  }
  document.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-reload]');
    if (!button) return;
    const iframe = document.getElementById(button.dataset.reload);
    iframe.dataset.since = String(Date.now());
    const badge = document.querySelector('.badge[data-for="' + iframe.id + '"]');
    badge.dataset.state = 'loading';
    badge.textContent = words.loading;
    iframe.src = iframe.src;
  });
  function status(iframe) {
    let doc;
    try { doc = iframe.contentDocument; } catch { return 'unknown'; }
    if (!doc) return iframe.dataset.loaded ? 'unknown' : 'loading';
    if (!doc.body) return 'loading';
    const steps = doc.body.dataset.steps;
    if (steps && steps.startsWith('failed')) return 'failed';
    const rendered = doc.body.querySelectorAll('*').length > 5 && (doc.body.innerText || '').trim().length > 0;
    if (rendered && (steps === undefined || steps === 'done')) return 'ok';
    const since = Number(iframe.dataset.since || 0);
    return since && Date.now() - since > 12000 ? 'blank' : 'loading';
  }
  function tick() {
    for (const iframe of document.querySelectorAll('.frame iframe')) {
      const badge = document.querySelector('.badge[data-for="' + iframe.id + '"]');
      const state = status(iframe);
      if (badge.dataset.state !== state) {
        badge.dataset.state = state;
        badge.textContent = words[state];
      }
    }
  }
  for (const iframe of document.querySelectorAll('.frame iframe')) {
    iframe.addEventListener('load', () => {
      iframe.dataset.loaded = 'true';
      iframe.dataset.since = String(Date.now());
    });
  }
  setInterval(tick, 700);
</script>
</body>
</html>
""")

FIGURE = Template("""<figure style="--preview-width:${preview_width}px">
<figcaption><div class="caption-top"><span class="scenario-number">$number</span><span class="badge" data-for="$fid" data-state="loading">$loading</span></div>
<h3>$title</h3>$note<div class="actions"><a href="$url" target="_blank" rel="noopener">$open</a><button type="button" data-reload="$fid">$reload</button></div></figcaption>
<div class="frame" data-w="$w" data-h="$h" style="width:${box_w}px;height:${box_h}px"><iframe id="$fid" title="$frame_title" src="$url" width="$w" height="$h" style="width:${w}px;height:${h}px;transform:scale($scale)"$lazy></iframe></div>
</figure>""")

WORDS = {
    "ru": {"open": "Открыть отдельно", "reload": "Обновить", "contents": "Содержание", "screens": "Экраны",
           "groups": "Разделов", "scenarios": "Состояний", "loading": "Загрузка", "ok": "Готово",
           "failed": "Шаги не прошли", "blank": "Пустой кадр", "unknown": "Другой источник"},
    "en": {"open": "Open separately", "reload": "Reload", "contents": "Contents", "screens": "Screens",
           "groups": "Groups", "scenarios": "States", "loading": "Loading", "ok": "Ready",
           "failed": "Steps failed", "blank": "Blank frame", "unknown": "Other origin"},
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render(spec: dict) -> str:
    lang = spec.get("lang", "en")
    words = WORDS.get(lang.split("-")[0], WORDS["en"])
    frame = spec.get("frame", {})
    dw, dh = int(frame.get("width", 390)), int(frame.get("height", 844))
    max_w = int(spec.get("max_width", 480))
    if min(dw, dh, max_w) <= 0:
        raise ValueError("frame dimensions and max_width must be positive")
    groups = spec.get("groups") or [{"scenarios": spec.get("scenarios", [])}]
    groups = [group for group in groups if group.get("scenarios")]
    total = sum(len(group["scenarios"]) for group in groups)
    if total == 0:
        raise ValueError("the scenario file has no scenarios")
    lazy = ' loading="lazy"' if spec.get("lazy", total > 16) else ""
    sections, nav, n = [], [], 0
    for gi, group in enumerate(groups, 1):
        title = esc(group.get("title") or words["screens"])
        description = esc(group.get("description", ""))
        count = f'{esc(words["scenarios"])}: {len(group["scenarios"])}'
        nav.append(f'<li><a href="#g{gi}"><span class="number">{gi:02d}</span><span>'
                   f'<span class="contents-title">{title}</span>'
                   + (f'<span class="contents-note">{description}</span>' if description else "")
                   + f'<span class="count">{count}</span></span></a></li>')
        figures = []
        for si, scenario in enumerate(group["scenarios"], 1):
            if "url" not in scenario or "title" not in scenario:
                raise ValueError(f"scenario needs title and url: {scenario}")
            n += 1
            w, h = int(scenario.get("width", dw)), int(scenario.get("height", dh))
            if min(w, h) <= 0:
                raise ValueError("scenario dimensions must be positive")
            scale = min(1.0, max_w / w)
            note = f'<p class="note">{esc(scenario["note"])}</p>' if scenario.get("note") else ""
            figures.append(FIGURE.substitute(
                title=esc(scenario["title"]), frame_title=esc(f'{gi}.{si} {scenario["title"]}'),
                number=f"{gi}.{si}", note=note, url=esc(scenario["url"]), fid=f"f{n}",
                w=w, h=h, scale=scale, preview_width=min(w, max_w) + 2,
                box_w=w * scale, box_h=h * scale, lazy=lazy,
                open=esc(words["open"]), reload=esc(words["reload"]), loading=esc(words["loading"]),
            ))
        head = f'<div class="section-head"><span class="number">{gi:02d}</span><div><h2>{title}</h2>'
        if description:
            head += f"<p>{description}</p>"
        head += f'<span class="count">{count}</span></div></div>'
        sections.append(f'<section id="g{gi}">\n{head}<div class="grid">\n' + "\n".join(figures) + "\n</div></section>")
    lead = f'<p class="lead">{esc(spec["lead"])}</p>' if spec.get("lead") else ""
    return PAGE.substitute(
        lang=esc(lang), title=esc(spec.get("title", "UI gallery")), lead=lead,
        group_summary=f'{esc(words["groups"])}: {len(groups)}', scenario_summary=f'{esc(words["scenarios"])}: {total}',
        contents_label=esc(words["contents"]), nav="\n".join(nav), sections="\n".join(sections),
        words_json=json.dumps({key: words[key] for key in ("loading", "ok", "failed", "blank", "unknown")}, ensure_ascii=False),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("scenarios", type=Path, help="scenario JSON file")
    parser.add_argument("--out", type=Path, required=True, help="gallery HTML to write, inside the served root")
    args = parser.parse_args()
    try:
        spec = json.loads(args.scenarios.read_text(encoding="utf-8"))
        page = render(spec)
    except (OSError, ValueError) as error:
        print(f"make_gallery: {error}", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")
    print(f'wrote {args.out} with {page.count("<iframe ")} frames')
    return 0


if __name__ == "__main__":
    sys.exit(main())
