"""Project status: which Phase 2 stages have their declared outputs on disk, and which are ready."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import TypeAdapter, ValidationError

from lens.schemas.common import Slug
from lens.stages import STAGES, Stage, template_regex
from lens.validate import checker_for, validate_file

PHASE2_PREFIX = ("c", "f")  # c: the C stages; f: presenter footage (ADR 0025)
BRAND_REQUIRED = ("tokens.json", "video.yaml", "DESIGN.md", "logo")
# Stages that only run when needed (scenes no archetype covers); having no outputs is fine.
OPTIONAL = frozenset({"c8_build_freeform"})
FOOTAGE = frozenset({"f1_ingest", "f2_transcript", "f3_cuts", "f4_edl", "f5_reframe", "f6_edit"})
# Per build route (brief `build`, ADR 0032): the stages the other route owns.
MOTION = frozenset({"c6_direction", "c8_motion", "c8_grade", "c12_mix"})
TEMPLATES = frozenset(
    {
        "c6_storyboard",
        "c8_build",
        "c8_build_freeform",
        "c8_audit",
        "c7_sketches",
        "c9_previews",
        "c10_audio",
        "c11_assemble",
        "c12_render",
    }
)
NOT_BUILT = {"motion": TEMPLATES, "templates": MOTION}
# Per voice mode (brief `voice`): stages that do not apply, and stages that may be skipped.
# presenter projects are built as reels (create reel), not by either route
NOT_USED = {"tts": FOOTAGE, "presenter": frozenset({"c4_voice"}) | MOTION}
# a presenter may speak freely (no script) and may skip framing (centre crop)
MAY_SKIP = {"tts": frozenset(), "presenter": frozenset({"c2_script", "f5_reframe"})}


def voice_mode(root: Path, project: str) -> str:
    path = root / "projects" / project / "brief.yaml"
    data = yaml.safe_load(path.read_text()) if path.exists() else None
    mode = data.get("voice", "tts") if isinstance(data, dict) else "tts"
    return mode if mode in NOT_USED else "tts"


def build_mode(root: Path, project: str) -> str:
    """The brief's build route: motion (default) or templates."""
    path = root / "projects" / project / "brief.yaml"
    data = yaml.safe_load(path.read_text()) if path.exists() else None
    mode = data.get("build", "motion") if isinstance(data, dict) else "motion"
    return mode if mode in NOT_BUILT else "motion"


def phase2_stages() -> list[Stage]:
    return [s for s in STAGES if s.id.startswith(PHASE2_PREFIX) and s.milestone.startswith("P")]


def check_slug(project: str) -> str:
    return TypeAdapter(Slug).validate_python(project)


@dataclass(frozen=True)
class StageStatus:
    stage: str
    state: str  # done | ready | waiting | invalid | optional | unused
    detail: str


def _outputs(root: Path, template: str) -> list[Path]:
    """Files on disk matching one write template (with {project} already filled in)."""
    parts = template.split("/")
    fixed = []
    for p in parts:
        if "{" in p or "*" in p:
            break
        fixed.append(p)
    base = root.joinpath(*fixed)
    if base.is_file():
        return [base]
    if not base.is_dir():
        return []
    rx = template_regex(template)
    return sorted(p for p in base.rglob("*") if p.is_file() and rx.fullmatch(p.relative_to(root).as_posix()))


class BrandError(ValueError):
    """The project's brief does not name a brand, or the brand folder is missing."""


def brand_of(root: Path, project: str) -> str | None:
    """The brand slug the project's brief names (`brand:`), or None before C1 has written the brief."""
    path = root / "projects" / project / "brief.yaml"
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text()) or {}
    brand = data.get("brand") if isinstance(data, dict) else None
    if not isinstance(brand, str):
        return None
    try:
        return check_slug(brand)
    except ValidationError as exc:
        raise BrandError(f"brand {brand!r} in projects/{project}/brief.yaml is not a lowercase slug") from exc


def brand_dir(root: Path, project: str) -> Path:
    """`brands/<brand>/`, the shared brand hand-off the project's brief names (ADR 0022)."""
    brand = brand_of(root, project)
    if brand is None:
        raise BrandError(f"projects/{project}/brief.yaml does not name a brand (brand: <slug>)")
    path = root / "brands" / brand
    if not path.is_dir():
        raise BrandError(f"brand {brand!r} has no folder brands/{brand}/")
    return path


def brand_missing(root: Path, brand: str) -> list[str]:
    """Hand-off files the brand folder still needs."""
    path = root / "brands" / brand
    return [name for name in BRAND_REQUIRED if not (path / name).exists()]


def _upstream(stage_id: str, by_id: dict[str, Stage]) -> set[str]:
    seen: set[str] = set()
    stack = [d for d in by_id[stage_id].after if d in by_id]
    while stack:
        sid = stack.pop()
        if sid not in seen:
            seen.add(sid)
            stack.extend(d for d in by_id[sid].after if d in by_id)
    return seen


def status(root: Path, project: str) -> list[StageStatus]:
    stages = phase2_stages()
    by_id = {s.id: s for s in stages}
    mode = voice_mode(root, project)
    build = build_mode(root, project)
    done: dict[str, bool] = {}
    out: list[StageStatus] = []
    for s in stages:
        if s.id in NOT_USED[mode]:
            done[s.id] = True
            out.append(StageStatus(s.id, "unused", f"not used by {mode} projects (brief voice)"))
            continue
        if s.id in NOT_BUILT[build]:
            done[s.id] = True
            out.append(StageStatus(s.id, "unused", f"not used by the {build} route (brief build)"))
            continue
        templates = [w.replace("{project}", project) for w in s.writes]
        found = {t: _outputs(root, t) for t in templates}
        # Done = the committed outputs; local media (data/create/, never committed) is only noted, unless
        # it is all the stage writes.
        committed = [t for t in templates if t.startswith("projects/")] or templates
        missing = [t for t in committed if not found[t]]
        local_missing = [t for t in templates if t not in committed and not found[t]]
        invalid = []
        for files in found.values():
            for f in files:
                rel = f.relative_to(root).as_posix()
                if checker_for(rel) is not None:
                    r = validate_file(f, root)
                    if not r.ok:
                        invalid.append(f"{rel}: {r.errors[0]}")
        skipped = (s.id in OPTIONAL or s.id in MAY_SKIP[mode]) and len(missing) == len(committed)
        done[s.id] = skipped or (not missing and not invalid)
        deps = sorted(_upstream(s.id, by_id))  # every Phase 2 stage it depends on, directly or not
        if invalid:
            out.append(StageStatus(s.id, "invalid", invalid[0]))
        elif skipped:
            why = (
                "runs only for scenes no archetype covers"
                if s.id in OPTIONAL
                else f"optional for {mode} projects"
            )
            out.append(StageStatus(s.id, "optional", why))
        elif not missing:
            names = ", ".join(
                t.split("/")[-1]
                if "{" not in t and "*" not in t
                else f"{len(found[t])} files in {t.rsplit('/', 1)[0]}/"
                for t in committed
            )
            note = " (local media missing: " + ", ".join(local_missing) + ")" if local_missing else ""
            out.append(StageStatus(s.id, "done", names + note))
        elif all(done.get(d, False) for d in deps):
            out.append(StageStatus(s.id, "ready", s.summary))
        else:
            waiting = [d for d in deps if not done.get(d, False)]
            out.append(StageStatus(s.id, "waiting", "after " + ", ".join(waiting)))
    return out
