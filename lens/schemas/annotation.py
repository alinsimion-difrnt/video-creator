"""A1 (`videos/<id>/a1[.pN].json`) and A2 (`videos/<id>/events/<eid>.a2.json`): Claude's annotations
(BUILD_PLAN 7.4, Appendix B). Shapes are checked here; enums against the taxonomy, and ids (shots, words,
boxes, SFX candidates, input hashes) against the packet in `lens.validate`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from lens.schemas.common import Provenance, Slug, Strict

Confidence = Literal["high", "medium", "low"]
WordSpan = tuple[int, int]  # first and last word index, inclusive


class Shot(Strict):
    shot: str = Field(pattern=r"^s\d{3,}$")
    shot_type: Slug
    shot_type_other: str | None = None
    composition: Slug
    composition_other: str | None = None
    focal_element: str = Field(min_length=1)
    transition_in: Slug
    transition_other: str | None = None
    on_screen_text: list[str]  # verbatim, one entry per text block
    text_word_count: int = Field(ge=0)
    typography: str | None  # style, weight, case, tracking; font names only as low-confidence guesses
    depth_cues: list[Slug]
    what_happens: str = Field(min_length=1)
    build_rebuild: str = Field(min_length=1)  # one concrete sentence a developer can implement
    confidence: Confidence


class Beat(Strict):
    beat: Slug
    shots: list[str] = Field(min_length=1)
    words: WordSpan | None = None


class Hook(Strict):
    text: str
    technique: Slug
    technique_other: str | None = None
    shots: list[str] = Field(min_length=1)
    words: WordSpan | None = None


class Cta(Strict):
    text: str | None  # None: the video has no call to action
    shots: list[str]


class SignatureMoment(Strict):
    shots: list[str] = Field(min_length=1)
    description: str = Field(min_length=1)
    why_premium: str = Field(min_length=1)


class Score(Strict):
    score: int | None = Field(ge=1, le=5)  # None only when it does not apply (e.g. no voice-over)
    evidence: str = Field(min_length=1)
    refs: list[str] = Field(default_factory=list)  # shot ids / word indices ("s003", "w12")


class Scores(Strict):
    hook: Score
    clarity: Score
    ui_showcase: Score
    motion_polish: Score
    sound_design: Score  # judged from the audio facts plus visuals; say so in the evidence
    vo_script_quality: Score
    brand_consistency: Score
    works_muted: Score
    overall: Score

    @model_validator(mode="after")
    def _applicable(self) -> Scores:
        for name in ("hook", "clarity", "motion_polish", "overall"):
            if getattr(self, name).score is None:
                raise ValueError(f"{name}: a score is required")
        return self


class Localization(Strict):
    score: int = Field(ge=1, le=5)
    baked_in_text: bool
    vo_dependent: bool
    notes: str


class VideoSummary(Strict):
    """Per-video judgement; written by the last A1 part (it reads the earlier parts)."""

    beats: list[Beat] = Field(min_length=1)
    hook: Hook
    cta: Cta
    tone: str = Field(min_length=1)
    signature_moments: list[SignatureMoment] = Field(max_length=3)
    scores: Scores
    localization_friendliness: Localization


class A1File(Strict):
    provenance: Provenance
    video: Slug
    task: str = Field(pattern=r"^a1-p\d+$")
    shots: list[Shot] = Field(min_length=1)
    summary: VideoSummary | None = None

    @model_validator(mode="after")
    def _unique(self) -> A1File:
        ids = [s.shot for s in self.shots]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate shot ids")
        return self


class Estimates(Strict):
    """Fallback guesses; S7 measures replace them. Always model estimates."""

    source: Literal["model_estimate"] = "model_estimate"
    duration_ms: float | None = Field(default=None, gt=0)
    easing_class: Slug | None = None


class Element(Strict):
    box: str | None = Field(default=None, pattern=r"^b\d{2}$")  # a candidate box id
    manual_box: tuple[int, int, int, int] | None = None  # [ymin, xmin, ymax, xmax] in 0..1000
    manual_reason: str | None = None
    label: str = Field(min_length=1)
    role: Slug
    role_other: str | None = None
    change_types: list[Slug] = Field(min_length=1)
    change_other: str | None = None
    is_text: bool
    text: str | None = None  # verbatim
    text_unit: Literal["whole", "line", "word", "char", "unknown"] | None = None
    estimates: Estimates | None = None

    @model_validator(mode="after")
    def _box(self) -> Element:
        if (self.box is None) == (self.manual_box is None):
            raise ValueError("give exactly one of box (a candidate id) or manual_box")
        if self.manual_box is not None:
            y0, x0, y1, x1 = self.manual_box
            if not (0 <= y0 < y1 <= 1000 and 0 <= x0 < x1 <= 1000):
                raise ValueError("manual_box must be [ymin, xmin, ymax, xmax] within 0..1000")
            if not self.manual_reason:
                raise ValueError("manual_box needs manual_reason")
        if self.is_text and (self.text is None or self.text_unit is None):
            raise ValueError("text elements need text and text_unit")
        return self


class SfxReview(Strict):
    id: str = Field(pattern=r"^x\d{3,}$")  # an SFX candidate id from facts.json
    verdict: Literal["confirm", "override", "unsure"]
    label: Slug  # the final label (taxonomy.sfx); "unsure" when the verdict is unsure
    note: str | None = None

    @model_validator(mode="after")
    def _consistent(self) -> SfxReview:
        if (self.verdict == "unsure") != (self.label == "unsure"):
            raise ValueError("label is 'unsure' exactly when the verdict is unsure")
        return self


class Pattern(Strict):
    id: Slug  # taxonomy.patterns, or "other"
    proposed_name: str | None = None  # "other": 2-4 words, reusable
    description: str = Field(min_length=1)
    why_premium: str = Field(min_length=1)

    @model_validator(mode="after")
    def _other(self) -> Pattern:
        if self.id == "other":
            words = len((self.proposed_name or "").split())
            if not 2 <= words <= 4:
                raise ValueError("pattern 'other' needs a proposed_name of 2-4 words")
        return self


class BuildHint(Strict):
    gsap: str = Field(min_length=1)  # HyperFrames/GSAP phrasing first
    remotion: str = Field(min_length=1)


class A2File(Strict):
    provenance: Provenance
    video: Slug
    event: str = Field(pattern=r"^e\d{3,}$")
    task: str = Field(pattern=r"^a2-e\d{3,}$")
    elements: list[Element] = Field(max_length=12)
    sfx_review: list[SfxReview]
    pattern: Pattern
    build_hint: BuildHint
    confidence: Confidence
    notes: str | None = None

    @model_validator(mode="after")
    def _ids(self) -> A2File:
        if self.task != f"a2-{self.event}":
            raise ValueError(f"task {self.task} does not match event {self.event}")
        boxes = [e.box for e in self.elements if e.box]
        if len(boxes) != len(set(boxes)):
            raise ValueError("a candidate box is used by more than one element")
        sfx = [r.id for r in self.sfx_review]
        if len(sfx) != len(set(sfx)):
            raise ValueError("duplicate sfx_review ids")
        return self
