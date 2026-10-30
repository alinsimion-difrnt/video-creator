"""Human preview of a video's packets: every task with its images, and what triage skipped.

Default: `data/packets/<id>/preview.html` next to the images (relative links). `embed=True` inlines
downscaled images so the page is one file that can be shared.
"""

from __future__ import annotations

import base64
import html
import io
import json
from pathlib import Path

from PIL import Image

from lens.schemas.packets import PacketManifest

CSS = """
/* Layout: one reading column; each task is a set-off panel with an image grid that stacks on phones. */
:root{--bg:#f6f6f4;--surface:#ffffff;--fg:#1d1f22;--muted:#62666d;--line:#e2e2de;--accent:#c2410c;
--sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
--mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121315;--surface:#1b1d20;
--fg:#ececea;--muted:#a3a7ad;--line:#2c2f33;--accent:#fb923c;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#121315;--surface:#1b1d20;--fg:#ececea;--muted:#a3a7ad;--line:#2c2f33;
--accent:#fb923c;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 var(--sans)}
main{max-width:72rem;margin:0 auto;padding:1.5rem 16px 4rem}
h1{font-size:1.5rem;line-height:1.2;margin:0 0 .25rem;text-wrap:balance}
h2{font-size:1.1rem;margin:2.25rem 0 .5rem;text-wrap:balance}
h3{font-size:.95rem;margin:0 0 .6rem;font-family:var(--mono);font-weight:500}
p{max-width:65ch}.muted{color:var(--muted)}
.eyebrow{font:500 .72rem/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
.stats{display:flex;flex-wrap:wrap;gap:1.5rem;margin:1rem 0 0;font-variant-numeric:tabular-nums}
.stat b{display:block;font:600 1.4rem/1.1 var(--mono)}.stat span{color:var(--muted);font-size:.85rem}
.task{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:1rem;margin:.75rem 0;
min-width:0}
.imgs{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,16rem),1fr));gap:.5rem}
.imgs img{display:block;width:100%;max-width:100%;height:auto;border-radius:3px;border:1px solid var(--line)}
.facts{display:grid;grid-template-columns:auto 1fr;gap:.2rem .9rem;margin:.75rem 0 0;font-size:.9rem}
.facts dt{color:var(--muted)}.facts dd{margin:0;min-width:0}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.82rem;font-variant-numeric:tabular-nums}
td,th{text-align:left;padding:.3rem .6rem;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:500}
code{font:.8rem var(--mono)}details{margin-top:.6rem}summary{cursor:pointer;color:var(--muted)}
summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
"""


