"""`lens validate`: check files against their schemas. Non-validating output is never committed."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from lens.config import REPO_ROOT
from lens.schemas import (
    A1File,
    A2File,
    Anchors,
    CandidatesFile,
    CompareReport,
    EvalFile,
    EventFacts,
    GoldFile,
    LensConfig,
    MeasureFile,
    PacketManifest,
    Palette,
    RecordFile,
    SignalsSummary,
    SourceEntry,
    SourcesFile,
    Taxonomy,
    VideoMeta,
)
from lens.schemas.cards import ArchetypeCard, PatternCard
from lens.schemas.compare import FixesFile
from lens.schemas.corpus import MotionStats, PacingStats, PatternsFile, Proposal, SoundStats
from lens.schemas.create import (
    Brief,
    Captions,
    CutApprovals,
    Cuts,
    Edits,
    Edl,
    Footage,
    Framing,
    LayoutPlan,
    MotionGrade,
    OverlayPlan,
    QaReport,
    SafeZoneReport,
    Script,
    SfxCue,
    Storyboard,
    Timeline,
    Tokens,
    Transcript,
    Voice,
    audio_tags,
)
from lens.schemas.exports import (
    ArchetypesExport,
    MotionTokens,
    PacingSpec,
    PatternsExport,
    SoundSpec,
    VoiceSpec,
)
from lens.schemas.scenes import SceneBatch, ScenesFile

TAXONOMY_PATH = Path("taxonomy/v1.yaml")


@dataclass(frozen=True)
class Result:
    path: str
    ok: bool
    errors: tuple[str, ...] = ()


def _load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)


def _format_errors(exc: ValidationError) -> tuple[str, ...]:
    out = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"]) or "<root>"
        out.append(f"{loc}: {err['msg']}")
    return tuple(out)


def _check_config(data: Any, root: Path, rel: str) -> list[str]:
    LensConfig.model_validate(data)
    return []


def _check_taxonomy(data: Any, root: Path, rel: str) -> list[str]:
    Taxonomy.model_validate(data)
    return []


def _check_proposals(data: Any, root: Path, rel: str) -> list[str]:
    if not isinstance(data, list):
        return ["proposals must be a list"]
    tax = Taxonomy.model_validate(_load(root / TAXONOMY_PATH))
    errors = []
    for p in (Proposal.model_validate(d) for d in data):
        if p.id in tax.patterns and p.status != "approved":
            errors.append(f"{p.id}: already a taxonomy pattern")
        if p.status == "approved" and p.id not in tax.patterns:
            errors.append(f"{p.id}: approved at G4 but missing from taxonomy patterns")
        if p.status.startswith("merged:") and p.status.split(":", 1)[1] not in tax.patterns:
            errors.append(f"{p.id}: merged into an unknown pattern")
        if p.nearest_pattern and p.nearest_pattern not in tax.patterns:
            errors.append(f"{p.id}: nearest_pattern {p.nearest_pattern!r} is not a taxonomy pattern")
    return errors


def _check_sources(data: Any, root: Path, rel: str) -> list[str]:
    sources = SourcesFile.model_validate(data)
    taxonomy = Taxonomy.model_validate(_load(root / TAXONOMY_PATH))
    errors = []
    for entry in sources.root:
        if entry.format not in taxonomy.format:
            errors.append(f"{entry.id}: format {entry.format!r} is not in taxonomy.format")
    return errors


_NO_OTHER_FIELD = object()


def _enum(
    errors: list[str], where: str, value: str, allowed: list[str], other: object = _NO_OTHER_FIELD
) -> None:
    """`value` must be in the taxonomy list; where the field has an *_other companion, "other" needs it."""
    if value == "other" and other is not _NO_OTHER_FIELD:
        if not other:
            errors.append(f"{where}: 'other' needs its *_other text")
    elif value not in allowed:
        errors.append(f"{where}: {value!r} is not in the taxonomy")


def _task(root: Path, video: str, task_id: str, rel: str, input_hash: str) -> tuple[Any, list[str]]:
    """The manifest task this file answers, and errors if it is not the task's output for this packet."""
    path = root / "packets" / video / "manifest.json"
    if not path.exists():
        return None, [f"no packet manifest for {video}"]
    manifest = PacketManifest.model_validate(_load(path))
    task = next((t for t in manifest.tasks if t.id == task_id), None)
    if task is None:
        return None, [f"{task_id} is not a task in packets/{video}/manifest.json"]
    errors = []
    rerun = re.fullmatch(r"runs/[a-z0-9][a-z0-9-]*/(.+)", rel)  # a blind re-annotation (lens eval)
    if task.output != rel and not (rerun and rerun.group(1) == task.output):
        errors.append(f"{task_id} writes {task.output}, not {rel}")
    if task.input_hash != input_hash:
        errors.append("provenance.input_hash differs from the task's (stale packet or copied header)")
    return (manifest, task), errors


