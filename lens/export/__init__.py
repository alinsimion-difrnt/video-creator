"""S10 exports (BUILD_PLAN 8.6): motion tokens, sound/pacing/voice specs, patterns, scene archetypes and
the `premium-explainer-patterns` skill pack, from the S9 stats and the approved A3 cards.

Brand-free by construction and by check: no video ids or examples are copied, and `leaks()` refuses any
export that names a corpus brand, a corpus video id or quotes corpus on-screen text.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from lens import __version__
from lens.hashing import cache_key, sha256_file
from lens.schemas import LensConfig
from lens.schemas.cards import ArchetypeCard, PatternCard
from lens.schemas.common import Annotator, Provenance
from lens.schemas.corpus import MotionStats, PacingStats, SoundStats, Stat
from lens.schemas.exports import (
    ArchetypesExport,
    EasingClass,
    ExportArchetype,
    ExportPattern,
    LoudnessSpec,
    MotionTokens,
    PacingSpec,
    PatternsExport,
    Range,
    SoundSpec,
    SpringPreset,
    VoiceSpec,
)
from lens.schemas.record import RecordFile
from lens.schemas.scenes import ScenesFile
from lens.validate import load_sources

STAGE = "s10_export"
SKILL_NAME = "premium-explainer-patterns"
SKILL_DESCRIPTION = (
    "Build premium SaaS explainer scenes from measured patterns. Use when storyboarding or building an "
    "explainer in HyperFrames/GSAP or Remotion: pick a scene archetype per beat, fill its slots, animate "
    "with the listed patterns, and take timing, easing, springs, sound cues, pacing and voice from the "
    "bundled specs."
)


class ExportError(RuntimeError):
    pass


def rng(s: Stat | None) -> Range:
    if s is None:
        return Range(median=None, low=None, high=None, n=0, videos=0)
    return Range(median=s.median, low=s.p25, high=s.p75, n=s.n, videos=s.videos)


def _load[T](model: type[T], path: Path) -> T:
    return model.model_validate_json(path.read_text("utf-8"))  # type: ignore[attr-defined, no-any-return]


def motion_tokens(m: MotionStats, prov: Provenance) -> MotionTokens:
    easing = {}
    for cls, share in m.easing_mix.items():
        css = "linear" if cls == "linear" else m.bezier_by_class.get(cls, "ease")
        easing[cls] = EasingClass(gsap=m.ease_by_class.get(cls, "none"), css=css, share=share)
    total = sum(c.n for c in m.springs) or 1
    springs = sorted(m.springs, key=lambda c: c.zeta.median or 0.0)
    named: list[SpringPreset] = []
    rest = springs
    if springs and (springs[0].zeta.median or 1.0) < 0.5:
        rest = springs[1:]
        c = springs[0]
        named.append(
            SpringPreset(
                name="bouncy",
                remotion=c.remotion,
                zeta=c.zeta.median,
                settle_ms=rng(c.settle_ms),
                share=round(c.n / total, 4),
            )
        )
    for i, c in enumerate(sorted(rest, key=lambda c: c.settle_ms.median or 0.0)):
        name = ["snappy", "smooth"][i] if i < 2 else f"smooth_{i}"
        named.append(
            SpringPreset(
                name=name,
                remotion=c.remotion,
                zeta=c.zeta.median,
                settle_ms=rng(c.settle_ms),
                share=round(c.n / total, 4),
            )
        )
    word, together = m.stagger_ms_by_unit.get("word"), m.stagger_ms_by_unit.get("all")
    n_word, n_all = (word.n if word else 0), (together.n if together else 0)
    return MotionTokens(
        provenance=prov,
        duration_ms_by_role={k: rng(v) for k, v in m.duration_ms_by_role.items() if v.n},
        duration_ms_by_change={k: rng(v) for k, v in m.duration_ms_by_change.items() if v.n},
        easing=easing,
        easing_by_role=m.easing_by_role,
        springs=named,
        overshoot_share=m.overshoot_share,
        overshoot_pct=rng(m.overshoot_pct),
        word_stagger_ms=rng(word),
        all_at_once_share=round(n_all / (n_all + n_word), 4) if n_all + n_word else None,
    )


def sound_spec(s: SoundStats, cfg: LensConfig, prov: Provenance) -> SoundSpec:
    targets = [
        LoudnessSpec(
            destination=d,
            min_lufs=t.min_lufs,
            max_lufs=t.max_lufs,
            max_true_peak_dbtp=t.max_true_peak_dbtp,
            source=t.source,
        )
        for d, t in cfg.targets.loudness.items()
    ]
    return SoundSpec(
        provenance=prov,
        sfx_per_min=rng(s.sfx_per_min),
        sfx_mix=s.sfx_label_mix,
        sfx_offset_ms_to_reveal={k: rng(v) for k, v in s.reveal_offset_ms_by_label.items() if v.n},
        sfx_on_beat_share=s.sfx_on_beat_share,
        corpus_lufs=rng(s.integrated_lufs),
        corpus_true_peak_dbtp=rng(s.true_peak_dbtp),
        corpus_lra_lu=rng(s.lra_lu),
        ducking_db=rng(s.ducking_db),
        targets=targets,
    )


def pacing_spec(p: PacingStats, scenes: ScenesFile, held: set[str], prov: Provenance) -> PacingSpec:
    return PacingSpec(
        provenance=prov,
        shot_s=rng(p.shot_s),
        shot_s_by_format={k: rng(v) for k, v in p.shot_s_by_format.items()},
        duration_s_by_format={k: rng(v) for k, v in p.duration_s_by_format.items()},
        scene_s_by_archetype={a.id: rng(a.duration_s) for a in scenes.archetypes if a.id not in held},
        pace_cv=rng(p.pace_cv),
        cuts_on_beat_share=rng(p.cuts_on_beat_share),
        time_to_first_ui_s=rng(p.time_to_first_ui_s),
        caption_words_per_group=rng(p.caption_words_per_group),
    )


def _fmt(r: Range, unit: str, digits: int = 0) -> str:
    if r.median is None or r.low is None or r.high is None:
        return "not measured"
    return f"{r.low:.{digits}f}-{r.high:.{digits}f} {unit} (typical {r.median:.{digits}f})"


def voice_spec(p: PacingStats, prov: Provenance) -> VoiceSpec:
    wpm, art, pause = rng(p.wpm), rng(p.articulation_wpm), rng(p.pause_mean_ms)
    p90, pitch, energy = rng(p.pause_p90_ms), rng(p.pitch_std_semitones), rng(p.energy_std_db)
    brief = [
        f"Overall pace {_fmt(wpm, 'words per minute')}, pauses included.",
        f"Speaking rate between pauses {_fmt(art, 'words per minute')}.",
        f"Pauses average {_fmt(pause, 'ms')}; the longest tenth reach {_fmt(p90, 'ms')}.",
        f"Pitch moves by {_fmt(pitch, 'semitones', 1)} (standard deviation): expressive, not flat.",
        f"Loudness varies by {_fmt(energy, 'dB', 1)} across the read.",
    ]
    return VoiceSpec(
        provenance=prov,
        wpm=wpm,
        articulation_wpm=art,
        pause_mean_ms=pause,
        pause_p90_ms=p90,
        pause_length_mix=p.pause_length_mix,
        pitch_std_semitones=pitch,
        energy_std_db=energy,
        phrase_rate_cv=rng(p.phrase_rate_cv),
        brief=brief,
    )


def export_pattern(c: PatternCard) -> ExportPattern:
    n = c.numbers
    return ExportPattern(
        id=c.id,
        name=c.name,
        summary=c.summary,
        when_to_use=c.when_to_use,
        avoid_when=c.avoid_when,
        steps=c.steps,
        build=c.build,
        sound=c.sound,
        why_premium=c.why_premium,
        duration_ms=rng(n.duration_ms),
        easing_mix=n.easing_mix,
        change_mix=n.change_mix,
        sfx_offset_ms=rng(n.sfx_offset_ms),
        videos=n.videos,
        caveats=c.caveats,
    )


def export_archetype(c: ArchetypeCard) -> ExportArchetype:
    n = c.numbers
    return ExportArchetype(
        id=c.id,
        name=c.name,
        summary=c.summary,
        when_to_use=c.when_to_use,
        slots=c.slots,
        steps=c.steps,
        patterns=c.patterns,
        build=c.build,
        sound=c.sound,
        duration_s=rng(n.duration_s),
        first_motion_s=rng(n.first_motion_s),
        events_per_scene=rng(n.events_per_shot),
        way_in=n.transition_mix,
        beats=n.beat_mix,
        sfx_cues_s={k: rng(v) for k, v in n.sfx_offset_s_by_label.items() if v.n},
        videos=n.videos,
        caveats=c.caveats,
    )


# --- leak check -----------------------------------------------------------------------------------


def forbidden(root: Path, cfg: LensConfig) -> list[str]:
    """Corpus brands, corpus video ids and corpus on-screen text (4+ words) that exports must not hold."""
    tiers = cfg.synth.weights.tier
    out: set[str] = set()
    for s in load_sources(root):
        if tiers.get(s.tier, 0.0) > 0:
            out.add(s.id)
            if len(s.brand) >= 3:
                out.add(s.brand)
    for p in sorted((root / "videos").glob("*/record.json")):
        rec = RecordFile.model_validate_json(p.read_text("utf-8"))
        if tiers.get(rec.tier, 0.0) <= 0:
            continue
        for sh in rec.shots:
            for t in sh.annotation.on_screen_text if sh.annotation else []:
                if len(t.split()) >= 4:
                    out.add(t.strip())
    return sorted(out)


def leaks(texts: dict[str, str], bad: list[str], word_brands: list[str] | None = None) -> list[str]:
    """Each forbidden string found in an export, case-insensitively; brands that are also ordinary words
    ("linear", "cursor") count only as the capitalised name, and not where it starts a sentence or item."""
    words = set(word_brands or [])
    found = []
    for name, text in texts.items():
        low = text.lower()
        for b in bad:
            if b in words:
                hits = [
                    m
                    for m in re.finditer(r"(?<![A-Za-z0-9])" + re.escape(b) + r"(?![A-Za-z0-9])", text)
                    if not _sentence_start(text, m.start())
                ]
                if hits:
                    found.append(f"{name}: {b!r}")
                continue
            pat = r"(?<![a-z0-9])" + re.escape(b.lower()) + r"(?![a-z0-9])"
            if re.search(pat, low):
                found.append(f"{name}: {b!r}")
    return found


def _sentence_start(text: str, i: int) -> bool:
    j = i - 1
    while j >= 0 and text[j] in ' \t*`"[#':
        j -= 1
    return j < 0 or text[j] in ".!?:\n-"


# --- skill pack ----------------------------------------------------------------------------------


def _r(r: Range, unit: str, digits: int = 0) -> str:
    return _fmt(r, unit, digits) + (f", {r.videos} videos" if r.videos else "")


def pattern_md(p: ExportPattern) -> str:
    lines = [
        f"# {p.name}",
        "",
        f"`{p.id}`",
        "",
        p.summary,
        "",
        "## When to use",
        *[f"- {x}" for x in p.when_to_use],
    ]
    if p.avoid_when:
        lines += ["", "## Avoid when", *[f"- {x}" for x in p.avoid_when]]
    lines += [
        "",
        "## Build",
        *[f"{i}. {x}" for i, x in enumerate(p.steps, 1)],
        "",
        f"- GSAP / HyperFrames: {p.build.gsap}",
        f"- Remotion: {p.build.remotion}",
        "",
        "## Measured in premium explainers",
        f"- Duration: {_r(p.duration_ms, 'ms')}",
        "- Easing: "
        + (", ".join(f"{k.replace('_', ' ')} {v:.0%}" for k, v in list(p.easing_mix.items())[:4]) or "n/a"),
        "- Changes: "
        + (", ".join(f"{k.replace('_', ' ')} {v:.0%}" for k, v in list(p.change_mix.items())[:4]) or "n/a"),
        f"- Sound offset to the landing: {_r(p.sfx_offset_ms, 'ms')}",
        "",
        "## Sound",
        p.sound,
        "",
        "## Why it reads as premium",
        p.why_premium,
    ]
    if p.caveats:
        lines += ["", "## Caveats", *[f"- {x}" for x in p.caveats]]
    return "\n".join(lines) + "\n"


def archetype_md(a: ExportArchetype) -> str:
    lines = [
        f"# {a.name}",
        "",
        f"`{a.id}`",
        "",
        a.summary,
        "",
        "## When to use",
        *[f"- {x}" for x in a.when_to_use],
        "",
        "## Slots (what you fill in)",
        *[f"- `{s.name}`{'' if s.required else ' (optional)'}: {s.what}" for s in a.slots],
        "",
        "## The scene, beat by beat",
        *[f"{i}. {x}" for i, x in enumerate(a.steps, 1)],
        "",
        "Patterns: " + ", ".join(f"[{p}](../patterns/{p}.md)" for p in a.patterns),
        "",
        f"- GSAP / HyperFrames: {a.build.gsap}",
        f"- Remotion: {a.build.remotion}",
        "",
        "## Measured in premium explainers",
        f"- Scene length: {_r(a.duration_s, 's', 1)}",
        f"- First motion after the scene starts: {_r(a.first_motion_s, 's', 1)}",
        f"- Motion events per scene: {_r(a.events_per_scene, 'events')}",
        "- Way in: "
        + (", ".join(f"{k.replace('_', ' ')} {v:.0%}" for k, v in list(a.way_in.items())[:3]) or "n/a"),
        *[
            f"- {k.replace('_', ' ')} sound: {_r(v, 's', 1)} after the scene starts"
            for k, v in a.sfx_cues_s.items()
        ],
        "",
        "## Sound",
        a.sound,
    ]
    if a.caveats:
        lines += ["", "## Caveats", *[f"- {x}" for x in a.caveats]]
    return "\n".join(lines) + "\n"


def skill_md(arch: ArchetypesExport, pats: PatternsExport) -> str:
    a_list = "\n".join(
        f"- [{a.name}](references/archetypes/{a.id}.md) (`{a.id}`): {a.summary}" for a in arch.archetypes
    )
    p_list = "\n".join(f"- [{p.name}](references/patterns/{p.id}.md) (`{p.id}`)" for p in pats.patterns)
    return f"""---
