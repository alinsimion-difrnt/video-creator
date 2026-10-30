"""S4 visual evidence (BUILD_PLAN 7.2): what Claude looks at, and what S7 measures from.

    data/evidence/<id>/evidence.json                       index: bursts, crops, energy curves, sheets
    data/evidence/<id>/events/<eid>/filmstrip.jpg          frames at motion-energy quantiles, cropped
    data/evidence/<id>/events/<eid>/end_marked.jpg         settled end frame, numbered candidate boxes
    data/evidence/<id>/events/<eid>/end_clean.jpg          the same frame without marks
    data/evidence/<id>/events/<eid>/spectrogram.jpg        mel spectrogram, SFX candidates marked
    data/evidence/<id>/events/<eid>/candidates.json        box ids and coordinates (validated)
    data/evidence/<id>/sheets/shot_<sid>_<n>.jpg           2 fps contact sheets per shot
    data/evidence/<id>/keyframes/shot_<sid>.jpg            mid-shot frame at proxy resolution

Bursts are frame ranges of the proxy (CFR at native fps), not copies: S7 decodes the proxy itself.
The proxy is decoded twice: pass 1 measures motion energy inside each event's crop, pass 2 keeps
only the frames the images need.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from lens import __version__
from lens.evidence import boxes as bx
from lens.evidence import draw
from lens.hashing import cache_key
from lens.ingest import read_marker, write_marker
from lens.media import iter_frames_rgb
from lens.schemas import LensConfig, SourceEntry
from lens.schemas.common import Annotator, Provenance
from lens.schemas.evidence import BoxOut, CandidatesFile
from lens.schemas.signals import SignalsSummary
from lens.schemas.video import VideoMeta

STAGE = "s4_evidence"


class EvidenceError(RuntimeError):
    pass


@dataclass
class EventPlan:
    id: str
    shot: str
    start_f: int
    end_f: int
    b0: int  # burst, inclusive
    b1: int
    bbox: bx.Box
    crop: bx.Box
    energy: list[float] = field(default_factory=list)
    qframes: list[int] = field(default_factory=list)


def _base_frames(root: Path, video: str) -> list[tuple[float, Path]]:
    base = root / "data" / "frames" / video / "base"
    return sorted((int(p.stem[1:]) / 1000.0, p) for p in base.glob("t*.jpg"))


def _above_captions(bbox: list[float] | None, summary: SignalsSummary, cfg: LensConfig) -> list[float] | None:
    """With burned-in captions, every word switch changes the caption band, so S3's event boxes
    reach down into it. Clip them to above the band (a box entirely inside it stays: it is a
    caption event, which S5 triage skips)."""
    if bbox is None or summary.captions is None or summary.captions.groups == 0:
        return bbox
    top = 1 - cfg.signals.captions.band_fraction
    if bbox[1] >= top or bbox[3] <= top:
        return bbox
    return [bbox[0], bbox[1], bbox[2], top]


def _plan(
    meta: VideoMeta, summary: SignalsSummary, detail: dict[str, Any], cfg: LensConfig
) -> list[EventPlan]:
    fps, n = meta.proxy.fps, meta.proxy.frames
    w, h = meta.proxy.width, meta.proxy.height
    pad = round(cfg.evidence.burst_pad_s * fps)
    shots = {s.id: (round(s.start_s * fps), min(n, round(s.end_s * fps))) for s in summary.video.shots}
    plans = []
    for e in detail.get("events", []):
        if e["kind"] not in ("motion", "camera"):
            continue
        s0, s1 = shots.get(e["shot"], (0, n))
        b0 = max(s0, e["start_f"] - pad, 0)
        b1 = min(s1 - 1, e["end_f"] + pad, n - 1)
        bbox = bx.norm_to_px(_above_captions(e["bbox"], summary, cfg), w, h)
        crop = bx.crop_box(bbox, w, h, cfg.evidence.crop_margin, cfg.evidence.crop_min_px)
        plans.append(EventPlan(e["id"], e["shot"], e["start_f"], e["end_f"], b0, max(b0, b1), bbox, crop))
    return plans


def _energy_pass(proxy: Path, meta: VideoMeta, plans: list[EventPlan]) -> None:
    """Mean absolute frame-to-frame change inside each event's crop, over its burst."""
    by_start = sorted(plans, key=lambda p: p.b0)
    active: list[EventPlan] = []
    nxt = 0
    prev: np.ndarray | None = None
    last = max((p.b1 for p in plans), default=-1)
    for f, frame in iter_frames_rgb(proxy, meta.proxy.fps, meta.proxy.width, meta.proxy.height):
        while nxt < len(by_start) and by_start[nxt].b0 == f:
            active.append(by_start[nxt])
            nxt += 1
        for p in active:
            if f == p.b0 or prev is None:
                p.energy.append(0.0)
            else:
                x0, y0, x1, y1 = p.crop
                a = frame[y0:y1, x0:x1].astype(np.int16)
                b = prev[y0:y1, x0:x1].astype(np.int16)
                p.energy.append(round(float(np.abs(a - b).mean()) / 255.0, 6))
        active = [p for p in active if p.b1 > f]
        prev = frame
        if f >= last:
            break