def _anchors(root: Path, video: str) -> Anchors | None:
    path = root / "data" / "packets" / video / "pass1" / "anchors.json"
    return Anchors.model_validate(_load(path)) if path.exists() else None


def _check_a1(data: Any, root: Path, rel: str) -> list[str]:
    a1 = A1File.model_validate(data)
    tax = Taxonomy.model_validate(_load(root / TAXONOMY_PATH))
    found, errors = _task(root, a1.video, a1.task, rel, a1.provenance.input_hash)
    if a1.provenance.stage != "a1_annotate_video":
        errors.append("provenance.stage must be a1_annotate_video")
    if found is None:
        return errors
    manifest, task = found
    got = [s.shot for s in a1.shots]
    if sorted(got) != sorted(task.shots):
        errors.append(f"shots {got} must be exactly the task's shots {task.shots}")
    for s in a1.shots:
        _enum(errors, f"{s.shot}.shot_type", s.shot_type, tax.shot_type, s.shot_type_other)
        _enum(errors, f"{s.shot}.composition", s.composition, tax.composition, s.composition_other)
        _enum(errors, f"{s.shot}.transition_in", s.transition_in, tax.transition, s.transition_other)
        for d in s.depth_cues:
            _enum(errors, f"{s.shot}.depth_cues", d, tax.depth_cue)
    a1_tasks = [t for t in manifest.tasks if t.kind == "a1"]
    last = a1_tasks[-1].id == a1.task
    if last and a1.summary is None:
        errors.append("the last A1 part writes the video summary")
    if not last and a1.summary is not None:
        errors.append(f"only the last A1 part ({a1_tasks[-1].id}) writes the video summary")
    if a1.summary is None:
        return errors
    sm = a1.summary
    shots = {s for t in a1_tasks for s in t.shots}
    anchors = _anchors(root, a1.video)
    n_words = len(anchors.words) if anchors else None
    refs: list[tuple[str, list[str], tuple[int, int] | None]] = [
        *((f"beats[{i}]", b.shots, b.words) for i, b in enumerate(sm.beats)),
        ("hook", sm.hook.shots, sm.hook.words),
        ("cta", sm.cta.shots, None),
        *((f"signature_moments[{i}]", m.shots, None) for i, m in enumerate(sm.signature_moments)),
    ]
    for where, ids, span in refs:
        for sid in ids:
            if sid not in shots:
                errors.append(f"summary.{where}: unknown shot {sid}")
        if span is not None and (span[0] > span[1] or (n_words is not None and span[1] >= n_words)):
            errors.append(f"summary.{where}: word span {list(span)} is outside the transcript")
    for b in sm.beats:
        _enum(errors, "summary.beats", b.beat, tax.beat)
    _enum(errors, "summary.hook.technique", sm.hook.technique, tax.hook_technique, sm.hook.technique_other)
    for name, score in sm.scores:
        for ref in score.refs:
            ok = ref in shots or (
                ref.startswith("w") and ref[1:].isdigit() and (n_words is None or int(ref[1:]) < n_words)
            )
            if not ok:
                errors.append(f"summary.scores.{name}: unknown ref {ref!r} (shot id or w<word index>)")
    return errors


