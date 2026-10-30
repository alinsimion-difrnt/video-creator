"""Vet AI-researched source candidates before they enter sources/sources.yaml.

Usage:
    uv run python scripts/vet_sources.py OUT_DIR file1.yaml file2.md ...

Accepts the YAML lists returned by the research prompt (also inside Markdown fences, with citation
junk like `\\[3\\]` or `[cite: 1]`). For every entry it:
- extracts the YouTube video id and de-duplicates across files;
- checks the video exists via YouTube oEmbed (no download) and records the real title and channel;
- flags a channel that does not look like the brand (possible re-upload);
- rejects non-video URLs (blogs, news, channel listings) and over-long videos (keynotes);
- maps formats outside the taxonomy, writes unique lowercase ids, keeps everything `status: draft`.

Writes OUT_DIR/candidates.yaml (validated entries, draft) and OUT_DIR/candidates-report.md.
Durations are NOT verifiable from a cloud runner (YouTube bot-blocks metadata); they are carried over
from the research output and marked unverified.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lens.config import load_config  # noqa: E402
from lens.schemas import SourcesFile, Taxonomy  # noqa: E402

YT_ID = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([A-Za-z0-9_-]{11})")
LONG_FORM = re.compile(r"keynote|full event|livestream|live at |opening session|everything revealed", re.I)
FORMAT_MAP = {"product_demo": "tutorial", "demo": "tutorial", "keynote": "other", "ad": "feature_reel"}
# Brand -> extra channel-name fragments that legitimately upload its videos.
BRAND_ALIASES = {
    "notion ai": ["notion"],
    "harvey ai": ["harvey"],
    "the browser company (arc)": ["browser company", "arc"],
    "arc": ["browser company", "arc"],
    "anthropic": ["anthropic", "claude"],
    "openai": ["openai"],
    "monday.com": ["monday"],
    "apollo.io": ["apollo"],
    "aws": ["amazon web services", "aws"],
    "google": ["google", "made by google", "pixel"],
    "microsoft": ["microsoft", "copilot", "surface", "windows"],
    "meta": ["meta"],
    "apple": ["apple"],
}


def clean(text: str) -> str:
    text = re.sub(r"\\\[\d+\\\]", "", text)  # \[3\]
    text = re.sub(r"\[cite:[^\]]*\]", "", text)  # [cite: 1]
    m = re.search(r"```(?:yaml)?\n(.*?)```", text, re.S)
    return m.group(1) if m else text


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def channel_matches(brand: str, channel: str) -> bool:
    c = norm(channel)
    keys = [brand.lower(), *BRAND_ALIASES.get(brand.lower(), [])]
    return any(norm(k) and (norm(k) in c or c in norm(k)) for k in keys)


def oembed(video_id: str) -> tuple[int, dict[str, Any]]:
    url = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(
        f"https://www.youtube.com/watch?v={video_id}", safe=""
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            return e.code, {}
        except (urllib.error.URLError, TimeoutError):
            time.sleep(2)
    return 0, {}


def slug(s: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


def duration_from_comment(raw_text: str, entry_id: str) -> int | None:
    m = re.search(rf"id:\s*{re.escape(entry_id)}\b.*?#\s*duration_s:\s*(\d+)", raw_text, re.S)
    if not m:
        return None
    # only accept if no other "- id:" sits between the entry and the duration comment
    span = raw_text[m.start() : m.end()]
    return int(m.group(1)) if span.count("- id:") == 0 else None


@dataclass
class Candidate:
    entry: dict[str, Any]
    origin: str
    video_id: str | None = None
    duration_s: int | None = None
    real_title: str | None = None
    channel: str | None = None
    verdict: str = "keep"  # keep | check | reject
    notes: list[str] = field(default_factory=list)


def main() -> None:
    out_dir = Path(sys.argv[1])
    files = [Path(p) for p in sys.argv[2:]]
    cfg = load_config()
    taxonomy = Taxonomy.model_validate(yaml.safe_load((ROOT / "taxonomy" / "v1.yaml").read_text()))
    max_s = cfg.analysis.max_minutes * 60

    cands: list[Candidate] = []
    for f in files:
        raw = clean(f.read_text(encoding="utf-8"))
        for e in yaml.safe_load(raw) or []:
            c = Candidate(entry=dict(e), origin=f.name)
            c.duration_s = duration_from_comment(raw, str(e.get("id", "")))
            cands.append(c)

    seen: dict[str, Candidate] = {}
    for c in cands:
        e = c.entry
        url = str(e.get("url") or "")
        m = YT_ID.search(url)
        if not m:
            c.verdict = "reject"
            c.notes.append("not a single-video URL (blog/news/channel page); find the video itself")
            continue
        c.video_id = m.group(1)
        if c.video_id in seen:
            c.verdict = "reject"
            c.notes.append(f"duplicate of {seen[c.video_id].entry.get('id')}")
            continue
        seen[c.video_id] = c
        status, meta = oembed(c.video_id)
        if status in (401, 403):
            # Exists, but embedding is disabled or it is restricted: real, needs a manual look.
            c.verdict = "check"
            c.notes.append(f"YouTube {status}: embedding disabled or restricted; open it by hand")
        elif status != 200:
            c.verdict = "reject"
            c.notes.append(f"YouTube says {status or 'no response'}: removed or made up")
            continue
        c.real_title, c.channel = meta.get("title"), meta.get("author_name")
        if not channel_matches(str(e.get("brand", "")), c.channel or ""):
            c.verdict = "check"
            c.notes.append(
                f"uploaded by '{c.channel}', not obviously {e.get('brand')}: re-upload or partner?"
            )
        if c.real_title and norm(c.real_title)[:20] != norm(str(e.get("title", "")))[:20]:
            c.notes.append(f'real title: "{c.real_title}"')
        if c.real_title and LONG_FORM.search(c.real_title):
            c.verdict = "reject"
            c.notes.append("keynote/livestream (title): far over the 5-min analysis cap")
        elif c.duration_s is None:
            c.notes.append("duration unknown")
        elif c.duration_s > max_s:
            c.verdict = "check"
            c.notes.append(f"reported {c.duration_s // 60} min (unverified): over the 5-min cap if true")

    used: set[str] = set()
    kept: list[dict[str, Any]] = []
    for c in cands:
        if c.verdict == "reject":
            continue
        e = c.entry
        fmt = str(e.get("format", "other"))
        fmt = FORMAT_MAP.get(fmt, fmt)
        if fmt not in taxonomy.format:
            c.notes.append(f"format {fmt!r} -> other")
            fmt = "other"
        base = slug(f"{e.get('brand', 'x')}-{(c.real_title or e.get('title', ''))[:40]}")[:60].strip("-")
        new_id, n = base, 2
        while new_id in used:
            new_id, n = f"{base}-{n}", n + 1
        used.add(new_id)
        tags = sorted({slug(str(t)) for t in e.get("tags", []) if slug(str(t))})
        if c.verdict == "check":
            tags.append("check")
        tier = str(e.get("tier", "reference"))
        entry = {
            "id": new_id,
            "url": f"https://www.youtube.com/watch?v={c.video_id}",
            "brand": str(e.get("brand", "")),
            "title": c.real_title or str(e.get("title", "")),
            "format": fmt,
            "tier": tier if tier in ("reference", "average", "competitor", "own") else "reference",
            "why": re.sub(r"\s+", " ", str(e.get("why", ""))).strip().rstrip("."),
            "tags": tags,
            "media": "full",
            "refetchable": True,
            "status": "draft",
        }
        kept.append(entry)
        c.entry = entry

    SourcesFile.model_validate(kept)  # same schema as sources.yaml
    out_dir.mkdir(parents=True, exist_ok=True)
    header = (
        "# Candidates vetted by scripts/vet_sources.py. All entries are drafts: Robert reviews, then moves\n"
        "# chosen ones into sources/sources.yaml with status: ready. Links checked via YouTube oEmbed;\n"
        "# durations could not be verified from the cloud (see candidates-report.md).\n"
    )
    (out_dir / "candidates.yaml").write_text(
        header + yaml.safe_dump(kept, sort_keys=False, allow_unicode=True, width=120)
    )

    def row(c: Candidate) -> str:
        e = c.entry
        dur = f"{c.duration_s // 60}:{c.duration_s % 60:02d}" if c.duration_s else "?"
        notes = "; ".join(c.notes) or "-"
        return f"| {e.get('id')} | {e.get('brand')} | {e.get('tier')} | {e.get('format')} | {dur} | {notes} |"

    lines = ["# Source candidates: vetting report", ""]
    for verdict, title in (
        ("keep", "Verified (link plays, brand's own channel)"),
        ("check", "Check by hand"),
        ("reject", "Rejected"),
    ):
        group = [c for c in cands if c.verdict == verdict]
        lines += [
            f"## {title}: {len(group)}",
            "",
            "| id | brand | tier | format | duration | notes |",
            "|---|---|---|---|---|---|",
        ]
        lines += [row(c) for c in group] + [""]
    (out_dir / "candidates-report.md").write_text("\n".join(lines))
    counts = {v: sum(c.verdict == v for c in cands) for v in ("keep", "check", "reject")}
    print(f"{len(cands)} entries from {len(files)} files: {counts}")


if __name__ == "__main__":
    main()
