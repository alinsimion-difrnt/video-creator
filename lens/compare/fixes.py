"""A4 compare-fixes (BUILD_PLAN 9.3): the brief for Claude's top-10 fixes, and their validation.

The brief holds the corpus placement (S11), the target's own timeline from code (shots, dead holds, SFX,
events with measured timing) and what the recipe book offers (exported patterns, archetypes, token
files). A fix must cite a metric, at least one timestamp inside the video and at least one reference
that exists: `pattern:<id>`, `archetype:<id>` or `token:<file>#<dotted.path>`.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lens import __version__
from lens.hashing import cache_key, sha256_file
from lens.packets import skill_id
from lens.schemas.common import Annotator, Provenance
from lens.schemas.compare import CompareReport, FixesFile
from lens.schemas.record import RecordFile
from lens.schemas.signals import SignalsSummary

SKILL = "compare-fixes"
STAGE = "a4_compare_fixes"
TOKEN_FILES = ("motion-tokens.json", "sound-spec.json", "pacing.json", "voice-spec.json")


def fixes_path(video: str) -> str:
    return f"reports/compare/{video}/fixes.json"


def _exports(root: Path, name: str) -> dict[str, Any]:
    return json.loads((root / "exports" / name).read_text("utf-8"))  # type: ignore[no-any-return]


def fixes_brief(root: Path, video: str) -> dict[str, Any]:
    out = root / "reports" / "compare" / video
    report = CompareReport.model_validate_json((out / "metrics.json").read_text("utf-8"))
    if report.mode != "corpus":
        raise ValueError(f"run `lens compare --video {video}` (corpus mode) first")
    vdir = root / "videos" / video
    rec = RecordFile.model_validate_json((vdir / "record.json").read_text("utf-8"))
    sig = SignalsSummary.model_validate_json((vdir / "signals.summary.json").read_text("utf-8"))
    pats = _exports(root, "patterns.json")["patterns"]
    archs = _exports(root, "archetypes.json")["archetypes"]
    events = []
    for e in rec.events:
        if e.status != "annotated":
            continue
        timed = [el.timing for el in e.elements if el.timing and el.timing.source == "measured"]
        events.append(
            {
                "event": e.id,
                "shot": e.shot,
                "start_s": round(e.start_s, 2),
                "pattern": e.pattern.id if e.pattern else None,
                "durations_ms": sorted(round(t.duration_ms) for t in timed if t.duration_ms),
                "easing": sorted({t.easing_class for t in timed if t.easing_class}),
            }
        )
    paths = [out / "metrics.json", vdir / "record.json", vdir / "signals.summary.json"]
    paths += [root / "exports" / n for n in ("patterns.json", "archetypes.json", *TOKEN_FILES)]
    return {
        "video": video,
        "skill": SKILL,
        "output": fixes_path(video),
        "duration_s": sig.video.duration_s,
        "format": rec.format,
        "metrics": [m.model_dump(mode="json") for m in report.metrics if m.status != "n/a"],
        "shots": [
            {
                "shot": s.id,
                "start_s": round(s.start_s, 2),
                "end_s": round(s.end_s, 2),
                "transition_in": s.transition_in,
                "what_happens": s.annotation.what_happens if s.annotation else None,
            }
            for s in rec.shots
        ],
        "dead_holds": [
            {"shot": h.shot, "start_s": round(h.start_s, 2), "end_s": round(h.end_s, 2)}
            for h in sig.video.holds
            if h.dead
        ],
        "sfx": [
            {
                "id": x.id,
                "time_s": round(x.sync_s, 2),
                "label": x.label,
                "reveal_offset_ms": x.reveal_offset_ms,
            }
            for x in rec.sfx
        ],
        "events": events,
        "patterns": [{"id": p["id"], "name": p["name"]} for p in pats],
        "archetypes": [{"id": a["id"], "name": a["name"]} for a in archs],
        "token_files": list(TOKEN_FILES),
        "provenance": Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CLAUDE_CODE,
            skill=skill_id(root, SKILL),
            input_hash=cache_key({"inputs": [sha256_file(p) for p in paths]}),
            created_at=datetime.now(UTC),
        ).model_dump(mode="json"),
    }


def _token_exists(root: Path, ref: str) -> bool:
    file, _, path = ref.partition("#")
    if file not in TOKEN_FILES or not (root / "exports" / file).exists():
        return False
    node: Any = _exports(root, file)
    for part in [p for p in path.split(".") if p]:
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            return False
    return True


def fixes_errors(root: Path, ff: FixesFile, rel: str) -> list[str]:
    errors = []
    if rel != fixes_path(ff.video):
        errors.append(f"video {ff.video!r} does not match the path")
    if ff.provenance.stage != STAGE:
        errors.append(f"provenance.stage must be {STAGE}")
    out = root / "reports" / "compare" / ff.video
    if not (out / "metrics.json").exists():
        return [*errors, "no metrics.json next to it"]
    report = CompareReport.model_validate_json((out / "metrics.json").read_text("utf-8"))
    metrics = {m.id for m in report.metrics}
    sig = SignalsSummary.model_validate_json(
        (root / "videos" / ff.video / "signals.summary.json").read_text("utf-8")
    )
    pats = {p["id"] for p in _exports(root, "patterns.json")["patterns"]}
    archs = {a["id"] for a in _exports(root, "archetypes.json")["archetypes"]}
    for i, f in enumerate(ff.fixes):
        where = f"fixes[{i}]"
        if f.metric not in metrics:
            errors.append(f"{where}: metric {f.metric!r} is not in metrics.json")
        if not f.timestamps_s:
            errors.append(f"{where}: needs at least one timestamp")
        for t in f.timestamps_s:
            if not 0 <= t <= sig.video.duration_s:
                errors.append(f"{where}: timestamp {t} is outside the video")
        if not f.refs:
            errors.append(f"{where}: needs at least one pattern, archetype or token reference")
        for r in f.refs:
            kind, _, val = r.partition(":")
            ok = (
                (kind == "pattern" and val in pats)
                or (kind == "archetype" and val in archs)
                or (kind == "token" and _token_exists(root, val))
            )
            if not ok:
                errors.append(f"{where}: reference {r!r} does not exist in exports/")
    return errors
