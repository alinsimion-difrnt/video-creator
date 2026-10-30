"""S8 reconcile: merge a video's code signals, A1/A2 annotations and S7 measurements into
`videos/<id>/record.json`, with a source on every value, and check that the pieces agree (BUILD_PLAN 7.6).

Timing numbers only ever come from code: S3 for shots, events and SFX, S7 for elements. Where S7 is
missing or below `measure.min_fit_quality`, an element falls back to the annotator's estimate and says so
(`model_estimate`). Checks: annotation ids exist in the signals, events lie inside their shots, every SFX
candidate has a final label, measured boxes belong to their event's elements.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from lens import __version__
from lens.hashing import cache_key, sha256_file
from lens.measure.curves import ease_class
from lens.measure.run import element_ids, manual_box_px
from lens.schemas import LensConfig, SourceEntry
from lens.schemas.annotation import A1File, A2File, Element, Shot, VideoSummary
from lens.schemas.common import Annotator, Provenance, ValueSource
from lens.schemas.evidence import CandidatesFile
from lens.schemas.measure import ElementOut, MeasureFile
from lens.schemas.packets import PacketManifest
from lens.schemas.record import (
    Box,
    Check,
    Coverage,
    ElementTiming,
    RecordElement,
    RecordEvent,
    RecordFile,
    RecordSfx,
    RecordShot,
)
from lens.schemas.signals import SignalsSummary
from lens.schemas.video import Palette, VideoMeta

__all__ = [
    "ReconcileError",
    "element_ids",
    "events_in_shots",
    "manual_box_px",
    "reconcile_video",
    "resolve_sfx",
]

STAGE = "s8_reconcile"
PROPAGATED = ("duplicate",)  # repeats of an annotated event take its pattern (ADR 0013: overlaps do not)

Review = tuple[str, str, str]  # (event, verdict, label)


class ReconcileError(RuntimeError):
    pass


def resolve_sfx(classifier: str, reviews: list[Review]) -> tuple[str, str, str | None]:
    """Final (label, label_source, verdict) of one SFX candidate. The earliest confident A2 review
    (confirm/override) decides; unsure reviews, or none, keep the S3 label."""
    confident = sorted(r for r in reviews if r[1] in ("confirm", "override"))
    if confident:
        _, verdict, label = confident[0]
        return label, "claude", verdict
    return classifier, "code", ("unsure" if reviews else None)


def events_in_shots(
    events: list[tuple[str, str, float, float]], shots: dict[str, tuple[float, float]], tolerance_s: float
) -> list[str]:
    """Ids of events that are not inside their shot (or whose shot is unknown)."""
    bad = []
    for eid, sid, start, end in events:
        bounds = shots.get(sid)
        if bounds is None or start < bounds[0] - tolerance_s or end > bounds[1] + tolerance_s:
            bad.append(eid)
    return bad


def _part(path: Path) -> int:
    m = re.search(r"a1\.p(\d+)\.json$", path.name)
    return int(m.group(1)) if m else 0


def _a1_parts(vdir: Path) -> list[A1File]:
    paths = sorted([*vdir.glob("a1.json"), *vdir.glob("a1.p*.json")], key=_part)
    return [A1File.model_validate_json(p.read_text("utf-8")) for p in paths]


def measured_changes(m: ElementOut) -> list[str]:
    """Change types the measured channels show (S7 already dropped channels that barely moved)."""
    out: list[str] = []
    for c in m.channels:
        d = c.end_value - c.start_value
        if c.name == "opacity" and d:
            out.append("fade")
        elif c.name == "x" and d:
            out.append("slide_right" if d > 0 else "slide_left")
        elif c.name == "y" and d:
            out.append("slide_down" if d > 0 else "slide_up")  # image y grows downwards
        elif c.name == "scale" and d:
            out.append("scale_up" if d > 0 else "scale_down")
    return sorted(set(out))


def _timing(el: Element, m: ElementOut | None) -> ElementTiming | None:
    if m is not None and m.source is ValueSource.MEASURED:
        best = max(m.channels, key=lambda c: c.fit_quality, default=None)
        return ElementTiming(
            source=ValueSource.MEASURED,
            duration_ms=m.timing.duration_ms if m.timing else (best.duration_ms if best else None),
            start_s=m.timing.start_s if m.timing else None,
            ease=m.timing.ease if m.timing else (best.gsap.ease if best else None),
            # The joint fit (one ease for every channel) names the class; one channel's fit alone
            # often reads "spring" or "ambiguous" for a plain ease-out.
            easing_class=ease_class(m.timing.ease) if m.timing else (best.cls if best else None),
            bezier=best.bezier if best else None,
            spring=best.spring.remotion if best else None,
            overshoot_pct=best.overshoot_pct if best else None,
            quality=m.quality,
            channels=[c.name for c in m.channels],
            changes=measured_changes(m),
            stagger_unit=m.stagger.unit if m.stagger else None,
            stagger_ms=m.stagger.stagger_ms if m.stagger else None,
        )
    est = el.estimates
    if est is None or (est.duration_ms is None and est.easing_class is None):
        return None
    return ElementTiming(
        source=ValueSource.MODEL_ESTIMATE, duration_ms=est.duration_ms, easing_class=est.easing_class
    )


def _elements(
    a2: A2File, measure: MeasureFile | None, cands: CandidatesFile | None, frame: tuple[int, int]
) -> list[RecordElement]:
    measured = {m.box: m for m in measure.elements} if measure else {}
    cand_px: dict[str, Box] = (
        {b.id: (b.xyxy[0], b.xyxy[1], b.xyxy[2], b.xyxy[3]) for b in cands.boxes} if cands else {}
    )
    out = []
    for el, bid in zip(a2.elements, element_ids(a2), strict=True):
        m = measured.get(bid)
        if m is not None and m.xyxy is not None:
            box: Box | None = m.xyxy
        elif el.manual_box is not None:
            box = manual_box_px(el.manual_box, *frame)
        else:
            box = cand_px.get(bid)
        out.append(
            RecordElement(
                id=bid,
                box=box,
                box_source="candidate" if el.box else "manual",
                label=el.label,
                role=el.role,
                role_other=el.role_other,
                change_types=el.change_types,
                change_other=el.change_other,
                is_text=el.is_text,
                text=el.text,
                text_unit=el.text_unit,
                timing=_timing(el, m),
                sfx_offset_ms=m.sfx_offset_ms if m else {},
            )
        )
    return out


def _inputs(root: Path, video: str) -> list[Path]:
    vdir = root / "videos" / video
    paths = [vdir / "meta.json", vdir / "signals.summary.json", vdir / "palette.json"]
    paths += sorted([*vdir.glob("a1.json"), *vdir.glob("a1.p*.json")])
    paths += sorted((vdir / "events").glob("e*.a2.json")) + sorted((vdir / "measure").glob("e*.json"))
    paths.append(root / "packets" / video / "manifest.json")
    return [p for p in paths if p.exists()]


def _candidates(root: Path, video: str, eid: str) -> CandidatesFile | None:
    """S4's candidates, or the verbatim copy S5 put in the packet (sessions without the evidence)."""
    for base in ("evidence", "packets"):
        path = root / "data" / base / video / "events" / eid / "candidates.json"
        if path.exists():
            return CandidatesFile.model_validate_json(path.read_text("utf-8"))
    return None