def _check_a2(data: Any, root: Path, rel: str) -> list[str]:
    a2 = A2File.model_validate(data)
    tax = Taxonomy.model_validate(_load(root / TAXONOMY_PATH))
    _, errors = _task(root, a2.video, a2.task, rel, a2.provenance.input_hash)
    if a2.provenance.stage != "a2_annotate_event":
        errors.append("provenance.stage must be a2_annotate_event")
    for i, e in enumerate(a2.elements):
        _enum(errors, f"elements[{i}].role", e.role, tax.element_role, e.role_other)
        for c in e.change_types:
            _enum(errors, f"elements[{i}].change_types", c, tax.change_type, e.change_other)
        if e.estimates and e.estimates.easing_class:
            _enum(errors, f"elements[{i}].estimates.easing_class", e.estimates.easing_class, tax.easing_class)
    for r in a2.sfx_review:
        _enum(errors, f"sfx_review.{r.id}", r.label, tax.sfx)
    if a2.pattern.id != "other" and a2.pattern.id not in tax.patterns:
        errors.append(f"pattern.id {a2.pattern.id!r} is not in taxonomy.patterns (or 'other')")
    packet = root / "data" / "packets" / a2.video / "events" / a2.event
    if (packet / "candidates.json").exists():
        boxes = {b.id for b in CandidatesFile.model_validate(_load(packet / "candidates.json")).boxes}
        for i, e in enumerate(a2.elements):
            if e.box and e.box not in boxes:
                errors.append(f"elements[{i}].box {e.box} is not a candidate (have {sorted(boxes)})")
    if (packet / "facts.json").exists():
        want = sorted(s.id for s in EventFacts.model_validate(_load(packet / "facts.json")).sfx)
        got = sorted(r.id for r in a2.sfx_review)
        if got != want:
            errors.append(f"sfx_review must cover exactly the SFX candidates {want}, got {got}")
    return errors


def _check_gold(data: Any, root: Path, rel: str) -> list[str]:
    gold = GoldFile.model_validate(data)
    tax = Taxonomy.model_validate(_load(root / TAXONOMY_PATH))
    errors: list[str] = []
    if rel != f"gold/{gold.video}/gold.yaml":
        errors.append(f"video {gold.video!r} does not match the path")
    for s in gold.shots:
        _enum(errors, f"{s.shot}.shot_type", s.shot_type, tax.shot_type)
        _enum(errors, f"{s.shot}.composition", s.composition, tax.composition)
        _enum(errors, f"{s.shot}.transition_in", s.transition_in, tax.transition)
        for d in s.depth_cues:
            _enum(errors, f"{s.shot}.depth_cues", d, tax.depth_cue)
    for e in gold.events:
        for el in e.elements:
            _enum(errors, f"{e.event}.{el.id}.role", el.role, tax.element_role)
            for c in el.change_types:
                _enum(errors, f"{e.event}.{el.id}.change_types", c, tax.change_type)
        for x in e.sfx:
            _enum(errors, f"{e.event}.{x.id}", x.label, tax.sfx)
        if e.pattern != "other" and e.pattern not in tax.patterns:
            errors.append(f"{e.event}.pattern {e.pattern!r} is not in taxonomy.patterns (or 'other')")
    return errors


def _check_card(data: Any, root: Path, rel: str) -> list[str]:
    from lens.synth.cards import STAGE, card_numbers_errors

    card = PatternCard.model_validate(data)
    errors = card_numbers_errors(root, card)
    if rel != f"corpus/patterns/{card.id}.json":
        errors.append(f"id {card.id!r} does not match the path")
    if card.provenance.stage != STAGE:
        errors.append(f"provenance.stage must be {STAGE}")
    return errors


