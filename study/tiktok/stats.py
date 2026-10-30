"""The TikTok study's numbers across videos (studies/README.md, "Synthesise"): studies/tiktok/stats.json from
sources.yaml (topic, plays, likes), measure/*.json (code) and notes/*.json (Claude's names). Pure functions
over rows; `build` does the reading and writing."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np
import yaml

from study.tiktok.config import STUDY

Row = dict[str, Any]

# measured numbers summarised per group: (label, path in the measure file)
METRICS: list[tuple[str, tuple[str, ...]]] = [
    ("duration_s", ("duration_s",)),
    ("cuts_per_min", ("shots", "cuts_per_min")),
    ("shot_median_s", ("shots", "shot_median_s")),
    ("first_cut_s", ("shots", "first_cut_s")),
    ("words_per_s", ("speech", "words_per_s")),
    ("first_word_s", ("speech", "first_word_s")),
    ("silence_share", ("speech", "silence_share")),
    ("text_share", ("text", "text_share")),
    ("caption_share", ("text", "caption_share")),
    ("caption_height", ("text", "caption_height_median")),
    ("outside_safe_share", ("text", "outside_safe_share")),
    ("face_share", ("face", "face_share")),
    ("face_height", ("face", "face_height_median")),
    ("face_cy", ("face", "face_cy_median")),
    ("events_per_min", ("density", "events_per_min")),
    ("punches_per_min", ("density", "punches_per_min")),
    ("loudness_lufs", ("sound", "loudness_lufs")),
    ("music_bed_db", ("sound", "music_bed_db")),
    ("loop", ("loop",)),
]


def get(d: dict[str, Any], path: tuple[str, ...]) -> float | None:
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return float(cur) if isinstance(cur, int | float) and not isinstance(cur, bool) else None


def summary(values: list[float]) -> dict[str, float | int] | None:
    """Median and the middle 50% (p25-p75) of the values that exist."""
    v = [x for x in values if x is not None]
    if not v:
        return None
    return {
        "n": len(v),
        "median": round(float(median(v)), 3),
        "p25": round(float(np.percentile(v, 25)), 3),
        "p75": round(float(np.percentile(v, 75)), 3),
    }


def metric_table(rows: list[Row]) -> dict[str, Any]:
    return {label: summary([get(r["measure"], path) for r in rows]) for label, path in METRICS}  # type: ignore[misc]


def engagement(r: Row) -> float:
    """Likes per play: how strongly viewers reacted, fairer across account sizes than raw likes."""
    plays = r.get("plays") or 0
    return (r.get("likes") or 0) / plays if plays else 0.0


def split_top(rows: list[Row], share: float = 0.25) -> tuple[list[Row], list[Row]]:
    """The top `share` by plays and the rest (plays: what the feed chose to show)."""
    ranked = sorted(rows, key=lambda r: -(r.get("plays") or 0))
    k = max(1, round(len(ranked) * share))
    return ranked[:k], ranked[k:]


def counts(notes: list[dict[str, Any]], path: tuple[str, ...]) -> dict[str, float]:
    """Share of notes with each value at `path` (a list value counts each of its items once)."""
    c: Counter[str] = Counter()
    for n in notes:
        cur: Any = n
        for k in path:
            cur = cur.get(k) if isinstance(cur, dict) else None
        for v in cur if isinstance(cur, list) else [cur]:
            if v is not None:
                c[str(v)] += 1
    total = max(1, len(notes))
    return {k: round(v / total, 3) for k, v in c.most_common()}


def build(out: Path = STUDY / "stats.json") -> dict[str, Any]:
    src = {r["id"]: r for r in yaml.safe_load((STUDY / "sources.yaml").read_text())}
    rows: list[Row] = []
    for vid, s in src.items():
        mf, nf = STUDY / "measure" / f"{vid}.json", STUDY / "notes" / f"{vid}.json"
        if not mf.exists():
            continue
        rows.append(
            {
                **s,
                "measure": json.loads(mf.read_text()),
                "note": json.loads(nf.read_text()) if nf.exists() else None,
            }
        )
    top, rest = split_top(rows)
    notes = [r["note"] for r in rows if r["note"]]

    def note_view(rs: list[Row]) -> dict[str, Any]:
        ns = [r["note"] for r in rs if r["note"]]
        return {
            "n": len(ns),
            "format": counts(ns, ("format",)),
            "hook_type": counts(ns, ("hook", "type")),
            "captions": counts(ns, ("graphics", "captions")),
            "caption_position": counts(ns, ("graphics", "caption_position")),
            "devices": counts(ns, ("graphics", "devices")),
            "density": counts(ns, ("graphics", "density")),
            "cta": counts(ns, ("cta", "kind")),
            "with_characters": round(sum(bool(n.get("characters")) for n in ns) / max(1, len(ns)), 3),
        }

    stats = {
        "videos": len(rows),
        "noted": len(notes),
        "all": {"measured": metric_table(rows), "named": note_view(rows)},
        "top_quarter_by_plays": {"measured": metric_table(top), "named": note_view(top)},
        "rest": {"measured": metric_table(rest), "named": note_view(rest)},
        "by_topic": {
            t: {"measured": metric_table(g), "named": note_view(g)}
            for t in sorted({r["topic"] for r in rows})
            if (g := [r for r in rows if r["topic"] == t])
        },
        "by_format": {
            f: {"measured": metric_table(g)}
            for f in sorted({r["note"]["format"] for r in rows if r["note"]})
            if (g := [r for r in rows if r["note"] and r["note"]["format"] == f])
        },
    }
    out.write_text(json.dumps(stats, indent=1) + "\n")
    return stats
