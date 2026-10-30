"""C11 captions: narration words grouped into burned-in caption groups (one clock with the timeline).

Sentences end groups; a pause of `gap_split_s` always starts one. A sentence longer than `max_words` or
`max_chars` is split where it balances best, preferring a comma or a pause. A group shows `lead_s` before its
first word and holds `hold_s` after its last, handing over `seam_s` before the next group. Rules per frame
come from config `create.design.captions` (landscape follows Acme v2: 65 groups of 2-6 words).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

from lens import __version__
from lens.hashing import cache_key
from lens.schemas.common import Annotator, Provenance
from lens.schemas.config import CaptionRules, LensConfig
from lens.schemas.create import CaptionGroup, Captions, CaptionWord, TimedWord, Timeline, Tokens

STAGE = "c11_assemble"
SENTENCE_END = (".", "?", "!", "…")
SOFT_BREAK = (",", ";", ":")
COMMA_BONUS = 12  # characters of imbalance a comma or pause is worth when choosing a split
FUNCTION_PENALTY = 40  # characters of imbalance worth avoiding a group that ends on "to", "the", "și" ...
PAUSE_BONUS = 20


def _chars(ws: list[TimedWord]) -> int:
    return len(" ".join(w.text for w in ws))


def _bare(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalnum() or ch == "'")


def _split(
    ws: list[TimedWord], rules: CaptionRules, function: frozenset[str] = frozenset()
) -> list[list[TimedWord]]:
    if (len(ws) <= rules.max_words and _chars(ws) <= rules.max_chars) or len(ws) == 1:
        return [ws]
    best_k, best_cost = 1, float("inf")
    for k in range(1, len(ws)):
        cost = float(abs(_chars(ws[:k]) - _chars(ws[k:])))
        if _bare(ws[k - 1].text) in function and not ws[k - 1].text.endswith(SOFT_BREAK):
            cost += FUNCTION_PENALTY
        if ws[k - 1].text.endswith(SOFT_BREAK):
            cost -= COMMA_BONUS
        if ws[k].start_s - ws[k - 1].end_s >= rules.gap_split_s / 2:
            cost -= PAUSE_BONUS
        if cost < best_cost:
            best_k, best_cost = k, cost
    return _split(ws[:best_k], rules, function) + _split(ws[best_k:], rules, function)


def _runs(words: list[TimedWord], rules: CaptionRules) -> list[list[TimedWord]]:
    """Sentences, also broken at long pauses and scene changes."""
    runs: list[list[TimedWord]] = [[]]
    for i, w in enumerate(words):
        runs[-1].append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        scene_change = nxt is not None and getattr(nxt, "scene", None) != getattr(w, "scene", None)
        if nxt is not None and (
            w.text.endswith(SENTENCE_END) or nxt.start_s - w.end_s >= rules.gap_split_s or scene_change
        ):
            runs.append([])
    return [r for r in runs if r]


def group_words(
    words: list[TimedWord], rules: CaptionRules, function_words: list[str] | None = None
) -> list[CaptionGroup]:
    """Caption groups; a group avoids ending on a function word (config `caption_function_words`)."""
    function = frozenset(_bare(w) for w in function_words or [])
    chunks = [c for run in _runs(words, rules) for c in _split(run, rules, function)]
    spans: list[tuple[float, float]] = []
    for n, chunk in enumerate(chunks):
        start = max(0.0, chunk[0].start_s - rules.lead_s)
        if spans:
            start = max(start, spans[-1][1])  # never before the previous group ends
        end = chunk[-1].end_s + rules.hold_s
        if n + 1 < len(chunks):
            end = min(end, chunks[n + 1][0].start_s - rules.lead_s - rules.seam_s)
        end = max(end, chunk[-1].start_s + 0.05, start + 0.05)
        spans.append((round(start, 3), round(end, 3)))
    groups: list[CaptionGroup] = []
    for chunk, (start, end) in zip(chunks, spans, strict=True):
        if groups and start < groups[-1].end:  # rounding must not reintroduce an overlap
            start = groups[-1].end
        groups.append(
            CaptionGroup(
                start=start,
                end=max(end, start + 0.05),
                words=[
                    CaptionWord(i=w.i, w=w.text, t=round(w.start_s, 3), end=round(w.end_s, 3)) for w in chunk
                ],
            )
        )
    return groups


def run_captions(root: Path, project: str, cfg: LensConfig) -> tuple[Path, Captions]:
    base = root / "projects" / project
    timeline = Timeline.model_validate(json.loads((base / "timeline.json").read_text()))
    tokens = Tokens.model_validate(json.loads((base / "tokens.json").read_text()))
    design = cfg.create.design
    rules = design.captions[tokens.frame]
    brief = yaml.safe_load((base / "brief.yaml").read_text()) if (base / "brief.yaml").exists() else {}
    language = (brief or {}).get("language", "en")
    function = design.caption_function_words.get(language) or [
        w for v in design.caption_function_words.values() for w in v
    ]
    groups = group_words(list(timeline.words), rules, function)
    captions = Captions(
        provenance=Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CODE,
            input_hash=cache_key(
                {"words": [w.model_dump() for w in timeline.words], "rules": rules.model_dump()}
            ),
            created_at=datetime.now(UTC),
        ),
        project=project,
        frame=tokens.frame,
        groups=groups,
    )
    path = base / "captions.json"
    path.write_text(captions.model_dump_json(indent=1) + "\n")
    return path, captions
