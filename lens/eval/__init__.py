"""`lens eval` (S13, BUILD_PLAN 11.2): machine checks of the annotation layer.

- Answer key: on our own render, Claude's element choices, change labels, easing guesses and SFX labels
  are compared with the HyperFrames source (tests/fixtures/acme-v1/answer-key.json).
- Consistency: a blind second annotation (`lens status --task ... --rerun <run>`) of an even sample of
  events is compared with the first.
- Measured share: annotated reference events whose timing S7 measured.

Thresholds and label maps live in config `eval`. The result goes to runs/eval/<hash>.json, where the hash
covers the skills and the taxonomy.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lens import __version__
from lens.gold import sample_evenly
from lens.hashing import cache_key, sha256_file
from lens.measure.curves import ease_class
from lens.schemas import LensConfig
from lens.schemas.annotation import A2File
from lens.schemas.common import Annotator, Provenance
from lens.schemas.eval import AnswerKeyScores, ConsistencyScores, EvalFile, MeasuredShare, Ratio
from lens.schemas.record import RecordFile

STAGE = "s13_eval"
Box = tuple[float, float, float, float]


def ratio(hits: float, n: float) -> Ratio:
    return Ratio(hits=hits, n=n, value=round(hits / n, 4) if n else None)


def iou(a: Box, b: Box) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def eval_hash(root: Path) -> str:
    """sha256 over the skills and the taxonomy (paths and contents)."""
    h = hashlib.sha256()
    files = sorted([*(root / ".claude" / "skills").rglob("*"), *(root / "taxonomy").rglob("*")])
    for p in files:
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()


# --- the answer key ---------------------------------------------------------------------------------


def _num(v: Any) -> float | None:
    if isinstance(v, int | float):
        return float(v)
    if isinstance(v, str):
        m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)(?:px|%)?\s*", v)
        return float(m.group(1)) if m else None
    return None


def true_changes(tween: dict[str, Any]) -> list[set[str]]:
    """The visible changes a GSAP tween makes, each as the set of change types that name it."""
    to, frm = tween.get("to", {}), tween.get("from", {})
    rest = {"x": 0.0, "y": 0.0, "opacity": 1.0, "autoAlpha": 1.0, "scale": 1.0, "scaleX": 1.0, "scaleY": 1.0}
    out: list[set[str]] = []
    for prop in sorted(set(to) | set(frm)):
        a = _num(frm.get(prop, rest.get(prop)))
        b = _num(to.get(prop, rest.get(prop)))
        if prop in ("opacity", "autoAlpha") and a is not None and b is not None and a != b:
            out.append({"fade"})
        elif prop in ("x", "y") and a is not None and b is not None and a != b:
            d = b - a
            out.append(
                {
                    ("slide_right" if d > 0 else "slide_left")
                    if prop == "x"
                    else ("slide_down" if d > 0 else "slide_up")
                }
            )
        elif prop in ("scale", "scaleX", "scaleY") and a is not None and b is not None and a != b:
            grow = b > a
            out.append({"scale_up", "pop"} if grow else {"scale_down"})
            if prop != "scale" and grow:
                out[-1] |= {"draw_on", "mask_reveal"}
        elif prop == "filter" and "blur" in str(frm.get(prop, "")) + str(to.get(prop, "")):
            out.append({"blur_in"} if "blur(0" in str(to.get(prop, "")) else {"blur_out"})
        elif prop in ("strokeDashoffset", "drawSVG"):
            out.append({"draw_on"})
        elif prop in ("color", "backgroundColor", "fill", "stroke"):
            out.append({"color_shift"})
    return out


def _tweens_in(key: dict[str, Any], t0: float, t1: float, scale: tuple[float, float]) -> list[dict[str, Any]]:
    out = []
    for tw in key["tweens"]:
        if not tw.get("boxes") or not tw.get("duration_s"):
            continue
        if tw["start_s"] > t1 or tw["start_s"] + tw["duration_s"] < t0:
            continue
        changes = true_changes(tw)
        if not changes:
            continue
        for b in tw["boxes"]:
            box = (b[0] * scale[0], b[1] * scale[1], b[2] * scale[0], b[3] * scale[1])
            out.append({"box": box, "changes": changes, "ease": tw.get("ease"), "id": tw["id"]})
    return out


def answer_key_scores(root: Path, cfg: LensConfig) -> AnswerKeyScores | None:
    ak = cfg.eval.answer_key
    key_path, rec_path = root / ak.path, root / "videos" / ak.video / "record.json"
    if not key_path.exists() or not rec_path.exists():
        return None
    key = json.loads(key_path.read_text("utf-8"))
    rec = RecordFile.model_validate_json(rec_path.read_text("utf-8"))
    scale = (rec.frame_size[0] / key["frame_size"][0], rec.frame_size[1] / key["frame_size"][1])
    prec = [0, 0]
    rec_ = [0, 0]
    chg = [0, 0]
    chg_m = [0, 0]
    est = [0, 0]
    meas = [0, 0]
    unjudged = 0
    events = [e for e in rec.events if e.status == "annotated"]
    for e in events:
        truth = _tweens_in(key, e.start_s - ak.event_pad_s, e.end_s + ak.event_pad_s, scale)
        boxes = [(el, el.box) for el in e.elements if el.box is not None]
        for el, b in boxes:
            fb = (float(b[0]), float(b[1]), float(b[2]), float(b[3]))
            ious = [iou(fb, t["box"]) for t in truth]
            if not any(ious):  # nothing the key animates is there (text swaps, captions): no answer
                unjudged += 1
                continue
            hits = [t for t, v in zip(truth, ious, strict=True) if v >= ak.min_iou]
            prec[1] += 1
            if not hits:
                continue
            prec[0] += 1
            changes = [c for t in hits for c in t["changes"]]
            uniq = {frozenset(c) for c in changes}
            named = set(el.change_types)
            both = named | set(el.timing.changes if el.timing else [])
            chg[1] += len(uniq)
            chg[0] += sum(1 for c in uniq if c & named)
            chg_m[1] += len(uniq)
            chg_m[0] += sum(1 for c in uniq if c & both)
            want = ease_class(hits[0]["ease"])
            if el.timing is not None and el.timing.easing_class:
                slot = est if el.timing.source == "model_estimate" else meas
                slot[1] += 1
                slot[0] += int(el.timing.easing_class == want)
        targets: set[Box] = {
            (round(t["box"][0]), round(t["box"][1]), round(t["box"][2]), round(t["box"][3])) for t in truth
        }
        rec_[1] += len(targets)
        fboxes: list[Box] = [(float(b[0]), float(b[1]), float(b[2]), float(b[3])) for _, b in boxes]
        rec_[0] += sum(1 for t in targets if any(iou(fb, t) >= ak.min_iou for fb in fboxes))
    clf = [0, 0]
    rev = [0, 0]
    lo, hi = ak.sfx_window_s
    for clip in key["sfx"]:
        accepted = set(ak.sfx_labels.get(clip["file"], []))
        if not accepted:
            continue
        for x in rec.sfx:
            if x.verdict is None or not (lo <= x.sync_s - clip["start_s"] <= hi):
                continue
            clf[1] += 1
            rev[1] += 1
            clf[0] += int(x.classifier_label in accepted)
            rev[0] += int(x.label in accepted)
    return AnswerKeyScores(
        video=ak.video,
        events=len(events),
        box_precision=ratio(*prec),
        box_unjudged=unjudged,
        box_recall=ratio(*rec_),
        change_types=ratio(*chg),
        change_types_with_measured=ratio(*chg_m),
        sfx_classifier=ratio(*clf),
        sfx_after_review=ratio(*rev),
        estimate_easing=ratio(*est),
        measured_easing=ratio(*meas),
    )


# --- consistency --------------------------------------------------------------------------------------


def consistency_sample(root: Path, cfg: LensConfig) -> list[str]:
    """`<video>/<eid>` for an even sample of the annotated events of the consistency videos."""
    items = [
        f"{v}/{p.name.split('.')[0]}"
        for v in cfg.eval.consistency.videos
        for p in sorted((root / "videos" / v / "events").glob("e*.a2.json"))
    ]
    return sample_evenly(items, cfg.eval.consistency.events)


def _a2(path: Path) -> A2File | None:
    return A2File.model_validate_json(path.read_text("utf-8")) if path.exists() else None


def consistency_scores(root: Path, cfg: LensConfig, run: str) -> ConsistencyScores:
    sample = consistency_sample(root, cfg)
    boxes = [0, 0]
    pattern = [0, 0]
    role = [0, 0]
    change = [0, 0]
    sfx = [0, 0]
    missing = []
    for item in sample:
        video, eid = item.split("/")
        rel = f"videos/{video}/events/{eid}.a2.json"
        first, second = _a2(root / rel), _a2(root / "runs" / run / rel)
        if first is None or second is None:
            missing.append(item)
            continue
        a = {el.box: el for el in first.elements if el.box}
        b = {el.box: el for el in second.elements if el.box}
        boxes[0] += len(a.keys() & b.keys())
        boxes[1] += len(a.keys() | b.keys())
        pattern[1] += 1
        pattern[0] += int(first.pattern.id == second.pattern.id)
        for bid in a.keys() & b.keys():
            role[1] += 1
            role[0] += int(a[bid].role == b[bid].role)
            ca, cb = set(a[bid].change_types), set(b[bid].change_types)
            change[0] += len(ca & cb)
            change[1] += len(ca | cb)
        la = {r.id: r.label for r in first.sfx_review}
        lb = {r.id: r.label for r in second.sfx_review}
        for xid in la.keys() & lb.keys():
            sfx[1] += 1
            sfx[0] += int(la[xid] == lb[xid])
    return ConsistencyScores(
        run=run,
        events=sample,
        missing=missing,
        boxes=ratio(*boxes),
        pattern=ratio(*pattern),
        role=ratio(*role),
        change_types=ratio(*change),
        sfx_label=ratio(*sfx),
    )


# --- measured share -------------------------------------------------------------------------------------


def measured_share(root: Path, cfg: LensConfig) -> MeasuredShare:
    tier = cfg.eval.measured_tier
    events = measured = 0
    for p in sorted((root / "videos").glob("*/record.json")):
        rec = RecordFile.model_validate_json(p.read_text("utf-8"))
        if rec.tier != tier:
            continue
        for e in rec.events:
            if e.status != "annotated" or not e.elements:
                continue
            events += 1
            measured += int(
                any(el.timing is not None and el.timing.source == "measured" for el in e.elements)
            )
    share = round(measured / events, 4) if events else None
    target = cfg.eval.min_measured_share
    return MeasuredShare(
        tier=tier,
        events=events,
        measured=measured,
        share=share,
        target=target,
        ok=bool(share and share >= target),
    )


def run_eval(root: Path, cfg: LensConfig, run: str | None) -> tuple[Path, EvalFile]:
    h = eval_hash(root)
    inputs = sorted((root / "videos").glob("*/record.json"))
    if run:
        inputs += sorted((root / "runs" / run).rglob("*.a2.json"))
    result = EvalFile(
        provenance=Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CODE,
            input_hash=cache_key(
                {"stage": STAGE, "hash": h, "run": run, "inputs": [sha256_file(p) for p in inputs]}
            ),
            created_at=datetime.now(UTC),
        ),
        hash=h,
        answer_key=answer_key_scores(root, cfg),
        consistency=consistency_scores(root, cfg, run) if run else None,
        measured=measured_share(root, cfg),
    )
    out = root / "runs" / "eval" / f"{h}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result.model_dump_json(indent=1) + "\n", "utf-8")
    return out, result