name: {SKILL_NAME}
description: {SKILL_DESCRIPTION}
---

# Premium explainer patterns

Measured from premium SaaS explainers by `lens` (explainer-video-creator). Timing numbers are
code-measured medians with their typical range; the words are written from those measurements.

## How to use
1. **Storyboard:** give each beat of the script one scene archetype below. Fill its slots with your
   content; keep scene lengths inside the archetype's measured range (`pacing.json` has them all).
2. **Animate:** use the archetype's patterns. Take durations from `motion-tokens.json`
   (`duration_ms_by_role`, `duration_ms_by_change`), easing from `easing` (GSAP name and CSS
   cubic-bezier per class) and springs from `springs` (Remotion configs).
3. **Sound:** place SFX with `sound-spec.json` (`sfx_offset_ms_to_reveal`: onset relative to the
   motion landing) and mix to a destination in `targets`.
4. **Voice:** brief the voice with `voice-spec.json` (`brief` lists plain instructions).

## Scene archetypes
{a_list}

## Patterns
{p_list}

## Files
`motion-tokens.json`, `sound-spec.json`, `pacing.json`, `voice-spec.json`, `archetypes.json`,
`patterns.json` (alongside this skill in `data/`), `references/` (one page per archetype and pattern).
"""


# --- run --------------------------------------------------------------------------------------------


def run_export(root: Path, cfg: LensConfig) -> list[Path]:
    stats = root / "corpus" / "stats"
    inputs = sorted(
        [
            *stats.glob("*.json"),
            *(root / "corpus" / "patterns").glob("*.json"),
            *(root / "corpus" / "archetypes").glob("*.json"),
        ]
    )
    prov = Provenance(
        tool_version=__version__,
        stage=STAGE,
        annotator=Annotator.CODE,
        input_hash=cache_key({p.relative_to(root).as_posix(): sha256_file(p) for p in inputs}),
        created_at=datetime.now(UTC),
    )
    held_p, held_a = set(cfg.synth.g4_hold), set(cfg.synth.g4_hold_archetypes)
    scenes = _load(ScenesFile, stats / "scenes.json")
    pattern_cards = [_load(PatternCard, p) for p in sorted((root / "corpus" / "patterns").glob("*.json"))]
    arch_cards = [_load(ArchetypeCard, p) for p in sorted((root / "corpus" / "archetypes").glob("*.json"))]
    pats = PatternsExport(
        provenance=prov, patterns=[export_pattern(c) for c in pattern_cards if c.id not in held_p]
    )
    kept = {p.id for p in pats.patterns}
    arch = ArchetypesExport(
        provenance=prov,
        archetypes=[
            export_archetype(c).model_copy(update={"patterns": [p for p in c.patterns if p in kept]})
            for c in arch_cards
            if c.id not in held_a
        ],
    )
    pacing = _load(PacingStats, stats / "pacing.json")
    files = {
        "motion-tokens.json": motion_tokens(_load(MotionStats, stats / "motion.json"), prov),
        "sound-spec.json": sound_spec(_load(SoundStats, stats / "sound.json"), cfg, prov),
        "pacing.json": pacing_spec(pacing, scenes, held_a, prov),
        "voice-spec.json": voice_spec(pacing, prov),
        "archetypes.json": arch,
        "patterns.json": pats,
    }
    texts = {name: m.model_dump_json(indent=1) + "\n" for name, m in files.items()}
    skill = Path("skill") / SKILL_NAME
    texts[str(skill / "SKILL.md")] = skill_md(arch, pats)
    for p in pats.patterns:
        texts[str(skill / "references" / "patterns" / f"{p.id}.md")] = pattern_md(p)
    for a in arch.archetypes:
        texts[str(skill / "references" / "archetypes" / f"{a.id}.md")] = archetype_md(a)
    for name in files:
        texts[str(skill / "data" / name)] = texts[name]
    bad = leaks(texts, forbidden(root, cfg), cfg.synth.export_word_brands)
    if bad:
        raise ExportError("exports would name corpus brands, ids or text:\n  " + "\n  ".join(bad[:40]))
    out_dir = root / "exports"
    written = []
    old = out_dir / skill
    if old.exists():
        for f in sorted(old.rglob("*"), reverse=True):
            f.unlink() if f.is_file() else f.rmdir()
    for name, text in texts.items():
        path = out_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, "utf-8")
        written.append(path)
    return written