def _frames(proxy: Path, meta: VideoMeta, wanted: set[int]) -> Iterator[tuple[int, np.ndarray]]:
    if not wanted:
        return
    last = max(wanted)
    for f, frame in iter_frames_rgb(proxy, meta.proxy.fps, meta.proxy.width, meta.proxy.height):
        if f in wanted:
            yield f, frame.copy()
        if f >= last:
            break


def _ocr_lines(frame: np.ndarray, crop: bx.Box, min_score: float) -> list[tuple[bx.Box, str]]:
    from lens.signals.captions import _ocr

    x0, y0, x1, y1 = crop
    out = _ocr()(np.ascontiguousarray(frame[y0:y1, x0:x1]))
    boxes = out.boxes if out.boxes is not None else []
    lines = []
    for quad, text, score in zip(boxes, out.txts or (), out.scores or (), strict=False):
        if score < min_score or not str(text).strip():
            continue
        q = np.asarray(quad)
        bx0, by0 = int(np.floor(q[:, 0].min())) + x0, int(np.floor(q[:, 1].min())) + y0
        bx1, by1 = int(np.ceil(q[:, 0].max())) + x0, int(np.ceil(q[:, 1].max())) + y0
        lines.append(((max(bx0, 0), max(by0, 0), bx1, by1), str(text).strip()))
    return lines


def candidates(
    start: np.ndarray, end: np.ndarray, plan: EventPlan, cfg: LensConfig, ocr: bool = True
) -> list[bx.Candidate]:
    """Diff components + OCR lines that changed + bbox_union, ranked by change, NMS, capped."""
    ev = cfg.evidence
    mask = bx.change_mask(start, end, cfg.signals.video.mask_threshold)
    keep = np.zeros_like(mask)
    x0, y0, x1, y1 = plan.crop
    keep[y0:y1, x0:x1] = True
    mask &= keep  # change elsewhere belongs to other events
    raw: list[tuple[bx.Box, str, str | None]] = [
        (b, "diff", None) for b in bx.diff_components(mask, ev.box_merge_px, ev.box_min_area)
    ]
    if ocr:
        integral = np.zeros((mask.shape[0] + 1, mask.shape[1] + 1), np.int64)
        integral[1:, 1:] = mask.cumsum(0).cumsum(1)
        for b, text in _ocr_lines(end, plan.crop, ev.ocr_min_score):
            if bx.area(b) and bx.score(b, integral) / bx.area(b) >= ev.ocr_min_changed:
                raw.append((b, "ocr", text))
    raw.append((plan.bbox, "union", None))
    return bx.rank_and_suppress(raw, mask, ev.box_nms_iou, ev.max_candidate_boxes)


def _filmstrip(frames: dict[int, np.ndarray], plan: EventPlan, fps: float, cfg: LensConfig) -> Image.Image:
    x0, y0, x1, y1 = plan.crop
    tiles = [Image.fromarray(frames[f][y0:y1, x0:x1]) for f in plan.qframes]
    caps = [f"{draw.stamp(f / fps)}  ·  f{f}" for f in plan.qframes]
    tiles.append(draw.context_thumb(frames[plan.b1], plan.crop, tiles[0].size))
    caps.append("context")
    q = " ".join(f"{v:g}" for v in cfg.evidence.filmstrip_quantiles)
    header = (
        f"{plan.id} · shot {plan.shot} · {draw.stamp(plan.start_f / fps)}-{draw.stamp(plan.end_f / fps)}"
        f" · frames at motion-energy quantiles {q}"
    )
    return draw.grid(tiles, caps, cols=4, long_edge=cfg.evidence.image_long_edge_px, header=header)


