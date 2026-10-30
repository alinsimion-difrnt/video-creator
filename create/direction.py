"""C6 direction (ADR 0032): the one file a motion builder reads instead of the repo.

projects/<project>/direction.md is assembled by code from what the repo already holds: the brief, the
narration's word clock, the brand tokens and DESIGN.md, the corpus exports (motion, pacing, sound, patterns)
and the learned rules in config `create.motion.rules`. Claude directs the motion freely inside it; c8_grade
checks the parts code can measure.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from create.build import css_vars
from lens import __version__
from lens.hashing import cache_key
from lens.schemas.config import LensConfig, Rect
from lens.schemas.create import Brief, Script, Timeline, Tokens

EXPORTS = ("motion-tokens.json", "pacing.json", "sound-spec.json", "patterns.json")
SFX_KINDS = (
    "chime",
    "click",
    "glitch",
    "impact",
    "pop",
    "swoosh_reverse",
    "whoosh",
)  # reveal offsets worth quoting


def film_s(brief: Brief, timeline: Timeline, final_hold_s: float) -> float:
    """The film's length: the timeline's, or the brief's `cut_s` (which may only shorten the close tail)."""
    if brief.cut_s is None:
        return timeline.total_s
    last = max(w.end_s for w in timeline.words)
    if brief.cut_s > timeline.total_s:
        raise ValueError(f"cut_s {brief.cut_s:g} s is longer than the timeline ({timeline.total_s:g} s)")
    if brief.cut_s < last + final_hold_s:
        raise ValueError(
            f"cut_s {brief.cut_s:g} s leaves no {final_hold_s:g} s final hold "
            f"after the last word ({last:g} s)"
        )
    return brief.cut_s


def _rng(d: dict[str, float], unit: float = 1000.0) -> str:
    return f"{d['median'] / unit:.2f} ({d['low'] / unit:.2f}-{d['high'] / unit:.2f})"


def design_rules(md: str, sections: list[str]) -> str:
    """The configured `## N.` sections of a brand's DESIGN.md, verbatim."""
    parts = re.split(r"(?m)^## ", md)
    return "\n\n".join("### " + p.strip() for p in parts if p.startswith(tuple(sections)))


def _rect(r: Rect) -> str:
    return f"x {r.x0}-{r.x1}, y {r.y0}-{r.y1}"


def frame_rules(tokens: Tokens, cfg: LensConfig) -> list[str]:
    """Where text and logos may sit on this frame (config create.design.frames); c8_grade checks them."""
    lay = tokens.layout
    frame = cfg.create.design.frames[tokens.frame]
    safe = "; ".join(_rect(r) for r in lay.safe)
    lines = [
        f"Safe area (px): every text and logo lies fully inside one of: {safe}. "
        f"Text at least {frame.min_text_px:g}px.",
    ]
    if tokens.captions is not None:
        lines.append(
            f"Caption band ({_rect(lay.caption_band)}): burned-in captions go there after the mix; keep text "
            "and logos out of it (backgrounds and shapes may pass behind)."
        )
    if lay.height > lay.width:
        lines.append(
            "Vertical: the platform's own UI (top tabs, the action rail on the right, the description at the "
            "bottom) covers the rest. Stack, do not spread: one idea per frame, big type, a single column, "
            "the hook in the first 2 s. Backgrounds and decoration may fill the whole frame."
        )
    return lines


def _load(base: Path, root: Path) -> dict[str, Any]:
    brief = Brief.model_validate(yaml.safe_load((base / "brief.yaml").read_text()))
    return {
        "brief": brief,
        "script": Script.model_validate(yaml.safe_load((base / "script.yaml").read_text())),
        "timeline": Timeline.model_validate_json((base / "timeline.json").read_text()),
        "tokens": Tokens.model_validate_json((base / "tokens.json").read_text()),
        "design": (root / "brands" / brief.brand / "DESIGN.md").read_text(),
        **{e: json.loads((root / "exports" / e).read_text()) for e in EXPORTS},
    }


