"""`videos/<id>/record.json`: S8 merges code signals, Claude's annotations and S7 measurements into one
record per video (BUILD_PLAN 7.6).

Every number says where it comes from. Shot and event times, palette and SFX timing are code
(`measured`). Element timing is `measured` when S7 fitted it above `measure.min_fit_quality`, otherwise the
annotator's fallback guess (`model_estimate`). Labels, patterns and scores are Claude's (the `annotation`,
`pattern` and `summary` blocks), never numbers about timing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from lens.schemas.annotation import BuildHint, Confidence, Pattern, Shot, VideoSummary
from lens.schemas.common import Provenance, Slug, Strict, ValueSource

Box = tuple[int, int, int, int]  # proxy pixels, x0 y0 x1 y1


class RecordShot(Strict):
    id: str = Field(pattern=r"^s\d{3,}$")
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)
    transition_in: str | None  # detected kind (code); the annotator's reading is in `annotation`
    motion_energy: float = Field(ge=0)
    wpm: float | None
    annotation: Shot | None  # A1; None when the video has no A1 yet


class ElementTiming(Strict):
    source: ValueSource
    duration_ms: float | None = Field(default=None, ge=0)
    start_s: float | None = None
    ease: str | None = None  # GSAP ease (measured only)
    easing_class: str | None = None  # class of the joint-fit ease (taxonomy), or the annotator's guess
    bezier: str | None = None
    spring: dict[str, float] | None = None  # Remotion {mass, stiffness, damping}
    overshoot_pct: float | None = Field(default=None, ge=0)
    quality: float | None = Field(default=None, ge=0, le=1)  # best channel fit
    channels: list[str] = Field(default_factory=list)  # x, y, scale, opacity that moved
    changes: list[str] = Field(default_factory=list)  # what the channels show: fade, slide_up, scale_up...
    stagger_unit: str | None = None
    stagger_ms: float | None = None


class RecordElement(Strict):
    id: str = Field(pattern=r"^[bm]\d{2}$")  # candidate box id, or m<element index> for a manual box
    box: Box | None  # None when neither S7 nor the evidence is available
    box_source: Literal["candidate", "manual"]
    label: str
    role: Slug
    role_other: str | None
    change_types: list[Slug]
    change_other: str | None
    is_text: bool
    text: str | None
    text_unit: str | None
    timing: ElementTiming | None  # None: not measured and no estimate given
    sfx_offset_ms: dict[str, float] = Field(default_factory=dict)  # SFX id -> onset minus landing


class RecordEvent(Strict):
    id: str = Field(pattern=r"^e\d{3,}$")
    shot: str
    kind: str
    start_s: float
    end_s: float
    camera_move: str
    status: Literal["annotated", "propagated", "skipped", "pending"]  # pending: a task, no output yet
    skip_reason: str | None = None
    of: str | None = None  # duplicate (propagated) or overlap (skipped): the event whose task covers it
    pattern: Pattern | None = None
    build_hint: BuildHint | None = None
    confidence: Confidence | None = None
    notes: str | None = None
    elements: list[RecordElement] = Field(default_factory=list)
    sfx: list[str] = Field(default_factory=list)  # SFX ids reviewed in this event


class RecordSfx(Strict):
    id: str = Field(pattern=r"^x\d{3,}$")
    sync_s: float
    classifier_label: str  # S3 rules/CLAP label
    clap_label: str | None
    clap_score: float | None
    label: str  # final label
    label_source: Literal["claude", "code"]  # claude: confirmed or overridden in an A2 review
    verdict: Literal["confirm", "override", "unsure"] | None  # None: no event reviewed it
    events: list[str]
    on_beat: bool
    reveal_offset_ms: float | None


class Check(Strict):
    name: str
    ok: bool
    detail: str | None = None


class Coverage(Strict):
    events: int = Field(ge=0)
    annotated: int = Field(ge=0)
    propagated: int = Field(ge=0)
    skipped: int = Field(ge=0)
    pending: int = Field(ge=0)
    elements: int = Field(ge=0)
    measured: int = Field(ge=0)
    estimated: int = Field(ge=0)


class RecordFile(Strict):
    provenance: Provenance
    video: Slug
    brand: str
    title: str
    format: str
    tier: str
    duration_s: float = Field(gt=0)
    fps: float = Field(gt=0)
    frame_size: tuple[int, int]
    palette: list[str]
    summary: VideoSummary | None
    shots: list[RecordShot]
    events: list[RecordEvent]
    sfx: list[RecordSfx]
    coverage: Coverage
    checks: list[Check]