def reconcile_video(entry: SourceEntry, root: Path, cfg: LensConfig, force: bool = False) -> str:
    """Write videos/<id>/record.json. Returns "built" or "cached"; raises ReconcileError (after writing)
    when a consistency check fails."""
    vdir = root / "videos" / entry.id
    out_path = vdir / "record.json"
    inputs = _inputs(root, entry.id)
    key = cache_key(
        {
            "stage": STAGE,
            "tool": __version__,
            "inputs": {p.relative_to(root).as_posix(): sha256_file(p) for p in inputs},
            "entry": entry.model_dump(mode="json"),
            "reconcile": cfg.reconcile.model_dump(),
        }
    )
    if not force and out_path.exists():
        try:
            if RecordFile.model_validate_json(out_path.read_text("utf-8")).provenance.input_hash == key:
                return "cached"
        except ValueError:
            pass

    meta = VideoMeta.model_validate_json((vdir / "meta.json").read_text("utf-8"))
    summary = SignalsSummary.model_validate_json((vdir / "signals.summary.json").read_text("utf-8"))
    palette_path = vdir / "palette.json"
    palette = Palette.model_validate_json(palette_path.read_text("utf-8")) if palette_path.exists() else None
    parts = _a1_parts(vdir)
    a1_shots: dict[str, Shot] = {s.shot: s for p in parts for s in p.shots}
    video_summary: VideoSummary | None = next((p.summary for p in reversed(parts) if p.summary), None)
    a2s = {
        a.event: a
        for a in (
            A2File.model_validate_json(p.read_text("utf-8"))
            for p in sorted((vdir / "events").glob("e*.a2.json"))
        )
    }
    measures = {
        m.event: m
        for m in (
            MeasureFile.model_validate_json(p.read_text("utf-8"))
            for p in sorted((vdir / "measure").glob("e*.json"))
        )
    }
    manifest_path = root / "packets" / entry.id / "manifest.json"
    manifest = (
        PacketManifest.model_validate_json(manifest_path.read_text("utf-8"))
        if manifest_path.exists()
        else None
    )
    tasks = {t.event for t in manifest.tasks if t.kind == "a2"} if manifest else set()
    skipped = {s.event: s for s in manifest.skipped} if manifest else {}
    frame = (meta.proxy.width, meta.proxy.height)

    shots = [
        RecordShot(
            id=s.id,
            start_s=s.start_s,
            end_s=s.end_s,
            transition_in=s.transition_in.kind if s.transition_in else None,
            motion_energy=s.motion_energy,
            wpm=s.wpm,
            annotation=a1_shots.get(s.id),
        )
        for s in summary.video.shots
    ]

    events: list[RecordEvent] = []
    for e in summary.video.events:
        base = {
            "id": e.id,
            "shot": e.shot,
            "kind": e.kind,
            "start_s": e.start_s,
            "end_s": e.end_s,
            "camera_move": e.camera_move,
        }
        a2 = a2s.get(e.id)
        skip = skipped.get(e.id)
        if a2 is not None:
            cands = _candidates(root, entry.id, e.id)
            events.append(
                RecordEvent(
                    **base,
                    status="annotated",
                    pattern=a2.pattern,
                    build_hint=a2.build_hint,
                    confidence=a2.confidence,
                    notes=a2.notes,
                    elements=_elements(a2, measures.get(e.id), cands, frame),
                    sfx=[r.id for r in a2.sfx_review],
                )
            )
        elif skip is not None and skip.of and skip.reason in PROPAGATED:
            parent = a2s.get(skip.of)
            events.append(
                RecordEvent(
                    **base,
                    status="propagated",
                    skip_reason=skip.reason,
                    of=skip.of,
                    pattern=parent.pattern if parent else None,
                    confidence=parent.confidence if parent else None,
                )
            )
        elif skip is not None:
            events.append(RecordEvent(**base, status="skipped", skip_reason=skip.reason, of=skip.of))
        elif e.id in tasks:
            events.append(RecordEvent(**base, status="pending"))
        else:
            events.append(
                RecordEvent(**base, status="skipped", skip_reason="no_evidence")
            )  # S4 built no burst for it

    reviews: dict[str, list[Review]] = {}
    for eid in sorted(a2s):
        for r in a2s[eid].sfx_review:
            reviews.setdefault(r.id, []).append((eid, r.verdict, r.label))
    sfx = []
    for s in summary.audio.sfx if summary.audio else []:
        label, source, verdict = resolve_sfx(s.label, reviews.get(s.id, []))
        sfx.append(
            RecordSfx(
                id=s.id,
                sync_s=s.sync_s,
                classifier_label=s.label,
                clap_label=s.clap_label,
                clap_score=s.clap_score,
                label=label,
                label_source="claude" if source == "claude" else "code",
                verdict=verdict,
                events=[r[0] for r in reviews.get(s.id, [])],
                on_beat=s.on_beat,
                reveal_offset_ms=s.reveal_offset_ms,
            )
        )

    checks = _checks(summary, parts, a1_shots, video_summary, a2s, measures, sfx, reviews, cfg)
    elements = [el for ev in events for el in ev.elements]
    record = RecordFile(
        provenance=Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CODE,
            input_hash=key,
            created_at=datetime.now(UTC),
        ),
        video=entry.id,
        brand=entry.brand,
        title=entry.title,
        format=entry.format,
        tier=entry.tier.value,
        duration_s=summary.video.duration_s,
        fps=summary.video.fps,
        frame_size=frame,
        palette=[s.hex for s in palette.video_palette] if palette else [],
        summary=video_summary,
        shots=shots,
        events=events,
        sfx=sfx,
        coverage=Coverage(
            events=len(events),
            annotated=sum(e.status == "annotated" for e in events),
            propagated=sum(e.status == "propagated" for e in events),
            skipped=sum(e.status == "skipped" for e in events),
            pending=sum(e.status == "pending" for e in events),
            elements=len(elements),
            measured=sum(bool(el.timing and el.timing.source is ValueSource.MEASURED) for el in elements),
            estimated=sum(
                bool(el.timing and el.timing.source is ValueSource.MODEL_ESTIMATE) for el in elements
            ),
        ),
        checks=checks,
    )
    out_path.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
    failed = [c for c in checks if not c.ok]
    if failed:
        raise ReconcileError("; ".join(f"{c.name}: {c.detail}" for c in failed))
    return "built"