def _spectrogram(
    wav: Path, plan: EventPlan, summary: SignalsSummary, fps: float, cfg: LensConfig
) -> Image.Image | None:
    import librosa

    from lens.evidence.spectro import Mark, render

    win = cfg.evidence.spectrogram_window_s
    t0 = max(0.0, plan.start_f / fps - win)
    t1 = (plan.end_f + 1) / fps + win
    y, sr = librosa.load(str(wav), sr=None, mono=True, offset=t0, duration=t1 - t0)
    sfx = summary.audio.sfx if summary.audio else []
    marks = [Mark(s.sync_s, f"{s.id} {s.label}") for s in sfx if t0 <= s.sync_s <= t1]
    what = "music+SFX stem (voice removed)" if "stems" in wav.parts else "full mix"
    title = f"{plan.id} · {what} · {draw.stamp(t0)}-{draw.stamp(t1)} · box = event · lines = SFX candidates"
    size = (cfg.evidence.spectrogram_width_px, cfg.evidence.spectrogram_height_px)
    return draw.fit(
        render(y, int(sr), t0, marks, (plan.start_f / fps, (plan.end_f + 1) / fps), size, title),
        cfg.evidence.image_long_edge_px,
    )


def _save(img: Image.Image, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=88)
    return path.name


def _sheets(
    root: Path, video: str, summary: SignalsSummary, out: Path, cfg: LensConfig
) -> dict[str, list[str]]:
    ev = cfg.evidence
    base = _base_frames(root, video)
    result: dict[str, list[str]] = {}
    for s in summary.video.shots:
        frames = [(t, p) for t, p in base if s.start_s <= t < s.end_s]
        chunks = [frames[i : i + ev.sheet_max_tiles] for i in range(0, len(frames), ev.sheet_max_tiles)]
        names = []
        for k, chunk in enumerate(chunks, start=1):
            tiles = [Image.open(p).convert("RGB") for _, p in chunk]
            header = (
                f"shot {s.id} · {draw.stamp(s.start_s)}-{draw.stamp(s.end_s)} · 2 fps"
                f" · sheet {k}/{len(chunks)}"
            )
            sheet = draw.grid(
                tiles, [draw.stamp(t) for t, _ in chunk], ev.sheet_cols, ev.image_long_edge_px, header=header
            )
            names.append(_save(sheet, out / "sheets" / f"shot_{s.id}_{k}.jpg"))
        result[s.id] = names
    return result


