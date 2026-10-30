"""A3 pattern cards: the writer's brief (`lens status --card <pid>`) and the Markdown rendering.

The brief carries the pattern's S9 stats (the only numbers a card may use) and what the annotators said
about its best-weighted events, in their own words (descriptions, why premium, build hints, elements).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lens import __version__
from lens.hashing import cache_key
from lens.packets import skill_id
from lens.schemas import LensConfig
from lens.schemas.cards import ArchetypeCard, PatternCard
from lens.schemas.common import Annotator, Provenance
from lens.schemas.corpus import PatternsFile, Stat
from lens.schemas.record import RecordFile
from lens.schemas.scenes import ScenesFile

SKILL = "write-pattern-cards"
STAGE = "a3_pattern_cards"


def card_path(pid: str) -> str:
    return f"corpus/patterns/{pid}.json"


def _patterns(root: Path) -> PatternsFile:
    return PatternsFile.model_validate_json((root / "corpus" / "stats" / "patterns.json").read_text("utf-8"))


def card_brief(root: Path, cfg: LensConfig, pid: str) -> dict[str, Any]:
    stats = next((p for p in _patterns(root).patterns if p.id == pid), None)
    if stats is None:
        raise KeyError(f"{pid} has no stats in corpus/stats/patterns.json (run `lens synth`)")
    records: dict[str, RecordFile] = {}
    members = []
    want = [(x.video, x.event) for x in stats.examples]
    from lens.synth import g4_assignments

    assigned = g4_assignments(root)
    tiers = cfg.synth.weights.tier
    for p in sorted((root / "videos").glob("*/record.json")):
        rec = RecordFile.model_validate_json(p.read_text("utf-8"))
        if tiers.get(rec.tier, 0.0) > 0:  # the corpus only: our own videos never describe a pattern
            records[rec.video] = rec
    # the best-weighted examples first, then other events of the pattern, up to the limit
    extra = [
        (r.video, e.id)
        for r in records.values()
        for e in r.events
        if e.status == "annotated"
        and e.pattern is not None
        and assigned.get(f"{r.video}/{e.id}", e.pattern.id) == pid
        and (r.video, e.id) not in want
    ]
    for video, eid in (want + extra)[: cfg.synth.card_members]:
        found = records.get(video)
        ev = next((e for e in found.events if e.id == eid), None) if found else None
        if found is None or ev is None or ev.pattern is None:
            continue
        members.append(
            {
                "video": video,
                "event": eid,
                "format": found.format,
                "description": ev.pattern.description,
                "why_premium": ev.pattern.why_premium,
                "build_hint": ev.build_hint.model_dump() if ev.build_hint else None,
                "elements": [
                    {"label": el.label, "role": el.role, "change_types": el.change_types}
                    for el in ev.elements
                ],
            }
        )
    return {
        "pattern": pid,
        "skill": SKILL,
        "output": card_path(pid),
        "numbers": stats.model_dump(mode="json"),
        "members": members,
        "provenance": Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CLAUDE_CODE,
            skill=skill_id(root, SKILL),
            input_hash=cache_key({"numbers": stats.model_dump(mode="json"), "members": members}),
            created_at=datetime.now(UTC),
        ).model_dump(mode="json"),
    }


def _ms(s: Stat) -> str:
    if s.median is None:
        return "not measured"
    ci = f", 90% interval {s.ci[0]:.0f} to {s.ci[1]:.0f}" if s.ci else ""
    return f"median {s.median:.0f} ms{ci} (n={s.n}, {s.videos} videos)"


def _mix(m: dict[str, float], k: int = 4) -> str:
    return (
        ", ".join(f"{label.replace('_', ' ')} {share:.0%}" for label, share in list(m.items())[:k]) or "none"
    )


def render_md(card: PatternCard) -> str:
    n = card.numbers
    lines = [
        f"# {card.name}",
        "",
        f"`{card.id}` · {n.events} events in {n.videos} videos",
        "",
        card.summary,
        "",
        "## When to use",
        *[f"- {x}" for x in card.when_to_use],
    ]
    if card.avoid_when:
        lines += ["", "## Avoid when", *[f"- {x}" for x in card.avoid_when]]
    lines += [
        "",
        "## How to build it",
        *[f"{i}. {x}" for i, x in enumerate(card.steps, 1)],
        "",
        f"- **GSAP / HyperFrames:** {card.build.gsap}",
        f"- **Remotion:** {card.build.remotion}",
        "",
        "## Measured",
        f"- Duration: {_ms(n.duration_ms)}",
        f"- Easing: {_mix(n.easing_mix)}",
        f"- Changes: {_mix(n.change_mix)}",
        f"- Elements: {_mix(n.role_mix)}",
        f"- Sound: {_mix(n.sfx_label_mix)}; offset to the landing {_ms(n.sfx_offset_ms)}",
        "",
        "## Sound",
        card.sound,
        "",
        "## Why it reads as premium",
        card.why_premium,
        "",
        "## Examples",
        *[
            f"- `{x.video}` {x.event}" + (f" (video score {x.score:.0f}/5)" if x.score else "")
            for x in card.examples
        ],
    ]
    if card.caveats:
        lines += ["", "## Caveats", *[f"- {x}" for x in card.caveats]]
    return "\n".join(lines) + "\n"


def render_all(root: Path) -> list[Path]:
    out = []
    for p in sorted((root / "corpus" / "patterns").glob("*.json")):
        card = PatternCard.model_validate_json(p.read_text("utf-8"))
        md = p.with_suffix(".md")
        md.write_text(render_md(card), "utf-8")
        out.append(md)
    return out


def card_numbers_errors(root: Path, card: PatternCard) -> list[str]:
    """The card's numbers must be the S9 stats verbatim, and its examples a subset of them."""
    stats = next((p for p in _patterns(root).patterns if p.id == card.id), None)
    if stats is None:
        return [f"{card.id} has no stats in corpus/stats/patterns.json"]
    errors = []
    if json.dumps(card.numbers.model_dump(mode="json"), sort_keys=True) != json.dumps(
        stats.model_dump(mode="json"), sort_keys=True
    ):
        errors.append("numbers differ from corpus/stats/patterns.json (copy them verbatim from the brief)")
    known = {(x.video, x.event) for x in stats.examples}
    for x in card.examples:
        if (x.video, x.event) not in known:
            errors.append(f"example {x.video}/{x.event} is not one of the pattern's examples")
    return errors


