"""G2 gold set (BUILD_PLAN 11.2): seed `gold/<id>/gold.yaml` from the annotations, and write Robert's
reviews back into it.

The gold file is human-owned (an external input, not a stage output). Seeding never overwrites a file
that holds reviewed items; reviews only change the items they name.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import yaml

from lens import __version__
from lens.hashing import cache_key, sha256_file
from lens.measure.run import element_ids
from lens.schemas import LensConfig, SourceEntry
from lens.schemas.annotation import A1File, A2File
from lens.schemas.common import Annotator, Provenance
from lens.schemas.gold import GoldElement, GoldEvent, GoldFile, GoldSfx, GoldShot
from lens.schemas.packets import EventFacts
from lens.schemas.signals import SignalsSummary

STAGE = "g2_gold"


class GoldError(RuntimeError):
    pass


def gold_path(root: Path, video: str) -> Path:
    return root / "gold" / video / "gold.yaml"


def sample_evenly(items: list[str], k: int) -> list[str]:
    """`k` items spread evenly over `items` (first and last included), in order."""
    if k <= 0 or not items:
        return []
    if len(items) <= k:
        return list(items)
    if k == 1:
        return [items[len(items) // 2]]
    picks = sorted({round(i * (len(items) - 1) / (k - 1)) for i in range(k)})
    return [items[i] for i in picks]


def _a1_shots(vdir: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for p in sorted([*vdir.glob("a1.json"), *vdir.glob("a1.p*.json")]):
        for s in A1File.model_validate_json(p.read_text("utf-8")).shots:
            out[s.shot] = s
    return out


def seed_gold(entry: SourceEntry, root: Path, cfg: LensConfig) -> GoldFile:
    """The annotators' answers for every shot and an even sample of annotated events, all pending."""
    vdir = root / "videos" / entry.id
    a1 = _a1_shots(vdir)
    if not a1:
        raise GoldError(f"{entry.id}: no A1 annotation")
    summary = SignalsSummary.model_validate_json((vdir / "signals.summary.json").read_text("utf-8"))
    shots = [
        GoldShot(
            shot=s.id,
            start_s=s.start_s,
            end_s=s.end_s,
            shot_type=a1[s.id].shot_type,
            composition=a1[s.id].composition,
            transition_in=a1[s.id].transition_in,
            depth_cues=list(a1[s.id].depth_cues),
        )
        for s in summary.video.shots
        if s.id in a1
    ]
    a2_paths = {p.name.split(".")[0]: p for p in (vdir / "events").glob("e*.a2.json")}
    picked = sample_evenly(sorted(a2_paths), cfg.gold.max_events_per_video)
    events = []
    inputs = [vdir / "signals.summary.json", *sorted(vdir.glob("a1*.json"))]
    for eid in picked:
        a2 = A2File.model_validate_json(a2_paths[eid].read_text("utf-8"))
        inputs.append(a2_paths[eid])
        facts_path = root / "data" / "packets" / entry.id / "events" / eid / "facts.json"
        if not facts_path.exists():
            raise GoldError(f"{entry.id}/{eid}: no packet facts (run `lens storage pull-packets`)")
        facts = EventFacts.model_validate_json(facts_path.read_text("utf-8"))
        sync = {x.id: x.sync_s for x in facts.sfx}
        events.append(
            GoldEvent(
                event=eid,
                shot=facts.shot,
                start_s=facts.start_s,
                end_s=facts.end_s,
                elements=[
                    GoldElement(id=i, label=el.label, role=el.role, change_types=list(el.change_types))
                    for el, i in zip(a2.elements, element_ids(a2), strict=True)
                ],
                pattern=a2.pattern.id,
                sfx=[GoldSfx(id=r.id, sync_s=sync[r.id], label=r.label) for r in a2.sfx_review],
            )
        )
    return GoldFile(
        provenance=Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.HUMAN,
            input_hash=cache_key({"stage": STAGE, "inputs": [sha256_file(p) for p in inputs]}),
            created_at=datetime.now(UTC),
        ),
        video=entry.id,
        watch_url=entry.page_url,
        shots=shots,
        events=events,
    )


def load_gold(path: Path) -> GoldFile:
    return GoldFile.model_validate(yaml.safe_load(path.read_text("utf-8")))


def write_gold(path: Path, gold: GoldFile) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = gold.model_dump(mode="json")
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110), "utf-8")


def seed_file(entry: SourceEntry, root: Path, cfg: LensConfig, force: bool = False) -> str:
    """Write the seeded gold file. Returns "seeded", or "kept" when a reviewed file exists."""
    path = gold_path(root, entry.id)
    if path.exists() and not force:
        old = load_gold(path)
        if any(s.status != "pending" for s in old.shots) or any(e.status != "pending" for e in old.events):
            return "kept"
    write_gold(path, seed_gold(entry, root, cfg))
    return "seeded"


def review_key(video: str, item: str) -> str:
    """The review page's document id for one item (`<video>~s003` / `<video>~e012`)."""
    return f"{video}~{item}"


def apply_reviews(gold: GoldFile, reviews: dict[str, dict[str, Any]]) -> tuple[GoldFile, int]:
    """Merge review documents (id -> body) into the gold file. A body carries `status` plus the
    corrected fields of its item; pending bodies and unknown fields are ignored. Returns the new file
    and the number of items changed."""
    changed = 0
    shots = []
    for s in gold.shots:
        body = reviews.get(review_key(gold.video, s.shot))
        if body and body.get("status") in ("confirmed", "corrected"):
            s = _merge(s, body, ("shot_type", "composition", "transition_in", "depth_cues", "status", "note"))
            changed += 1
        shots.append(s)
    events = []
    for e in gold.events:
        body = reviews.get(review_key(gold.video, e.event))
        if body and body.get("status") in ("confirmed", "corrected"):
            e = _merge(e, body, ("elements", "missed", "pattern", "sfx", "status", "note"))
            changed += 1
        events.append(e)
    return gold.model_copy(update={"shots": shots, "events": events}), changed


def _merge[T: GoldShot | GoldEvent](item: T, body: dict[str, Any], fields: tuple[str, ...]) -> T:
    data = item.model_dump(mode="json")
    data.update({k: body[k] for k in fields if k in body})
    return cast(T, type(item).model_validate(data))
