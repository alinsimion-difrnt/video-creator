"""A whole presenter video in one composition (`create reel`, create/kit/reel.html).

projects/<p>/reel.yaml (ReelPlan) says where the presenter is from which word on (full, split, pip, off),
which animated widgets (create/kit/motion.js) appear on which words, where the captions go, a slow push-in
per shot and a light grade. Code decides every position and time:
- presenter poses as `create pip` (create/footage/layout.py), with the split seam from the plan;
- widget boxes: product widgets in the product area of the layout at that moment, overlays in a zone clear of
  the face (F5 framing) and of the captions;
- captions above the head (the frame's `caption_top`) in full shots, above the seam in split, in the caption
  band over the product in pip / off. Never on the presenter's face or chest (Robert, 2026-10-09).
One render instead of three (layout, overlays, burn), so a variant costs one pass.
"""

from __future__ import annotations

import itertools
import json
import math
import shutil
import subprocess
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import yaml

from create.bundle import fonts, gsap
from create.burn import caption_vars, mux, probe, render_comp
from create.footage.edits import load_plan
from create.footage.layout import face_at, poses
from create.footage.overlays import face_box_at
from create.footage.pip import bubble_position
from lens.schemas.config import CaptionPlate, CreateFrame, FootageReel, LensConfig, Rect
from lens.schemas.create import Captions, Edl, Framing, LayoutPlan, ReelItem, ReelPlan, Timeline, Tokens

KIT = Path(__file__).resolve().parent.parent / "kit"
DEFAULT_W = {"sticker": 0, "cta": 0, "tiles": 0, "logo": 0, "pixel": 0}  # 0: the widget's own width
PRODUCT_W, OVERLAY_W = 640, 600  # layout widths before fitting (product widgets grow into their box)
MIN_LEFT_W = 380  # beside the face only when a sticker's words still fit a line
MIN_CHEST_H = 80  # a chest zone thinner than a one-line sticker is no zone
OVERSHOOT = 24  # a card's spring and drift reach this far past its box
# Motion styles (ADR 0033) set an entrance per kind of widget; pixel and handoff keep their own (stepped)
CARD_KINDS = frozenset(
    {
        "chat",
        "search",
        "sources",
        "review",
        "queries",
        "chart",
        "bars",
        "pins",
        "code",
        "bucket",
        "agents",
        "shredder",
    }
)
STICKER_KINDS = frozenset({"sticker", "tiles", "logo", "cta"})
NUMBER_KINDS = frozenset({"counter"})


@dataclass(frozen=True)
class Block:
    """A stretch of the edit in one presenter layout (a pseudo-scene for layout.poses)."""

    scene: str
    start_s: float
    end_s: float
    layout: str


def blocks(plan: ReelPlan, timeline: Timeline, duration: float) -> list[Block]:
    words = {w.i: w for w in timeline.words}
    out: list[Block] = []
    for k, b in enumerate(plan.layout):
        if b.word not in words:
            raise ValueError(f"reel.yaml layout: word {b.word} is not in the timeline")
        start = 0.0 if k == 0 else words[b.word].start_s
        end = words[plan.layout[k + 1].word].start_s if k + 1 < len(plan.layout) else duration
        out.append(Block(f"b{k:02d}", round(start, 3), round(end, 3), b.layout))
    return out


def layout_at(t: float, bl: list[Block]) -> str:
    for b in bl:
        if b.start_s - 1e-6 <= t < b.end_s:
            return b.layout
    return bl[-1].layout


def product_box(
    layout: str,
    frame: CreateFrame,
    seam: int,
    bubble: tuple[int, int, int],
    strip: float,
    captions_top: bool = False,
    pip_low: bool = False,
) -> Rect:
    """Where product widgets go in this layout: inside the safe area, clear of the captions and the bubble.
    Boxes start a little below the safe top (a card's spring overshoot) and keep off the action rail."""
    core = frame.safe[0]
    top = core.y0 + 32
    wide = max(r.x1 for r in frame.safe)  # the upper extension: clear of the rail above y 840
    if layout == "split":
        # clear of the caption strip by a little more than a card's entrance overshoot and drift; inside the
        # upper safe extension when it ends above y 840, else the core
        y1 = int(seam - strip - 40)
        ext_y1 = min(r.y1 for r in frame.safe if r.x1 == wide)
        if y1 <= ext_y1:  # wide enough to use the upper extension: stay above its edge with the overshoot
            y1 = min(y1, ext_y1 - OVERSHOOT)
        x1 = wide if y1 <= ext_y1 else core.x1
        return Rect(x0=core.x0, y0=top, x1=x1, y1=y1)
    if layout == "pip":
        _, by, _ = bubble
        if pip_low:  # the captions sit just above the low bubble, the card gets everything above them
            y1 = int(by - strip - OVERSHOOT - 12)
            return Rect(x0=core.x0, y0=top, x1=wide if y1 <= 840 - OVERSHOOT else core.x1, y1=y1)
        return Rect(x0=core.x0, y0=top, x1=wide, y1=by - 30)
    if captions_top and frame.caption_top is not None:  # off: captions on top, the card fills the core below
        return Rect(x0=core.x0, y0=frame.caption_top.y1 + 40, x1=core.x1, y1=core.y1)  # off the rail
    return Rect(x0=core.x0, y0=top, x1=core.x1, y1=frame.caption_band.y0 - 30)


def overlay_box(
    item: ReelItem,
    face: tuple[float, float, float, float],
    frame: CreateFrame,
    captions_top: bool,
    margin: int,
    hair_k: float = 0.3,
    aspect: float = 0.6,
    chin_k: float = 0.0,
) -> Rect:
    """An overlay's zone, clear of the face and the captions: on the chest (under the chin, above the bottom
    UI), left of the face (under the captions), or above the head (when the captions are not there).
    `auto` takes the zone where a widget of this height/width `aspect` can be largest."""
    c0 = frame.safe[0]
    inset = margin // 2  # tilted, drifting widgets reach a little past their box
    core = Rect(x0=c0.x0 + inset, y0=c0.y0, x1=c0.x1 - inset, y1=c0.y1 - OVERSHOOT)
    fx0, fy0, _, fy1 = face
    hair = fy0 - hair_k * (fy1 - fy0)
    top_cap = frame.caption_top if captions_top else None
    chest_y0 = int(fy1 + margin + chin_k * (fy1 - fy0))  # a beard and the zoom reach below the face box
    zones: dict[str, Rect] = {}
    if core.y1 - chest_y0 >= MIN_CHEST_H:  # a framing with the chin low leaves no chest inside the safe area
        zones["chest"] = Rect(x0=core.x0, y0=chest_y0, x1=core.x1, y1=core.y1)
    left_y0 = int(top_cap.y1 + margin) if top_cap is not None else core.y0
    if fx0 - 2 * margin - core.x0 >= 200:
        # twice the margin: the push-in and punch-ins move the face outwards
        zones["left"] = Rect(x0=core.x0, y0=left_y0, x1=int(fx0 - 2 * margin), y1=core.y1)
    if top_cap is None:
        zones["top"] = Rect(x0=core.x0, y0=core.y0, x1=core.x1, y1=max(core.y0 + 160, int(hair - margin)))
    if not zones:
        raise ValueError(f"overlay on word {item.word}: no room (chest, left or top) in this shot")
    if item.position != "auto":
        if item.position not in zones:
            raise ValueError(f"overlay on word {item.word}: no room {item.position!r} (captions or face)")
        return zones[item.position]

    def room(r: Rect) -> float:  # the widest widget of this aspect that fits
        return min(r.x1 - r.x0, (r.y1 - r.y0) / aspect)

    # beside the face (over the wall or sky) beats the chest unless the chest gives clearly more room
    return max(zones.items(), key=lambda kz: room(kz[1]) * (1.25 if kz[0] == "left" else 1.0))[1]


