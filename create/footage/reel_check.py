"""Checks for a reel plan before it is rendered (`create reel --check`, ADR 0026).

The six variants and five review rounds of Robert's first take kept finding the same things: cards that show
nothing new for too long, an empty product area, names he says that the card does not show, stickers that
wrap, text too small for a phone, graphics under TikTok's buttons, on his face or under the captions. The
plan checks find the first four from the built composition data alone. The layout checks open the page in
Chromium (no video, no render), seek each widget's moment and measure where it really lands.

Thresholds: config `create.footage.reel.check`. Errors fail the check; warnings are for a person to judge.
"""

from __future__ import annotations

import itertools
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lens.schemas.config import CreateFrame, ReelCheck
from lens.schemas.create import Timeline

REQUIRED = {  # widget kind -> spec fields it cannot draw without (create/kit/motion.js)
    "chat": ("prompt",),
    "search": ("query",),
    "sources": ("items",),
    "review": ("text",),
    "counter": ("value",),
    "chart": ("title",),
    "cta": ("text", "url"),
    "sticker": ("text",),
    "queries": ("specific",),  # vague is optional: a follow-up beat shows only the specific ones
    "tiles": ("items",),
    "pins": ("places",),
    "code": ("lines", "edits"),
    "bucket": ("folders",),
    "pixel": ("sprite",),
    "bars": ("items",),
}
KIT_JS = Path(__file__).resolve().parent.parent / "kit" / "motion.js"


def kit_names(js: str | None = None) -> tuple[set[str], set[str]]:
    """The pixel sprites and entrance styles motion.js knows (so a typo fails the check, not the render)."""
    src = js if js is not None else KIT_JS.read_text()
    block = src[src.index("const PX = {") : src.index("};", src.index("const PX = {"))]
    sprites = set(re.findall(r"^\s+(\w+): \[", block, re.M))
    motions = set(re.findall(r'"(\w+)"', re.search(r"const MOTIONS = \[([^\]]*)\]", src).group(1)))  # type: ignore[union-attr]
    return sprites, motions


NOT_NAMES = {"i", "i'm", "i've", "i'll", "i'd"}


@dataclass(frozen=True)
class Finding:
    level: str  # error | warn
    rule: str
    at_s: float
    message: str

    def line(self) -> str:
        return f"{self.level.upper():5} {self.rule:<16} {self.at_s:6.1f}s  {self.message}"


def _text(spec: Any) -> str:
    """Every string in a widget spec, lowercased (what the card can show)."""
    if isinstance(spec, str):
        return spec.lower()
    if isinstance(spec, dict):
        return " ".join(_text(v) for v in spec.values())
    if isinstance(spec, list):
        return " ".join(_text(v) for v in spec)
    return ""


def spoken_names(timeline: Timeline, w0: int, w1: int) -> list[str]:
    """Capitalised words said between two word indexes, not at a sentence start (names, places, products)."""
    words = {w.i: w.text for w in timeline.words}
    out = []
    for i in range(w0, w1 + 1):
        raw = words.get(i)
        if raw is None:
            continue
        clean = re.sub("[^\\w'\u2019.-]", "", raw).strip(".-")
        prev = words.get(i - 1, ".")
        if (
            len(clean) <= 2  # "AI", "OK": too generic to expect on a card
            or not clean[0].isupper()
            or clean.lower() in NOT_NAMES
            or prev.rstrip('"”').endswith((".", "?", "!"))
        ):
            continue
        out.append(clean)
    return out