def run_evidence(entry: SourceEntry, root: Path, cfg: LensConfig, force: bool = False) -> str:
    vdir = root / "videos" / entry.id
    summary_path = vdir / "signals.summary.json"
    if not summary_path.exists():
        return "skipped"
    meta = VideoMeta.model_validate_json((vdir / "meta.json").read_text(encoding="utf-8"))
    summary = SignalsSummary.model_validate_json(summary_path.read_text(encoding="utf-8"))
    key = cache_key(
        {
            "stage": STAGE,
            "tool": __version__,
            "signals": summary.provenance.input_hash,
            "evidence": cfg.evidence.model_dump(),
            "mask": cfg.signals.video.mask_threshold,
        }
    )
    out = root / "data" / "evidence" / entry.id
    marker = read_marker(root, entry.id, STAGE)
    if not force and marker and marker.get("cache_key") == key and (out / "evidence.json").exists():
        return "cached"
    proxy = root / "data" / "media" / entry.id / "proxy.mp4"
    detail_path = root / "data" / "signals" / entry.id / "signals.json"
    if not proxy.exists() or not detail_path.exists():
        raise EvidenceError(f"{entry.id}: proxy or S3 detail missing; run `lens frames` / `lens signals`")
    detail = json.loads(detail_path.read_text(encoding="utf-8"))
    if out.exists():
        shutil.rmtree(out)  # this stage owns the directory; no stale event folders
    out.mkdir(parents=True)
    fps = meta.proxy.fps

    plans = _plan(meta, summary, detail, cfg)
    _energy_pass(proxy, meta, plans)
    for p in plans:
        p.qframes = [p.b0 + i for i in bx.quantile_frames(p.energy, cfg.evidence.filmstrip_quantiles)]

    keyframes = {
        s.id: min(meta.proxy.frames - 1, round((s.start_s + s.end_s) / 2 * fps)) for s in summary.video.shots
    }
    wanted = {f for p in plans for f in (*p.qframes, p.b0, p.b1)} | set(keyframes.values())
    need: dict[int, list[EventPlan]] = {}
    for p in plans:
        for f in {*p.qframes, p.b0, p.b1}:
            need.setdefault(f, []).append(p)
    held: dict[str, dict[int, np.ndarray]] = {p.id: {} for p in plans}
    remaining = {p.id: len({*p.qframes, p.b0, p.b1}) for p in plans}
    # SFX are easier to see without the voice: prefer S3's accompaniment stem.
    wav = root / "data" / "signals" / entry.id / "stems" / "accompaniment.wav"
    if not wav.exists():
        wav = root / "data" / "media" / entry.id / "audio.wav"
    now = datetime.now(UTC)
    prov = Provenance(
        tool_version=__version__, stage=STAGE, annotator=Annotator.CODE, input_hash=key, created_at=now
    )
    index: dict[str, Any] = {"video": entry.id, "fps": fps, "size": [meta.proxy.width, meta.proxy.height]}
    events_index: dict[str, Any] = {}
    kf_names: dict[str, str] = {}

    for f, frame in _frames(proxy, meta, wanted):
        for sid, kf in keyframes.items():
            if kf == f:
                img = draw.fit(Image.fromarray(frame), cfg.evidence.image_long_edge_px)
                kf_names[sid] = _save(img, out / "keyframes" / f"shot_{sid}.jpg")
        for p in need.get(f, []):
            held[p.id][f] = frame
            remaining[p.id] -= 1
            if remaining[p.id]:
                continue
            frames = held.pop(p.id)
            edir = out / "events" / p.id
            _save(_filmstrip(frames, p, fps, cfg), edir / "filmstrip.jpg")
            cands = candidates(frames[p.b0], frames[p.b1], p, cfg)
            ids = [f"b{i:02d}" for i in range(1, len(cands) + 1)]
            _save(
                draw.set_of_marks(frames[p.b1], [c.box for c in cands], ids, cfg.evidence.image_long_edge_px),
                edir / "end_marked.jpg",
            )
            _save(
                draw.fit(Image.fromarray(frames[p.b1]), cfg.evidence.image_long_edge_px),
                edir / "end_clean.jpg",
            )
            spec = _spectrogram(wav, p, summary, fps, cfg) if wav.exists() else None
            if spec is not None:
                _save(spec, edir / "spectrogram.jpg")
            w, h = meta.proxy.width, meta.proxy.height
            cfile = CandidatesFile(
                provenance=prov,
                video=entry.id,
                event=p.id,
                frame_size=(w, h),
                start_frame=p.b0,
                end_frame=p.b1,
                boxes=[
                    BoxOut(
                        id=i,
                        source=c.source,
                        xyxy=c.box,
                        norm=(
                            round(c.box[0] / w, 4),
                            round(c.box[1] / h, 4),
                            round(c.box[2] / w, 4),
                            round(c.box[3] / h, 4),
                        ),
                        changed_share=min(1.0, c.changed_share),
                        text=c.text,
                    )
                    for i, c in zip(ids, cands, strict=True)
                ],
            )
            (edir / "candidates.json").write_text(cfile.model_dump_json(indent=2) + "\n", encoding="utf-8")
            events_index[p.id] = {
                "shot": p.shot,
                "start_f": p.start_f,
                "end_f": p.end_f,
                "burst": [p.b0, p.b1],
                "bbox": list(p.bbox),
                "crop": list(p.crop),
                "filmstrip_frames": p.qframes,
                "energy": p.energy,
                "spectrogram": spec is not None,
                "boxes": len(cands),
            }
    missing = [p.id for p in plans if p.id not in events_index]
    if missing:
        raise EvidenceError(f"{entry.id}: frames not decoded for {', '.join(missing)}")
    index["events"] = dict(sorted(events_index.items()))
    index["shots"] = {
        sid: {"sheets": sheets, "keyframe": kf_names.get(sid)}
        for sid, sheets in _sheets(root, entry.id, summary, out, cfg).items()
    }
    index["provenance"] = json.loads(prov.model_dump_json())
    (out / "evidence.json").write_text(json.dumps(index, indent=1) + "\n", encoding="utf-8")
    write_marker(
        root, entry.id, STAGE, {"cache_key": key, "tool_version": __version__, "created_at": now.isoformat()}
    )
    return "built"