def _check_scene_batch(data: Any, root: Path, rel: str) -> list[str]:
    from lens.config import load_config
    from lens.synth.scenes import batch_errors, batch_path

    sb = SceneBatch.model_validate(data)
    tax = Taxonomy.model_validate(_load(root / TAXONOMY_PATH))
    errors = batch_errors(root, load_config(), sb, list(tax.scene_archetype))
    if rel != batch_path(sb.batch):
        errors.append(f"batch {sb.batch!r} does not match the path")
    return errors


def _check_scene_proposals(data: Any, root: Path, rel: str) -> list[str]:
    if not isinstance(data, list):
        return ["scene proposals must be a list"]
    tax = Taxonomy.model_validate(_load(root / TAXONOMY_PATH))
    errors = []
    for p in (Proposal.model_validate(d) for d in data):
        if p.status == "approved" and p.id not in tax.scene_archetype:
            errors.append(f"{p.id}: approved at G4 but missing from taxonomy scene_archetype")
        if p.status.startswith("merged:") and p.status.split(":", 1)[1] not in tax.scene_archetype:
            errors.append(f"{p.id}: merged into an unknown scene archetype")
    return errors


def _check_archetype(data: Any, root: Path, rel: str) -> list[str]:
    from lens.synth.cards import STAGE, archetype_errors

    card = ArchetypeCard.model_validate(data)
    errors = archetype_errors(root, card)
    if rel != f"corpus/archetypes/{card.id}.json":
        errors.append(f"id {card.id!r} does not match the path")
    if card.provenance.stage != STAGE:
        errors.append(f"provenance.stage must be {STAGE}")
    return errors


def _check_fixes(data: Any, root: Path, rel: str) -> list[str]:
    from lens.compare.fixes import fixes_errors

    return fixes_errors(root, FixesFile.model_validate(data), rel)


def _project_errors(project: str, rel: str) -> list[str]:
    want = rel.split("/")[1]
    return [] if project == want else [f"project {project!r} does not match the path ({want!r})"]


def _project_file(root: Path, project: str, name: str) -> Any | None:
    path = root / "projects" / project / name
    return _load(path) if path.exists() else None


def _create_config(root: Path) -> Any:
    from lens.config import load_config

    return load_config(root / "config" / "lens.yaml")


def _check_brief(data: Any, root: Path, rel: str) -> list[str]:
    brief = Brief.model_validate(data)
    tax = Taxonomy.model_validate(_load(root / TAXONOMY_PATH))
    errors = _project_errors(brief.project, rel)
    if not (root / "brands" / brief.brand).is_dir():
        errors.append(f"brand {brief.brand!r} has no folder brands/{brief.brand}/")
    if brief.format not in tax.format:
        errors.append(f"format {brief.format!r} is not in taxonomy.format")
    cfg = _create_config(root)
    if brief.destination not in cfg.targets.loudness:
        errors.append(f"destination {brief.destination!r} has no loudness target in config")
    if brief.destination not in cfg.create.design.destination_frames:
        errors.append(
            f"destination {brief.destination!r} has no frame in config create.design.destination_frames"
        )
    return errors


def _script_scene_ids(root: Path, project: str, errors: list[str]) -> list[str] | None:
    raw = _project_file(root, project, "script.yaml")
    if raw is None:
        errors.append(f"projects/{project}/script.yaml is missing")
        return None
    return [s.id for s in Script.model_validate(raw).scenes]


def _check_script(data: Any, root: Path, rel: str) -> list[str]:
    script = Script.model_validate(data)
    tax = Taxonomy.model_validate(_load(root / TAXONOMY_PATH))
    allowed = set(_create_config(root).create.voice.allowed_tags)
    errors = _project_errors(script.project, rel)
    raw = _project_file(root, script.project, "brief.yaml")
    facts = {f.id for f in Brief.model_validate(raw).facts} if raw is not None else None
    if facts is None:
        errors.append(f"projects/{script.project}/brief.yaml is missing")
    for sc in script.scenes:
        _enum(errors, f"{sc.id}.beat", sc.beat, tax.beat)
        for f in sc.facts:
            if facts is not None and f not in facts:
                errors.append(f"{sc.id}: fact {f!r} is not in the brief")
        for tag in audio_tags(sc.spoken):
            if tag not in allowed:
                errors.append(f"{sc.id}: audio tag [{tag}] is not in config create.voice.allowed_tags")
    errors += script_style_errors(script, _create_config(root).create.script)
    if raw is not None:
        errors += script_length_errors(script, Brief.model_validate(raw), _create_config(root))
    return errors


