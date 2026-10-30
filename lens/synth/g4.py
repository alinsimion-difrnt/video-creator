"""Gate G4 page: the pattern catalog and the taxonomy proposals as plain Agree/Disagree questions.

Each item states Claude's recommendation in plain words with links to watch examples. The page (an
Artifact with `db`) saves `g4/<item>` = {verdict: agree|disagree, note}; Claude applies the verdicts to
taxonomy/proposals.yaml and taxonomy/v1.yaml. The page holds no media.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from lens.schemas.cards import PatternCard
from lens.schemas.corpus import Proposal
from lens.validate import load_sources


def _watch(root: Path, member: str, urls: dict[str, str | None]) -> dict[str, Any] | None:
    video, eid = member.split("/")
    url = urls.get(video)
    rec = json.loads((root / "videos" / video / "record.json").read_text("utf-8"))
    pool = rec["shots"] if eid.startswith("s") else rec["events"]
    ev = next((e for e in pool if e["id"] == eid), None)
    if not url or ev is None:
        return None
    t = max(0, int(ev["start_s"]) - 1)
    sep = "&" if "?" in url else "?"
    return {"label": f"{rec['brand']} at {t // 60}:{t % 60:02d}", "url": f"{url}{sep}t={t}s"}


def g4_items(root: Path, hold: dict[str, str]) -> list[dict[str, Any]]:
    """`hold`: pattern id -> plain reason to keep a card out of the recipe book for now."""
    urls = {s.id: s.page_url for s in load_sources(root)}
    rows = yaml.safe_load((root / "taxonomy" / "proposals.yaml").read_text("utf-8")) or []
    items = []
    for p in (Proposal.model_validate(r) for r in rows):
        rec = p.recommendation or p.suggestion
        if rec == "add" or rec == "new":
            ask = f"Add “{p.name}” as a new pattern?"
        elif rec.startswith("merge:"):
            ask = f"Treat “{p.name}” as the same pattern as “{rec.split(':', 1)[1].replace('_', ' ')}”?"
        else:
            ask = f"Leave “{p.name}” out of the pattern list?"
        links = [w for w in (_watch(root, m, urls) for m in p.members[:3]) if w]
        items.append(
            {
                "key": f"proposal~{p.id}",
                "ask": ask,
                "what": p.plain or p.name,
                "why": p.why or "",
                "links": links,
            }
        )
    cards = sorted((root / "corpus" / "patterns").glob("*.json"))
    keep = []
    for path in cards:
        c = PatternCard.model_validate_json(path.read_text("utf-8"))
        if c.id in hold:
            links = [w for w in (_watch(root, f"{x.video}/{x.event}", urls) for x in c.examples[:2]) if w]
            items.append(
                {
                    "key": f"hold~{c.id}",
                    "ask": f"Keep “{c.name}” out of the recipe book for now?",
                    "what": c.summary,
                    "why": hold[c.id],
                    "links": links,
                }
            )
        else:
            keep.append(c.name)
    items.append(
        {
            "key": "catalog",
            "ask": f"Put these {len(keep)} patterns in the recipe book?",
            "what": "; ".join(keep) + ".",
            "why": "Each is seen in several premium explainers and has a card with measured timing.",
            "links": [],
        }
    )
    return items


def g4_scene_items(root: Path, hold: dict[str, str]) -> list[dict[str, Any]]:
    """Scene archetypes: the `other` scene proposals, seed archetypes with too few examples, and the
    seed archetypes to keep."""
    from lens.schemas.scenes import ScenesFile

    urls = {s.id: s.page_url for s in load_sources(root)}
    rows = yaml.safe_load((root / "taxonomy" / "scene_proposals.yaml").read_text("utf-8")) or []
    items = []
    for p in (Proposal.model_validate(r) for r in rows):
        rec = p.recommendation or p.suggestion
        name = p.name
        if rec in ("add", "new"):
            ask = f"Add “{name}” as a scene type?"
        elif rec.startswith("merge:"):
            ask = f"Treat “{name}” as the same scene type as “{rec.split(':', 1)[1].replace('_', ' ')}”?"
        else:
            ask = f"Leave “{name}” out of the scene types?"
        links = [w for w in (_watch(root, m, urls) for m in p.members[:3]) if w]
        items.append(
            {"key": f"scene~{p.id}", "ask": ask, "what": p.plain or name, "why": p.why or "", "links": links}
        )
    stats = ScenesFile.model_validate_json((root / "corpus" / "stats" / "scenes.json").read_text("utf-8"))
    for aid, why in hold.items():
        items.append(
            {
                "key": f"scene-hold~{aid}",
                "ask": f"Leave “{aid.replace('_', ' ')}” out of the scene types for now?",
                "what": "One of the ten starting scene types from the Acme v1 lessons.",
                "why": why,
                "links": [],
            }
        )
    keep = [a.id.replace("_", " ") for a in stats.archetypes if a.id not in hold]
    items.append(
        {
            "key": "scene-catalog",
            "ask": f"Keep these {len(keep)} starting scene types?",
            "what": "; ".join(keep) + ".",
            "why": "Each has examples in at least 5 videos (the logo close in 49).",
            "links": [],
        }
    )
    return items


def render_g4(root: Path, hold: dict[str, str], scenes: dict[str, str] | None = None) -> str:
    items = g4_scene_items(root, scenes) if scenes is not None else g4_items(root, hold)
    data = json.dumps(items, separators=(",", ":")).replace("</", "<\\/")
    html = (Path(__file__).with_name("g4.html")).read_text("utf-8").replace("/*ITEMS*/[]", data)
    if scenes is not None:
        html = html.replace("Pattern Catalog Approval", "Scene Types Approval").replace(
            "grouped the motion in 55 explainers into named patterns",
            "sorted the shots of 55 explainers into scene types (whole-scene templates)",
        )
    return html