def plan_findings(data: dict[str, Any], timeline: Timeline, chk: ReelCheck) -> list[Finding]:
    """Checks on the built composition data (`build()`'s reel-data.json): times are final there."""
    out: list[Finding] = []
    items, duration = data["items"], float(data["duration"])
    words = sorted(timeline.words, key=lambda w: w.start_s)
    for it in items:
        spec, kind = it.get("spec") or {}, it["kind"]
        missing = [f for f in REQUIRED.get(kind, ()) if not spec.get(f)]
        if missing:
            out.append(Finding("error", "spec", it["t0"], f"{kind} needs {', '.join(missing)}"))
        sprites, motions = kit_names()
        names = [spec.get("sprite")] if kind == "pixel" and spec.get("sprite") else []
        if kind == "handoff":
            names += [spec[k] for k in ("giver", "receiver", "item") if spec.get(k)]
        names += [str(v)[3:] for k, v in spec.items() if k == "icon" and str(v).startswith("px:")]
        names += [str(x.get("icon"))[3:] for x in [*(spec.get("items") or []), *(spec.get("places") or [])]
                  if isinstance(x, dict) and str(x.get("icon", "")).startswith("px:")]  # fmt: skip
        for n in names:
            if n not in sprites:
                out.append(
                    Finding(
                        "error", "spec", it["t0"], f"no pixel sprite '{n}' ({', '.join(sorted(sprites))})"
                    )
                )
        if spec.get("motion") and spec["motion"] not in motions:
            out.append(
                Finding(
                    "error", "spec", it["t0"], f"motion '{spec['motion']}' is not one of {sorted(motions)}"
                )
            )
        beats = [it["t0"], *it.get("marks", []), it["t1"]]
        ordered = kind in (
            "chat",
            "search",
            "review",
            "queries",
        )  # stages in order (sources: rows, then highlight)
        if ordered and it.get("marks") and it["marks"] != sorted(it["marks"]):
            out.append(Finding("warn", "marks", it["t0"], f"{kind}: marks go backwards"))
        for a, b in itertools.pairwise(sorted(beats)):
            if b - a > chk.max_beat_gap_s:
                out.append(Finding("warn", "long-hold", a, f"{kind} '{it['title']}' shows nothing new for "
                                   f"{b - a:.1f} s; split it or add a beat (marks)"))  # fmt: skip
        if kind == "logo" and it["where"] != "product":  # it lands on the shirt (and any logo printed on it)
            out.append(
                Finding("warn", "logo-overlay", it["t0"], "the logo belongs on a product card or cutaway")
            )
        if kind == "sticker" and len(str(spec.get("text", ""))) > chk.max_sticker_chars:
            out.append(
                Finding("warn", "sticker-long", it["t0"], f"'{spec.get('text')}' wraps; keep stickers short")
            )
        w0 = next((w.i for w in words if w.start_s >= it["t0"] - 0.35), None)
        w1 = next((w.i for w in reversed(words) if w.start_s <= it["t1"]), None)
        if w0 is not None and w1 is not None and kind != "logo":  # the end card is the brand, not the words
            shown = _text(spec)
            absent = [n for n in spoken_names(timeline, w0, w1) if n.lower() not in shown]
            if absent:
                said = ", ".join(dict.fromkeys(absent))
                msg = f"{kind} '{it['title']}' does not show what is said: {said}"
                out.append(Finding("warn", "names", it["t0"], msg))
    # the product area is never empty in split / off (a panel plan fills it with the bespoke panel, ADR 0034)
    poses = data["poses"]
    for k, p in enumerate(poses):
        if data.get("panel") or p["layout"] not in ("split", "off"):
            continue
        start = p["t"] + data["transition"] / 2
        end = poses[k + 1]["t"] - data["transition"] / 2 if k + 1 < len(poses) else duration
        spans = sorted((max(i["t0"], start), min(i["t1"], end)) for i in items if i["where"] == "product")
        cur = start
        for a, b in [*spans, (end, end)]:
            if b <= cur:
                continue
            if a - cur > chk.max_product_empty_s:
                out.append(
                    Finding("error", "empty-product", cur, f"the product area is empty for {a - cur:.1f} s")
                )
            cur = max(cur, b)
    # something new on screen often enough (widgets in and out, their beats, layout moves, punch-ins)
    ev = [0.0, duration]
    for it in items:
        ev += [it["t0"], it["t1"], *it.get("marks", [])]
    ev += [p["t"] for p in poses[1:]] + [p["t0"] for p in data.get("punches", [])]
    for pr in data.get("props", []):  # a prop entering, acting or leaving is something new (ADR 0027)
        ev += [pr["t0"], pr["t1"], *(b["t"] for k in ("styles", "acts", "tags") for b in pr[k])]
        ev += [m["t"] for m in pr["moves"]] + [a["t"] for a in pr["acc"]]
    ev += [f["t0"] for f in data.get("fx", [])]
    for a, b in itertools.pairwise(sorted(ev)):
        if b - a > chk.max_static_s and not data.get("panel"):  # the panel's own beats are not in the plan
            out.append(Finding("warn", "static", a, f"nothing new on screen for {b - a:.1f} s"))
    return out


