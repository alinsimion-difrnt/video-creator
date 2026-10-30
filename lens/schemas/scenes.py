"""Scene archetypes (BUILD_PLAN 8.5): which kind of scene each annotated shot is, and the code-measured
stats per kind.

`corpus/scenes/<batch>.json` (A3, text only): Claude sorts each shot of a batch into a taxonomy
`scene_archetype`, or `other` with a proposed name, from what A1 and A2 already said about it.
`corpus/stats/scenes.json` (S9): durations, motion, transitions, beats and SFX cues per archetype.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from lens.schemas.common import Provenance, Slug, Strict
from lens.schemas.corpus import Shares, Stat, Weighting


class SceneAssignment(Strict):
    video: Slug
    shot: str = Field(pattern=r"^s\d{3,}$")
    archetype: Slug  # taxonomy scene_archetype, or "other"
    proposed_name: str | None = None  # "other": 2-4 words, reusable
    confidence: Literal["high", "medium", "low"]

    @model_validator(mode="after")
    def _other(self) -> SceneAssignment:
        if self.archetype == "other":
            words = len((self.proposed_name or "").split())
            if not 2 <= words <= 4:
                raise ValueError("archetype 'other' needs a proposed_name of 2-4 words")
        return self


class SceneBatch(Strict):
    provenance: Provenance
    batch: str = Field(pattern=r"^b\d{2,}$")
    items: list[SceneAssignment]


class SceneExample(Strict):
    video: Slug
    shot: str
    score: float | None


class ArchetypeStats(Strict):
    id: Slug
    shots: int = Field(ge=0)
    videos: int = Field(ge=0)
    weight: float = Field(ge=0)
    duration_s: Stat
    events_per_shot: Stat  # annotated motion events in the shot
    first_motion_s: Stat  # first event start minus shot start
    pattern_mix: Shares
    transition_mix: Shares  # A1's reading of the way in
    shot_type_mix: Shares
    beat_mix: Shares  # story beats the shot belongs to (A1 summary)
    sfx_label_mix: Shares
    sfx_offset_s_by_label: dict[str, Stat]  # SFX onset minus shot start
    examples: list[SceneExample]


class ScenesFile(Strict):
    provenance: Provenance
    weighting: Weighting
    shots: int  # assigned shots in weighted videos
    archetypes: list[ArchetypeStats]
    other_shots: int