def caption_heights(
    captions: Captions,
    frame: CreateFrame,
    bl: list[Block],
    edl: Edl,
    framing: Framing | None,
    plan: ReelPlan,
    half: float,
    gap_px: float,
    hair_k: float = 0.3,
    zoom_k: float = 1.0,
    pip_top: float | None = None,
    chin_k: float = 0.35,
) -> list[dict[str, Any]]:
    """Per group: centre y, zone (top, seam, band) and whether it sits on the light product canvas.
    `pip_top`: the low bubble's top edge; pip captions then sit just above it (zone seam).
    `chin_k`: with `plan.caption_shirt`, a caption with no air above the head sits this many face-heights
    below the chin (plus the zoom's growth), inside the caption band."""
    band, top = frame.caption_band, frame.caption_top
    light = plan.product_bg != "ink"  # dark ink captions on a light product canvas
    out = []
    for g in captions.groups:
        layout = layout_at((g.start + g.end) / 2, bl)  # the layout most of the group plays in
        if layout == "split":
            out.append({"cy": round(plan.split_seam - gap_px - half, 1), "zone": "seam", "light": light})
        elif layout == "pip" and pip_top is not None:
            out.append({"cy": round(pip_top - gap_px - half, 1), "zone": "seam", "light": light})
        elif layout == "off" and plan.captions == "top" and top is not None:  # product fills below them
            out.append({"cy": round((top.y0 + top.y1) / 2, 1), "zone": "top", "light": light})
        elif layout in ("pip", "off"):
            out.append({"cy": round((band.y0 + band.y1) / 2, 1), "zone": "band", "light": light})
        elif plan.captions == "top" and top is not None:
            _, fy0, _, fy1 = face_box_at(g.start, edl, framing, frame.width, frame.height)
            hair = fy0 - hair_k * (fy1 - fy0)
            # the push-in and punch-ins scale about the face centre: the head grows up by this much
            grow = ((fy0 + fy1) / 2 - hair) * (zoom_k - 1)
            cy = min((top.y0 + top.y1) / 2, hair - grow - 2.5 * gap_px - half)  # clear air above the hair
            if plan.caption_shirt and cy < top.y0 + half:  # no air above the head: shirt, under the chin
                low = fy1 + chin_k * (fy1 - fy0) + (fy1 - (fy0 + fy1) / 2) * (zoom_k - 1) + half
                if low + half <= band.y1:
                    out.append({"cy": round(max(low, band.y0 + half), 1), "zone": "band", "light": False})
                    continue
            out.append({"cy": round(max(cy, top.y0 + half), 1), "zone": "top", "light": False})
        else:
            out.append({"cy": round((band.y0 + band.y1) / 2, 1), "zone": "band", "light": False})
    return out


def shots(edl: Edl, framing: Framing | None, w: int, h: int) -> list[dict[str, float]]:
    """Each shot's span and push-in origin (the face centre)."""
    out = []
    for s in edl.segments:
        t0 = s.rec_in / edl.fps
        t1 = (s.rec_in + s.src_out - s.src_in) / edl.fps
        cx, cy, _ = face_at((t0 + t1) / 2, edl, framing, w, h)
        out.append({"t0": round(t0, 4), "t1": round(t1, 4), "ox": round(cx, 1), "oy": round(cy, 1)})
    return out


def motion_style(plan: ReelPlan, rcfg: FootageReel) -> dict[str, Any]:
    """The plan's motion style (ADR 0033) as the page reads it: the named preset from config with the
    plan's overrides, plus the timing numbers. No `motion:` in the plan means `classic` (ADR 0026)."""
    name = plan.motion.style if plan.motion is not None else "classic"
    if name not in rcfg.styles:
        known = ", ".join(sorted(rcfg.styles))
        raise ValueError(f"motion style {name!r} is not in config create.footage.reel.styles ({known})")
    style = rcfg.styles[name].model_dump(exclude={"note"})
    if plan.motion is not None:
        style |= {k: v for k, v in plan.motion.model_dump(exclude={"style"}).items() if v is not None}
    return style | {
        "style": name,
        "handover_s": rcfg.handover_s,
        "kicker_h": rcfg.kicker_h,
        "bg_drift_s": rcfg.bg_drift_s,
        "cut_nudge_px": rcfg.cut_nudge_px,
    }


def styled_spec(spec: dict[str, Any], kind: str, motion: dict[str, Any]) -> dict[str, Any]:
    """The widget's spec with the style's entrance for its kind of widget, unless the plan chose one."""
    groups = (("cards", CARD_KINDS), ("stickers", STICKER_KINDS), ("numbers", NUMBER_KINDS))
    group = next((g for g, kinds in groups if kind in kinds), None)
    if group is None or spec.get("motion") or motion.get(group) is None:
        return dict(spec)
    return dict(spec) | {"motion": motion[group]}


def snap_to_cut(t0: float, cuts: list[float], within: float) -> float:
    """A card whose word starts just after a cut enters on the cut: the edit and the graphic agree."""
    for c in cuts:
        if 0 < t0 - c <= within:
            return round(c, 3)
    return t0


def plan_items(
    plan: ReelPlan,
    timeline: Timeline,
    bl: list[Block],
    edl: Edl,
    framing: Framing | None,
    frame: CreateFrame,
    bubble: tuple[int, int, int],
    strip: float,
    margin: int,
    duration: float,
    rcfg: FootageReel,
    hair_k: float = 0.3,
    motion: dict[str, Any] | None = None,
    cuts: list[float] | None = None,
) -> list[dict[str, Any]]:
    words = {w.i: w for w in timeline.words}
    motion = motion if motion is not None else motion_style(plan, rcfg)
    out = []
    for n, it in enumerate(plan.items):
        missing = [i for i in (it.word, it.until, *it.marks) if i not in words]
        if missing:
            raise ValueError(f"reel item {n} ({it.kind}): words {missing} are not in the timeline")
        t0, t1 = words[it.word].start_s, min(words[it.until].end_s, duration - 0.05)
        if motion["snap_cuts"] and cuts:
            t0 = snap_to_cut(t0, cuts, rcfg.snap_cuts_s)
        t0 = settle(t0, bl, plan.transition_s)
        layout = layout_at((t0 + t1) / 2, bl)
        if it.where == "product":
            if layout == "full":
                raise ValueError(
                    f"reel item {n} ({it.kind}) is a product widget, but the presenter is full there"
                )
            r = product_box(
                layout, frame, plan.split_seam, bubble, strip, plan.captions == "top", plan.pip_low
            )
        else:
            face = face_span(t0, t1, edl, framing, frame)
            aspect = rcfg.overlay_aspect.get(it.kind, 0.6)
            pref = (
                it
                if it.position != "auto" or plan.overlay_zone == "auto"
                else it.model_copy(update={"position": plan.overlay_zone})
            )
            try:
                r = overlay_box(
                    pref, face, frame, plan.captions == "top", margin, hair_k, aspect, rcfg.chest_chin_gap
                )
                if pref.position == "left" and r.x1 - r.x0 < MIN_LEFT_W:  # words would wrap one per line
                    raise ValueError("left zone too narrow")
            except ValueError:  # the preferred zone does not fit in this shot: the roomiest one
                r = overlay_box(
                    it, face, frame, plan.captions == "top", margin, hair_k, aspect, rcfg.chest_chin_gap
                )
        if it.w is not None:
            w = it.w
        elif it.where == "product":
            w = DEFAULT_W.get(it.kind, PRODUCT_W)
        else:  # lay out at the zone's width, so the widget (stickers too) wraps to it instead of shrinking
            own = it.kind in ("cta", "tiles", "logo", "pixel")
            w = 0 if own else int(min(OVERLAY_W, r.x1 - r.x0))
        out.append(
            {
                "kind": it.kind,
                "where": it.where,
                "spec": styled_spec(it.spec, it.kind, motion),
                "w": w or None,
                "t0": round(t0, 3),
                "t1": round(t1, 3),
                "marks": [round(words[m].start_s, 3) for m in it.marks],
                "box": [r.x0, r.y0, r.x1, r.y1],
                "title": str(it.spec.get("title") or it.spec.get("text") or it.spec.get("label") or it.kind),
                "handover_pref": it.handover,
            }
        )
    return hold_product(out, bl, duration, str(motion["handover"]), float(motion["handover_s"]))


def face_span(
    t0: float, t1: float, edl: Edl, framing: Framing | None, frame: CreateFrame
) -> tuple[float, float, float, float]:
    """The face box over a whole span: the union across every shot it covers (a cut can move the face)."""
    times = [t0, t1, (t0 + t1) / 2]
    times += [s.rec_in / edl.fps + 0.01 for s in edl.segments if t0 < s.rec_in / edl.fps < t1]
    boxes = [face_box_at(t, edl, framing, frame.width, frame.height) for t in times]
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def settle(t0: float, bl: list[Block], transition_s: float) -> float:
    """A widget that would start while the layout is still moving waits until the move is done."""
    for a, b in itertools.pairwise(bl):
        if a.layout != b.layout and b.start_s - transition_s / 2 <= t0 < b.start_s + transition_s / 2:
            return round(b.start_s + transition_s / 2, 3)
    return t0


def punches(
    plan: ReelPlan, timeline: Timeline, edl: Edl, framing: Framing | None, frame: CreateFrame, bl: list[Block]
) -> list[dict[str, float]]:
    """Quick zooms on the plan's key words (full shots only), about the face."""
    words = {w.i: w for w in timeline.words}
    out = []
    for i in plan.punches:
        if i not in words:
            raise ValueError(f"reel.yaml punches: word {i} is not in the timeline")
        w = words[i]
        if layout_at(w.start_s, bl) != "full":
            continue
        cx, cy, _ = face_at(w.start_s, edl, framing, frame.width, frame.height)
        t0, t1 = round(w.start_s, 3), round(w.end_s, 3)
        out.append({"t0": t0, "t1": t1, "ox": round(cx, 1), "oy": round(cy, 1)})
    for z in plan.zooms:  # held: in on one word, out on another
        if z.word not in words or z.until not in words:
            raise ValueError("reel.yaml zooms: a word is not in the timeline")
        a, b = words[z.word].start_s, words[z.until].start_s
        cx, cy, _ = face_at(a, edl, framing, frame.width, frame.height)
        out.append(
            {"t0": round(a, 3), "t1": round(b, 3), "ox": round(cx, 1), "oy": round(cy, 1), "scale": z.scale}
        )
    return sorted(out, key=lambda p: p["t0"])


