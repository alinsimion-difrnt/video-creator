"""Run the presenter-footage stages for one project (F1-F4, C5 presenter mode, F6). Paths: lens/stages.py."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from create.footage.cuts import apply_cuts, apply_notes, cold_open, propose_cuts, remap_words, split_long
from create.footage.media import conform, finish_voice, render_edit
from create.footage.timeline import build_presenter_timeline
from create.footage.transcribe import keyterms_for, transcribe_take
from lens import __version__
from lens.hashing import cache_key
from lens.schemas.common import Annotator, Provenance
from lens.schemas.config import LensConfig
from lens.schemas.create import (
    Brief,
    CutApprovals,
    CutNotes,
    Cuts,
    Edl,
    EdlSegment,
    Footage,
    FootageTake,
    Framing,
    Timeline,
    Transcript,
    TranscriptWord,
)

VIDEO_EXT = {".mov", ".mp4", ".m4v", ".mkv", ".webm", ".avi", ".mts"}


def _prov(stage: str, inputs: dict[str, Any]) -> Provenance:
    return Provenance(
        tool_version=__version__, stage=stage, annotator=Annotator.CODE, input_hash=cache_key(inputs),
        created_at=datetime.now(UTC),
    )  # fmt: skip


def _base(root: Path, project: str) -> tuple[Path, Path]:
    return root / "projects" / project, root / "data" / "create" / project / "footage"


def _brief(root: Path, project: str) -> Brief:
    return Brief.model_validate(yaml.safe_load((root / "projects" / project / "brief.yaml").read_text()))


def _rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def take_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", Path(name).stem.lower()).strip("-")
    return slug or "take"


def run_ingest(root: Path, project: str, cfg: LensConfig) -> tuple[Path, Footage]:
    """F1: every video in data/create/<p>/footage/raw/ (name order = take order) -> masters + footage.json."""
    base, data = _base(root, project)
    raws = sorted(p for p in (data / "raw").glob("*") if p.suffix.lower() in VIDEO_EXT)
    if not raws:
        raise FileNotFoundError(f"no videos in {(data / 'raw').relative_to(root)}")
    fc = cfg.create.footage
    takes = []
    for raw in raws:
        tid = take_id(raw.name)
        master, audio = data / "master" / f"{tid}.mov", data / "master" / f"{tid}.wav"
        info = conform(raw, master, audio, fc)
        takes.append(
            FootageTake(
                id=tid, raw=_rel(root, raw), master=_rel(root, master), audio=_rel(root, audio), **info
            )
        )
    if len({t.id for t in takes}) != len(takes):
        raise ValueError("two raw files give the same take id; rename one")
    footage = Footage(
        provenance=_prov("f1_ingest", {"raw": [(t.raw, t.frames) for t in takes], "cfg": fc.model_dump()}),
        project=project, fps=fc.fps, takes=takes,
    )  # fmt: skip
    path = base / "footage.json"
    path.write_text(footage.model_dump_json(indent=1) + "\n")
    return path, footage


def run_transcript(
    root: Path, project: str, cfg: LensConfig, keyterms: list[str] | None = None, language: str | None = None
) -> tuple[Path, Transcript]:
    """F2: words of every take, verbatim, on the masters' clocks. `language` overrides the brief's ("": let
    the engine detect it)."""
    base, data = _base(root, project)
    footage = Footage.model_validate(json.loads((base / "footage.json").read_text()))
    brief = _brief(root, project)
    fc = cfg.create.footage
    terms = keyterms_for(brief.product.name, brief.product.spoken, keyterms or [])
    words: list[TranscriptWord] = []
    asked = brief.language if language is None else language
    language = asked or brief.language
    for t in footage.takes:
        ws, language = transcribe_take(root / t.audio, t.id, data / "stt", fc, asked, terms, len(words))
        words += ws
    model = fc.stt_model if fc.stt_engine == "elevenlabs" else fc.whisper_model
    transcript = Transcript(
        provenance=_prov(
            "f2_transcript",
            {"takes": [t.model_dump() for t in footage.takes], "engine": fc.stt_engine, "model": model,
             "terms": terms},
        ),
        project=project, engine=fc.stt_engine, model=model, language=language[:2], words=words,
    )  # fmt: skip
    path = base / "transcript.json"
    path.write_text(transcript.model_dump_json(indent=1) + "\n")
    return path, transcript


def run_cuts(root: Path, project: str, cfg: LensConfig) -> tuple[Path, Cuts]:
    """F3: proposed cuts (silences, fillers, false starts, cue-word retakes) for Robert to approve."""
    base, _ = _base(root, project)
    footage = Footage.model_validate(json.loads((base / "footage.json").read_text()))
    transcript = Transcript.model_validate(json.loads((base / "transcript.json").read_text()))
    fc = cfg.create.footage
    proposals = propose_cuts(
        list(transcript.words),
        fc,
        _brief(root, project).language,
        {t.id: t.duration_s for t in footage.takes},
    )
    notes_path = base / "cut-notes.yaml"  # Robert's own instructions (optional): start, end, keep, cut
    notes = None
    if notes_path.exists():
        notes = CutNotes.model_validate(yaml.safe_load(notes_path.read_text()))
        durations = {t.id: t.duration_s for t in footage.takes}
        proposals = apply_notes(proposals, notes, list(transcript.words), durations[notes.take])
    cuts = Cuts(
        provenance=_prov(
            "f3_cuts",
            {
                "words": [w.model_dump() for w in transcript.words],
                "cuts": fc.cuts.model_dump(),
                "notes": notes.model_dump() if notes else None,
            },
        ),
        project=project, proposals=proposals,
    )  # fmt: skip
    path = base / "cuts.json"
    path.write_text(cuts.model_dump_json(indent=1) + "\n")
    return path, cuts


def write_approvals(root: Path, project: str, approve: list[str] | str, reject: list[str]) -> Path:
    """Robert's decisions (the human gate between F3 and F4)."""
    approvals = CutApprovals.model_validate(
        {"approve": approve if approve == "all" else list(approve), "reject": reject}
    )
    path = root / "projects" / project / "cuts-approved.yaml"
    head = (
        "# Robert's cut decisions (human gate, ADR 0025). approve: all | [ids]; reject wins over approve.\n"
    )
    path.write_text(head + yaml.safe_dump(approvals.model_dump(), sort_keys=False, allow_unicode=True))
    return path


