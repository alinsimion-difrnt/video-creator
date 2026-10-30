"""S7 runner: measure the chosen candidate boxes of one event and write videos/<id>/measure/<eid>.json.

Boxes come from A2 (`videos/<id>/events/<eid>.a2.json`, M5) or, until then, from `lens measure --box`.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from lens import __version__
from lens.hashing import cache_key
from lens.measure import ElementMeasure, measure_element, sfx_offset_ms, text_stagger
from lens.media import iter_frames_rgb
from lens.schemas import LensConfig, SourceEntry
from lens.schemas.annotation import A2File
from lens.schemas.common import Annotator, Provenance, ValueSource
from lens.schemas.evidence import CandidatesFile
from lens.schemas.measure import (
    ChannelOut,
    ElementOut,
    GsapOut,
    MeasureFile,
    SpringOut,
    StaggerOut,
    TimingOut,
)
from lens.schemas.signals import SignalsSummary
from lens.schemas.video import VideoMeta

STAGE = "s7_measure"


class MeasureError(RuntimeError):
    pass


def word_boxes(box: tuple[int, int, int, int], text: str) -> list[tuple[int, int, int, int]]:
    """Split an OCR line box into word boxes in proportion to character counts (OCR gives lines)."""
    words = text.split()
    if len(words) < 2:
        return []
    x0, y0, x1, y1 = box
    total = sum(len(w) for w in words) + (len(words) - 1)
    out, pos = [], 0
    for w in words:
        a = x0 + (x1 - x0) * pos / total
        b = x0 + (x1 - x0) * (pos + len(w)) / total
        out.append((int(a), y0, max(int(a) + 1, round(b)), y1))
        pos += len(w) + 1
    return out


def _element(
    em: ElementMeasure, box_id: str, fps: float, summary: SignalsSummary, cfg: LensConfig
) -> ElementOut:
    chans = []
    for c in em.channels:
        f, ch = c.fit, c.channel
        sp = f.spring.spring
        chans.append(
            ChannelOut(
                name=ch.name,
                start_f=ch.start_f,
                end_f=ch.end_f,
                start_value=round(ch.start_value, 3),
                end_value=round(ch.end_value, 3),
                observed_start=ch.observed_start,
                cls=f.cls,
                gsap=GsapOut(
                    ease=f.gsap.name,
                    duration_ms=round(f.gsap.duration_s * 1000, 1),
                    rmse=round(f.gsap.rmse, 5),
                ),
                bezier=f.bezier.css,
                bezier_rmse=round(f.bezier.rmse, 5),
                spring=SpringOut(
                    zeta=round(sp.zeta, 4),
                    omega0=round(sp.omega0, 3),
                    settle_ms=round(sp.settle_s(cfg.measure.progress_end_tolerance) * 1000, 1),
                    remotion=sp.remotion(),
                    remotion_exact=sp.remotion_exact,
                    rmse=round(f.spring.rmse, 5),
                ),
                overshoot_pct=f.overshoot_pct,
                duration_ms=f.duration_ms,
                fit_quality=f.fit_quality,
            )
        )
    timing = None
    if em.timing is not None:
        timing = TimingOut(
            ease=em.timing.name,
            start_s=round(em.timing.t0, 4),
            duration_ms=round(em.timing.duration_s * 1000, 1),
            rmse=round(em.timing.rmse, 5),
        )
    quality = max((c.fit.fit_quality for c in em.channels), default=0.0)
    offsets: dict[str, float] = {}
    primary = em.primary
    if primary is not None and summary.audio is not None:
        landing = primary.channel.end_f
        for s in summary.audio.sfx:
            off = sfx_offset_ms(s.sync_s, landing, fps)
            if abs(off) <= cfg.signals.sfx_reveal_window_s * 1000:
                offsets[s.id] = off
    good = em.track.confidence[em.track.confidence >= 0]
    return ElementOut(
        box=box_id,
        method="ncc",
        mean_confidence=round(float(good.mean()) if good.size else 0.0, 3),
        channels=chans,
        timing=timing,
        sfx_offset_ms=offsets,
        source=ValueSource.MEASURED if quality >= cfg.measure.min_fit_quality else ValueSource.MODEL_ESTIMATE,
        quality=round(quality, 4),
    )


Boxes = list[tuple[str, tuple[int, int, int, int], str | None]]  # (id, xyxy, OCR text or None)


def element_ids(a2: A2File) -> list[str]:
    """Ids of A2 elements as S7/S8 key them: the candidate box id, or m<1-based element index>."""
    return [e.box if e.box else f"m{i:02d}" for i, e in enumerate(a2.elements, start=1)]


def manual_box_px(box: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    """An A2 manual box ([ymin, xmin, ymax, xmax] per mille of the full end frame) in proxy pixels."""
    y0, x0, y1, x1 = box
    return (
        round(x0 * width / 1000),
        round(y0 * height / 1000),
        round(x1 * width / 1000),
        round(y1 * height / 1000),
    )


def _measure_boxes(
    frames: list[np.ndarray],
    b0: int,
    fps: float,
    crop: tuple[int, int, int, int],
    frame_size: tuple[int, int],
    boxes: Boxes,
    summary: SignalsSummary,
    cfg: LensConfig,
) -> tuple[list[ElementOut], dict[str, str]]:
    w, h = frame_size
    m = cfg.measure.track_margin_px
    elements, failed = [], {}
    for bid, box, text in boxes:
        x0 = min(crop[0], box[0])
        y0 = min(crop[1], box[1])
        x1 = max(crop[2], box[2])
        y1 = max(crop[3], box[3])
        search = (max(0, x0 - m), max(0, y0 - m), min(w, x1 + m), min(h, y1 + m))
        if box[2] - box[0] < 2 or box[3] - box[1] < 2:
            failed[bid] = "box smaller than 2 px"
            continue
        try:
            em = measure_element(frames, b0, fps, box, search, cfg.measure)
        except (ValueError, IndexError, ZeroDivisionError) as exc:
            failed[bid] = f"{type(exc).__name__}: {exc}"
            continue
        el = _element(em, bid, fps, summary, cfg).model_copy(update={"xyxy": box})
        if text:
            wb = word_boxes(box, text)
            if wb:
                st = text_stagger(frames, b0, fps, wb, cfg.measure)
                el = el.model_copy(
                    update={
                        "stagger": StaggerOut(
                            unit=st.unit, stagger_ms=st.stagger_ms, reveal_frames=st.reveal_frames
                        )
                    }
                )
        elements.append(el)
    return elements, failed


def _write(
    root: Path,
    video: str,
    event: str,
    fps: float,
    key: str,
    elements: list[ElementOut],
    failed: dict[str, str],
) -> Path:
    out = MeasureFile(
        provenance=Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CODE,
            input_hash=key,
            created_at=datetime.now(UTC),
        ),
        video=video,
        event=event,
        fps=fps,
        elements=elements,
        failed=failed,
    )
    path = root / "videos" / video / "measure" / f"{event}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(out.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return path


def _inputs(root: Path, video: str) -> tuple[VideoMeta, SignalsSummary, dict[str, Any]]:
    vdir = root / "videos" / video
    ev_dir = root / "data" / "evidence" / video
    meta = VideoMeta.model_validate_json((vdir / "meta.json").read_text(encoding="utf-8"))
    summary = SignalsSummary.model_validate_json((vdir / "signals.summary.json").read_text(encoding="utf-8"))
    index_path = ev_dir / "evidence.json"
    if not index_path.exists():
        raise MeasureError(f"{video}: no S4 evidence on disk (`lens storage pull-media --kind evidence`)")
    index: dict[str, Any] = json.loads(index_path.read_text(encoding="utf-8"))
    return meta, summary, index


def _candidates(root: Path, video: str, event: str) -> CandidatesFile:
    path = root / "data" / "evidence" / video / "events" / event / "candidates.json"
    return CandidatesFile.model_validate_json(path.read_text("utf-8"))


def _key(cands: CandidatesFile, boxes: Boxes, cfg: LensConfig) -> str:
    return cache_key(
        {
            "stage": STAGE,
            "tool": __version__,
            "candidates": cands.provenance.input_hash,
            "boxes": [[b, list(xy), t] for b, xy, t in boxes],
            "measure": cfg.measure.model_dump(),
        }
    )


def measure_event(entry: SourceEntry, root: Path, cfg: LensConfig, event: str, box_ids: list[str]) -> Path:
    """Measure hand-picked candidate boxes of one event (`lens measure --event --box`)."""
    meta, summary, index = _inputs(root, entry.id)
    if event not in index["events"]:
        raise MeasureError(f"{entry.id}: no evidence for {event}; run `lens evidence`")
    cands = _candidates(root, entry.id, event)
    by_id = {b.id: b for b in cands.boxes}
    unknown = [b for b in box_ids if b not in by_id]
    if unknown:
        raise MeasureError(f"{event}: unknown box id(s) {', '.join(unknown)} (see candidates.json)")
    boxes: Boxes = [
        (
            bid,
            (by_id[bid].xyxy[0], by_id[bid].xyxy[1], by_id[bid].xyxy[2], by_id[bid].xyxy[3]),
            by_id[bid].text if by_id[bid].source == "ocr" else None,
        )
        for bid in box_ids
    ]
    b0, b1 = index["events"][event]["burst"]
    fps, w, h = meta.proxy.fps, meta.proxy.width, meta.proxy.height
    frames = []
    for f, frame in iter_frames_rgb(root / "data" / "media" / entry.id / "proxy.mp4", fps, w, h):
        if f >= b0:
            frames.append(frame.copy())
        if f >= b1:
            break
    if len(frames) != b1 - b0 + 1:
        raise MeasureError(f"{event}: decoded {len(frames)} of {b1 - b0 + 1} burst frames")
    crop = tuple(index["events"][event]["crop"])
    elements, failed = _measure_boxes(frames, b0, fps, crop, (w, h), boxes, summary, cfg)
    return _write(root, entry.id, event, fps, _key(cands, boxes, cfg), elements, failed)


def measure_video(entry: SourceEntry, root: Path, cfg: LensConfig, force: bool = False) -> list[Path]:
    """S7 for every A2-annotated event of a video, decoding the proxy once. Returns the files written
    (events whose inputs are unchanged are skipped)."""
    vdir = root / "videos" / entry.id
    a2_paths = sorted((vdir / "events").glob("e*.a2.json"))
    if not a2_paths:
        return []
    meta, summary, index = _inputs(root, entry.id)
    fps, w, h = meta.proxy.fps, meta.proxy.width, meta.proxy.height
    plans: list[tuple[str, int, int, tuple[int, int, int, int], Boxes, dict[str, str], str]] = []
    for path in a2_paths:
        a2 = A2File.model_validate_json(path.read_text(encoding="utf-8"))
        eid = a2.event
        if eid not in index["events"]:
            raise MeasureError(f"{entry.id}: A2 for {eid} but no evidence for it")
        cands = _candidates(root, entry.id, eid)
        by_id = {b.id: b for b in cands.boxes}
        boxes: Boxes = []
        failed: dict[str, str] = {}
        for el, bid in zip(a2.elements, element_ids(a2), strict=True):
            if el.box is not None:
                b = by_id.get(el.box)
                if b is None:
                    failed[bid] = "not in candidates.json"
                    continue
                boxes.append(
                    (bid, (b.xyxy[0], b.xyxy[1], b.xyxy[2], b.xyxy[3]), b.text if b.source == "ocr" else None)
                )
            elif el.manual_box is not None:
                boxes.append((bid, manual_box_px(el.manual_box, w, h), None))
        key = _key(cands, boxes, cfg)
        out = vdir / "measure" / f"{eid}.json"
        if not force and out.exists():
            try:
                if MeasureFile.model_validate_json(out.read_text("utf-8")).provenance.input_hash == key:
                    continue
            except ValueError:
                pass
        b0, b1 = index["events"][eid]["burst"]
        crop = tuple(index["events"][eid]["crop"])
        plans.append((eid, b0, b1, crop, boxes, failed, key))
    if not plans:
        return []
    written: list[Path] = []
    held: dict[str, list[np.ndarray]] = {p[0]: [] for p in plans}
    todo = {p[0]: p for p in plans}
    last = max(p[2] for p in plans)
    for f, frame in iter_frames_rgb(root / "data" / "media" / entry.id / "proxy.mp4", fps, w, h):
        active = [p for p in todo.values() if p[1] <= f <= p[2]]
        if active:
            copy = frame.copy()
            for p in active:
                held[p[0]].append(copy)
        for p in [p for p in active if p[2] == f]:
            eid, b0, b1, crop, boxes, failed, key = p
            frames = held.pop(eid)
            del todo[eid]
            if len(frames) != b1 - b0 + 1:
                raise MeasureError(f"{eid}: decoded {len(frames)} of {b1 - b0 + 1} burst frames")
            elements, more = _measure_boxes(frames, b0, fps, crop, (w, h), boxes, summary, cfg)
            written.append(_write(root, entry.id, eid, fps, key, elements, {**failed, **more}))
        if f >= last:
            break
    if todo:
        raise MeasureError(f"{entry.id}: proxy ended before the bursts of {', '.join(sorted(todo))}")
    return sorted(written)