def split_heads(
    bl: list[Block],
    ps: list[Any],
    edl: Edl,
    framing: Framing | None,
    frame: CreateFrame,
    plan: ReelPlan,
    hair_k: float,
) -> tuple[list[Any], list[list[float]]]:
    """Whole head visible in split (Robert: "you are cutting my face"): each shot's face is moved down until
    its hair (the face box raised by `hair_k` heights, plus the push-in's growth) clears the seam by
    `split_head_gap` px. A block's pose takes its first shot's move; later shots in the block add a
    [t, extra y, seconds] step (a hard set at the cut), and the move is taken off as the layout leaves."""
    assert plan.split_head_gap is not None
    seam, w, h, head_gap = plan.split_seam, frame.width, frame.height, plan.split_head_gap

    def dy_of(t0: float, t1: float) -> float:
        _, y0, _, y1 = face_box_at((t0 + t1) / 2, edl, framing, w, h)
        top = y0 - hair_k * (y1 - y0)
        grow = ((y0 + y1) / 2 - top) * (plan.push - 1)
        return max(0.0, seam + head_gap + grow - top)

    spans = [(s["t0"], s["t1"]) for s in shots(edl, framing, w, h)]
    out, steps = list(ps), []
    half_t = plan.transition_s / 2
    for k, b in enumerate(bl):
        if b.layout != "split":
            continue
        inside = [sp for sp in spans if sp[1] > b.start_s and sp[0] < b.end_s]
        if not inside:
            continue
        ref = dy_of(*inside[0])
        out[k] = replace(out[k], y=ref)
        for t0, t1 in inside[1:]:
            if b.start_s + 0.05 < t0 < b.end_s - half_t:
                steps.append([round(t0, 3), round(dy_of(t0, t1) - ref, 1), 0.0])
        if k + 1 < len(bl) and any(abs(st[1]) > 0.5 for st in steps if b.start_s < st[0] < b.end_s):
            steps.append([round(b.end_s - half_t, 3), 0.0, plan.transition_s])
    return out, steps


def hold_product(
    items: list[dict[str, Any]],
    bl: list[Block],
    duration: float,
    handover: str = "cut",
    handover_s: float = 0.55,
) -> list[dict[str, Any]]:
    """A product widget stays until the next one in its layout block arrives, or until the block ends (it
    has left by the end of the block), so the product area is never empty in a split.

    How the next card takes over (ADR 0033, `handover`, an item's own `handover` first): `cut` is the first
    take's rule, the next card lands 0.12 s after this one has left (no crossfade); morph, push and stack
    keep this card for `handover_s` more while MK.handover carries the two into each other."""
    index = {id(i): n for n, i in enumerate(items)}
    prod = sorted((i for i in items if i["where"] == "product"), key=lambda i: i["t0"])
    for k, it in enumerate(prod):
        block = next((b for b in bl if b.start_s - 1e-6 <= it["t0"] < b.end_s), None)
        if block is None:
            continue
        nxt = prod[k + 1]["t0"] if k + 1 < len(prod) and prod[k + 1]["t0"] < block.end_s else None
        end = nxt if nxt is not None else block.end_s  # gone as the next arrives or the layout moves
        it["t1"] = round(min(max(it["t1"], end), duration - 0.05), 3)
        if nxt is None:
            continue
        kind = prod[k + 1].get("handover_pref") or handover
        if kind == "cut":  # a clean hand-over: the next card lands after this one has left (no crossfade)
            prod[k + 1]["t0"] = round(nxt + 0.12, 3)
            continue
        it["t1"] = round(min(nxt + handover_s, duration - 0.05), 3)  # carried into the next card
        it["handover_out"] = kind
        prod[k + 1]["handover"] = kind
        prod[k + 1]["prev"] = index[id(it)]
    for it in items:
        it.pop("handover_pref", None)
    no_overlap([i for i in items if i["where"] == "overlay"])
    return items


def kicker_runs(items: list[dict[str, Any]], bl: list[Block], kick_h: int) -> list[dict[str, Any]]:
    """Product cards in a row (one layout block, one after the other) with the same kicker share one step
    label (ADR 0033, MK.kicker): it enters once, its step flips as each card arrives, and it leaves with the
    last card. Those cards lose their own kicker and give the label the top of their box. A lone card keeps
    its own label."""
    runs: list[dict[str, Any]] = []
    prod = sorted((i for i in items if i["where"] == "product"), key=lambda i: i["t0"])
    for it in prod:
        spec = it.get("spec") or {}
        text = spec.get("kicker")
        if not text:
            continue
        block = next((b for b in bl if b.start_s - 1e-6 <= it["t0"] < b.end_s), None)
        last = runs[-1] if runs else None
        follows = last is not None and last["block"] is block and it["t0"] <= last["t1"] + 0.2
        if last is not None and follows and last["text"] == text:
            run = last
        else:
            run = {"text": text, "block": block, "t0": it["t0"], "t1": it["t1"], "steps": [], "items": []}
            runs.append(run)
        run["t1"] = max(run["t1"], it["t1"])
        step = str(spec.get("step") or "")
        if not run["steps"] or run["steps"][-1][1] != step:
            run["steps"].append([it["t0"], step])
        run["items"].append(it)
    out = []
    for run in runs:
        if len(run["items"]) < 2:
            continue
        x0, y0, x1, _ = run["items"][0]["box"]
        for it in run["items"]:
            it["spec"] = {k: v for k, v in it["spec"].items() if k not in ("kicker", "step")}
            it["box"] = [it["box"][0], it["box"][1] + kick_h, it["box"][2], it["box"][3]]
            it["align"] = "top"  # the card hugs the label: the same top edge for the whole run
        out.append({"t0": run["t0"], "t1": run["t1"], "text": run["text"], "steps": run["steps"],
                    "box": [x0, y0, x1, y0 + kick_h]})  # fmt: skip
    return out


def no_overlap(overlays: list[dict[str, Any]]) -> None:
    """Overlays sharing space never crossfade: one leaves before the next lands."""
    ov = sorted(overlays, key=lambda i: i["t0"])
    for a, b in itertools.pairwise(ov):
        ax0, ay0, ax1, ay1 = a["box"]
        bx0, by0, bx1, by1 = b["box"]
        if a["t1"] > b["t0"] and ax0 < bx1 and ax1 > bx0 and ay0 < by1 and ay1 > by0:
            a["t1"] = round(max(a["t0"] + 0.8, b["t0"]), 3)
            b["t0"] = round(max(b["t0"], a["t1"] + 0.12), 3)


def css_vars(
    tokens: Tokens,
    frame: CreateFrame,
    plan: ReelPlan,
    d: int,
    xy: tuple[int, int],
    ring_w: int,
    plate: CaptionPlate | None = None,
) -> str:
    c = tokens.colors
    g = plan.grade
    grade = (
        f"contrast({g.contrast:g}) saturate({g.saturate:g}) brightness({g.brightness:g}) sepia({g.warmth:g})"
    )
    accent = c["accent"].lstrip("#")
    r, gg, b = (int(accent[i : i + 2], 16) for i in (0, 2, 4))
    v = caption_vars(tokens, frame) | {
        "--canvas": c["canvas"],
        "--surface": c["surface"],
        "--ink": c["ink"],
        "--muted": c["ink_muted"],
        "--accent": c["accent"],
        "--accent-fill": c.get("accent_fill", c["accent"]),
        "--second": c.get("second", c["ink"]),
        "--success": c.get("success", c["accent"]),
        "--error": c.get("error", c["accent"]),
        "--fill": c["fill_subtle"],
        "--chip": c["chip"],
        "--tint": f"rgba({r},{gg},{b},0.12)",
        "--hl": f"rgba({r},{gg},{b},0.28)",
        "--map": "#E8EEF3",
        "--river": "#B9D3EA",
        "--heading": f'"{tokens.families["heading"].family}", {tokens.families["heading"].fallback}',
        "--body": f'"{tokens.families["body"].family}", {tokens.families["body"].fallback}',
        "--grade": grade,
        "--d": f"{d}px",
        "--bx": f"{xy[0]}px",
        "--by": f"{xy[1]}px",
        "--ring": c["surface"],
        "--ring-w": f"{ring_w}px",
        "--cap-cx": f"{frame.width / 2:g}px",
    }
    if plate is not None:
        v |= {"--size": f"{plate.size_px}px", "--max-w": f"{plate.max_width_px}px"}
    return ":root{" + ";".join(f"{k}:{x}" for k, x in v.items()) + "}"