def approved_ids(cuts: Cuts, approvals: CutApprovals) -> list[str]:
    ids = [c.id for c in cuts.proposals] if approvals.approve == "all" else list(approvals.approve)
    unknown = sorted(set(ids) - {c.id for c in cuts.proposals})
    if unknown:
        raise ValueError(f"cuts-approved.yaml names unknown cuts: {', '.join(unknown)}")
    return [i for i in ids if i not in set(approvals.reject)]


def run_edl(root: Path, project: str, cfg: LensConfig) -> tuple[Path, Edl]:
    """F4: the approved cuts applied, as frame-exact segments."""
    base, _ = _base(root, project)
    footage = Footage.model_validate(json.loads((base / "footage.json").read_text()))
    cuts = Cuts.model_validate(json.loads((base / "cuts.json").read_text()))
    approvals_path = base / "cuts-approved.yaml"
    if not approvals_path.exists():
        raise FileNotFoundError(
            f"no {approvals_path.relative_to(root)} yet: review cuts.json, "
            f"then `create cuts {project} --approve ...`"
        )
    approvals = CutApprovals.model_validate(yaml.safe_load(approvals_path.read_text()) or {})
    ids = approved_ids(cuts, approvals)
    chosen = [c for c in cuts.proposals if c.id in set(ids)]
    segments = apply_cuts(chosen, {t.id: t.frames for t in footage.takes}, footage.fps)
    transcript = Transcript.model_validate(json.loads((base / "transcript.json").read_text()))
    c = cfg.create.footage.cuts
    segments = split_long(
        segments, list(transcript.words), footage.fps, c.punch_max_s, c.punch_min_s, c.punch_hook_s
    )
    notes_path = base / "cut-notes.yaml"
    if notes_path.exists():
        notes = CutNotes.model_validate(yaml.safe_load(notes_path.read_text()))
        if notes.open_with is not None:
            ow = notes.open_with
            segments = cold_open(segments, notes.take, ow.start_s, ow.end_s, footage.fps)
        if notes.close_with is not None:  # a still shot again at the end (no words): room for the end card
            cw = notes.close_with
            a, b = round(cw.start_s * footage.fps), round(cw.end_s * footage.fps)
            end = segments[-1].rec_in + segments[-1].src_out - segments[-1].src_in
            segments = [
                *segments,
                EdlSegment(take=notes.take, src_in=a, src_out=b, rec_in=end, cold_open=True),
            ]
    edl = Edl(
        provenance=_prov("f4_edl", {"cuts": cuts.model_dump(mode="json")["proposals"], "ids": ids,
                                    "takes": [t.frames for t in footage.takes]}),
        project=project, fps=footage.fps, segments=segments, applied=ids,
        duration_frames=sum(s.src_out - s.src_in for s in segments),
    )  # fmt: skip
    path = base / "edl.json"
    path.write_text(edl.model_dump_json(indent=1) + "\n")
    return path, edl


def run_presenter_timing(root: Path, project: str, cfg: LensConfig) -> tuple[Path, Timeline]:
    """C5 (presenter mode): the kept words on the edited clock -> timeline.json."""
    base, _ = _base(root, project)
    transcript = Transcript.model_validate(json.loads((base / "transcript.json").read_text()))
    cuts = Cuts.model_validate(json.loads((base / "cuts.json").read_text()))
    edl = Edl.model_validate(json.loads((base / "edl.json").read_text()))
    removed = {i for c in cuts.proposals if c.id in set(edl.applied) for i in c.words}
    words = remap_words(list(transcript.words), list(edl.segments), edl.fps, removed)
    timeline = build_presenter_timeline(
        project, words, edl.duration_frames / edl.fps, edl.fps, cfg.create.footage.scene_target_s
    )
    path = base / "timeline.json"
    path.write_text(timeline.model_dump_json(indent=1) + "\n")
    return path, timeline


def run_edit(root: Path, project: str, cfg: LensConfig) -> list[Path]:
    """F6: the edited presenter video at the destination frame, cut to the F5 crops when they exist (cuts
    applied, fades at each cut) -> data/create/<p>/footage/edited/."""
    base, data = _base(root, project)
    footage = Footage.model_validate(json.loads((base / "footage.json").read_text()))
    edl = Edl.model_validate(json.loads((base / "edl.json").read_text()))
    masters = {t.id: root / t.master for t in footage.takes}
    _, frame = cfg.create.design.frame_for(_brief(root, project).destination)
    fc = cfg.create.footage
    segs = list(edl.segments)
    framing_path = base / "framing.json"
    framing = Framing.model_validate(json.loads(framing_path.read_text())) if framing_path.exists() else None
    full = [f.full for f in framing.segments] if framing else None
    edited = data / "edited" / f"{project}-edited.mp4"
    raw = data / "edited" / f"{project}-edited-raw.mp4"
    render_edit(segs, masters, edl.fps, fc.crossfade_ms, raw, (frame.width, frame.height), full)
    band = cfg.targets.loudness[_brief(root, project).destination]
    finish_voice(raw, edited, fc.voice, (band.min_lufs + band.max_lufs) / 2)
    raw.unlink()
    return [edited]
