"""Pixel-art TikTok clips for the animation study (studies/README.md, track 2; Robert's tag list): the
most-liked short clips that are clearly pixel art, a few per creator. Candidates and metadata come from
`study/web/tiktok.cjs` (data/study/pixel/tiktok/); the pick goes to studies/pixel-art/tiktok.yaml."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from study.pixel.config import MEDIA, STUDY

PIXEL = re.compile(r"pixel|sprite|aseprite|8-?bit|16-?bit|retro ?game", re.I)


def pick(metas: list[dict[str, Any]], n: int, per_creator: int, max_seconds: float) -> list[dict[str, Any]]:
    """The n most-liked clips whose caption says pixel art, at most `per_creator` each, up to max_seconds."""
    ok = [
        m
        for m in metas
        if PIXEL.search(m.get("text") or "") and 0 < float(m.get("duration_s") or 0) <= max_seconds
    ]
    ok.sort(key=lambda m: (-int(m.get("likes") or 0), str(m["id"])))
    seen: Counter[str] = Counter()
    out = []
    for m in ok:
        if seen[m.get("handle") or ""] >= per_creator:
            continue
        seen[m.get("handle") or ""] += 1
        out.append(m)
        if len(out) >= n:
            break
    return out


def build(
    n: int = 60, per_creator: int = 3, max_seconds: float = 90, out: Path = STUDY / "tiktok.yaml"
) -> int:
    metas = [json.loads(f.read_text()) for f in sorted((MEDIA / "tiktok" / "meta").glob("*.json"))]
    rows = [
        {
            "id": m["id"],
            "url": f"https://www.tiktok.com/@{m['handle']}/video/{m['id']}",
            "creator": m["handle"],
            "duration_s": m["duration_s"],
            "plays": m["plays"],
            "likes": m["likes"],
            "posted": datetime.fromtimestamp(int(m["create_time"]), UTC).date().isoformat(),
            "caption": (m.get("text") or "")[:120],
        }
        for m in pick(metas, n, per_creator, max_seconds)
    ]
    head = (
        "# Pixel-art TikTok clips for the animation study (study/pixel/clips.py) from Robert's tags\n"
        "# (#pixelart, #pixelanimation, #aseprite, ...): most-liked, caption says pixel art, <= 90 s,\n"
        "# at most 3 per creator.\n"
    )
    out.write_text(head + yaml.safe_dump(rows, sort_keys=False, allow_unicode=True, width=120))
    return len(rows)
