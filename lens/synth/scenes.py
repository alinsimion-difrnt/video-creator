"""Scene archetypes (BUILD_PLAN 8.5): A3 batches and briefs for sorting shots, and the S9 stats per
archetype.

Batches are deterministic: every annotated shot of the weighted corpus (own videos excluded), in video
and shot order, cut into `synth.scene_batch` shots. Sorting is text only: the brief carries what A1 said
about each shot and which patterns its events were given.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from lens import __version__
from lens.hashing import cache_key, sha256_file
from lens.packets import skill_id
from lens.schemas import LensConfig
from lens.schemas.common import Annotator, Provenance
from lens.schemas.corpus import Stat
from lens.schemas.record import RecordFile
from lens.schemas.scenes import ArchetypeStats, SceneBatch, SceneExample, ScenesFile
from lens.synth.cluster import Embed, propose
from lens.synth.stats import shares

SKILL = "sort-scenes"
STAGE = "a3_scene_types"
STATS_STAGE = "s9_scene_stats"


def _records(root: Path, cfg: LensConfig) -> list[RecordFile]:
    tiers = cfg.synth.weights.tier
    out = []
    for p in sorted((root / "videos").glob("*/record.json")):
        rec = RecordFile.model_validate_json(p.read_text("utf-8"))
        if tiers.get(rec.tier, 0.0) > 0:
            out.append(rec)
    return out


def batches(root: Path, cfg: LensConfig) -> dict[str, list[tuple[str, str]]]:
    """batch id -> [(video, shot)] for every annotated shot of the corpus."""
    shots = [(r.video, s.id) for r in _records(root, cfg) for s in r.shots if s.annotation is not None]
    n = cfg.synth.scene_batch
    return {f"b{i // n + 1:02d}": shots[i : i + n] for i in range(0, len(shots), n)}


def batch_path(batch: str) -> str:
    return f"corpus/scenes/{batch}.json"


def scene_brief(root: Path, cfg: LensConfig, batch: str) -> dict[str, Any]:
    plan = batches(root, cfg)
    if batch not in plan:
        raise KeyError(f"{batch} is not a scene batch (have {', '.join(plan)})")
    wanted = set(plan[batch])
    recs = {r.video: r for r in _records(root, cfg) if any(v == r.video for v, _ in wanted)}
    shots = []
    for video, sid in plan[batch]:
        rec = recs[video]
        s = next(x for x in rec.shots if x.id == sid)
        a = s.annotation
        assert a is not None
        events = [e for e in rec.events if e.shot == sid and e.status == "annotated" and e.pattern]
        beats = [b.beat for b in rec.summary.beats if sid in b.shots] if rec.summary else []
        shots.append(
            {
                "video": video,
                "shot": sid,
                "format": rec.format,
                "duration_s": round(s.end_s - s.start_s, 2),
                "position": f"{rec.shots.index(s) + 1} of {len(rec.shots)}",
                "beats": beats,
                "shot_type": a.shot_type,
                "composition": a.composition,
                "focal_element": a.focal_element,
                "text_word_count": a.text_word_count,
                "what_happens": a.what_happens,
                "patterns": [e.pattern.id for e in events if e.pattern],
            }
        )
    paths = [root / "videos" / v / "record.json" for v in sorted(recs)]
    return {
        "batch": batch,
        "skill": SKILL,
        "output": batch_path(batch),
        "shots": shots,
        "provenance": Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CLAUDE_CODE,
            skill=skill_id(root, SKILL),
            input_hash=cache_key({"batch": plan[batch], "inputs": [sha256_file(p) for p in paths]}),
            created_at=datetime.now(UTC),
        ).model_dump(mode="json"),
    }


def batch_errors(root: Path, cfg: LensConfig, sb: SceneBatch, archetypes: list[str]) -> list[str]:
    plan = batches(root, cfg)
    if sb.batch not in plan:
        return [f"{sb.batch} is not a scene batch"]
    errors = []
    want = plan[sb.batch]
    got = [(i.video, i.shot) for i in sb.items]
    if sorted(got) != sorted(want) or len(set(got)) != len(got):
        errors.append(f"items must cover exactly the {len(want)} shots of {sb.batch}, once each")
    for i in sb.items:
        if i.archetype != "other" and i.archetype not in archetypes:
            errors.append(f"{i.video}/{i.shot}: {i.archetype!r} is not a scene_archetype (or 'other')")
    if sb.provenance.stage != STAGE:
        errors.append(f"provenance.stage must be {STAGE}")
    return errors


def load_assignments(root: Path) -> dict[tuple[str, str], tuple[str, str | None]]:
    """(video, shot) -> (archetype, proposed name) from every batch file."""
    out = {}
    for p in sorted((root / "corpus" / "scenes").glob("b*.json")):
        sb = SceneBatch.model_validate_json(p.read_text("utf-8"))
        for i in sb.items:
            out[(i.video, i.shot)] = (i.archetype, i.proposed_name)
    return out


def scene_g4_assignments(root: Path) -> dict[str, str]:
    """<video>/<shot> -> archetype for `other` shots of scene proposals approved or merged at G4."""
    path = root / "taxonomy" / "scene_proposals.yaml"
    rows = (yaml.safe_load(path.read_text("utf-8")) if path.exists() else None) or []
    out: dict[str, str] = {}
    for o in rows:
        status = o.get("status", "proposed")
        target = (
            o["id"]
            if status == "approved"
            else status.split(":", 1)[1]
            if status.startswith("merged:")
            else None
        )
        if target:
            out.update(dict.fromkeys(o.get("members", []), target))
    return out


def scene_stats(
    root: Path, cfg: LensConfig, weight_of: dict[str, float], mk: Callable[..., Stat], prov: Provenance
) -> ScenesFile:
    from lens.synth import _weighting

    assigned = load_assignments(root)
    decided = scene_g4_assignments(root)
    groups: dict[str, list[tuple[RecordFile, Any]]] = defaultdict(list)
    other = 0
    recs = {r.video: r for r in _records(root, cfg)}
    for (video, sid), (arch, _) in assigned.items():
        rec = recs.get(video)
        shot = next((s for s in rec.shots if s.id == sid), None) if rec else None
        if rec is None or shot is None:
            continue
        arch = decided.get(f"{video}/{sid}", arch) if arch == "other" else arch
        if arch == "other":
            other += 1
        else:
            groups[arch].append((rec, shot))
    out = []
    for aid, members in sorted(groups.items()):
        rows: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
        pats, trans, types, beats, sfx = [], [], [], [], []
        sfx_off: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
        ranked = []
        for rec, s in members:
            w, v = weight_of.get(rec.video, 0.0), rec.video
            rows["dur"].append((s.end_s - s.start_s, w, v))
            evs = [e for e in rec.events if e.shot == s.id and e.status == "annotated"]
            rows["events"].append((float(len(evs)), w, v))
            if evs:
                rows["first"].append((min(e.start_s for e in evs) - s.start_s, w, v))
            pats += [(e.pattern.id, w) for e in evs if e.pattern]
            if s.annotation:
                trans.append((s.annotation.transition_in, w))
                types.append((s.annotation.shot_type, w))
            if rec.summary:
                beats += [(b.beat, w) for b in rec.summary.beats if s.id in b.shots]
            for x in rec.sfx:
                if s.start_s <= x.sync_s < s.end_s:
                    sfx.append((x.label, w))
                    sfx_off[x.label].append((x.sync_s - s.start_s, w, v))
            score = rec.summary.scores.overall.score if rec.summary else None
            ranked.append((w * (1 + len(evs) / 10), v, s.id, score))
        ranked.sort(key=lambda r: (-r[0], r[1], r[2]))
        examples, seen = [], set()
        for _, v, sid, score in ranked:
            if v in seen:
                continue
            seen.add(v)
            examples.append(SceneExample(video=v, shot=sid, score=score))
            if len(examples) >= cfg.synth.max_examples:
                break

        def st(key: str, src: dict[str, list[tuple[float, float, str]]] = rows) -> Stat:
            r = src.get(key, [])
            return mk([x[0] for x in r], [x[1] for x in r], [x[2] for x in r])

        out.append(
            ArchetypeStats(
                id=aid,
                shots=len(members),
                videos=len({r.video for r, _ in members}),
                weight=round(sum(weight_of.get(r.video, 0.0) for r, _ in members), 4),
                duration_s=st("dur"),
                events_per_shot=st("events"),
                first_motion_s=st("first"),
                pattern_mix=shares(pats),
                transition_mix=shares(trans),
                shot_type_mix=shares(types),
                beat_mix=shares(beats),
                sfx_label_mix=shares(sfx),
                sfx_offset_s_by_label={k: st(k, sfx_off) for k in sorted(sfx_off)},
                examples=examples,
            )
        )
    out.sort(key=lambda a: (-a.weight, a.id))
    return ScenesFile(
        provenance=prov, weighting=_weighting(cfg), shots=len(assigned), archetypes=out, other_shots=other
    )


def write_scene_proposals(root: Path, cfg: LensConfig, archetypes: list[str], embed: Embed) -> int:
    """Cluster `other` scenes (same rules as patterns) into taxonomy/scene_proposals.yaml."""
    recs = {r.video: r for r in _records(root, cfg)}
    items = []
    for (video, sid), (arch, name) in sorted(load_assignments(root).items()):
        rec = recs.get(video)
        shot = next((s for s in rec.shots if s.id == sid), None) if rec else None
        if arch == "other" and shot is not None and shot.annotation is not None:
            # Grouped by the sorter's name alone: the same name is the same scene type, however
            # differently the shots are described; only near-synonym names are merged.
            items.append((f"{video}/{sid}", name or "", ""))
    brand_of: dict[str, str | None] = {v: r.brand.lower() for v, r in recs.items()}
    path = root / "taxonomy" / "scene_proposals.yaml"
    old = (yaml.safe_load(path.read_text("utf-8")) if path.exists() else None) or []
    kept = ("plain", "recommendation", "why", "status")
    prior = {o["id"]: {k: o[k] for k in kept if o.get(k)} for o in old if isinstance(o, dict) and "id" in o}
    done = [o for o in old if isinstance(o, dict) and o.get("status", "proposed") != "proposed"]
    settled = {m for o in done for m in o.get("members", [])}
    items = [i for i in items if i[0] not in settled]
    proposals, _ = propose(items, archetypes, cfg.synth.cluster, embed, brand_of)
    rows = done + [p.model_copy(update=prior.get(p.id, {})).model_dump(mode="json") for p in proposals]
    header = "# Written by s9_scene_stats (clusters of `other` scenes). Reviewed by Robert at gate G4.\n"
    path.write_text(header + yaml.safe_dump(rows, sort_keys=False, allow_unicode=True, width=110), "utf-8")
    return len(proposals)


def pending_batches(root: Path, cfg: LensConfig) -> list[tuple[str, int]]:
    return [(b, len(v)) for b, v in batches(root, cfg).items() if not (root / batch_path(b)).exists()]


def run_scene_stats(root: Path, cfg: LensConfig, embed: Embed) -> tuple[int, int, int]:
    """Write corpus/stats/scenes.json and taxonomy/scene_proposals.yaml. Returns (archetypes, other
    shots, proposals)."""
    from lens.schemas.taxonomy import Taxonomy
    from lens.synth import load_corpus
    from lens.synth.stats import stat

    s = cfg.synth
    weight_of = {v.record.video: v.weight for v in load_corpus(root, cfg)}
    inputs = sorted((root / "corpus" / "scenes").glob("b*.json"))
    prov = Provenance(
        tool_version=__version__,
        stage=STATS_STAGE,
        annotator=Annotator.CODE,
        input_hash=cache_key(
            {"synth": s.model_dump(mode="json"), "inputs": [sha256_file(p) for p in inputs]}
        ),
        created_at=datetime.now(UTC),
    )

    def mk(values: list[float], weights: list[float], videos: list[str]) -> Stat:
        return stat(values, weights, videos, min_n=s.min_n, bootstrap=s.bootstrap, ci=s.ci, seed=s.seed)

    out = scene_stats(root, cfg, weight_of, mk, prov)
    path = root / "corpus" / "stats" / "scenes.json"
    path.write_text(out.model_dump_json(indent=1) + "\n", "utf-8")
    tax = Taxonomy.model_validate(yaml.safe_load((root / "taxonomy" / "v1.yaml").read_text("utf-8")))
    n = write_scene_proposals(root, cfg, list(tax.scene_archetype), embed)
    return len(out.archetypes), out.other_shots, n
