"""Pick the 200 TikToks of the study from the discovered candidates (studies/README.md, "Find").

Candidates: studies/tiktok/candidates/*.jsonl (id, handle, topic, where it was found). Metadata per video:
data/study/tiktok/meta/<id>.json (caption, length, plays, likes, date) from `study/web/tiktok.cjs meta`.
Output: studies/tiktok/sources.yaml."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

import yaml

from study.tiktok.config import MEDIA, STUDY, Select

TOPICS = ("ai", "marketing", "claude", "geo", "seo")
_NOT_EN = frozenset(  # German and Tagalog function words (both pass the ASCII test)
    {
        "zeige",
        "mir",
        "dein",
        "deine",
        "den",
        "und",
        "ich",
        "mit",
        "für",
        "ist",
        "nicht",
        "das",
        "der",
        "die",
        "ang",
        "ng",
        "ka",
        "ni",
        "sa",
        "mga",
        "para",
        "ko",
        "mo",
        "yung",
        "lang",
    }
)
_EN = {
    "the",
    "to",
    "and",
    "you",
    "is",
    "how",
    "your",
    "this",
    "for",
    "with",
    "what",
    "in",
    "of",
    "it",
    "my",
    "i",
}


@dataclass(frozen=True)
class Candidate:
    id: str
    handle: str
    topic: str
    found: str  # "creator:<handle>" or "discover:<phrase>"
    caption: str
    duration_s: float
    plays: int
    likes: int
    create_time: int


def looks_english(text: str) -> bool:
    """A caption written in English: mostly ASCII letters and enough common English words (two once the
    caption has six words or more). Captions made only of hashtags count when the tags are ASCII."""
    letters = [c for c in text if c.isalpha()]
    if letters and sum(c.isascii() for c in letters) / len(letters) < 0.9:
        return False
    tokens = re.findall(r"[a-z']+", re.sub(r"#\w+", " ", text.lower()))
    if not tokens:
        return True
    hits = sum(t in _EN for t in tokens)
    if sum(t in _NOT_EN for t in tokens) >= 2:
        return False
    return hits >= (2 if len(tokens) >= 6 else 1)


def topic_of(c: Candidate, keywords: dict[str, str], exclude: str = "") -> str | None:
    """The candidate's topic when its caption matches it, else the first topic whose keywords match, else
    None (off-topic: a discover page also lists unrelated viral videos; `exclude` drops known false hits)."""
    text = c.caption.lower()
    if exclude and re.search(exclude, text):
        return None
    if c.topic in keywords and re.search(keywords[c.topic], text):
        return c.topic
    for t, pat in keywords.items():
        if re.search(pat, text):
            return t
    return None


def select(cands: list[Candidate], cfg: Select, now: float) -> list[Candidate]:
    """Per topic, the most-liked on-topic videos that pass the filters (at most `max_per_creator` per
    creator), then the remaining slots filled from any topic by likes, up to `total`."""
    ok = []
    for c in cands:
        topic = topic_of(c, cfg.topic_keywords, cfg.exclude)
        if (
            topic is not None
            and cfg.min_seconds <= c.duration_s <= cfg.max_seconds
            and (now - c.create_time) / 86400 <= cfg.max_age_days
            and c.likes >= cfg.min_likes
            and looks_english(c.caption)
        ):
            ok.append(replace(c, topic=topic))
    ok.sort(key=lambda c: (-c.likes, c.id))
    picked: list[Candidate] = []
    seen: set[str] = set()
    per_creator: Counter[str] = Counter()
    per_topic: Counter[str] = Counter()

    def take(c: Candidate) -> None:
        picked.append(c)
        seen.add(c.id)
        per_creator[c.handle] += 1
        per_topic[c.topic] += 1

    for c in ok:
        if (
            c.id in seen
            or per_creator[c.handle] >= cfg.max_per_creator
            or per_topic[c.topic] >= cfg.per_topic
        ):
            continue
        take(c)
    for c in ok:
        if len(picked) >= cfg.total:
            break
        if c.id not in seen and per_creator[c.handle] < cfg.max_per_creator:
            take(c)
    return picked[: cfg.total]


def load_candidates(meta_dir: Path = MEDIA / "meta") -> list[Candidate]:
    found: dict[str, tuple[str, str, str]] = {}
    for f in sorted((STUDY / "candidates").glob("*.jsonl")):
        for line in f.read_text().splitlines():
            row = json.loads(line)
            where = f"creator:{row['handle']}" if "handle" in row else f"discover:{row['phrase']}"
            for v in row["videos"]:
                found.setdefault(v["id"], (v["handle"], row["topic"], where))
    out: list[Candidate] = []
    for vid, (handle, topic, where) in found.items():
        mf = meta_dir / f"{vid}.json"
        if not mf.exists():
            continue
        meta = json.loads(mf.read_text())
        out.append(
            Candidate(
                vid,
                meta.get("handle") or handle,
                topic,
                where,
                meta.get("text") or "",
                float(meta.get("duration_s") or 0),
                int(meta.get("plays") or 0),
                int(meta.get("likes") or 0),
                int(meta.get("create_time") or 0),
            )
        )
    return out


def write_sources(picked: list[Candidate], path: Path = STUDY / "sources.yaml") -> None:
    by_topic: dict[str, int] = defaultdict(int)
    rows = []
    for c in picked:
        by_topic[c.topic] += 1
        rows.append(
            {
                "id": c.id,
                "url": f"https://www.tiktok.com/@{c.handle}/video/{c.id}",
                "creator": c.handle,
                "topic": c.topic,
                "found": c.found,
                "duration_s": c.duration_s,
                "plays": c.plays,
                "likes": c.likes,
                "posted": datetime.fromtimestamp(c.create_time, UTC).date().isoformat(),
                "caption": c.caption[:120],
            }
        )
    head = (
        "# The TikTok study's videos (studies/README.md), picked by study/tiktok/sources.py from\n"
        "# studies/tiktok/candidates. Per topic: "
        + ", ".join(f"{t} {by_topic.get(t, 0)}" for t in TOPICS)
        + f". Total {len(rows)}.\n"
    )
    path.write_text(head + yaml.safe_dump(rows, sort_keys=False, allow_unicode=True, width=120))