def pending_cards(root: Path, cfg: LensConfig) -> list[tuple[str, str]]:
    """(pattern id, "missing" | "stale"): cards to (re)write. Stale = the brief's inputs changed."""
    out = []
    for stats in _patterns(root).patterns:
        path = root / card_path(stats.id)
        if not path.exists():
            out.append((stats.id, "missing"))
            continue
        card = PatternCard.model_validate_json(path.read_text("utf-8"))
        if card.provenance.input_hash != card_brief(root, cfg, stats.id)["provenance"]["input_hash"]:
            out.append((stats.id, "stale"))
    return out


# --- scene archetype cards --------------------------------------------------------------------------

ARCHETYPE_SKILL = "write-archetype-cards"


def archetype_path(aid: str) -> str:
    return f"corpus/archetypes/{aid}.json"


def _scenes(root: Path) -> ScenesFile:
    return ScenesFile.model_validate_json((root / "corpus" / "stats" / "scenes.json").read_text("utf-8"))


def archetype_brief(root: Path, cfg: LensConfig, aid: str) -> dict[str, Any]:
    from lens.synth.scenes import load_assignments

    stats = next((a for a in _scenes(root).archetypes if a.id == aid), None)
    if stats is None:
        raise KeyError(f"{aid} has no stats in corpus/stats/scenes.json (run `lens scenes`)")
    shots = [k for k, (a, _) in sorted(load_assignments(root).items()) if a == aid]
    want = [(x.video, x.shot) for x in stats.examples]
    order = want + [k for k in shots if k not in want]
    members = []
    for video, sid in order[: cfg.synth.card_members]:
        rec = RecordFile.model_validate_json((root / "videos" / video / "record.json").read_text("utf-8"))
        s = next((x for x in rec.shots if x.id == sid), None)
        if s is None or s.annotation is None:
            continue
        a = s.annotation
        members.append(
            {
                "video": video,
                "shot": sid,
                "format": rec.format,
                "shot_type": a.shot_type,
                "composition": a.composition,
                "what_happens": a.what_happens,
                "build_rebuild": a.build_rebuild,
                "patterns": [e.pattern.id for e in rec.events if e.shot == sid and e.pattern],
            }
        )
    patterns = sorted(p.stem for p in (root / "corpus" / "patterns").glob("*.json"))
    return {
        "archetype": aid,
        "skill": ARCHETYPE_SKILL,
        "output": archetype_path(aid),
        "numbers": stats.model_dump(mode="json"),
        "members": members,
        "pattern_cards": patterns,
        "provenance": Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CLAUDE_CODE,
            skill=skill_id(root, ARCHETYPE_SKILL),
            input_hash=cache_key({"numbers": stats.model_dump(mode="json"), "members": members}),
            created_at=datetime.now(UTC),
        ).model_dump(mode="json"),
    }