def prop_findings(data: dict[str, Any], min_visible: float) -> list[Finding]:
    """Props that a shot's crop cuts off (a punch-in can crop the couch away)."""
    out = []
    for pr in data.get("props", []):
        for t, share in pr.get("visible", []):
            if share < min_visible:
                out.append(Finding("warn", "prop-offscreen", t, f"{pr['id']}: only {share:.0%} on screen"))
        if pr.get("exit", {}).get("cut"):  # its last beat ends too close to the end for its exit
            msg = f"{pr['id']}: no time left for its exit, so it stays; start its beats earlier"
            out.append(Finding("warn", "prop-exit-cut", pr["exit"]["t"], msg))
    return out


def sample_times(items: list[dict[str, Any]]) -> list[tuple[int, float]]:
    """When to measure each widget: once landed, and once fully built (after its last beat)."""
    out = []
    for n, it in enumerate(items):
        land = min(it["t0"] + 0.8, (it["t0"] + it["t1"]) / 2)
        built = min(max(it.get("marks") or [land]) + 0.45, it["t1"] - 0.35)
        out += [(n, round(land, 3))] + ([(n, round(built, 3))] if built > land + 0.2 else [])
    return out


def _inside(r: tuple[float, float, float, float], frame: CreateFrame, tol: float) -> bool:
    x0, y0, x1, y1 = r
    return any(
        x0 >= s.x0 - tol and y0 >= s.y0 - tol and x1 <= s.x1 + tol and y1 <= s.y1 + tol for s in frame.safe
    )


def _overlap(a: tuple[float, ...], b: tuple[float, ...], tol: float = 0.0) -> bool:
    """The rects overlap by more than `tol` in both directions (a spring's overshoot does not count)."""
    return min(a[2], b[2]) - max(a[0], b[0]) > tol and min(a[3], b[3]) - max(a[1], b[1]) > tol


def judge(
    measures: list[dict[str, Any]], items: list[dict[str, Any]], frame: CreateFrame, chk: ReelCheck,
    faces: dict[float, tuple[float, float, float, float]],
) -> list[Finding]:  # fmt: skip
    """Findings from the measured page: safe area, face, captions, text size. Pure (testable)."""
    out: list[Finding] = []
    for m in measures:
        it, t, r = items[m["item"]], m["t"], tuple(m["rect"])
        name = f"{it['kind']} '{it['title']}'"
        if r[2] - r[0] < 1:
            continue  # not on screen at this moment
        if not _inside(r, frame, chk.edge_tol_px):
            out.append(Finding("error", "safe-area", t, f"{name} reaches outside the safe area {_fmt(r)}"))
        face = faces.get(t)
        if it["where"] == "overlay" and face is not None and _overlap(r, face, chk.edge_tol_px):
            out.append(Finding("error", "on-face", t, f"{name} covers the face {_fmt(r)}"))
        for c in m.get("captions", []):
            if _overlap(r, tuple(c), chk.edge_tol_px):
                out.append(Finding("error", "on-captions", t, f"{name} is under a caption {_fmt(tuple(c))}"))
        if m.get("min_text") and round(m["min_text"]) < chk.min_card_text_px:  # as shown: whole pixels
            msg = f"{name}: '{m.get('min_text_of', '')}' is {m['min_text']:.0f} px on screen"
            out.append(Finding("warn", "small-text", t, f"{msg} (min {chk.min_card_text_px:g})"))
    return out