def _checks(
    summary: SignalsSummary,
    parts: list[A1File],
    a1_shots: dict[str, Shot],
    video_summary: VideoSummary | None,
    a2s: dict[str, A2File],
    measures: dict[str, MeasureFile],
    sfx: list[RecordSfx],
    reviews: dict[str, list[Review]],
    cfg: LensConfig,
) -> list[Check]:
    def check(name: str, problems: list[str]) -> Check:
        return Check(name=name, ok=not problems, detail=", ".join(problems[:20]) or None)

    shot_ids = {s.id for s in summary.video.shots}
    event_ids = {e.id for e in summary.video.events}
    sfx_ids = {s.id for s in sfx}
    out = []
    if parts:
        missing = sorted(shot_ids - set(a1_shots))
        extra = sorted(set(a1_shots) - shot_ids)
        out.append(check("a1_shots", [f"missing {s}" for s in missing] + [f"unknown {s}" for s in extra]))
        out.append(check("a1_summary", [] if video_summary else ["no part wrote the summary"]))
    out.append(check("a2_events", sorted(set(a2s) - event_ids)))
    shots = {s.id: (s.start_s, s.end_s) for s in summary.video.shots}
    tolerance = cfg.reconcile.shot_tolerance_frames / summary.video.fps
    spans = [(e.id, e.shot, e.start_s, e.end_s) for e in summary.video.events]
    out.append(check("events_in_shots", events_in_shots(spans, shots, tolerance)))
    out.append(check("sfx_ids", sorted(set(reviews) - sfx_ids)))
    out.append(check("sfx_labels", [s.id for s in sfx if not s.label]))
    stray = []
    for eid, a2 in a2s.items():
        m = measures.get(eid)
        if m is not None:
            ids = set(element_ids(a2))
            stray += [f"{eid}/{b}" for b in [el.box for el in m.elements] + list(m.failed) if b not in ids]
    out.append(check("measure_boxes", stray))
    return out
