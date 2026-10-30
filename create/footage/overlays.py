"""Graphics over the presenter's own video (`create overlay`, create/kit/overlays.html).

projects/<p>/overlays.yaml (OverlayPlan) lists keyword pop-ups, cards, stats and lists, each starting on a
word of the timeline. Code decides where each goes: a zone inside the frame's core safe area that keeps clear
of the face at that moment (F5 framing) and of the caption band, above the head when there is room, else
beside it. The browser then fits the graphic inside its zone. Styles come from the brand tokens.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from create.bundle import fonts, gsap
from create.burn import mux, probe, render_comp
from create.footage.framing import face_box
from lens.schemas.config import CreateFrame, LensConfig, Rect
from lens.schemas.create import Edl, Framing, OverlayItem, OverlayPlan, Timeline, Tokens

KIT = Path(__file__).resolve().parent.parent / "kit"
MIN_W, MIN_H = 260, 120  # a zone smaller than this is not used


def face_box_at(
    t: float, edl: Edl | None, framing: Framing | None, w: int, h: int
) -> tuple[float, float, float, float]:
    """(x0, y0, x1, y1) of the face at edited time `t` in output pixels (a centred guess without framing)."""
    guess = (w * 0.32, h * 0.25, w * 0.68, h * 0.48)  # generous: graphics keep clear of an unknown face
    if edl is None or framing is None:
        return guess
    return face_box(t, edl, framing, w) or guess


def zones(frame: CreateFrame, face: tuple[float, float, float, float], margin: int) -> dict[str, Rect | None]:
    """Where a graphic may go: above the head (centred on the frame), or left / right of the face."""
    core, band = frame.safe[0], frame.caption_band
    wide = max(frame.safe, key=lambda r: r.x1 - r.x0)  # the vertical upper extension reaches further right
    fx0, fy0, fx1, _ = face
    out: dict[str, Rect | None] = {}
    half = min(frame.width / 2 - wide.x0, wide.x1 - frame.width / 2)  # symmetric about the frame's centre
    top_y1 = int(min(fy0 - margin, band.y0 - margin))
    out["top"] = _rect(frame.width / 2 - half, wide.y0, frame.width / 2 + half, min(top_y1, wide.y1))
    side_y0, side_y1 = max(core.y0, fy0), min(core.y1, band.y0 - margin)
    out["left"] = _rect(core.x0, side_y0, fx0 - margin, side_y1)
    out["right"] = _rect(fx1 + margin, side_y0, core.x1, side_y1)
    return out


def _rect(x0: float, y0: float, x1: float, y1: float) -> Rect | None:
    if x1 - x0 < MIN_W or y1 - y0 < MIN_H:
        return None
    return Rect(x0=int(x0), y0=int(y0), x1=int(x1), y1=int(y1))


def place(
    item: OverlayItem, frame: CreateFrame, face: tuple[float, float, float, float], margin: int
) -> Rect:
    """The zone for one item: its asked position if usable, else the largest usable zone (top on a tie)."""
    zs = zones(frame, face, margin)
    if item.position != "auto" and zs.get(item.position) is not None:
        chosen = zs[item.position]
        assert chosen is not None
        return chosen
    usable = [(k, z) for k, z in zs.items() if z is not None]
    if not usable:  # nothing clears the face: the top of the safe area, the graphic is scaled to fit
        core = frame.safe[0]
        return Rect(x0=core.x0, y0=core.y0, x1=core.x1, y1=core.y0 + MIN_H)
    return max(usable, key=lambda kz: ((kz[1].x1 - kz[1].x0) * (kz[1].y1 - kz[1].y0), kz[0] == "top"))[1]


def plan_items(
    plan: OverlayPlan, timeline: Timeline, edl: Edl | None, framing: Framing | None, frame: CreateFrame,
    margin: int, duration: float,
) -> list[dict[str, Any]]:  # fmt: skip
    words = {w.i: w for w in timeline.words}
    out = []
    for n, it in enumerate(plan.items):
        if it.word not in words or (it.until is not None and it.until not in words):
            raise ValueError(f"overlay {n}: word {it.word} or until {it.until} is not in the timeline")
        t0 = words[it.word].start_s
        t1 = words[it.until].end_s if it.until is not None else t0 + it.duration_s
        face = face_box_at((t0 + t1) / 2, edl, framing, frame.width, frame.height)
        z = place(it, frame, face, margin)
        out.append(it.model_dump() | {"t0": round(t0, 3), "t1": round(min(t1, duration - 0.05), 3),
                                      "zone": [z.x0, z.y0, z.x1, z.y1]})  # fmt: skip
    return out


def overlay_comp(
    tokens: Tokens, frame: CreateFrame, items: list[dict[str, Any]], duration: float, lang: str
) -> str:
    c, lay, fam = tokens.colors, tokens.layout, tokens.families
    v = {
        "--w": f"{frame.width}px", "--h": f"{frame.height}px", "--surface": c["surface"], "--ink": c["ink"],
        "--muted": c["ink_muted"], "--accent": c["accent"],
        "--accent-fill": c.get("accent_fill", c["accent"]), "--radius": f"{lay.card_radius}px",
        "--shadow": lay.card_shadow, "--heading": f'"{fam["heading"].family}", {fam["heading"].fallback}',
        "--body": f'"{fam["body"].family}", {fam["body"].fallback}',
    }  # fmt: skip
    data = {"items": items, "duration": round(duration, 6)}
    out = (KIT / "overlays.html").read_text()
    for key, val in {
        "{{LANG}}": lang, "{{W}}": str(frame.width), "{{H}}": str(frame.height),
        "{{DURATION}}": f"{duration:.6f}",
        "{{DATA}}": json.dumps(data, ensure_ascii=False).replace("</", "<\\/"),
        "{{CSS_VARS}}": ":root{" + ";".join(f"{k}:{x}" for k, x in v.items()) + "}",
    }.items():  # fmt: skip
        out = out.replace(key, val)
    return out


def run_overlay(root: Path, project: str, cfg: LensConfig, out: Path | None = None, lang: str = "en") -> Path:
    base = root / "projects" / project
    tokens = Tokens.model_validate(json.loads((base / "tokens.json").read_text()))
    timeline = Timeline.model_validate(json.loads((base / "timeline.json").read_text()))
    plan = OverlayPlan.model_validate(yaml.safe_load((base / "overlays.yaml").read_text()))
    edl_p, fr_p = base / "edl.json", base / "framing.json"
    edl = Edl.model_validate(json.loads(edl_p.read_text())) if edl_p.exists() else None
    framing = Framing.model_validate(json.loads(fr_p.read_text())) if fr_p.exists() else None
    frame = cfg.create.design.frames[tokens.frame]
    plate = root / "data" / "create" / project / "footage" / "edited" / f"{project}-edited.mp4"
    frames, fps, _ = probe(plate)
    duration = frames / fps
    items = plan_items(plan, timeline, edl, framing, frame, cfg.create.footage.overlays.margin, duration)
    comp = root / "data" / "create" / project / "render" / "overlays"
    (comp / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    cache = root / "data" / "create" / "_cache"
    shutil.copy(gsap(cache), comp / "assets" / "gsap.min.js")
    css, files = fonts(cache, tokens.fonts_css)
    for f in files:
        shutil.copy(f, comp / "assets" / "fonts" / f.name)
    (comp / "assets" / "fonts.css").write_text(css)
    shutil.copy(plate, comp / "presenter.mp4")
    (comp / "index.html").write_text(overlay_comp(tokens, frame, items, duration, lang))
    render_comp(cfg.create.render, comp)
    target = out or root / "data" / "create" / project / "render" / f"{project}-overlays.mp4"
    mux(comp / "video.mp4", plate, duration, target)
    got, _, _ = probe(target)
    if got != frames:
        raise RuntimeError(f"frame count mismatch: output {got}, presenter {frames}")
    side = {"items": [{"t0": i["t0"], "t1": i["t1"], "zone": i["zone"], "title": i["title"]} for i in items]}
    target.with_suffix(".overlays.json").write_text(json.dumps(side, indent=1, ensure_ascii=False))
    return target