def script_style_errors(script: Script, rules: Any) -> list[str]:
    """C2 style guard: banned devices and words (config create.script), and tag density."""
    errors = []
    for sc in script.scenes:
        text = re.sub(r"\[[^\]]*\]", "", sc.spoken)
        for rule in rules.banned:
            if re.search(rule.pattern, text, re.IGNORECASE):
                errors.append(f"{sc.id}: {rule.reason}")
        if len(audio_tags(sc.spoken)) > rules.max_tags_per_scene:
            errors.append(f"{sc.id}: more than {rules.max_tags_per_scene} audio tags")
    return errors


def script_length_errors(script: Script, brief: Brief, cfg: Any) -> list[str]:
    """The script, read at the planning pace with the configured silences, must fit the brief's band."""
    words = sum(len(re.sub(r"\[[^\]]*\]", "", s.spoken).split()) for s in script.scenes)
    t = cfg.create.timing
    est = words / cfg.create.script.planning_wpm * 60 + t.pre_roll_s + t.close_tail_s
    est += t.scene_tail_s * (len(script.scenes) - 1)
    if not brief.length.min_s <= est <= brief.length.max_s:
        return [
            f"about {est:.0f} s at {cfg.create.script.planning_wpm:g} wpm; the brief asks "
            f"{brief.length.min_s:g}-{brief.length.max_s:g} s"
        ]
    return []


def _check_voice(data: Any, root: Path, rel: str) -> list[str]:
    voice = Voice.model_validate(data)
    errors = _project_errors(voice.project, rel)
    want = _script_scene_ids(root, voice.project, errors)
    got = [s.scene for s in voice.scenes]
    if want is not None and got != want:
        errors.append(f"scenes {got} must be the script's scenes in order {want}")
    for s in voice.scenes:
        path = f"data/create/{voice.project}/voice/{s.scene}-t{s.take}.mp3"
        if s.audio != path:
            errors.append(f"{s.scene}: audio must be {path}")
    return errors


def _check_timeline(data: Any, root: Path, rel: str) -> list[str]:
    timeline = Timeline.model_validate(data)
    errors = _project_errors(timeline.project, rel)
    brief = _project_file(root, timeline.project, "brief.yaml")
    if isinstance(brief, dict) and brief.get("voice") == "presenter":
        return errors  # scenes follow the edited takes' sentences, not a script (ADR 0025)
    want = _script_scene_ids(root, timeline.project, errors)
    got = [s.scene for s in timeline.scenes]
    if want is not None and got != want:
        errors.append(f"scenes {got} must be the script's scenes in order {want}")
    return errors


def _check_tokens(data: Any, root: Path, rel: str) -> list[str]:
    from create.tokens import token_errors

    tokens = Tokens.model_validate(data)
    from create.project import BrandError, brand_dir

    errors = _project_errors(tokens.project, rel)
    try:
        brand: Path | None = brand_dir(root, tokens.project)
    except BrandError as exc:
        errors.append(str(exc))
        brand = None
    return errors + token_errors(tokens, _create_config(root).create.design, brand)


