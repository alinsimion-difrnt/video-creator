"""Stage registry: every stage declares what it reads and the exact paths it writes.

This module is the source of truth for the strict DAG (BUILD_PLAN section 2.9). It is
used by `lens dag --check` and by the `.claude/hooks/guard_paths.py` PreToolUse hook,
so it must stay standard-library only.

Path templates are repo-relative POSIX paths:
- `{name}` matches one path segment, or part of one (e.g. `{eid}.a2.json`);
- `*` matches within one segment, `**` matches any number of segments.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from functools import cache


class Runner(StrEnum):
    CODE = "code"
    CLAUDE = "claude"


@dataclass(frozen=True)
class Stage:
    id: str
    runner: Runner
    after: tuple[str, ...]
    reads: tuple[str, ...]
    writes: tuple[str, ...]
    milestone: str
    summary: str


# Paths owned by humans or by the repo itself, not by any stage.
EXTERNAL_INPUTS: tuple[str, ...] = (
    "sources/**",
    "taxonomy/v1.yaml",
    "config/**",
    "gold/**",
    ".claude/skills/**",
    "tests/fixtures/acme-v1/answer-key.json",  # our own render's ground truth (lens eval)
    "brands/{brand}/**",  # a shared brand hand-off (tokens, rules, SVG logos) named by the brief, ADR 0022
    "data/create/{project}/footage/raw/**",  # Robert's own takes (presenter projects, ADR 0025)
    "projects/{project}/cuts-approved.yaml",  # Robert's cut decisions (the human gate between F3 and F4)
    "projects/{project}/cut-notes.yaml",  # Robert's own cut instructions (start, end, keep, cut; ADR 0030)
    "projects/{project}/edits.yaml",  # Robert's crops, zoom changes and notes from the edit page
    "projects/{project}/layout.yaml",  # where the presenter is per scene (full, corner bubble, off)
    "projects/{project}/overlays.yaml",  # graphics over the presenter's own video, on their words
    "projects/{project}/reel.yaml",  # the whole presenter video in one composition (create reel)
    "projects/{project}/assets/**",  # Robert's own pictures for reel props (a fish PNG), never committed
    "projects/{project}/panel/**",  # the bespoke panel page Claude writes per video (create panel, ADR 0034)
    "data/create/{project}/panel/assets/**",  # its logos, photos, icons, fonts (third-party: never committed)
)

STAGES: tuple[Stage, ...] = (
    Stage(
        "s1_ingest",
        Runner.CODE,
        (),
        ("sources/sources.yaml",),
        ("data/media/{video}/original.{ext}", "data/state/{video}/s1_ingest.json"),
        "M1",
        "Fetch sources into the local mirror (https, r2://inbox/, file://)",
    ),
    Stage(
        "s2_normalize",
        Runner.CODE,
        ("s1_ingest",),
        ("data/media/{video}/original.{ext}",),
        (
            "data/media/{video}/proxy.mp4",
            "data/media/{video}/audio.wav",
            "data/frames/{video}/base/**",
            "videos/{video}/meta.json",
            "videos/{video}/palette.json",
            "data/state/{video}/s2_normalize.json",
        ),
        "M1",
        "ffprobe, proxy at native fps, audio, 2 fps base frames, palette",
    ),
    Stage(
        "s3_signals",
        Runner.CODE,
        ("s2_normalize",),
        ("data/media/{video}/proxy.mp4", "data/media/{video}/audio.wav", "data/frames/{video}/base/**"),
        (
            "data/signals/{video}/**",
            "videos/{video}/signals.summary.json",
            "data/state/{video}/s3_signals.json",
        ),
        "M2",
        "Cuts, transitions, events, camera, audio, SFX candidates, rhythm metrics",
    ),
    Stage(
        "s4_evidence",
        Runner.CODE,
        ("s3_signals",),
        ("data/media/{video}/proxy.mp4", "data/signals/{video}/**"),
        ("data/evidence/{video}/**", "data/state/{video}/s4_evidence.json"),
        "M3",
        "Bursts, filmstrips, candidate boxes, set-of-marks, spectrograms, contact sheets",
    ),
    Stage(
        "s5_packets",
        Runner.CODE,
        ("s4_evidence",),
        (
            "data/evidence/{video}/**",
            "data/signals/{video}/**",
            "videos/{video}/signals.summary.json",
            "videos/{video}/palette.json",
        ),
        ("data/packets/{video}/**", "packets/{video}/manifest.json", "data/state/{video}/s5_packets.json"),
        "M3",
        "Annotation packets within image budgets, plus event triage",
    ),
    Stage(
        "a0_annotate_batch",
        Runner.CLAUDE,
        ("s5_packets",),
        ("packets/{video}/manifest.json",),
        ("runs/{run_id}/summary.md", "runs/{run_id}/cost.json"),
        "M5",
        "Orchestrator: pick pending tasks, dispatch subagents, summarise",
    ),
    Stage(
        "a1_annotate_video",
        Runner.CLAUDE,
        ("s5_packets",),
        ("data/packets/{video}/pass1/**", "taxonomy/v1.yaml"),
        ("videos/{video}/a1.json", "videos/{video}/a1.{part}.json", "runs/{run_id}/progress/a1-{task}.json"),
        "M5",
        "Structure, beats, scores per video",
    ),
    Stage(
        "a2_annotate_event",
        Runner.CLAUDE,
        ("s5_packets",),
        ("data/packets/{video}/events/**", "taxonomy/v1.yaml"),
        (
            "videos/{video}/events/{eid}.a2.json",
            "runs/{run_id}/progress/a2-{task}.json",
            "runs/{run_id}/videos/{video}/events/{eid}.a2.json",  # blind re-annotation for lens eval
        ),
        "M5",
        "Elements by box id, SFX review, pattern per event",
    ),
    Stage(
        "s7_measure",
        Runner.CODE,
        ("a2_annotate_event", "s4_evidence"),
        (
            "videos/{video}/events/{eid}.a2.json",
            "data/evidence/{video}/**",
            "data/media/{video}/proxy.mp4",
            "videos/{video}/signals.summary.json",
        ),
        ("videos/{video}/measure/{eid}.json",),
        "M4",
        "Track chosen boxes, fit bezier/spring, opacity, text stagger, SFX offset",
    ),
    Stage(
        "s8_reconcile",
        Runner.CODE,
        ("a1_annotate_video", "s7_measure", "s3_signals"),
        (
            "videos/{video}/a1.json",
            "videos/{video}/a1.{part}.json",
            "videos/{video}/measure/{eid}.json",
            "videos/{video}/events/{eid}.a2.json",
            "videos/{video}/signals.summary.json",
            "videos/{video}/meta.json",
            "videos/{video}/palette.json",
            "packets/{video}/manifest.json",
            "data/evidence/{video}/**",
            "data/packets/{video}/events/**",
        ),
        ("videos/{video}/record.json",),
        "M5",
        "Merge into record.json with per-field source",
    ),
    Stage(
        "s9_synth",
        Runner.CODE,
        ("s8_reconcile",),
        ("videos/{video}/record.json", "videos/{video}/signals.summary.json", "taxonomy/v1.yaml"),
        (
            "corpus/stats/motion.json",
            "corpus/stats/sound.json",
            "corpus/stats/pacing.json",
            "corpus/stats/patterns.json",
            "taxonomy/proposals.yaml",
        ),
        "M8",
        "Weighted stats and pattern clustering",
    ),
    Stage(
        "a3_scene_types",
        Runner.CLAUDE,
        ("s9_synth",),
        ("videos/{video}/record.json", "taxonomy/v1.yaml"),
        ("corpus/scenes/{batch}.json",),
        "M8",
        "Sort each annotated shot into a scene archetype (text only)",
    ),
    Stage(
        "s9_scene_stats",
        Runner.CODE,
        ("a3_scene_types",),
        ("corpus/scenes/{batch}.json", "videos/{video}/record.json", "videos/{video}/signals.summary.json"),
        ("corpus/stats/scenes.json", "taxonomy/scene_proposals.yaml"),
        "M8",
        "Code-measured stats per scene archetype; clusters of `other` scenes",
    ),
    Stage(
        "a3_pattern_cards",
        Runner.CLAUDE,
        ("s9_synth", "s9_scene_stats"),
        ("corpus/stats/**", "taxonomy/proposals.yaml", "taxonomy/scene_proposals.yaml"),
        ("corpus/patterns/**", "corpus/archetypes/**"),
        "M8",
        "Pattern cards and scene archetypes",
    ),
    Stage(
        "s10_export",
        Runner.CODE,
        ("a3_pattern_cards", "s9_synth"),
        ("corpus/stats/**", "corpus/patterns/**", "corpus/archetypes/**"),
        ("exports/**",),
        "M0/M8",
        "JSON Schemas (M0), tokens, specs, archetypes and skill pack (M8)",
    ),
    Stage(
        "s11_compare",
        Runner.CODE,
        ("s8_reconcile", "s9_synth"),
        ("videos/{video}/record.json", "videos/{video}/signals.summary.json", "corpus/stats/**"),
        ("reports/compare/{video}/metrics.json",),
        "M4.5/M9",
        "Placements against targets or the format cohort",
    ),
    Stage(
        "a4_compare_fixes",
        Runner.CLAUDE,
        ("s11_compare", "s10_export"),
        (
            "reports/compare/{video}/metrics.json",
            "videos/{video}/record.json",
            "videos/{video}/signals.summary.json",
            "exports/**",
        ),
        ("reports/compare/{video}/fixes.json",),
        "M9",
        "Top 10 fixes with evidence",
    ),
    Stage(
        "s12_report",
        Runner.CODE,
        ("s11_compare", "a4_compare_fixes"),
        ("reports/compare/{video}/metrics.json", "reports/compare/{video}/fixes.json"),
        ("reports/compare/{video}/{date}.html", "reports/compare/{video}/{date}.md"),
        "M4.5/M9",
        "Render the compare report",
    ),
    Stage(
        "s13_eval",
        Runner.CODE,
        ("s8_reconcile", "a2_annotate_event"),
        (
            "gold/**",
            "videos/{video}/record.json",
            "videos/{video}/events/{eid}.a2.json",
            "runs/{run_id}/videos/{video}/events/{eid}.a2.json",
            "tests/fixtures/acme-v1/answer-key.json",
            ".claude/skills/**",
            "taxonomy/v1.yaml",
        ),
        ("runs/eval/{hash}.json",),
        "M6",
        "Gold-set evaluation",
    ),
    # Phase 2 — Create (docs/phase2-plan.md section 4). `projects/{project}/` holds small text artifacts;
    # media goes to `data/create/{project}/` (never committed).
    Stage(
        "c1_brief",
        Runner.CLAUDE,
        (),
        ("brands/{brand}/**", "taxonomy/v1.yaml"),
        ("projects/{project}/brief.yaml",),
        "P2",
        "Short interview: product, audience, destination, length band, facts with sources, tone",
    ),
    Stage(
        "c2_script",
        Runner.CLAUDE,
        ("c1_brief", "s10_export"),
        ("projects/{project}/brief.yaml", "exports/voice-spec.json", "exports/pacing.json"),
        ("projects/{project}/script.yaml",),
        "P2",
        "One spoken line per scene with warm audio tags; every claim cites a brief fact",
    ),
    Stage(
        "c3_tokens",
        Runner.CODE,
        ("c1_brief",),
        ("brands/{brand}/**",),
        ("projects/{project}/tokens.json",),
        "P2",
        "Video tokens from the brand hand-off: contrast, glyph check, sizes for the destination's frame",
    ),
    Stage(
        "c4_voice",
        Runner.CODE,
        ("c2_script", "s10_export"),
        ("projects/{project}/script.yaml", "exports/voice-spec.json"),
        ("projects/{project}/voice.json", "data/create/{project}/voice/**"),
        "P1",
        "ElevenLabs with-timestamps per scene, N takes, keep the one closest to the voice spec",
    ),
    # Presenter footage (ADR 0025): Robert's own takes instead of a TTS voice (brief `voice: presenter`).
    Stage(
        "f1_ingest",
        Runner.CODE,
        (),
        ("data/create/{project}/footage/raw/**",),
        ("projects/{project}/footage.json", "data/create/{project}/footage/master/**"),
        "P7",
        "Conform each raw take: constant fps, SDR Rec.709, short GOP, PCM audio, 16 kHz wav",
    ),
    Stage(
        "f2_transcript",
        Runner.CODE,
        ("f1_ingest", "c1_brief"),
        (
            "projects/{project}/footage.json",
            "data/create/{project}/footage/master/**",
            "projects/{project}/brief.yaml",
        ),
        ("projects/{project}/transcript.json", "data/create/{project}/footage/stt/**"),
        "P7",
        "Every word, verbatim with fillers, on the masters' clocks (ElevenLabs Scribe; whisper fallback)",
    ),
    Stage(
        "f3_cuts",
        Runner.CODE,
        ("f2_transcript",),
        (
            "projects/{project}/transcript.json",
            "projects/{project}/footage.json",
            "projects/{project}/cut-notes.yaml",
        ),
        ("projects/{project}/cuts.json",),
        "P7",
        "Proposed cuts: long pauses, fillers, false starts, cue-word retakes (Robert approves)",
    ),
    Stage(
        "f4_edl",
        Runner.CODE,
        ("f3_cuts",),
        (
            "projects/{project}/cuts.json",
            "projects/{project}/cuts-approved.yaml",
            "projects/{project}/cut-notes.yaml",
            "projects/{project}/footage.json",
            "projects/{project}/transcript.json",
        ),
        ("projects/{project}/edl.json",),
        "P7",
        "The approved cuts as frame-exact segments on one edited clock",
    ),
    Stage(
        "f5_reframe",
        Runner.CODE,
        ("f4_edl",),
        (
            "projects/{project}/edl.json",
            "projects/{project}/footage.json",
            "projects/{project}/edits.yaml",
            "data/create/{project}/footage/master/**",
        ),
        ("projects/{project}/framing.json", "data/create/{project}/footage/faces/**"),
        "P7",
        "One steady face-aware crop per segment (YuNet), alternating punch-ins",
    ),
    Stage(
        "f6_edit",
        Runner.CODE,
        ("f4_edl", "f5_reframe"),
        (
            "projects/{project}/edl.json",
            "projects/{project}/footage.json",
            "projects/{project}/framing.json",
            "data/create/{project}/footage/master/**",
        ),
        ("data/create/{project}/footage/edited/**",),
        "P7",
        "The edited presenter video: kept segments frame-exact, short audio fades at each cut",
    ),
    Stage(
        "f7_matte",
        Runner.CODE,
        ("f6_edit", "c5_timing"),
        (
            "projects/{project}/reel.yaml",
            "projects/{project}/timeline.json",
            "data/create/{project}/footage/edited/**",
        ),
        ("data/create/{project}/footage/matte/**",),
        "P7",
        "The presenter cut out (local model) where the reel plan puts props behind them, ADR 0027",
    ),
    Stage(
        "c5_timing",
        Runner.CODE,
        ("c4_voice", "f4_edl"),
        (
            "projects/{project}/voice.json",
            "projects/{project}/script.yaml",
            "exports/pacing.json",
            "projects/{project}/edl.json",
            "projects/{project}/transcript.json",
            "projects/{project}/cuts.json",
        ),
        ("projects/{project}/timeline.json", "data/create/{project}/timing/**"),
        "P1",
        "Scene bounds = voice + tail (TTS) or the edited takes' words (presenter); every word on one clock",
    ),
    Stage(
        "c6_storyboard",
        Runner.CLAUDE,
        ("c5_timing", "c3_tokens"),
        (
            "projects/{project}/timeline.json",
            "projects/{project}/script.yaml",
            "projects/{project}/tokens.json",
            "exports/archetypes.json",
            "exports/patterns.json",
        ),
        ("projects/{project}/storyboard.json",),
        "P3",
        "An archetype per scene with its slots filled; free-form only with a reason",
    ),
    Stage(
        "c8_build",
        Runner.CODE,
        ("c6_storyboard", "c3_tokens", "s10_export"),
        (
            "projects/{project}/storyboard.json",
            "projects/{project}/tokens.json",
            "projects/{project}/timeline.json",
            "projects/{project}/brief.yaml",
            "brands/{brand}/**",
            "exports/motion-tokens.json",
        ),
        ("projects/{project}/scenes/{scene}.html", "data/create/{project}/bundle/**"),
        "P3",
        "Fill the HyperFrames templates (create/templates) with tokens, corpus motion and word cues",
    ),
    Stage(
        "c8_build_freeform",
        Runner.CLAUDE,
        ("c6_storyboard", "c3_tokens", "s10_export"),
        (
            "projects/{project}/storyboard.json",
            "projects/{project}/tokens.json",
            "projects/{project}/timeline.json",
            "exports/motion-tokens.json",
        ),
        ("projects/{project}/freeform/{scene}.html",),
        "P3",
        "Builder subagent for scenes no archetype covers, under the same scene contract",
    ),
    # The motion route (brief `build: motion`, ADR 0032): Claude directs one composition inside our learnings.
    Stage(
        "c6_direction",
        Runner.CODE,
        ("c5_timing", "c3_tokens", "s10_export"),
        (
            "projects/{project}/brief.yaml",
            "projects/{project}/script.yaml",
            "projects/{project}/timeline.json",
            "projects/{project}/tokens.json",
            "brands/{brand}/**",
            "exports/motion-tokens.json",
            "exports/pacing.json",
            "exports/sound-spec.json",
            "exports/patterns.json",
        ),
        ("projects/{project}/direction.md",),
        "P3",
        "Direction pack: word clock, brand rules, measured motion/pacing/sound, recipes, learned rules",
    ),
    Stage(
        "c8_motion",
        Runner.CLAUDE,
        ("c6_direction",),
        ("projects/{project}/direction.md", "projects/{project}/timeline.json", "brands/{brand}/logo/**"),
        ("projects/{project}/motion/index.html", "projects/{project}/motion/sfx.json"),
        "P3",
        "motion-builder subagent: one composition and its SFX cues, graded with create grade",
    ),
    Stage(
        "c8_grade",
        Runner.CODE,
        ("c8_motion", "c3_tokens", "s10_export"),
        (
            "projects/{project}/motion/index.html",
            "projects/{project}/motion/sfx.json",
            "projects/{project}/brief.yaml",
            "projects/{project}/timeline.json",
            "projects/{project}/tokens.json",
            "brands/{brand}/**",
            "exports/pacing.json",
            "exports/sound-spec.json",
        ),
        ("projects/{project}/motion/grade.json", "data/create/{project}/motion/render/**"),
        "P3",
        "Render the build; check layout, contrast, brand, motion, text, accents, overlaps, pacing, SFX",
    ),
    Stage(
        "c8_audit",
        Runner.CODE,
        ("c8_build", "c8_build_freeform"),
        (
            "data/create/{project}/bundle/**",
            "projects/{project}/storyboard.json",
            "projects/{project}/tokens.json",
        ),
        ("projects/{project}/audit/safe-zones.json",),
        "P3",
        "Safe-zone audit: text and logos inside the frame's safe area and out of the caption band (config)",
    ),
    Stage(
        "c7_sketches",
        Runner.CODE,
        ("c8_build", "c8_build_freeform"),
        ("data/create/{project}/bundle/**", "projects/{project}/storyboard.json"),
        ("data/create/{project}/sketches/**",),
        "P4",
        "Final frame of each built scene on one sheet (Robert locks layout and copy); not in git",
    ),
    Stage(
        "c9_previews",
        Runner.CODE,
        ("c7_sketches",),
        ("data/create/{project}/bundle/**",),
        ("data/create/{project}/previews/**",),
        "P4",
        "Low-res motion preview per scene (Robert locks motion)",
    ),
    Stage(
        "c10_audio",
        Runner.CODE,
        ("c5_timing", "c6_storyboard", "s10_export", "c10_music"),
        (
            "projects/{project}/timeline.json",
            "projects/{project}/storyboard.json",
            "exports/sound-spec.json",
            "exports/pacing.json",
        ),
        (
            "projects/{project}/audio_plan.json",
            "data/create/{project}/sfx/**",
        ),
        "P5",
        "SFX cues at measured offsets, carve and ducking (templates route)",
    ),
    Stage(
        "c10_music",
        Runner.CODE,
        ("c5_timing",),
        ("projects/{project}/timeline.json", "projects/{project}/brief.yaml"),
        ("data/create/{project}/music/**",),
        "P5",
        "Music bed built for the video: one Eleven Music chunk per scene, checked for dropouts",
    ),
    Stage(
        "c11_assemble",
        Runner.CODE,
        ("c8_build", "c8_build_freeform", "c10_audio", "c4_voice"),
        (
            "projects/{project}/scenes/{scene}.html",
            "projects/{project}/freeform/{scene}.html",
            "projects/{project}/audio_plan.json",
            "projects/{project}/timeline.json",
            "data/create/{project}/voice/**",
            "data/create/{project}/music/**",
            "data/create/{project}/sfx/**",
        ),
        ("projects/{project}/index.html", "projects/{project}/captions.json"),
        "P5",
        "Frames, captions from TTS word timings, voice, music and SFX on one timeline",
    ),
    Stage(
        "c12_mix",
        Runner.CODE,
        ("c8_grade", "c10_music", "c5_timing"),
        (
            "data/create/{project}/motion/render/**",
            "projects/{project}/motion/sfx.json",
            "projects/{project}/brief.yaml",
            "data/create/{project}/timing/**",
            "data/create/{project}/music/**",
        ),
        ("data/create/{project}/motion/final/**",),
        "P5",
        "Narration + ducked music bed + the build's SFX at the destination's loudness (motion route)",
    ),
    Stage(
        "c12_render",
        Runner.CODE,
        ("c11_assemble",),
        ("projects/{project}/index.html", "projects/{project}/captions.json"),
        ("data/create/{project}/render/**",),
        "P6",
        "HyperFrames render on Robert's machine (ADR 0019)",
    ),
    Stage(
        "c13_qa",
        Runner.CODE,
        ("c12_render", "c12_mix", "s10_export"),
        ("data/create/{project}/render/**", "data/create/{project}/motion/final/**", "exports/**"),
        ("projects/{project}/qa/**",),
        "P6",
        "lens signals + compare on the render, against the section 1 targets of the plan",
    ),
)

_PLACEHOLDER = re.compile(r"\{[a-z_]+\}")


def by_id() -> dict[str, Stage]:
    return {s.id: s for s in STAGES}


def _segment_regex(segment: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(segment):
        m = _PLACEHOLDER.match(segment, i)
        if m:
            out.append(r"[^/]+")
            i = m.end()
        elif segment[i] == "*":
            out.append(r"[^/]*")
            i += 1
        else:
            out.append(re.escape(segment[i]))
            i += 1
    return "".join(out)


@cache
def template_regex(template: str) -> re.Pattern[str]:
    """Compile a path template into a full-match, case-insensitive regex."""
    parts: list[str] = []
    for seg in template.split("/"):
        if seg == "**":
            parts.append(r"(?:.*)")
        else:
            parts.append(_segment_regex(seg))
    pattern = "/".join(parts).replace("/(?:.*)", "(?:/.*)?")
    return re.compile(pattern, re.IGNORECASE)


def _sample(template: str) -> str:
    """A concrete path the template matches (placeholders → 'x', globs → 'x')."""
    segs = []
    for seg in template.split("/"):
        if seg == "**":
            segs.append("x")
        else:
            segs.append(_PLACEHOLDER.sub("x", seg).replace("*", "x"))
    return "/".join(segs)


def templates_overlap(a: str, b: str) -> bool:
    """Heuristic: two templates overlap if one's prefix-or-sample is matched by the other.

    Case-insensitive on purpose: case-only differences collide on macOS/Windows file systems.
    """
    if template_regex(a).fullmatch(_sample(b)) or template_regex(b).fullmatch(_sample(a)):
        return True
    # A `**` directory claims everything below it.
    for x, y in ((a, b), (b, a)):
        if x.endswith("/**"):
            prefix = x[: -len("/**")]
            if template_regex(prefix + "/**").fullmatch(_sample(y)):
                return True
    return False


def _ancestors(stage_id: str, stages: dict[str, Stage]) -> set[str]:
    seen: set[str] = set()
    stack = list(stages[stage_id].after)
    while stack:
        sid = stack.pop()
        if sid in seen or sid not in stages:
            continue
        seen.add(sid)
        stack.extend(stages[sid].after)
    return seen


def check_dag(stages: Iterable[Stage] = STAGES) -> list[str]:
    """Return a list of problems; empty means the registry is a valid strict DAG."""
    reg: dict[str, Stage] = {}
    errors: list[str] = []
    for s in stages:
        if s.id in reg:
            errors.append(f"duplicate stage id: {s.id}")
        reg[s.id] = s

    for s in reg.values():
        for dep in s.after:
            if dep not in reg:
                errors.append(f"{s.id}: unknown dependency {dep!r}")
        for t in (*s.reads, *s.writes):
            literal = _PLACEHOLDER.sub("", t)
            if literal != literal.lower():
                errors.append(f"{s.id}: path {t!r} is not lowercase")

    # Cycles (DFS with colours).
    state: dict[str, int] = {}

    def visit(sid: str, path: list[str]) -> None:
        state[sid] = 1
        for dep in reg[sid].after:
            if dep not in reg:
                continue
            if state.get(dep) == 1:
                errors.append("cycle: " + " -> ".join([*path, sid, dep]))
            elif state.get(dep) is None:
                visit(dep, [*path, sid])
        state[sid] = 2

    for sid in reg:
        if sid not in state:
            visit(sid, [])

    # No two stages may declare overlapping writes (case-insensitively).
    items = list(reg.values())
    for i, a in enumerate(items):
        for b in items[i + 1 :]:
            for wa in a.writes:
                for wb in b.writes:
                    if templates_overlap(wa, wb):
                        errors.append(f"write overlap: {a.id} {wa!r} vs {b.id} {wb!r}")

    # Every read must come from an upstream stage or an external input.
    for s in reg.values():
        upstream = _ancestors(s.id, reg) if not any(e.startswith("cycle") for e in errors) else set()
        for r in s.reads:
            if any(templates_overlap(r, ext) for ext in EXTERNAL_INPUTS):
                continue
            if not any(templates_overlap(r, w) for u in upstream for w in reg[u].writes):
                errors.append(f"{s.id}: reads {r!r}, which no upstream stage writes")
    return errors


def allowed_writes(stage_ids: Iterable[str]) -> tuple[str, ...]:
    reg = by_id()
    out: list[str] = []
    for sid in stage_ids:
        if sid not in reg:
            raise KeyError(f"unknown stage {sid!r}")
        out.extend(reg[sid].writes)
    return tuple(out)


def is_write_allowed(rel_path: str, stage_ids: Iterable[str]) -> bool:
    """True if the repo-relative path is declared by one of the given stages.

    Paths must also be lowercase: case-only variants collide on case-insensitive file systems.
    """
    if rel_path != rel_path.lower():
        return False
    return any(template_regex(t).fullmatch(rel_path) for t in allowed_writes(stage_ids))
