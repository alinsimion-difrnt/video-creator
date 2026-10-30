"""S5 annotation packets (BUILD_PLAN 7.3): what an annotator reads, and the committed task manifest.

Annotators only use ids given here: shot ids, word indices, event ids, box ids (candidates.json),
SFX candidate ids. They never invent timestamps.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from lens.schemas.common import Provenance, Slug, Strict


class ShotAnchor(Strict):
    id: str
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)
    transition_in: str | None  # kind of the transition into this shot
    events: int = Field(ge=0)


class WordAnchor(Strict):
    i: int = Field(ge=0)
    text: str
    start_s: float = Field(ge=0)
    end_s: float = Field(ge=0)


class SfxFact(Strict):
    id: str
    sync_s: float
    label: str
    clap_label: str | None = None
    clap_score: float | None = None
    offset_ms: float | None = None  # sync minus event start (event facts only)


class Anchors(Strict):
    """`pass1/anchors.json`: the ids and times a Pass 1 (A1) annotator may cite."""

    provenance: Provenance
    video: Slug
    duration_s: float = Field(gt=0)
    fps: float = Field(gt=0)
    shots: list[ShotAnchor]
    words: list[WordAnchor]
    bpm: float | None
    beats_s: list[float]
    integrated_lufs: float | None
    palette: list[str]  # hex, by share
    sfx: list[SfxFact]


class CameraFact(Strict):
    move: str  # S3 camera_move
    pan_x: float  # summed global shift over the burst, fraction of width (+ = content moves right)
    pan_y: float
    scale: float  # product of per-frame scale over the burst


class EventFacts(Strict):
    """`events/<eid>/facts.json`: measured context for one event (A2)."""

    provenance: Provenance
    video: Slug
    event: str
    shot: str
    start_s: float
    end_s: float
    burst_frames: tuple[int, int]
    filmstrip_frames: list[int]
    energy: list[float]  # per burst frame, inside the crop
    camera: CameraFact
    sfx: list[SfxFact]
    words: list[WordAnchor]  # spoken around the event
    siblings: list[str] = Field(default_factory=list)  # repeated events that share this result


class PacketTask(Strict):
    id: str = Field(pattern=r"^(a1-p\d+|a2-e\d{3,})$")
    kind: Literal["a1", "a2"]
    images: list[str] = Field(min_length=1)  # paths relative to data/packets/<video>/
    files: list[str]  # JSON the annotator reads, same base
    shots: list[str] = Field(default_factory=list)  # a1: shot range covered
    event: str | None = None  # a2
    siblings: list[str] = Field(default_factory=list)  # a2: events the result is propagated to
    output: str  # repo-relative path the annotator writes
    input_hash: str


class Skipped(Strict):
    event: str
    reason: Literal["low_energy", "small", "caption_band", "tier", "duplicate", "overlap"]
    of: str | None = None  # duplicate / overlap: the event whose task covers it


class PacketManifest(Strict):
    """`packets/<id>/manifest.json`, the only committed packet file. Status is derived from the
    outputs on disk by `lens status`, so this file never changes when annotation happens."""

    provenance: Provenance
    video: Slug
    tier: str
    max_images_per_task: int = Field(ge=1)
    event_images: int = Field(ge=1)
    tasks: list[PacketTask]
    skipped: list[Skipped]

    @model_validator(mode="after")
    def _budgets(self) -> PacketManifest:
        for t in self.tasks:
            limit = self.event_images if t.kind == "a2" else self.max_images_per_task
            if len(t.images) > limit:
                raise ValueError(f"{t.id}: {len(t.images)} images over the budget of {limit}")
        ids = [t.id for t in self.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate task ids")
        return self