def _texts(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [t for v in value.values() for t in _texts(v)]
    if isinstance(value, list):
        return [t for v in value for t in _texts(v)]
    return []


def _check_storyboard(data: Any, root: Path, rel: str) -> list[str]:
    board = Storyboard.model_validate(data)
    errors = _project_errors(board.project, rel)
    raw = _project_file(root, board.project, "timeline.json")
    if raw is None:
        return [*errors, f"projects/{board.project}/timeline.json is missing"]
    timeline = Timeline.model_validate(raw)
    got, want = [s.scene for s in board.scenes], [s.scene for s in timeline.scenes]
    if got != want:
        errors.append(f"scenes {got} must be the timeline's scenes in order {want}")
    archetypes = {a["id"]: a for a in _load(root / "exports" / "archetypes.json")["archetypes"]}
    words = {w.i: w.scene for w in timeline.words}
    for sc in board.scenes:
        arch = archetypes.get(sc.archetype)
        if arch is None and sc.archetype != "freeform":
            errors.append(f"{sc.scene}: archetype {sc.archetype!r} is not in exports/archetypes.json")
        if arch is not None:
            names = {s["name"] for s in arch["slots"]}
            for slot in sc.slots:
                if slot not in names:
                    errors.append(f"{sc.scene}: {slot!r} is not a slot of {sc.archetype}")
            for s in arch["slots"]:
                if s["required"] and s["name"] not in sc.slots:
                    errors.append(f"{sc.scene}: {sc.archetype} needs slot {s['name']!r}")
        for c in sc.cues:
            if words.get(c.word) != sc.scene:
                errors.append(f"{sc.scene}: cue word {c.word} is not spoken in this scene")
            if c.target is not None and c.target not in sc.slots:
                errors.append(f"{sc.scene}: cue target {c.target!r} is not a filled slot")
        texts = _texts(sc.slots) + ([sc.title] if sc.title else [])
        if any("—" in t for t in texts):
            errors.append(f"{sc.scene}: em dash in on-screen copy (brand DESIGN.md §6)")
        if any(re.search(r"\d", t) for t in texts) and not sc.example_data:
            errors.append(f"{sc.scene}: on-screen numbers need example_data (honesty guard, handoff 7.9)")
    return errors


def _owned(model: Any, data: Any, rel: str) -> list[str]:
    return _project_errors(model.model_validate(data).project, rel)


def _check_transcript(data: Any, root: Path, rel: str) -> list[str]:
    t = Transcript.model_validate(data)
    errors = _project_errors(t.project, rel)
    raw = _project_file(root, t.project, "footage.json")
    if raw is not None:
        takes = {k.id: k.duration_s for k in Footage.model_validate(raw).takes}
        for w in t.words:
            if w.take not in takes or w.end_s > takes[w.take] + 0.05:
                errors.append(f"word {w.i} {w.text!r} is outside take {w.take!r}")
                break
    return errors


def _check_cuts(data: Any, root: Path, rel: str) -> list[str]:
    cuts = Cuts.model_validate(data)
    errors = _project_errors(cuts.project, rel)
    ids = [c.id for c in cuts.proposals]
    if len(ids) != len(set(ids)):
        errors.append("cut ids must be unique")
    for c in cuts.proposals:
        if c.end_s <= c.start_s:
            errors.append(f"{c.id}: end must follow start")
    return errors


def _check_edl(data: Any, root: Path, rel: str) -> list[str]:
    edl = Edl.model_validate(data)
    errors = _project_errors(edl.project, rel)
    raw = _project_file(root, edl.project, "footage.json")
    if raw is not None:
        frames = {k.id: k.frames for k in Footage.model_validate(raw).takes}
        for s in edl.segments:
            if s.take not in frames or s.src_out > frames[s.take]:
                errors.append(f"segment {s.take}@{s.src_in} is outside its take")
    return errors


def _check_layout(data: Any, root: Path, rel: str) -> list[str]:
    from create.footage.layout import check_plan

    plan = LayoutPlan.model_validate(data or {})
    raw = _project_file(root, rel.split("/")[1], "timeline.json")
    return check_plan(plan, Timeline.model_validate(raw)) if raw is not None else []


def _check_overlays(data: Any, root: Path, rel: str) -> list[str]:
    plan = OverlayPlan.model_validate(data)
    raw = _project_file(root, rel.split("/")[1], "timeline.json")
    if raw is None:
        return []
    known = {w.i for w in Timeline.model_validate(raw).words}
    return [
        f"overlay {n}: word {it.word} or until {it.until} is not in the timeline"
        for n, it in enumerate(plan.items)
        if it.word not in known or (it.until is not None and it.until not in known)
    ]


def _check_captions(data: Any, root: Path, rel: str) -> list[str]:
    caps = Captions.model_validate(data)
    errors = _project_errors(caps.project, rel)
    raw = _project_file(root, caps.project, "timeline.json")
    if raw is not None:
        words = {w.i: w for w in Timeline.model_validate(raw).words}
        for g in caps.groups:
            for w in g.words:
                tw = words.get(w.i)
                if tw is None or tw.text != w.w or abs(tw.start_s - w.t) > 0.002:
                    errors.append(f"caption word {w.i} {w.w!r} does not match the timeline")
                    break
    return errors


def _check_safe_zones(data: Any, root: Path, rel: str) -> list[str]:
    report = SafeZoneReport.model_validate(data)
    errors = _project_errors(report.project, rel)
    if report.frame not in _create_config(root).create.design.frames:
        errors.append(f"frame {report.frame!r} is not in config create.design.frames")
    return errors


def _check_sfx(data: Any, root: Path, rel: str) -> list[str]:
    """A motion build's SFX cues: names from the library, gains in range (config create.motion)."""
    if not isinstance(data, list):
        return ["sfx.json must be a list of cues"]
    motion = _create_config(root).create.motion
    lo, hi = motion.sfx_gain_db
    errors = []
    for i, raw in enumerate(data):
        cue = SfxCue.model_validate(raw)
        if cue.sfx not in motion.sfx:
            errors.append(f"cue {i}: {cue.sfx!r} is not in config create.motion.sfx")
        if not lo <= cue.gain_db <= hi:
            errors.append(f"cue {i}: gain {cue.gain_db:g} dB is outside {lo:g}..{hi:g}")
    return errors


def _model(model: type[BaseModel], data: Any) -> list[str]:
    model.model_validate(data)
    return []


# Path pattern (repo-relative) → checker(data, repo root, repo-relative path).
CHECKERS: dict[str, Callable[[Any, Path, str], list[str]]] = {
    "config/lens.yaml": _check_config,
    "taxonomy/v1.yaml": _check_taxonomy,
    "taxonomy/proposals.yaml": _check_proposals,
    "sources/sources.yaml": _check_sources,
    "videos/*/meta.json": lambda data, root, rel: _model(VideoMeta, data),
    "videos/*/palette.json": lambda data, root, rel: _model(Palette, data),
    "videos/*/signals.summary.json": lambda data, root, rel: _model(SignalsSummary, data),
    "reports/compare/*/metrics.json": lambda data, root, rel: _model(CompareReport, data),
    "packets/*/manifest.json": lambda data, root, rel: _model(PacketManifest, data),
    "videos/*/measure/*.json": lambda data, root, rel: _model(MeasureFile, data),
    "videos/*/record.json": lambda data, root, rel: _model(RecordFile, data),
    "videos/*/a1.json": _check_a1,
    "videos/*/a1.p*.json": _check_a1,
    "videos/*/events/*.a2.json": _check_a2,
    "gold/*/gold.yaml": _check_gold,
    "runs/*/videos/*/events/*.a2.json": _check_a2,
    "runs/eval/*.json": lambda data, root, rel: _model(EvalFile, data),
    "corpus/stats/motion.json": lambda data, root, rel: _model(MotionStats, data),
    "corpus/stats/sound.json": lambda data, root, rel: _model(SoundStats, data),
    "corpus/stats/pacing.json": lambda data, root, rel: _model(PacingStats, data),
    "corpus/stats/patterns.json": lambda data, root, rel: _model(PatternsFile, data),
    "corpus/patterns/*.json": _check_card,
    "corpus/scenes/*.json": _check_scene_batch,
    "corpus/archetypes/*.json": _check_archetype,
    "reports/compare/*/fixes.json": _check_fixes,
    "exports/motion-tokens.json": lambda data, root, rel: _model(MotionTokens, data),
    "exports/sound-spec.json": lambda data, root, rel: _model(SoundSpec, data),
    "exports/pacing.json": lambda data, root, rel: _model(PacingSpec, data),
    "exports/voice-spec.json": lambda data, root, rel: _model(VoiceSpec, data),
    "exports/archetypes.json": lambda data, root, rel: _model(ArchetypesExport, data),
    "exports/patterns.json": lambda data, root, rel: _model(PatternsExport, data),
    "corpus/stats/scenes.json": lambda data, root, rel: _model(ScenesFile, data),
    "taxonomy/scene_proposals.yaml": _check_scene_proposals,
    # Phase 2 projects (docs/phase2-plan.md)
    "projects/*/brief.yaml": _check_brief,
    "projects/*/script.yaml": _check_script,
    "projects/*/voice.json": _check_voice,
    "projects/*/timeline.json": _check_timeline,
    "projects/*/tokens.json": _check_tokens,
    "projects/*/storyboard.json": _check_storyboard,
    "projects/*/audit/safe-zones.json": _check_safe_zones,
    "projects/*/captions.json": _check_captions,
    "projects/*/motion/grade.json": lambda data, root, rel: _owned(MotionGrade, data, rel),
    "projects/*/motion/sfx.json": _check_sfx,
    "projects/*/footage.json": lambda data, root, rel: _owned(Footage, data, rel),
    "projects/*/transcript.json": _check_transcript,
    "projects/*/cuts.json": _check_cuts,
    "projects/*/cuts-approved.yaml": lambda data, root, rel: _model(CutApprovals, data or {}),
    "projects/*/edits.yaml": lambda data, root, rel: _model(Edits, data or {}),
    "projects/*/edl.json": _check_edl,
    "projects/*/framing.json": lambda data, root, rel: _owned(Framing, data, rel),
    "projects/*/layout.yaml": _check_layout,
    "projects/*/overlays.yaml": _check_overlays,
    "projects/*/qa/*.json": lambda data, root, rel: _owned(QaReport, data, rel),
    # Local data (gitignored, synced to R2); validated when present.
    "data/evidence/*/events/*/candidates.json": lambda data, root, rel: _model(CandidatesFile, data),
    "data/packets/*/events/*/candidates.json": lambda data, root, rel: _model(CandidatesFile, data),
    "data/packets/*/events/*/facts.json": lambda data, root, rel: _model(EventFacts, data),
    "data/packets/*/pass1/anchors.json": lambda data, root, rel: _model(Anchors, data),
}


def checker_for(rel_path: str) -> Callable[[Any, Path, str], list[str]] | None:
    for pattern, fn in CHECKERS.items():
        if fnmatch(rel_path, pattern):
            return fn
    return None


def load_sources(root: Path = REPO_ROOT) -> list[SourceEntry]:
    """Validated sources (raises ValueError with readable errors if invalid)."""
    result = validate_file(root / "sources" / "sources.yaml", root)
    if not result.ok:
        raise ValueError("sources/sources.yaml is invalid:\n" + "\n".join(result.errors))
    return SourcesFile.model_validate(_load(root / "sources" / "sources.yaml")).root


def validate_file(path: Path, root: Path = REPO_ROOT) -> Result:
    abs_path = path if path.is_absolute() else (Path.cwd() / path)
    try:
        rel = abs_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return Result(str(path), False, ("path is outside the repository",))
    fn = checker_for(rel)
    if fn is None:
        return Result(rel, False, ("no schema is registered for this path",))
    try:
        data = _load(abs_path)
        errors = fn(data, root, rel)
    except FileNotFoundError:
        return Result(rel, False, ("file not found",))
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        return Result(rel, False, (f"parse error: {exc}",))
    except ValidationError as exc:
        return Result(rel, False, _format_errors(exc))
    return Result(rel, not errors, tuple(errors))


def validate_all(root: Path = REPO_ROOT) -> list[Result]:
    """Validate every committed file that has a registered schema."""
    results = []
    for pattern in CHECKERS:
        for path in sorted(root.glob(pattern)):
            results.append(validate_file(path, root))
    return results