def _src(path: Path, base: Path, embed: bool, long_edge: int) -> str:
    if not embed:
        return html.escape(path.relative_to(base).as_posix())
    img = Image.open(path).convert("RGB")
    img.thumbnail((long_edge, long_edge), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=72)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def render_preview(
    root: Path,
    video: str,
    embed: bool = False,
    max_events: int | None = None,
    long_edge: int = 1000,
    title: str | None = None,
) -> str:
    """A full HTML document; with `embed`, a self-contained fragment (title, style, content) for
    hosts that add their own document skeleton."""
    m = PacketManifest.model_validate_json(
        (root / "packets" / video / "manifest.json").read_text(encoding="utf-8")
    )
    base = root / "data" / "packets" / video
    a1 = [t for t in m.tasks if t.kind == "a1"]
    a2 = [t for t in m.tasks if t.kind == "a2"]
    shown = a2 if max_events is None else a2[:max_events]
    e = html.escape
    name = title or f"{video} packets"
    fonts = (
        "<link rel=stylesheet href='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600"
        "&family=IBM+Plex+Sans:wght@400;600&display=swap'>"
    )
    head = f"<title>{e(name)}</title>{fonts}<style>{CSS}</style>"
    parts = [
        head
        if embed
        else f"<!doctype html><html lang=en><head><meta charset=utf-8>"
        f"<meta name=viewport content='width=device-width,initial-scale=1'>{head}</head><body>",
        "<main>",
        "<div class=eyebrow>Annotation packets</div>",
        f"<h1>{e(name)}</h1>",
        f"<p class=muted>What Claude will see, task by task, for <code>{e(video)}</code> (tier {e(m.tier)})."
        f" Budgets: at most {m.max_images_per_task} images per Pass 1 task"
        f" and {m.event_images} per event task."
        f" Built {m.provenance.created_at:%Y-%m-%d}.</p>",
        "<div class=stats>",
        f"<div class=stat><b>{len(a1)}</b><span>Pass 1 tasks</span></div>",
        f"<div class=stat><b>{len(a2)}</b><span>event tasks</span></div>",
        f"<div class=stat><b>{sum(len(t.images) for t in m.tasks)}</b><span>images</span></div>",
        f"<div class=stat><b>{len(m.skipped)}</b><span>events skipped by triage</span></div>",
        "</div>",
        "<h2>Pass 1 (A1): structure, beats, scores</h2>",
    ]
    for t in a1:
        imgs = "".join(
            f"<img loading=lazy src='{_src(base / i, base, embed, long_edge)}' alt='{e(i)}'>"
            for i in t.images
        )
        parts.append(
            f"<section class=task><h3>{e(t.id)} · shots {e(', '.join(t.shots))} · {len(t.images)} images</h3>"
            f"<div class=imgs>{imgs}</div><p class=muted>writes <code>{e(t.output)}</code></p></section>"
        )
    parts.append("<h2>Events (A2): elements by box id, SFX review, pattern</h2>")
    if len(shown) < len(a2):
        parts.append(f"<p class=muted>Showing {len(shown)} of {len(a2)} event tasks.</p>")
    for t in shown:
        facts = json.loads((base / f"events/{t.event}/facts.json").read_text(encoding="utf-8"))
        cands = json.loads((base / f"events/{t.event}/candidates.json").read_text(encoding="utf-8"))
        imgs = "".join(
            f"<img loading=lazy src='{_src(base / i, base, embed, long_edge)}' alt='{e(i)}'>"
            for i in t.images
        )
        sfx = ", ".join(f"{s['id']} {s['label']} ({s['offset_ms']:+.0f} ms)" for s in facts["sfx"]) or "none"
        words = " ".join(w["text"] for w in facts["words"]) or "—"
        sib = f" · result also covers {', '.join(t.siblings)}" if t.siblings else ""
        rows = "".join(
            f"<tr><td>{e(b['id'])}</td><td>{e(b['source'])}</td><td>{b['changed_share']:.2f}</td>"
            f"<td>{e(b.get('text') or '')}</td></tr>"
            for b in cands["boxes"]
        )
        parts.append(
            f"<section class=task><h3>{e(t.event or '')} · shot {e(facts['shot'])} · "
            f"{facts['start_s']:.2f} to {facts['end_s']:.2f} s{e(sib)}</h3><div class=imgs>{imgs}</div>"
            f"<dl class=facts><dt>SFX nearby</dt><dd>{e(sfx)}</dd><dt>Words</dt><dd>{e(words)}</dd>"
            f"<dt>Camera</dt><dd>{e(facts['camera']['move'])}</dd></dl>"
            f"<details><summary>{len(cands['boxes'])} candidate boxes</summary><div class=scroll><table>"
            f"<tr><th>id</th><th>source</th><th>changed</th><th>text</th></tr>{rows}</table></div></details>"
            "</section>"
        )
    if m.skipped:
        rows = "".join(
            f"<tr><td>{e(s.event)}</td><td>{e(s.reason)}</td><td>{e(s.of or '')}</td></tr>" for s in m.skipped
        )
        parts.append(
            "<h2>Skipped by triage</h2><div class=scroll><table><tr><th>event</th><th>reason</th>"
            f"<th>covered by</th></tr>{rows}</table></div>"
        )
    parts.append("</main>" if embed else "</main></body></html>")
    return "\n".join(parts)
