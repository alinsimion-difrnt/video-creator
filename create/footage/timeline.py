"""C5 in presenter mode: the kept words on the edited clock, split into scenes at sentence ends.

Fillers and audio events stay in the sound but not in the timeline (captions and cues use real words only).
A scene closes at the first sentence end after `scene_target_s`; scene bounds sit halfway through the pause
between scenes, so every word lies inside its scene's voice.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from lens import __version__
from lens.hashing import cache_key
from lens.schemas.common import Annotator, Provenance
from lens.schemas.create import Timeline, TimelineScene, TimelineWord, TranscriptWord

STAGE = "c5_timing"
_END = (".", "?", "!", "…")


_STUTTER = re.compile(r"^([^\W\d_]{1,3})-(\1[^\W\d_]*.*)$", re.IGNORECASE)


def _sentence_case(words: list[TranscriptWord]) -> list[TranscriptWord]:
    """A sentence's first kept word starts upper-case (a cut "Um, it tracks" reads "It tracks"), and a
    stuttered word reads clean ("t-tracking" -> "tracking"; the sound is untouched)."""
    out = []
    start = True
    for w in words:
        m = _STUTTER.match(w.text)
        if m:
            w = w.model_copy(update={"text": m.group(2)})
        if start and w.text[:1].islower():
            w = w.model_copy(update={"text": w.text[:1].upper() + w.text[1:]})
        out.append(w)
        start = w.text.endswith(_END)
    return out


def build_presenter_timeline(
    project: str, words: list[TranscriptWord], duration_s: float, fps: int, scene_target_s: float
) -> Timeline:
    spoken = _sentence_case([w for w in words if w.kind == "word"])
    if not spoken:
        raise ValueError("no spoken words left after the cuts")
    groups: list[list[TranscriptWord]] = [[]]
    for w in spoken:
        groups[-1].append(w)
        if w.text.endswith(_END) and w.end_s - groups[-1][0].start_s >= scene_target_s:
            groups.append([])
    groups = [g for g in groups if g]
    if len(groups) > 99:
        raise ValueError("more than 99 scenes: raise create.footage.scene_target_s")
    scenes: list[TimelineScene] = []
    out: list[TimelineWord] = []
    start = 0.0
    for k, g in enumerate(groups):
        sid = f"s{k + 1:02d}"
        last = k == len(groups) - 1
        end = duration_s if last else round((g[-1].end_s + groups[k + 1][0].start_s) / 2, 3)
        end = max(end, g[-1].end_s)
        scenes.append(
            TimelineScene(
                scene=sid,
                start_s=round(start, 3),
                end_s=round(end, 3),
                voice_start_s=round(g[0].start_s, 3),
                voice_end_s=round(g[-1].end_s, 3),
            )
        )
        for w in g:
            out.append(TimelineWord(scene=sid, i=len(out), text=w.text, start_s=w.start_s, end_s=w.end_s))
        start = end
    return Timeline(
        provenance=Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CODE,
            input_hash=cache_key({"words": [w.model_dump() for w in words], "duration": duration_s}),
            created_at=datetime.now(UTC),
        ),
        project=project,
        fps=fps,
        total_s=round(duration_s, 3),
        scenes=scenes,
        words=out,
    )