def _fmt(r: tuple[float, ...]) -> str:
    return "[" + ", ".join(f"{v:.0f}" for v in r) + "]"


MEASURE_JS = """([n, t]) => { window.__timelines.reel.seek(t, false);
  const box = document.getElementById('item' + n); const w = box && box.querySelector('.mk');
  if (!w) return null;
  const rect = (el) => { const b = el.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; };
  const shown = (el) => { for (let e = el; e; e = e.parentElement) { const s = getComputedStyle(e);
      if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) < 0.05) return false; }
    return true; };
  let minText = null, minOf = '';
  w.querySelectorAll('*').forEach(el => {
    // own text of more than two characters (rank badges and icon digits are not reading text)
    const own = Array.from(el.childNodes).some(c => c.nodeType === 3 && c.textContent.trim().length > 2);
    if (!own || !shown(el) || !el.offsetHeight) return;
    const k = el.getBoundingClientRect().height / el.offsetHeight;  // the scale the card is shown at
    const px = parseFloat(getComputedStyle(el).fontSize) * k;
    if (minText === null || px < minText) { minText = px; minOf = el.textContent.trim().slice(0, 40); }
  });
  const caps = Array.from(document.querySelectorAll('.cap .txt')).filter(shown).map(rect);
  return { rect: shown(w) ? rect(w) : [0, 0, 0, 0], min_text: minText, min_text_of: minOf,
           captions: caps }; }"""


def measure(comp: Path, samples: list[tuple[int, float]]) -> list[dict[str, Any]]:
    """Open the composition (no video) in Chromium and measure each widget at its sample times."""
    from playwright.sync_api import sync_playwright

    from create.browser import launch

    page_dir = comp / "preview"
    page_dir.mkdir(exist_ok=True)
    html = (comp / "index.html").read_text().replace('src="presenter.mp4"', 'src=""')
    (page_dir / "check.html").write_text(html.replace("<head>", '<head><base href="../">', 1))
    out = []
    with sync_playwright() as pw:
        browser = launch(pw)
        w, h = (int(x) for x in re.search(r'data-width="(\d+)" data-height="(\d+)"', html).groups())  # type: ignore[union-attr]
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto((page_dir / "check.html").as_uri())
        page.evaluate("document.fonts.ready")
        for n, t in samples:
            m = page.evaluate(MEASURE_JS, [n, t])
            if m is not None:
                out.append(m | {"item": n, "t": t})
        browser.close()
    return out


def run_check(
    root: Path, project: str, cfg: Any, plan_path: Path | None = None, browser: bool = True
) -> list[Finding]:
    """Build the composition, run the plan checks and (with `browser`) the layout checks."""
    from create.footage.overlays import face_box_at
    from create.footage.reel import build
    from lens.schemas.create import Edl, Framing, Tokens

    comp, _ = build(root, project, cfg, plan_path)
    data = json.loads((comp / "reel-data.json").read_text())
    base = root / "projects" / project
    timeline = Timeline.model_validate(json.loads((base / "timeline.json").read_text()))
    chk = cfg.create.footage.reel.check
    found = plan_findings(data, timeline, chk) + prop_findings(
        data, cfg.create.footage.reel.props.min_visible
    )
    if browser:
        tokens = Tokens.model_validate(json.loads((base / "tokens.json").read_text()))
        frame = cfg.create.design.frames[tokens.frame]
        edl = Edl.model_validate(json.loads((base / "edl.json").read_text()))
        fr_p = base / "framing.json"
        framing = Framing.model_validate(json.loads(fr_p.read_text())) if fr_p.exists() else None
        samples = sample_times(data["items"])
        faces = {t: face_box_at(t, edl, framing, frame.width, frame.height) for _, t in samples}
        found += judge(measure(comp, samples), data["items"], frame, chk, faces)
    return sorted(found, key=lambda f: (f.level != "error", f.at_s))