def build(
    root: Path, project: str, cfg: LensConfig, plan_path: Path | None = None, scale: float = 1.0
) -> tuple[Path, dict[str, Any]]:
    """Write the composition folder (data/create/<p>/render/reel/) and return it with the sidecar data.
    `scale` < 1 renders the same page smaller (a draft for review rounds); positions stay in frame pixels."""
    base = root / "projects" / project
    tokens = Tokens.model_validate(json.loads((base / "tokens.json").read_text()))
    timeline = Timeline.model_validate(json.loads((base / "timeline.json").read_text()))
    captions = Captions.model_validate(json.loads((base / "captions.json").read_text()))
    edl = Edl.model_validate(json.loads((base / "edl.json").read_text()))
    fr_p = base / "framing.json"
    framing = Framing.model_validate(json.loads(fr_p.read_text())) if fr_p.exists() else None
    plan = load_plan(base, plan_path)
    frame = cfg.create.design.frames[tokens.frame]
    rc = cfg.create.footage.reframe
    plate = root / "data" / "create" / project / "footage" / "edited" / f"{project}-edited.mp4"
    n, fps, _ = probe(plate)
    duration = n / fps
    bl = blocks(plan, timeline, duration)
    d = rc.pip_size[tokens.frame]
    xy = bubble_position(frame, d, rc.pip_margin, plan.corner, avoid_band=not plan.pip_low)
    layout_plan = LayoutPlan(
        default="full",
        corner=plan.corner,
        transition_s=plan.transition_s,
        scenes={b.scene: b.layout for b in bl},
    )
    ps = poses(
        SimpleNamespace(scenes=bl),  # type: ignore[arg-type]  # poses reads only .scenes
        layout_plan,
        edl,
        framing,
        frame,
        d,
        rc.pip_margin,
        rc.pip_face_scale,
        float(plan.split_seam),
        rc.split_face_offset,
        avoid_band=not plan.pip_low,
    )
    gap = cfg.create.design.caption_seam_gap_px
    shifts: list[list[float]] = []
    if plan.split_head_gap is not None:
        ps, shifts = split_heads(bl, ps, edl, framing, frame, plan, rc.hair_above_face)
    full = next((p for p in ps if p.layout == "full"), None)
    if full is not None:  # "off" fades the presenter out where they stand: no ghost shrinking into a corner
        ps = [replace(full, t=p.t, layout="off") if p.layout == "off" else p for p in ps]
    c = tokens.captions
    assert c is not None
    cplate = cfg.create.footage.reel.caption_plate if plan.caption_plate else None
    half = c.size_px * c.line_height + c.padding_px[0]  # two lines at most
    if cplate is not None:  # one line on a plate: its half height (a longer group wraps and grows upwards)
        half = (cplate.size_px * c.line_height + 2 * cplate.pad_y) / 2
    zoom_k = plan.push * (cfg.create.footage.reel.punch_scale if plan.punches else 1.0)
    pip_top = float(xy[1]) if plan.pip_low else None
    heights = caption_heights(
        captions,
        frame,
        bl,
        edl,
        framing,
        plan,
        half,
        gap,
        rc.hair_above_face,
        zoom_k,
        pip_top,
        cfg.create.design.caption_face_gap,
    )
    strip = 2 * half + 2 * gap
    motion = motion_style(plan, cfg.create.footage.reel)
    sh = shots(edl, framing, frame.width, frame.height)
    cuts = [s["t0"] for s in sh[1:]]
    items = plan_items(
        plan,
        timeline,
        bl,
        edl,
        framing,
        frame,
        (xy[0], xy[1], d),
        strip,
        cfg.create.footage.overlays.margin,
        duration,
        cfg.create.footage.reel,
        rc.hair_above_face,
        motion,
        cuts,
    )
    kickers = kicker_runs(items, bl, int(motion["kicker_h"])) if motion["kicker"] == "run" else []
    if any(it.hold for it in plan.items):
        held_on_palm(root, base, cfg, plan, edl, framing, frame, items)
    data = {
        "duration": round(duration, 6),
        "poses": [asdict(p) for p in ps],
        "transition": plan.transition_s,
        "panel": plan.panel,
        "shots": sh,
        "cuts": cuts,
        "push": plan.push,
        "items": items,
        "motion": motion,
        "kickers": kickers,
        "fit_up": cfg.create.footage.reel.fit_up,
        "fps": edl.fps,
        "max_width": cplate.max_width_px if cplate else c.max_width_px,
        "dim": max(c.dim_opacity, cfg.create.footage.reel.caption_dim),
        "punches": punches(plan, timeline, edl, framing, frame, bl),
        "caption_style": plan.caption_style,
        "plate": cplate.model_dump() | {"h1": 2 * half} if cplate else None,
        "shifts": shifts,
        "punch_scale": cfg.create.footage.reel.punch_scale,
        "text": tokens.colors[c.text],
        "text_light": tokens.colors["ink"],
        "active": tokens.colors[c.active],
        "groups": [g.model_dump() | h for g, h in zip(captions.groups, heights, strict=True)],
    }
    comp = root / "data" / "create" / project / "render" / "reel"
    (comp / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    cache = root / "data" / "create" / "_cache"
    shutil.copy(gsap(cache), comp / "assets" / "gsap.min.js")
    for name in ("motion.js", "motion.css", "props.js", "fred.js"):
        shutil.copy(KIT / name, comp / "assets" / name)
    css, files = fonts(cache, tokens.fonts_css)
    for f in files:
        shutil.copy(f, comp / "assets" / "fonts" / f.name)
    (comp / "assets" / "fonts.css").write_text(css)
    logo = tokens.logo.on_dark if plan.product_bg == "ink" and tokens.logo.on_dark else tokens.logo.primary
    brand_logo = root / "brands" / str(_brand(base)) / logo  # the light logo on a dark product area
    if brand_logo.exists():
        shutil.copy(brand_logo, comp / "assets" / "logo.svg")
    shutil.copy(plate, comp / "presenter.mp4")
    matte_html = add_props(root, project, base, cfg, plan, timeline, edl, framing, frame, tokens, data, comp)
    if plan.music is not None:
        on_the_beat(root, cfg, plan, data)
    out_w, out_h = round(frame.width * scale / 2) * 2, round(frame.height * scale / 2) * 2
    html = (KIT / "reel.html").read_text()
    for key, val in {
        "{{MATTE}}": matte_html,
        "{{FXMEDIA}}": data.pop("fx_media", ""),
        "{{BLOCK}}": str(data["block"]),
        "{{BLOCK_HALF}}": str(int(str(data["block"])) // 2),
        "{{BLOCK_Q}}": str(max(2, int(str(data["block"])) // 4)),
        "{{BLOCK_Q_HALF}}": str(max(1, int(str(data["block"])) // 8)),
        "{{BLOCK_H}}": str(max(2, int(str(data["block"])) // 2)),
        "{{BLOCK_H_HALF}}": str(max(1, int(str(data["block"])) // 4)),
        "{{LANG}}": _lang(base),
        "{{OUT_W}}": str(out_w),
        "{{OUT_H}}": str(out_h),
        "{{DURATION}}": f"{duration:.6f}",
        "{{PRODUCT_BG}}": plan.product_bg,
        "{{DATA}}": json.dumps(data, ensure_ascii=False).replace("</", "<\\/"),
        "{{CSS_VARS}}": css_vars(tokens, frame, plan, d, xy, rc.pip_ring, cplate)
        + f":root{{--out-w:{out_w}px;--out-h:{out_h}px;--out-k:{scale:g}}}",
    }.items():
        html = html.replace(key, str(val))
    (comp / "index.html").write_text(html)
    (comp / "reel-data.json").write_text(json.dumps(data, ensure_ascii=False))  # read by create reel --check
    recap_panels(comp, data)
    bullet_time(root, cfg, comp, data)
    shutil.rmtree(comp / "preview", ignore_errors=True)  # preview pages are not part of the render
    meta = {  # read by `create qa`: what is on screen beyond the presenter
        "captions": [
            {"start": g.start, "end": g.end, "words": len(g.words), "text": " ".join(w.w for w in g.words)}
            | h
            for g, h in zip(captions.groups, heights, strict=True)
        ],
        "caption_half_height": half,
        "caption_shirt": plan.caption_shirt,
        "layout": {"scenes": [asdict(b) for b in bl], "seam": plan.split_seam},
        "overlays": {"items": [_side(i) for i in items if i["where"] == "overlay"]},
        "product": {"items": [_side(i) for i in items if i["where"] == "product"]},
        "props": {"events": prop_sounds(data)},
        "audio": plan_audio(root, cfg, plan, timeline)
        + cast("list[dict[str, Any]]", data.pop("music_cue", [])),
    }
    return comp, meta


def snap(t: float, grid: list[float], within: float) -> float:
    """`t` moved onto the nearest grid time when one is within `within` s; else unchanged."""
    if not grid:
        return t
    g = min(grid, key=lambda b: abs(b - t))
    return g if abs(g - t) <= within else t


def on_the_beat(root: Path, cfg: LensConfig, plan: ReelPlan, data: dict[str, Any]) -> None:
    """The plan's music bed (tournament n06): Eleven Music for the video's length, its beats measured in
    code (lens.signals.audio.beats); hits snapped onto the nearest beat; the bars' first beats for the
    page's pulse; the bed itself as an audio cue for the mix."""
    import numpy as np

    from create.footage import sfx
    from create.footage.beatgrid import track

    assert plan.music is not None
    mc = cfg.create.footage.music
    path = sfx.el_music(root / "data" / "create" / "_cache", plan.music.prompt, data["duration"], mc.model)
    sr = 22050  # decoded by ffmpeg: librosa's numba beat tracker segfaults in the cloud sandbox (n06)
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
        capture_output=True, check=True,
    ).stdout  # fmt: skip
    b = track(np.frombuffer(raw, np.float32), sr)
    grid = [t for t in b.times if t < data["duration"]]
    data["beats"] = {"bpm": b.bpm, "confidence": b.confidence, "times": grid,
                     "bars": grid[::4] if plan.music.pulse else [], "pulse": mc.pulse_scale}  # fmt: skip
    if plan.music.snap:
        for p in data.get("punches", []):
            d = p["t1"] - p["t0"]
            p["t0"] = round(snap(p["t0"], grid, mc.snap_s), 3)
            p["t1"] = round(p["t0"] + d, 3)
        for tr in data.get("props", []):  # Fred's gag items pop on the beat too (n06 i2)
            for g in tr.get("gags", []):
                g["t"] = round(snap(g["t"], grid, mc.snap_s), 3)
        for f in data.get("fx", []):
            if f["kind"] in ("shake", "flash", "glitch", "burst"):
                d = f["t1"] - f["t0"]
                f["t0"] = round(snap(f["t0"], grid, mc.snap_s), 3)
                f["t1"] = round(f["t0"] + d, 3)
    data["music_cue"] = [{"t": 0.0, "file": str(path), "gain_db": plan.music.gain_db}]


def plan_audio(root: Path, cfg: LensConfig, plan: ReelPlan, timeline: Timeline) -> list[dict[str, Any]]:
    """The plan's own sound cues (ADR 0030) as files at times: formula sounds, ElevenLabs sound effects (from
    a prompt) and narration, each cached (data/create/_cache/). Effects sit `level_db` under the voice."""
    from create.footage import sfx

    cache = root / "data" / "create" / "_cache"
    starts = {w.i: w.start_s for w in timeline.words}
    out = []
    for a in plan.audio:
        if a.word not in starts:
            raise ValueError(f"reel.yaml audio: word {a.word} is not in the timeline")
        level = cfg.create.footage.sfx.level_db
        if a.say is not None:
            vc = (
                cfg.create.voice
                if a.voice is None
                else cfg.create.voice.model_copy(update={"voice_id": a.voice})
            )
            path, _ = sfx.el_voice(cache, a.say, vc)
            gain = a.gain_db
        elif a.prompt is not None:
            path, gain = sfx.el_sound(cache, a.prompt, a.duration_s), level + a.gain_db
        else:
            path, gain = sfx.sound(cache, str(a.sound)), level + a.gain_db
        out.append({"t": round(max(0.0, starts[a.word] + a.offset_s), 3), "file": str(path), "gain_db": gain})
    return out


def add_props(
    root: Path,
    project: str,
    base: Path,
    cfg: LensConfig,
    plan: ReelPlan,
    timeline: Timeline,
    edl: Edl,
    framing: Framing | None,
    frame: CreateFrame,
    tokens: Tokens,
    data: dict[str, Any],
    comp: Path,
) -> str:
    """Props and effects (ADR 0027) into the page data; their art into assets/props/. Returns the matte's
    <video> element when the plan uses it (props behind the presenter, an anime background)."""
    from create.footage import props as pr
    from create.footage.props_art import accessory_files, fred3d_sets, fred_pixel_sets, make_art

    pc = cfg.create.footage.reel.props
    rs = pr.rooms(edl, framing, _masters(base), frame)
    art_dir = comp / "assets" / "props"
    shutil.rmtree(art_dir, ignore_errors=True)
    tracks = []
    for p in plan.props:
        image = base / "assets" / p.image if p.image else None
        if image is not None and not image.exists():
            raise FileNotFoundError(
                f"prop {p.id}: {image} is missing (put the PNG in projects/{project}/assets/)"
            )
        styles = {p.style, *(b.style for b in p.beats if b.style)}
        art = make_art(p.id, p.art, image, styles, art_dir, pc.pixel_cells, p.colors)
        track = pr.prop_track(p, timeline, edl, framing, rs, art, pc, data["duration"])
        track["fps"] = art.fps
        if art.rig:  # Fred's pixel and 3D styles are frame sets (pixel art; ray-marched volumes)
            sets: dict[str, Any] = {}
            if combos := pr.style_combos(track, "pixel"):
                from create.pixel import fred as pixel_fred

                sets |= fred_pixel_sets(p.id, combos, art_dir)
                track["set_fps"] = {"px-": dict(pixel_fred.FPS)}
            if combos := pr.style_combos(track, "toon3d"):
                from create.render3d import fred3d

                sets |= fred3d_sets(p.id, combos, art_dir, root / "data" / "create" / "_cache")
                track["set_fps"] = track.get("set_fps", {}) | {"3d-": dict(fred3d.FPS)}
            if sets:
                track["pixel_sets"] = sets
                track["files"] = track["files"] | {
                    f: f for st in sets.values() for fs in st.values() for f in fs
                }
        if track.get("gags"):  # pixel gag items (create/pixel/items.py), at Fred's pixel size
            from create.footage.props_art import gag_files

            for g in track["gags"]:
                g.update(gag_files(p.id, g["name"], art_dir))
                g["rel"] = round(g["rel"] * pc.gag_scale, 4)
        tracks.append(track)
    # hands first: a carry aims at where the prop is then (r02: Pixie aimed at the plan's palm spot)
    follows = [(t, f) for t in tracks for f in t.get("follows", [])]
    for t, f in follows:  # carried by a hand: keyed from the presenter's pose
        from create.footage import pose as ps

        if f["by"] == "flee":  # ahead of the hand nearest its exit side until it runs off
            got = pose_samples(root, base, cfg, edl, framing, rs, f["t"], f["t"] + pc.flee_chase_s)
            lead = ps.lead_path(got, t["exit"]["kind"].endswith("left"))
            bolt = pc.speeds["run"] * t["w"] * pc.flee_bolt
            pr.apply_flee(t, f, lead, pc.flee_gap, pc.flee_chase_s, data["duration"], bolt)
            continue
        first = pr.position_at(t, f["t"])
        side_path = pose_samples(root, base, cfg, edl, framing, rs, f["t"], f["end"])
        pick = "lower" if f["by"] == "palm" else "lowest"
        _, path = ps.hand_path(side_path, first, cfg.create.footage.pose.smooth, pick)
        pr.apply_follow(t, f, path)
        if (
            "release" in f
        ):  # put down off the frame (a crop edge): he hops back on screen. Where the hand puts
            # him is the truth, even under the platform's UI: the safe-area hop put him on Robert's knee (r01)
            put = pr.position_at(t, f["release"])
            safe = pr.clamp(put, pr.spans(rs, f["release"], t["t1"]), t["w"], t["h"])
            if math.dist(put, safe) > 1:
                hop = pr.travel_s(math.dist(put, safe), t["w"], "hop", pc)
                t0h = f["release"] + 0.15
                t["moves"].append(
                    {
                        "t": round(t0h, 3),
                        "d": hop,
                        "x": safe[0],
                        "y": safe[1],
                        "ease": "power1.inOut",
                        "gait": "hop" if t.get("rig") else None,
                        "dir": 1 if safe[0] >= put[0] else -1,
                    }
                )
                t["moves"].sort(key=lambda m: m["t"])
    pr.link_carries(tracks, pc)
    for (
        t
    ) in tracks:  # an item held near the right edge goes in his other fin (r07: the book ran off the frame)
        for g in t.get("gags", []):
            x, _ = pr.position_at(t, g["t"])
            r = pr.room_at(g["t"], rs, edl)
            g["mirror"] = x * r.k + r.tx > frame.width * 0.7
            g["flip_left"] = x * r.k + r.tx < frame.width * 0.35  # near the left edge: "left" items go right
            if plan.gag_spot and g.get("place") in ("left", "above"):  # at a spot in the safe area (r16)
                sx, sy = (float(v) for v in plan.gag_spot["frame"])
                rx, ry = (sx * frame.width - r.tx) / r.k, (sy * frame.height - r.ty) / r.k
                _, y = pr.position_at(t, g["t"])
                g["spot"] = [round(rx - (x - t["w"] / 2), 1), round(ry - (y - t["h"]), 1)]
                g["rel"] = round(g["rel"] * float(plan.gag_spot.get("scale", 1.0)), 4)
    for t in tracks:  # a speech bubble near the right edge opens to the left (r02: "100?!" ran off the frame)
        for g in t["tags"]:
            if g["kind"] == "say":
                x, _ = pr.position_at(t, g["t"])
                r = pr.room_at(g["t"], rs, edl)
                g["flip"] = x * r.k + r.tx > frame.width * 0.55
            if (
                g["kind"] == "tag"
            ):  # a name tag high in the frame goes beside the head: above, it sat under the
                # captions and showed as a stray "d" (r05)
                x, y = pr.position_at(t, g["t"])
                r = pr.room_at(g["t"], rs, edl)
                tx = x * r.k + r.tx  # ... or near the right edge, where above it sat in the action rail (r06)
                g["side"] = (y - t["h"]) * r.k + r.ty < pc.tag_side_above
                g["lift"] = (
                    tx > frame.width * 0.7
                )  # near the right edge: above, shifted left (r07: beside the
                # head it landed on Fred standing next to her)
    if any(t["behind"] for t in tracks):  # behind the presenter: placed where the matte lets them show
        from create.footage.matte import alpha_at

        for t in tracks:
            for m in t["moves"] if t["behind"] else []:
                at = m["t"] + m["d"]
                alpha = alpha_at(root, project, round(at * edl.fps))
                if alpha is None:
                    continue
                r = pr.room_at(at, rs, edl)  # the matte is in frame pixels, props in master pixels (audit)
                fy = pr.peek_y(alpha, m["x"] * r.k + r.tx, m["y"] * r.k + r.ty, t["w"] * r.k, t["h"] * r.k,
                               pc.peek_share)  # fmt: skip
                m["y"] = round((fy - r.ty) / r.k, 1)
    for t in tracks:  # which image shows when (sprite cycles, pixel Fred), after carries cut stays short
        if t["frames"] or t.get("pixel_sets"):
            t["sched"] = pr.sprite_schedule(t, t.get("pixel_sets"))
        c = t["carry"]
        if c and c.get("rig") and c["style"] in pr.SET_PREFIX:  # a pixel / 3D Fred in the mouth: idle frame
            other = next(o for o in tracks if o["id"] == c["id"])
            key = pr.SET_PREFIX[c["style"]] + ("-".join(sorted(c["acc"])) or "plain")
            c.update(
                {
                    "file": other["pixel_sets"][key]["idle"][0],
                    "rig": False,
                    "pixel": c["style"] == "pixel",
                    "acc": [],
                }
            )
    for t in tracks:  # for create reel --check (prop-offscreen)
        t["visible"] = pr.visible_share(t, rs)
    fx = pr.fx_track(plan.fx, timeline, data["duration"], edl, framing, rs, tracks, pc.anchors)
    for k, f in enumerate(fx):  # words painted on the room's wood (tournament n08)
        if f["kind"] == "wall":
            paint_wall(root, base, cfg, edl, f, comp / "assets" / f"wall{k}.png", f"assets/wall{k}.png")
    for k, f in enumerate(fx):  # comic panels: freeze-frames of the presenter's own video (tournament n07)
        if f["kind"] == "panels":
            pan = comp / "assets" / "panels"
            pan.mkdir(parents=True, exist_ok=True)
            f["files"] = []
            for j, shot in enumerate(f["shots"]):
                out = pan / f"p{k}-{j}.jpg"
                subprocess.run(
                    ["ffmpeg", "-y", "-v", "error", "-ss", f"{shot:.3f}", "-i", str(comp / "presenter.mp4"),
                     "-frames:v", "1", "-q:v", "3", str(out)],
                    check=True,
                )  # fmt: skip
                f["files"].append(f"assets/panels/{out.name}")
    for f in fx:  # steel limbs on the presenter: the joints keyed from the pose
        if f["kind"] == "automail":
            from create.footage import pose as ps

            samples = pose_samples(root, base, cfg, edl, framing, rs, f["t0"], f["t1"])
            win = cfg.create.footage.pose.smooth
            f["limbs"] = {
                limb: [[t, pts] for t, pts in ps.limb_path(samples, limb, win)]
                for limb in f["spec"].get("limbs", ["right_arm", "left_leg"])  # Edward Elric's automail
            }
    from create.footage.matte import covering, load_index, matte_dir, matte_spans

    fps = edl.fps
    need = matte_spans(plan, timeline, fps, round(data["duration"] * fps), cfg.create.footage.matte.pad_s)
    clips: list[dict[str, Any]] = []
    if need:
        try:
            clips = covering(load_index(root, project), need)
        except FileNotFoundError:
            if pr.needs_matte(plan):  # props behind the presenter cannot work without it
                raise
            clips = []  # anime without the cut-out: its lines go round the frame's edges instead
    fam = tokens.families
    data.update(
        {
            "rooms": pr.room_data(rs),
            "room_k": round(sorted(r.k for r in rs)[len(rs) // 2], 6),
            "props": tracks,
            "pixel_cells": pc.pixel_cells,
            "props_kit": {"acc": accessory_files(art_dir)} if tracks else {},
            "fx": fx,
            "matte": bool(clips),
            "fg_spans": [[round(c["start"] / fps, 4), round(c["end"] / fps, 4)] for c in clips],
            "grade": plan.grade.model_dump(),
            "fonts": {
                "heading": f'"{fam["heading"].family}", {fam["heading"].fallback}',
                "body": f'"{fam["body"].family}", {fam["body"].fallback}',
                "mono": '"DejaVu Sans Mono", "Menlo", monospace',
            },
            "block": int(next((f["spec"].get("block", 24) for f in fx if f["kind"] == "blocky"), 24)),
        }
    )
    for old in comp.glob("matte-*.webm"):
        old.unlink()
    tags = []
    for k, c in enumerate(clips):
        shutil.copy(matte_dir(root, project) / c["file"], comp / f"matte-{k}.webm")
        t0, d = c["start"] / fps, (c["end"] - c["start"]) / fps
        tags.append(
            f'<video class="fg" id="fg{k}" src="matte-{k}.webm" muted playsinline data-start="{t0:.4f}" '
            f'data-duration="{d:.4f}" data-track-index="{k + 1}"></video>'
        )
    media = []
    for k, f in enumerate(f for f in fx if f["kind"] == "freeze"):  # bullet time (n05): made after the page
        f["file"] = f"assets/freeze{k}.mp4"
        f["media_id"] = f"freeze{k}"
        media.append(
            f'<video class="freeze" id="freeze{k}" src="{f["file"]}" muted playsinline '
            f'data-start="{f["t0"]:.4f}" '
            f'data-duration="{f["t1"] - f["t0"]:.4f}" data-track-index="{90 + k}"></video>'
        )
    data["fx_media"] = "\n".join(media)
    for k, f in enumerate(f for f in fx if f["kind"] == "clone"):  # a second presenter (tournament n03)
        need_a, need_b = f["src_t"] + 1e-3, f["src_t"] + f["t1"] - f["t0"] - 1e-3
        n, c = next(
            (n, c) for n, c in enumerate(clips) if c["start"] / fps <= need_a and c["end"] / fps >= need_b
        )  # fmt: skip
        sp = f["spec"]
        sc = float(sp.get("scale", 0.9))
        style = (
            f"transform: translateX({float(sp.get('dx', 0.4)) * frame.width:.1f}px) "
            f"scale({-sc if sp.get('flip') else sc}, {sc}); "
            # one colour, a hologram (n03 i0: rotating every hue turned his blue jeans brown)
            f"filter: grayscale(1) sepia(1) hue-rotate({float(sp.get('hue', 160))}deg) "
            f"saturate({float(sp.get('saturate', 3))}) brightness(1.08)"
        )
        tags.append(
            f'<video class="clone" id="clone{k}" src="matte-{n}.webm" muted playsinline style="{style}" '
            f'data-start="{f["t0"]:.4f}" data-duration="{f["t1"] - f["t0"]:.4f}" '
            f'data-media-start="{f["src_t"] - c["start"] / fps:.4f}" '
            f'data-track-index="{len(clips) + k + 1}"></video>'
        )
        f["clone_id"] = f"clone{k}"
    return "\n".join(tags)


def paint_wall(
    root: Path, base: Path, cfg: LensConfig, edl: Edl, f: dict[str, Any], mask_out: Path, rel: str
) -> None:
    """The surface for fx wall, measured on one master frame (the camera is locked): the wood mask over the
    surface's bounding box (a PNG the page masks the paint with) and the CSS transform taking a flat card
    onto the surface between spec rows (create/footage/surface.py)."""
    import numpy as np
    from PIL import Image

    from create.footage import surface as sf
    from lens.schemas.create import Footage

    sc, sp = cfg.create.footage.surface, f["spec"]
    footage = Footage.model_validate(json.loads((base / "footage.json").read_text()))
    take = next(t for t in footage.takes if t.id == edl.segments[0].take)
    ss = (
        f"{float(sp.get('frame_s', edl.segments[0].src_in / edl.fps)):.3f}"  # any frame: the camera is locked
    )
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", ss, "-i", str(root / take.master),
         "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
        capture_output=True, check=True,
    ).stdout  # fmt: skip
    import io

    img = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"))
    mask = sf.wood_mask(img, (sc.hue[0], sc.hue[1]), sc.sat_min, (sc.val[0], sc.val[1]))
    x0, x1 = (int(v) for v in sp.get("columns", [0, img.shape[1]]))
    q = sf.plane_quad(mask, x0, x1)
    r0, r1 = (float(v) for v in sp.get("rows", sc.rows))
    (lx, lt), (rx, rt), (_, rb), (_, lb) = q
    dst = [
        (lx, lt + (lb - lt) * r0),
        (rx, rt + (rb - rt) * r0),
        (rx, rt + (rb - rt) * r1),
        (lx, lt + (lb - lt) * r1),
    ]
    bx, by = min(p[0] for p in dst), min(p[1] for p in dst)
    bw, bh = max(p[0] for p in dst) - bx, max(p[1] for p in dst) - by
    cw = round(x1 - x0)
    ch = round(cw * sc.card_aspect)
    h = sf.homography([(0, 0), (cw, 0), (cw, ch), (0, ch)], [(x - bx, y - by) for x, y in dst])
    crop = mask[int(by) : int(by + bh) + 1, int(bx) : int(bx + bw) + 1]
    alpha = (crop * 255).astype(np.uint8)
    Image.fromarray(np.dstack([np.full_like(alpha, 255)] * 3 + [alpha]), "RGBA").save(mask_out)
    import base64

    # inlined: Chromium refuses a CSS mask image from a file:// page as cross-origin (n08 i0: no paint at all)
    uri = "data:image/png;base64," + base64.b64encode(mask_out.read_bytes()).decode()
    f |= {"mask": uri, "bbox": [round(bx, 1), round(by, 1), round(bw, 1), round(bh, 1)], "card": [cw, ch],
          "matrix": sf.css_matrix3d(h)}  # fmt: skip


def held_on_palm(
    root: Path,
    base: Path,
    cfg: LensConfig,
    plan: ReelPlan,
    edl: Edl,
    framing: Framing | None,
    frame: CreateFrame,
    items: list[dict[str, Any]],
) -> None:
    """Cards held on the presenter's palm (`hold: palm`, tournament n04): each gets a box of `held_w` and
    a path (record time, frame x, y of the box's top left) keyed from the lower palm, Fred's hand."""
    from create.footage import pose as ps
    from create.footage import props as pr
    from create.footage.framing import segment_index

    rc = cfg.create.footage.reel
    rs = pr.rooms(edl, framing, _masters(base), frame)
    for spec, it in zip(plan.items, items, strict=True):
        if spec.hold != "palm":
            continue
        aspect = rc.overlay_aspect.get(spec.kind, 0.6)
        w = round(min(rc.held_w, rc.held_h / aspect))  # a tall card narrower: it must fit under the chin
        h = round(w * aspect)
        got = pose_samples(root, base, cfg, edl, framing, rs, it["t0"], it["t1"])
        _, path = ps.hand_path(got, (frame.width / 2, frame.height), cfg.create.footage.pose.smooth, "lower")
        keyed = []
        for t, mx, my in path[::2]:
            r = pr.room_at(t, rs, edl)
            fx, fy = mx * r.k + r.tx, my * r.k + r.ty
            # inside the safe area, not just the frame (n04: cards on a hand right of centre crossed the rail)
            sa = frame.safe[0]  # the safe area's lower part (clear of the action rail and the description)
            x0 = min(max(fx - w / 2, sa.x0), sa.x1 - w)
            # never over his face: a raised hand lifts the card only to his chin (n04 i0: it covered his face)
            n = segment_index(t, edl)
            face = framing.segments[n].face if framing is not None else None
            chin = (face[1] + face[3]) * r.k + r.ty + rc.held_chin_gap if face else 0.0
            y0 = min(max(fy - h - w * rc.held_lift, chin), sa.y1 - h)
            keyed.append([round(t, 3), round(x0, 1), round(y0, 1)])
        for k in range(len(keyed)):  # a tray on a moving hand tilts with it (n04 i2): degrees from x speed
            a, b = keyed[max(0, k - 1)], keyed[min(len(keyed) - 1, k + 1)]
            vx = (b[1] - a[1]) / max(1e-3, b[0] - a[0])
            keyed[k].append(round(max(-rc.held_tilt, min(rc.held_tilt, -vx * rc.held_tilt_k)), 2))
        if keyed:
            it["box"] = [keyed[0][1], keyed[0][2], keyed[0][1] + w, keyed[0][2] + h]
            it["path"] = keyed
            it["w"] = w


def pose_samples(
    root: Path,
    base: Path,
    cfg: LensConfig,
    edl: Edl,
    framing: Framing | None,
    rs: list[Any],
    t0: float,
    t1: float,
) -> list[tuple[float, Any]]:
    """The presenter's pose (create/footage/pose.py) between two record times, on each edit segment's take,
    with the sample times mapped back to record time."""
    from create.footage import pose as ps
    from create.footage import props as pr
    from lens.schemas.create import Footage

    footage = Footage.model_validate(json.loads((base / "footage.json").read_text()))
    masters = {t.id: root / t.master for t in footage.takes}
    out: list[tuple[float, Any]] = []
    for n, s in enumerate(edl.segments):
        r0, r1 = s.rec_in / edl.fps, (s.rec_in + s.src_out - s.src_in) / edl.fps
        a, b = max(t0, r0), min(t1, r1)
        if b <= a:
            continue
        shift = s.src_in / edl.fps - r0  # source time = record time + shift
        face = pr.take_face(framing, s.take, rs[n].mw, rs[n].mh)
        got = ps.track(masters[s.take], a + shift, b + shift, face, root, cfg.create.footage.pose)
        out += [(round(t - shift, 3), pts) for t, pts in got if a - 1e-3 <= t - shift <= b + 1e-3]
    return out


def prop_sounds(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Sound cues for props and effects (create sfx): a pop as a prop lands or an accessory pops on, a boing
    as a hat drops, a shimmer on a style change or an anime / blocky switch, a whoosh as one runs off."""
    out: list[dict[str, Any]] = []
    for p in data.get("props", []):
        if p["enter"]["kind"] in ("pop", "drop"):
            out.append({"t": p["t0"], "sound": "pop"})
        out += [{"t": s["t"], "sound": "sparkle"} for s in p["styles"][1:]]
        for a in p["acc"]:
            if a["t"] > p["t0"] + 0.05 and a["add"]:
                hat = any(x in ("top_hat", "crown") for x in a["add"])
                out.append(
                    {"t": round(a["t"] + (0.45 if hat else 0.0), 3), "sound": "boing" if hat else "pop"}
                )
        out += [{"t": g["t"], "sound": "pop"} for g in p["tags"]]
        if p["exit"]["kind"] in ("run_left", "run_right", "swim_left", "swim_right"):
            out.append({"t": p["exit"]["t"], "sound": "whoosh"})
        if p.get("carry"):
            out.append({"t": p["carry"]["t"], "sound": "pop"})
    for f in data.get("fx", []):
        if f["kind"] in ("anime", "blocky", "flash", "glitch"):
            out.append({"t": f["t0"], "sound": "sparkle"})
    return sorted(out, key=lambda e: e["t"])


def _masters(base: Path) -> dict[str, tuple[int, int]]:
    """Each take's master size (footage.json), for props in room space."""
    p = base / "footage.json"
    if not p.exists():
        return {}
    from lens.schemas.create import Footage

    f = Footage.model_validate(json.loads(p.read_text()))
    return {t.id: (t.width, t.height) for t in f.takes}


def _brand(base: Path) -> str:
    return str((yaml.safe_load((base / "brief.yaml").read_text()) or {}).get("brand", ""))


def _lang(base: Path) -> str:
    return str((yaml.safe_load((base / "brief.yaml").read_text()) or {}).get("language", "en"))


def run_reel(
    root: Path,
    project: str,
    cfg: LensConfig,
    plan_path: Path | None = None,
    out: Path | None = None,
    force: bool = False,
    draft: bool = False,
) -> Path:
    """Check the plan (`create reel --check`; the layout checks too when playwright is installed), then
    render. A plan with check errors is not rendered unless `force`: a render costs ~6 minutes. A `draft`
    renders at config `create.footage.reel.draft_scale` (for review rounds; not a deliverable)."""
    import importlib.util

    from create.footage.reel_check import run_check

    found = run_check(
        root, project, cfg, plan_path, browser=importlib.util.find_spec("playwright") is not None
    )
    errors = [f for f in found if f.level == "error"]
    if errors and not force:
        raise ValueError(
            "the reel plan has check errors (create reel --check):\n" + "\n".join(f.line() for f in errors)
        )
    rcfg = cfg.create.footage.reel
    comp, meta = build(root, project, cfg, plan_path, rcfg.draft_scale if draft else 1.0)
    render_comp(cfg.create.render, comp, rcfg.frame_format)
    plate = comp / "presenter.mp4"
    n, fps, _ = probe(plate)
    target = out or root / "data" / "create" / project / "render" / f"{project}-reel.mp4"
    mux(comp / "video.mp4", plate, n / fps, target)
    got, _, _ = probe(target)
    if got != n:
        raise RuntimeError(f"frame count mismatch: output {got}, presenter {n}")
    meta_path = target.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    plan = load_plan(root / "projects" / project, plan_path)
    if plan.sounds and (
        meta.get("overlays", {}).get("items")
        or meta.get("product", {}).get("items")
        or meta.get("props", {}).get("events")
        or meta.get("audio")
    ):
        from create.footage.sfx import mix

        dry = target.with_name(target.stem + "-dry.mp4")
        target.replace(dry)
        mix(dry, meta_path, target, root / "data" / "create" / "_cache", cfg.create.footage.sfx,
            cfg.create.footage.voice.true_peak_db)  # fmt: skip
        dry.unlink()
    return target


def preview(comp: Path, times: list[float], out: Path, cols: int = 4, scale: float = 0.33) -> Path:
    """A contact sheet of the composition at `times` without rendering video: each still is the presenter's
    real frame (ffmpeg) under the page seeked to that time (Chromium, playwright). For design reviews."""
    shots_png, (w, h) = stills(comp, times)
    return _sheet(shots_png, w, h, out, cols, scale)


def bullet_time(root: Path, cfg: LensConfig, comp: Path, data: dict[str, Any]) -> None:
    """fx freeze (tournament n05): the page as seen just before the freeze, its depth (create/footage/
    depth.py), and the camera's 2.5D swing round it rendered to the clip the page plays over everything."""
    import urllib.request

    import numpy as np
    from PIL import Image

    from create.footage import depth as dp

    todo = [f for f in data.get("fx", []) if f["kind"] == "freeze"]
    if not todo:
        return
    dc = cfg.create.footage.depth
    model = root / "data" / "create" / "_cache" / "depth" / dc.model
    if not model.exists():
        model.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(dc.url, model)
    if dp.sha256(model) != dc.sha256:
        raise RuntimeError(f"{model}: sha256 does not match config create.footage.depth")
    for f in todo:
        shots, (w, h) = stills(comp, [max(0.0, f["t0"] - 1 / 30)], hide="#stage")
        rgb = np.asarray(Image.open(shots[0]).convert("RGB"))
        if f["spec"].get("look", True):  # frozen time looks unlike live time (n05 i3)
            rgb = dp.time_look(rgb, drain=0.45, cool=0.12, vignette=0.55)
        near = dp.depth(rgb, model, dc.side) ** 1.5  # the near end gets most of the move
        n = max(2, round((f["t1"] - f["t0"]) * dc.fps))
        k = w / 1080  # the orbit is set for a 1080 px wide frame
        enc = subprocess.Popen(
            ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
             "-r", str(dc.fps), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16",
             str(comp / f["file"])],
            stdin=subprocess.PIPE,
        )  # fmt: skip
        assert enc.stdin is not None
        amp, push = float(f["spec"].get("amp", dc.amp)), float(f["spec"].get("push", dc.push))
        for dx, dy, z in dp.orbit(n, amp * k, push):
            enc.stdin.write(np.ascontiguousarray(dp.warp(rgb, near, dx, dy, z)).tobytes())
        enc.stdin.close()
        if enc.wait() != 0:
            raise RuntimeError(f"bullet time {f['file']}: ffmpeg failed")


def recap_panels(comp: Path, data: dict[str, Any]) -> None:
    """A comic recap shows the moment as the viewer saw it, characters included: its panels are stills of
    this very page at the shot times (taken before the recap starts), over the raw frames reel.py cut first
    (n07 i1: raw frames had Robert but no Pixie, the subject of the recap)."""
    from PIL import Image

    for f in data.get("fx", []):
        if f["kind"] != "panels" or not f.get("shots"):
            continue
        shots, _ = stills(comp, f["shots"])
        for png, rel in zip(shots, f["files"], strict=True):
            Image.open(png).convert("RGB").save(comp / rel, quality=90)


def stills(comp: Path, times: list[float], hide: str = "") -> tuple[list[Path], tuple[int, int]]:
    """The composition as the viewer sees it at `times` (the presenter's frame under the seeked page), as PNGs
    in comp/preview/; and the page size. Also feeds a comic recap its panels (tournament n07)."""
    from playwright.sync_api import sync_playwright

    from create.browser import launch

    stills = comp / "preview"
    stills.mkdir(exist_ok=True)
    # the page lives in preview/ (one root composition per HyperFrames project); <base> keeps asset paths
    html = (comp / "index.html").read_text().replace('src="presenter.mp4"', 'src="" poster=""')
    html = html.replace("<head>", '<head><base href="../">', 1)
    if hide:  # e.g. the captions, kept live over a clip made from this still (n05 i1: they warped with it)
        html = html.replace(
            "</head>", f"<style>{hide} {{ visibility: hidden !important; }}</style></head>", 1
        )
    # the cut-out clips get a poster per still too (n02: unseeked, they showed their first frame throughout)
    import re

    fgs = [  # (element id, file, start, duration, offset into the file)
        (f"fg{m.group(1)}", f"matte-{m.group(1)}.webm", float(m.group(2)), float(m.group(3)), 0.0)
        for m in re.finditer(
            r'id="fg(\d+)" src="matte-\d+\.webm"[^>]*data-start="([\d.]+)" data-duration="([\d.]+)"', html
        )
    ] + [
        (f"clone{m.group(1)}", m.group(2), float(m.group(3)), float(m.group(4)), float(m.group(5)))
        for m in re.finditer(
            r'id="clone(\d+)" src="(matte-\d+\.webm)"[^>]*data-start="([\d.]+)" data-duration="([\d.]+)" '
            r'data-media-start="([\d.]+)"',
            html,
        )
    ]
    html = re.sub(r'(id="(?:fg|clone)\d+") src="(matte-\d+\.webm)"', r'\1 src="" poster=""', html)
    page_path = stills / "page.html"
    page_path.write_text(html)
    shots_png = []
    with sync_playwright() as pw:
        browser = launch(pw)
        w, h = (int(x) for x in _size(html))
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(page_path.as_uri())
        page.evaluate("document.fonts.ready")
        for k, t in enumerate(times):
            jpg = stills / f"f{k:03d}.jpg"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-ss",
                    f"{t:.3f}",
                    "-i",
                    str(comp / "presenter.mp4"),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "3",
                    str(jpg),
                ],
                check=True,
            )
            page.evaluate(
                """([src, t]) => new Promise(res => { const v = document.getElementById('face');
                   const img = new Image();
                   img.onload = () => { v.poster = src; window.__timelines.reel.seek(t, false);
                   requestAnimationFrame(() => requestAnimationFrame(res)); }; img.src = src; })""",
                [f"preview/{jpg.name}", t],
            )
            for eid, file, start, dur, off in fgs:
                if not start <= t < start + dur:
                    continue
                cut = stills / f"{eid}-{k:03d}.png"
                subprocess.run(
                    ["ffmpeg", "-y", "-v", "error", "-c:v", "libvpx-vp9", "-ss", f"{t - start + off:.3f}",
                     "-i", str(comp / file), "-frames:v", "1", str(cut)],
                    check=True,
                )  # fmt: skip
                page.evaluate(
                    """([id, src]) => new Promise(res => { const v = document.getElementById(id);
                       const img = new Image(); img.onload = () => { v.poster = src;
                       requestAnimationFrame(() => requestAnimationFrame(res)); }; img.src = src; })""",
                    [eid, f"preview/{cut.name}"],
                )
            png = stills / f"s{k:03d}.png"
            page.screenshot(path=str(png))
            shots_png.append(png)
        browser.close()
    return shots_png, (w, h)


def _sheet(shots_png: list[Path], w: int, h: int, out: Path, cols: int, scale: float) -> Path:
    tw, th = round(w * scale), round(h * scale)
    rows = (len(shots_png) + cols - 1) // cols
    inputs: list[str] = []
    for p in shots_png:
        inputs += ["-i", str(p)]
    labels = "".join(f"[{i}:v]scale={tw}:{th}[v{i}];" for i in range(len(shots_png)))
    pad = len(shots_png) < rows * cols
    stack = "".join(f"[v{i}]" for i in range(len(shots_png)))
    layout = "|".join(f"{(i % cols) * tw}_{(i // cols) * th}" for i in range(len(shots_png)))
    filt = f"{labels}{stack}xstack=inputs={len(shots_png)}:layout={layout}" + (":fill=black" if pad else "")
    if len(shots_png) == 1:
        filt = f"[0:v]scale={tw}:{th}"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", filt, "-frames:v", "1", str(out)],
        check=True,
    )
    return out


def _size(html: str) -> tuple[str, str]:
    import re

    m = re.search(r'data-width="(\d+)" data-height="(\d+)"', html)
    assert m is not None
    return m.group(1), m.group(2)


def _side(i: dict[str, Any]) -> dict[str, Any]:
    """An item as the sidecar records it (create qa: placement; create sfx: kind and click time)."""
    out = {"t0": i["t0"], "t1": i["t1"], "zone": i["box"], "title": i["title"], "kind": i["kind"]}
    if i.get("handover"):
        out["handover"] = i["handover"]  # create sfx: a carried card arrives with a whoosh, not a pop
    if i["kind"] == "cta":
        out["click"] = i["marks"][0] if i["marks"] else round(i["t0"] + (i["t1"] - i["t0"]) * 0.45, 3)
    return out