def archetype_errors(root: Path, card: ArchetypeCard) -> list[str]:
    stats = next((a for a in _scenes(root).archetypes if a.id == card.id), None)
    if stats is None:
        return [f"{card.id} has no stats in corpus/stats/scenes.json"]
    errors = []
    if json.dumps(card.numbers.model_dump(mode="json"), sort_keys=True) != json.dumps(
        stats.model_dump(mode="json"), sort_keys=True
    ):
        errors.append("numbers differ from corpus/stats/scenes.json (copy them verbatim from the brief)")
    known = {(x.video, x.shot) for x in stats.examples}
    errors += [
        f"example {x.video}/{x.shot} is not one of the archetype's examples"
        for x in card.examples
        if (x.video, x.shot) not in known
    ]
    cards = {p.stem for p in (root / "corpus" / "patterns").glob("*.json")}
    errors += [f"pattern {p!r} has no card" for p in card.patterns if p not in cards]
    return errors


def _s(st: Stat, unit: str = "s") -> str:
    if st.median is None:
        return "not measured"
    ci = f", 90% interval {st.ci[0]:.1f} to {st.ci[1]:.1f}" if st.ci else ""
    return f"median {st.median:.1f} {unit}{ci} (n={st.n}, {st.videos} videos)"


def render_archetype_md(card: ArchetypeCard) -> str:
    n = card.numbers
    cues = [
        f"- {label.replace('_', ' ')}: {_s(st)} after the scene starts"
        for label, st in n.sfx_offset_s_by_label.items()
        if st.n
    ]
    lines = [
        f"# {card.name}",
        "",
        f"`{card.id}` · {n.shots} shots in {n.videos} videos",
        "",
        card.summary,
        "",
        "## When to use",
        *[f"- {x}" for x in card.when_to_use],
        "",
        "## What you fill in",
        *[f"- **{s.name}**{'' if s.required else ' (optional)'}: {s.what}" for s in card.slots],
        "",
        "## The scene, beat by beat",
        *[f"{i}. {x}" for i, x in enumerate(card.steps, 1)],
        "",
        "Patterns: " + ", ".join(f"[{p}](../patterns/{p}.md)" for p in card.patterns),
        "",
        f"- **GSAP / HyperFrames:** {card.build.gsap}",
        f"- **Remotion:** {card.build.remotion}",
        "",
        "## Measured",
        f"- Scene length: {_s(n.duration_s)}",
        f"- Motion events per scene: {_s(n.events_per_shot, 'events')}",
        f"- First motion: {_s(n.first_motion_s)} after the scene starts",
        f"- Way in: {_mix(n.transition_mix)}",
        f"- Story beat: {_mix(n.beat_mix)}",
        f"- Sound: {_mix(n.sfx_label_mix)}",
        "",
        "## Sound cues",
        card.sound,
        *cues,
        "",
        "## Examples",
        *[
            f"- `{x.video}` {x.shot}" + (f" (video score {x.score:.0f}/5)" if x.score else "")
            for x in card.examples
        ],
    ]
    if card.caveats:
        lines += ["", "## Caveats", *[f"- {x}" for x in card.caveats]]
    return "\n".join(lines) + "\n"


def render_archetypes(root: Path) -> list[Path]:
    out = []
    for p in sorted((root / "corpus" / "archetypes").glob("*.json")):
        card = ArchetypeCard.model_validate_json(p.read_text("utf-8"))
        md = p.with_suffix(".md")
        md.write_text(render_archetype_md(card), "utf-8")
        out.append(md)
    return out