def direction_md(root: Path, project: str, cfg: LensConfig) -> str:
    base = root / "projects" / project
    d = _load(base, root)
    brief: Brief = d["brief"]
    tl: Timeline = d["timeline"]
    tokens: Tokens = d["tokens"]
    motion, pacing, sound = d["motion-tokens.json"], d["pacing.json"], d["sound-spec.json"]
    patterns = {p["id"]: p for p in d["patterns.json"]["patterns"]}
    mc = cfg.create.motion
    unknown = [p for p in mc.patterns if p not in patterns]
    if unknown:
        raise ValueError(f"config create.motion.patterns: not in exports/patterns.json: {', '.join(unknown)}")
    dur = film_s(brief, tl, mc.final_hold_s)
    target = cfg.targets.loudness[brief.destination]
    key = cache_key(
        {
            "tool": __version__,
            "project": project,
            "inputs": {k: v for k, v in d.items() if isinstance(v, str)},
            "brief": brief.model_dump(mode="json"),
            "timeline": tl.model_dump(mode="json")["words"],
            "motion": mc.model_dump(),
            "exports": [d[e]["provenance"]["input_hash"] for e in EXPORTS],
        }
    )

    L: list[str] = [
        f"<!-- c6_direction {__version__} input_hash={key} -->",
        f"# Direction pack: {project} ({dur:g} s)",
        "",
        "## 1. The job",
        f"Product: {brief.product.name} ({brief.product.url}). Audience: {brief.audience}",
        f"Message: {brief.message}",
        f"Tone: {brief.tone}",
        f"Frame: {tokens.layout.width}x{tokens.layout.height}, {tl.fps} fps, exactly {dur:g} s. "
        f"Destination: {brief.destination}. Language: {brief.language}.",
        *frame_rules(tokens, cfg),
        "Facts you may show (nothing else is claimed):",
        *(f"- {f.id}: {f.claim}" for f in brief.facts),
        "",
        "## 2. Narration word clock (seconds from the film's start; cue every reveal to a word, never guess)",
    ]
    scenes = {s.id: s for s in d["script"].scenes}
    for sc in tl.scenes:
        if sc.start_s >= dur:
            break
        ws = [w for w in tl.words if w.scene == sc.scene]
        s = scenes.get(sc.scene)
        L.append(
            f"- {sc.scene} ({s.beat if s else ''}) {sc.start_s:.2f}-{min(sc.end_s, dur):.2f} s: "
            + " ".join(f"{w.text}@{w.start_s:.2f}" for w in ws)
        )
        if s and s.on_screen:  # what the script says this scene shows
            L += [f"  - on screen: {item}" for item in s.on_screen]
        if s and s.notes:
            L.append(f"  - notes: {s.notes}")
    L += [
        f"- final hold: the last frame stays still for at least {mc.final_hold_s:g} s before {dur:g} s",
        "",
        f"## 3. Brand ({brief.brand}): CSS variables, use them verbatim",
        "```css",
        css_vars(tokens),
        "```",
        f"Logo files: assets/logo.svg (primary){', assets/logo-on-dark.svg' if tokens.logo.on_dark else ''}. "
        "Fonts: assets/fonts.css. GSAP: assets/gsap.min.js. No network at render time.",
        "",
        f"Design rules (brands/{brief.brand}/DESIGN.md, verbatim):",
        "",
        design_rules(d["design"], mc.design_sections),
        "",
        "## 4. Motion, measured from premium explainers (seconds: median (low-high))",
        "Pick any value inside low-high; the median is a safe default. A move longer than "
        f"{mc.grade.max_move_s:g} s needs a reason (a carrier morph or a camera move).",
        "",
    ]
    L += [f"- {k}: {_rng(v)}" for k, v in motion["duration_ms_by_role"].items() if v["n"] >= 5]
    L += [f"- change {k}: {_rng(v)}" for k, v in motion["duration_ms_by_change"].items() if v["n"] >= 5]
    L += [
        "- eases (GSAP, share of measured moves): "
        + ", ".join(f"{k} `{v['gsap']}` {v['share']:.0%}" for k, v in motion["easing"].items()),
        "- springs: "
        + "; ".join(f"{s['name']} settles in {_rng(s['settle_ms'])}" for s in motion["springs"]),
        f"- word stagger: {_rng(motion['word_stagger_ms'])}; overshoot on {motion['overshoot_share']:.0%} of "
        f"moves, {motion['overshoot_pct']['median']:.0f}% median; "
        f"{motion['all_at_once_share']:.0%} of groups "
        "enter all at once (stagger the rest)",
    ]
    shot = pacing["shot_s_by_format"].get(brief.format, pacing["shot_s"])
    L += [
        "",
        "## 5. Pacing",
        f"- a new visual idea every {shot['median']:.1f} s (range {shot['low']:.1f}-{shot['high']:.1f}) "
        f"for {brief.format}; never idle past {shot['high']:.1f} s",
        f"- no empty container held for {cfg.signals.dead_hold_min_s:g} s or more (lens flags a dead hold)",
    ]
    pm = sound["sfx_per_min"]

    def n(per_min: float) -> int:
        return round(per_min * dur / 60)

    offsets = sound["sfx_offset_ms_to_reveal"]
    lo, hi = mc.sfx_gain_db
    L += [
        "",
        "## 6. Sound",
        f"- SFX for {dur:g} s: about {n(pm['median'])} (range {n(pm['low'])}-{n(pm['high'])}); "
        f"measured {pm['median']:.0f} per minute",
        "- SFX onset relative to its reveal (ms, negative = before): "
        + "; ".join(
            f"{k} {offsets[k]['median']:.0f} ({offsets[k]['low']:.0f}..{offsets[k]['high']:.0f})"
            for k in SFX_KINDS
            if k in offsets and offsets[k]["n"] >= 5
        ),
        f"- library (assets/sfx/<name>.mp3): {', '.join(mc.sfx)}; gain {lo:g}..{hi:g} dB per cue",
        "- optional `x` per cue: the reveal's horizontal centre as a share of the frame width (0 left, "
        "1 right); c12_mix pans the cue toward it",
        "- the narration and a music bed built for the video are mixed by c12_mix; you only place SFX",
        f"- final mix: {target.min_lufs:g} to {target.max_lufs:g} LUFS, true peak <= "
        f"{target.max_true_peak_dbtp:g} dBTP (c12_mix normalises)",
        "",
        "## 7. Recipe menu (exports/patterns.json; name the ids you use)",
    ]
    for pid in mc.patterns:
        p = patterns[pid]
        L.append(f"- **{pid}**: {p['summary']} Steps: " + " / ".join(p["steps"][: mc.pattern_steps]))
    L += ["", "## 8. Rules learned so far (each must hold)"]
    L += [f"{i}. {' '.join(r.rule.split())} _({r.source})_" for i, r in enumerate(mc.rules, 1)]
    return "\n".join(L) + "\n"


def run_direction(root: Path, project: str, cfg: LensConfig) -> Path:
    out = root / "projects" / project / "direction.md"
    out.write_text(direction_md(root, project, cfg))
    return out
