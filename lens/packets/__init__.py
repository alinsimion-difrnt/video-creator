"""S5 annotation packets (BUILD_PLAN 7.3): evidence bundled per task within image budgets.

    data/packets/<id>/pass1/anchors.json, sheets/*.jpg, keyframes/*.jpg      A1 (one or more parts)
    data/packets/<id>/events/<eid>/ filmstrip end_marked end_clean spectrogram .jpg,
                                    facts.json, candidates.json              A2 (one per kept event)
    packets/<id>/manifest.json      committed: tasks, budgets, triage, input hashes

Triage happens here, in code, to save quota: tiny, faint and caption-band events are skipped,
repeated events (a stagger of identical cards) become one task whose result covers its siblings,
and A2 runs only for `annotate.a2_tiers`.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from lens import __version__
from lens.frames.phash import dhash, hamming
from lens.hashing import cache_key, sha256_file
from lens.ingest import read_marker, write_marker
from lens.schemas import LensConfig, SourceEntry
from lens.schemas.common import Annotator, Provenance
from lens.schemas.packets import (
    Anchors,
    CameraFact,
    EventFacts,
    PacketManifest,
    PacketTask,
    SfxFact,
    ShotAnchor,
    Skipped,
    WordAnchor,
)
from lens.schemas.signals import SignalsSummary
from lens.schemas.video import Palette, VideoMeta

STAGE = "s5_packets"
EVENT_IMAGES = ("filmstrip.jpg", "end_marked.jpg", "end_clean.jpg", "spectrogram.jpg")


class PacketError(RuntimeError):
    pass


@dataclass
class EventInfo:
    id: str
    shot: str
    start_f: int
    end_f: int
    energy: float
    bbox: tuple[float, float, float, float] | None  # 0..1
    hash: str | None = None  # dHash of the end-frame crop
    siblings: list[str] = field(default_factory=list)
    burst: tuple[int, int] | None = None  # S4 burst (inclusive): the frames the annotator sees

    @property
    def frames(self) -> int:
        return self.end_f - self.start_f + 1


def _close(a: float, b: float, ratio: float) -> bool:
    return abs(a - b) <= ratio * max(a, b, 1e-9)


def triage(events: list[EventInfo], cfg: LensConfig, tier: str) -> tuple[list[EventInfo], list[Skipped]]:
    """Events that get an A2 task (with their siblings), and the rest with a reason."""
    p = cfg.packets
    band_top = 1 - cfg.signals.captions.band_fraction
    kept: list[EventInfo] = []
    skipped: list[Skipped] = []
    for e in events:
        if tier not in cfg.annotate.a2_tiers:
            skipped.append(Skipped(event=e.id, reason="tier"))
            continue
        if e.energy < p.min_event_energy:
            skipped.append(Skipped(event=e.id, reason="low_energy"))
            continue
        if e.bbox is not None:
            x0, y0, x1, y1 = e.bbox
            if (x1 - x0) * (y1 - y0) < p.min_event_area:
                skipped.append(Skipped(event=e.id, reason="small"))
                continue
            if p.skip_caption_band and y0 >= band_top:
                skipped.append(Skipped(event=e.id, reason="caption_band"))
                continue
        leader = next((k for k in kept if _duplicate(k, e, cfg)), None)
        if leader is not None:
            leader.siblings.append(e.id)
            skipped.append(Skipped(event=e.id, reason="duplicate", of=leader.id))
            continue
        covering = next((k for k in kept if _overlap(k, e) >= p.overlap_merge_min), None)
        if covering is not None:
            skipped.append(Skipped(event=e.id, reason="overlap", of=covering.id))
            continue
        kept.append(e)
    return kept, skipped


def _overlap(a: EventInfo, b: EventInfo) -> float:
    """Shared burst frames as a share of the shorter burst (same shot only): one build seen twice."""
    if a.shot != b.shot or a.burst is None or b.burst is None:
        return 0.0
    shared = min(a.burst[1], b.burst[1]) - max(a.burst[0], b.burst[0]) + 1
    shorter = min(a.burst[1] - a.burst[0], b.burst[1] - b.burst[0]) + 1
    return max(shared, 0) / shorter


def _duplicate(a: EventInfo, b: EventInfo, cfg: LensConfig) -> bool:
    """Same shot, same-sized box, similar duration and a near-identical settled look."""
    p = cfg.packets
    if a.shot != b.shot or a.hash is None or b.hash is None or a.bbox is None or b.bbox is None:
        return False
    wa, ha = a.bbox[2] - a.bbox[0], a.bbox[3] - a.bbox[1]
    wb, hb = b.bbox[2] - b.bbox[0], b.bbox[3] - b.bbox[1]
    return (
        hamming(a.hash, b.hash) <= p.dedupe_max_distance
        and _close(a.frames, b.frames, p.dedupe_duration_ratio)
        and _close(wa, wb, p.dedupe_duration_ratio)
        and _close(ha, hb, p.dedupe_duration_ratio)
    )


def pack_pass1(shot_images: list[tuple[str, list[str]]], limit: int) -> list[tuple[list[str], list[str]]]:
    """Group shots in order into tasks of at most `limit` images; a shot too big for one task
    is split across consecutive tasks. Returns (shot ids, images) per task."""
    tasks: list[tuple[list[str], list[str]]] = []
    shots: list[str] = []
    images: list[str] = []
    for sid, imgs in shot_images:
        if images and len(images) + len(imgs) > limit:
            tasks.append((shots, images))
            shots, images = [], []
        for k in range(0, max(len(imgs), 1), limit):
            chunk = imgs[k : k + limit]
            if images and len(images) + len(chunk) > limit:
                tasks.append((shots, images))
                shots, images = [], []
            shots.append(sid) if sid not in shots else None
            images.extend(chunk)
    if images:
        tasks.append((shots, images))
    return tasks


def _hash_files(base: Path, rel: list[str]) -> str:
    return cache_key({r: sha256_file(base / r) for r in rel})


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def _crop_hash(img_path: Path, bbox: tuple[float, float, float, float] | None) -> str | None:
    if bbox is None or not img_path.exists():
        return None
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    x0, y0, x1, y1 = (round(bbox[0] * w), round(bbox[1] * h), round(bbox[2] * w), round(bbox[3] * h))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return None
    return dhash(np.asarray(img.crop((x0, y0, x1, y1))))


def build_packets(entry: SourceEntry, root: Path, cfg: LensConfig, force: bool = False) -> str:
    vdir = root / "videos" / entry.id
    ev_dir = root / "data" / "evidence" / entry.id
    index_path = ev_dir / "evidence.json"
    if not index_path.exists():
        return "skipped"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    key = cache_key(
        {
            "stage": STAGE,
            "tool": __version__,
            "evidence": index["provenance"]["input_hash"],
            "packets": cfg.packets.model_dump(),
            "annotate": cfg.annotate.model_dump(),
            "captions": cfg.signals.captions.band_fraction,
            "tier": entry.tier.value,
        }
    )
    manifest_path = root / "packets" / entry.id / "manifest.json"
    marker = read_marker(root, entry.id, STAGE)
    if not force and marker and marker.get("cache_key") == key and manifest_path.exists():
        return "cached"
    if manifest_path.exists():
        old = PacketManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        done = [t.output for t in old.tasks if (root / t.output).exists()]
        if done:
            raise PacketError(
                f"{entry.id} already has {len(done)} annotation file(s) (e.g. {done[0]}); rebuilding its "
                "packets would change task ids and hashes and orphan them"
            )

    meta = VideoMeta.model_validate_json((vdir / "meta.json").read_text(encoding="utf-8"))
    summary = SignalsSummary.model_validate_json((vdir / "signals.summary.json").read_text(encoding="utf-8"))
    palette_path = vdir / "palette.json"
    palette = (
        Palette.model_validate_json(palette_path.read_text(encoding="utf-8"))
        if palette_path.exists()
        else None
    )
    sig_dir = root / "data" / "signals" / entry.id
    detail = json.loads((sig_dir / "signals.json").read_text(encoding="utf-8"))
    curves = np.load(sig_dir / "curves.npz")
    fps = meta.proxy.fps
    now = datetime.now(UTC)
    prov = Provenance(
        tool_version=__version__, stage=STAGE, annotator=Annotator.CODE, input_hash=key, created_at=now
    )

    out = root / "data" / "packets" / entry.id
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    words = [
        WordAnchor(i=w["i"], text=w["text"], start_s=w["start_s"], end_s=w["end_s"])
        for w in detail.get("words", [])
    ]
    sfx_out = summary.audio.sfx if summary.audio else []
    events_by_shot: dict[str, int] = {}
    for e in summary.video.events:
        events_by_shot[e.shot] = events_by_shot.get(e.shot, 0) + 1

    # Pass 1
    anchors = Anchors(
        provenance=prov,
        video=entry.id,
        duration_s=meta.proxy.duration_s,
        fps=fps,
        shots=[
            ShotAnchor(
                id=s.id,
                start_s=s.start_s,
                end_s=s.end_s,
                transition_in=s.transition_in.kind if s.transition_in else None,
                events=events_by_shot.get(s.id, 0),
            )
            for s in summary.video.shots
        ],
        words=words,
        bpm=summary.audio.bpm if summary.audio else None,
        beats_s=list(detail.get("beats", {}).get("times", [])),
        integrated_lufs=summary.audio.loudness.integrated_lufs if summary.audio else None,
        palette=[s.hex for s in palette.video_palette] if palette else [],
        sfx=[
            SfxFact(id=s.id, sync_s=s.sync_s, label=s.label, clap_label=s.clap_label, clap_score=s.clap_score)
            for s in sfx_out
        ],
    )
    (out / "pass1").mkdir()
    (out / "pass1" / "anchors.json").write_text(anchors.model_dump_json(indent=2) + "\n", encoding="utf-8")
    shot_images: list[tuple[str, list[str]]] = []
    for sid, shot in index["shots"].items():
        imgs = []
        for name in shot["sheets"]:
            _copy(ev_dir / "sheets" / name, out / "pass1" / "sheets" / name)
            imgs.append(f"pass1/sheets/{name}")
        if shot.get("keyframe"):
            _copy(ev_dir / "keyframes" / shot["keyframe"], out / "pass1" / "keyframes" / shot["keyframe"])
            imgs.append(f"pass1/keyframes/{shot['keyframe']}")
        shot_images.append((sid, imgs))
    parts = pack_pass1(shot_images, cfg.annotate.max_images_per_task)
    tasks: list[PacketTask] = []
    for n, (shots, imgs) in enumerate(parts, start=1):
        output = f"videos/{entry.id}/a1.json" if len(parts) == 1 else f"videos/{entry.id}/a1.p{n}.json"
        files = ["pass1/anchors.json"]
        tasks.append(
            PacketTask(
                id=f"a1-p{n}",
                kind="a1",
                images=imgs,
                files=files,
                shots=shots,
                output=output,
                input_hash=_hash_files(out, imgs + files),
            )
        )

    # Pass 2 (events)
    s3_events = {e["id"]: e for e in detail.get("events", [])}
    infos = []
    fw, fh = index["size"]
    for eid in index["events"]:
        e = s3_events[eid]
        x0, y0, x1, y1 = index["events"][eid]["bbox"]  # S4's box (clipped above captions), px
        bbox = (x0 / fw, y0 / fh, x1 / fw, y1 / fh) if e["bbox"] is not None else None
        digest = _crop_hash(ev_dir / "events" / eid / "end_clean.jpg", bbox)
        b0, b1 = index["events"][eid]["burst"]
        infos.append(
            EventInfo(eid, e["shot"], e["start_f"], e["end_f"], e["energy"], bbox, digest, burst=(b0, b1))
        )
    kept, skipped = triage(infos, cfg, entry.tier.value)
    win, wwin = cfg.evidence.spectrogram_window_s, cfg.packets.words_window_s
    for info in kept:
        ix = index["events"][info.id]
        src, dst = ev_dir / "events" / info.id, out / "events" / info.id
        imgs = []
        for name in EVENT_IMAGES:
            if (src / name).exists():
                _copy(src / name, dst / name)
                imgs.append(f"events/{info.id}/{name}")
        _copy(src / "candidates.json", dst / "candidates.json")
        start_s, end_s = info.start_f / fps, (info.end_f + 1) / fps
        b0, b1 = ix["burst"]
        facts = EventFacts(
            provenance=prov,
            video=entry.id,
            event=info.id,
            shot=info.shot,
            start_s=round(start_s, 4),
            end_s=round(end_s, 4),
            burst_frames=(b0, b1),
            filmstrip_frames=ix["filmstrip_frames"],
            energy=ix["energy"],
            camera=CameraFact(
                move=s3_events[info.id]["camera_move"],
                pan_x=round(float(curves["tx"][b0 + 1 : b1 + 1].sum()), 4),
                pan_y=round(float(curves["ty"][b0 + 1 : b1 + 1].sum()), 4),
                scale=round(float(np.prod(curves["scale"][b0 + 1 : b1 + 1])), 4),
            ),
            sfx=[
                SfxFact(
                    id=s.id,
                    sync_s=s.sync_s,
                    label=s.label,
                    clap_label=s.clap_label,
                    clap_score=s.clap_score,
                    offset_ms=round((s.sync_s - start_s) * 1000, 1),
                )
                for s in sfx_out
                if start_s - win <= s.sync_s <= end_s + win
            ],
            words=[w for w in words if w.end_s >= start_s - wwin and w.start_s <= end_s + wwin],
            siblings=info.siblings,
        )
        (dst / "facts.json").write_text(facts.model_dump_json(indent=2) + "\n", encoding="utf-8")
        files = [f"events/{info.id}/facts.json", f"events/{info.id}/candidates.json"]
        tasks.append(
            PacketTask(
                id=f"a2-{info.id}",
                kind="a2",
                images=imgs,
                files=files,
                event=info.id,
                siblings=info.siblings,
                output=f"videos/{entry.id}/events/{info.id}.a2.json",
                input_hash=_hash_files(out, imgs + files),
            )
        )

    manifest = PacketManifest(
        provenance=prov,
        video=entry.id,
        tier=entry.tier.value,
        max_images_per_task=cfg.annotate.max_images_per_task,
        event_images=cfg.annotate.event_images,
        tasks=tasks,
        skipped=skipped,
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    write_marker(
        root, entry.id, STAGE, {"cache_key": key, "tool_version": __version__, "created_at": now.isoformat()}
    )
    return "built"


def _valid_output(root: Path, rel: str) -> bool:
    from lens.validate import validate_file

    return (root / rel).exists() and validate_file(root / rel, root).ok


def status(root: Path) -> list[dict[str, Any]]:
    """Per video with a manifest: tasks done (output on disk and valid) and pending, and pending images."""
    rows = []
    for path in sorted((root / "packets").glob("*/manifest.json")):
        m = PacketManifest.model_validate_json(path.read_text(encoding="utf-8"))
        pending = [t for t in m.tasks if not _valid_output(root, t.output)]
        rows.append(
            {
                "video": m.video,
                "tasks": len(m.tasks),
                "done": len(m.tasks) - len(pending),
                "pending": [t.id for t in pending],
                "pending_images": sum(len(t.images) for t in pending),
                "skipped": len(m.skipped),
            }
        )
    return rows


SKILL_FOR = {"a1": ("annotate-video", "a1_annotate_video"), "a2": ("annotate-event", "a2_annotate_event")}


def skill_id(root: Path, skill: str) -> str:
    """`<skill>@<hash>`: the SKILL.md an annotation was made with (provenance.skill)."""
    return f"{skill}@{sha256_file(root / '.claude' / 'skills' / skill / 'SKILL.md')[:12]}"


def rerun_output(run_id: str, output: str) -> str:
    """Where a re-annotation for `lens eval` (a second, blind answer) goes: runs/<run>/<task output>."""
    return f"runs/{run_id}/{output}"


def task_brief(root: Path, video: str, task_id: str, rerun: str | None = None) -> dict[str, Any]:
    """Everything an annotator needs for one task, including the exact provenance to copy: annotators
    never compute hashes or timestamps themselves (they may only run `lens validate` and `lens status`).
    With `rerun`, the output goes to runs/<rerun>/ and the canonical answer is left untouched."""
    path = root / "packets" / video / "manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"no packet manifest for {video}")
    m = PacketManifest.model_validate_json(path.read_text(encoding="utf-8"))
    task = next((t for t in m.tasks if t.id == task_id), None)
    if task is None:
        raise KeyError(f"{task_id} is not a task of {video}")
    skill, stage = SKILL_FOR[task.kind]
    base = f"data/packets/{video}"
    a1 = [t for t in m.tasks if t.kind == "a1"]
    return {
        "video": video,
        "task": task.id,
        "kind": task.kind,
        "skill": skill,
        "output": rerun_output(rerun, task.output) if rerun else task.output,
        "images": [f"{base}/{p}" for p in task.images],
        "files": [f"{base}/{p}" for p in task.files],
        "shots": task.shots,
        "event": task.event,
        "siblings": task.siblings,
        "writes_summary": task.kind == "a1" and a1[-1].id == task.id,
        "earlier_parts": [t.output for t in a1[: a1.index(task)]] if task.kind == "a1" else [],
        "provenance": Provenance(
            tool_version=__version__,
            stage=stage,
            annotator=Annotator.CLAUDE_CODE,
            skill=skill_id(root, skill),
            input_hash=task.input_hash,
            created_at=datetime.now(UTC),
        ).model_dump(mode="json"),
    }
