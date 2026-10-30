"""Robert's own corrections from the edit page (`create edits <p> --page`), kept in projects/<p>/edits.yaml.

The page sends back values, not wishes: a shot's crop (zoom and shift), a plan's push-in, quick zooms to drop
and held zooms to rescale, plus notes pinned to a time. F5 uses the crops as given (reframe.py), `create
reel` applies the plan changes over the plan file (load_plan), and the notes are for Claude to act on. So a
correction lands exactly once, as he set it, instead of being reinterpreted round after round.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from lens.schemas.create import EditNote, Edits, PlanEdit, ReelPlan, ShotEdit

HEAD = (
    "# Robert's corrections from the edit page (create edits --page). Shots: F5 crops as he set them;\n"
    "# plans: zoom changes `create reel` applies over that plan file; notes: for Claude (done: acted on).\n"
)


def load_edits(base: Path) -> Edits:
    p = base / "edits.yaml"
    return Edits.model_validate(yaml.safe_load(p.read_text()) or {}) if p.exists() else Edits()


def write_edits(base: Path, edits: Edits) -> Path:
    p = base / "edits.yaml"
    body = yaml.safe_dump(edits.model_dump(mode="json"), sort_keys=False, allow_unicode=True)
    p.write_text(HEAD + body)
    return p


def apply_plan(plan: ReelPlan, edit: PlanEdit | None) -> ReelPlan:
    """The plan with Robert's zoom changes: his push-in, without the dropped quick zooms, held zooms
    rescaled (scale 1 removes one). Edits naming a word the plan no longer zooms on are ignored."""
    if edit is None:
        return plan
    scales = {z.word: z.scale for z in edit.zooms}
    zooms = [
        z.model_copy(update={"scale": scales.get(z.word, z.scale)})
        for z in plan.zooms
        if scales.get(z.word, z.scale) > 1
    ]
    return plan.model_copy(
        update={
            "push": plan.push if edit.push is None else edit.push,
            "punches": [w for w in plan.punches if w not in set(edit.drop_punches)],
            "zooms": zooms,
        }
    )


def load_plan(base: Path, plan_path: Path | None = None) -> ReelPlan:
    """A reel plan as `create reel` uses it: the plan file with edits.yaml's changes for that file."""
    path = plan_path or base / "reel.yaml"
    plan = ReelPlan.model_validate(yaml.safe_load(path.read_text()))
    return apply_plan(plan, load_edits(base).plans.get(path.name))


def merge(edits: Edits, sent: dict[str, Any]) -> Edits:
    """Fold one page's answer into the project's edits: shots replace by (take, src_in), the plan's push
    replaces, dropped punches add up, held zooms replace by word, notes are appended."""
    shots = {(s.take, s.src_in): s for s in edits.shots}
    for raw in sent.get("shots", []):
        s = ShotEdit.model_validate(raw)
        shots[(s.take, s.src_in)] = s
    plans = dict(edits.plans)
    name = sent.get("plan")
    if name and any(k in sent for k in ("push", "drop_punches", "zooms")):
        old = plans.get(name, PlanEdit())
        zooms = {z.word: z for z in old.zooms}
        zooms.update({z.word: z for z in PlanEdit.model_validate({"zooms": sent.get("zooms", [])}).zooms})
        plans[name] = PlanEdit.model_validate(
            {
                "push": sent.get("push", old.push),
                "drop_punches": sorted(set(old.drop_punches) | set(sent.get("drop_punches", []))),
                "zooms": [z.model_dump() for z in sorted(zooms.values(), key=lambda z: z.word)],
            }
        )
    notes = list(edits.notes) + [EditNote.model_validate({**n, "plan": name}) for n in sent.get("notes", [])]
    return Edits(shots=sorted(shots.values(), key=lambda s: (s.take, s.src_in)), plans=plans, notes=notes)


def read_answer(text: str) -> dict[str, Any]:
    """The page's answer as pasted: the JSON object, even inside a code fence or with words around it."""
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b < a:
        raise ValueError("no edit-page answer (a JSON object) found")
    data = json.loads(text[a : b + 1])
    if not isinstance(data, dict) or "edits" not in data:
        raise ValueError("not an edit-page answer: it has no 'edits' key")
    return data
