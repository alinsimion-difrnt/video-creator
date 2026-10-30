"""`gold/<id>/gold.yaml`: Robert's corrected answers for the G2 gold set (BUILD_PLAN 11.2).

`lens gold seed` copies the annotators' answers for the shots and a sample of events, each item
`pending`. Robert reviews them on the gold review page; `lens gold import` writes his verdicts back:
`confirmed` (the annotator was right) or `corrected` (the values here are his). `lens eval` scores
the annotations against every item that is not `pending`. Only labels are gold; timing stays measured.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from lens.schemas.common import Provenance, Slug, Strict

Status = Literal["pending", "confirmed", "corrected"]


class GoldShot(Strict):
    shot: str = Field(pattern=r"^s\d{3,}$")
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)
    shot_type: Slug
    composition: Slug
    transition_in: Slug
    depth_cues: list[Slug]
    status: Status = "pending"
    note: str | None = None


class GoldElement(Strict):
    id: str = Field(pattern=r"^[bm]\d{2}$")  # candidate box id, or m<element index> for a manual box
    label: str
    role: Slug
    change_types: list[Slug] = Field(min_length=1)
    moves: bool = True  # False: the annotator picked something that is not an element of this event


class GoldSfx(Strict):
    id: str = Field(pattern=r"^x\d{3,}$")
    sync_s: float
    label: Slug  # taxonomy.sfx, or "unsure"


class GoldEvent(Strict):
    event: str = Field(pattern=r"^e\d{3,}$")
    shot: str
    start_s: float
    end_s: float
    elements: list[GoldElement]
    missed: list[str] = Field(default_factory=list)  # candidate box ids that move but were not picked
    pattern: Slug  # taxonomy.patterns, or "other"
    sfx: list[GoldSfx]
    status: Status = "pending"
    note: str | None = None


class GoldFile(Strict):
    provenance: Provenance
    video: Slug
    watch_url: str | None  # the public page, for checking motion and sound by ear
    shots: list[GoldShot]
    events: list[GoldEvent]
