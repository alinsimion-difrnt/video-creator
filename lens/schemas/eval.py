"""`runs/eval/<hash>.json`: `lens eval` scores for the annotation layer (BUILD_PLAN 11.2, M6).

`<hash>` covers `.claude/skills/**` and `taxonomy/**`, so a skill or taxonomy change needs a new eval.
Three machine checks, no human gold (Robert's call at G2):
- answer key: Claude's choices on our own render against its HyperFrames source (exact truth);
- consistency: a blind second annotation of a sample of events against the first;
- measured share: how many annotated reference events got code-measured timing.
"""

from __future__ import annotations

from pydantic import Field

from lens.schemas.common import Provenance, Sha256, Slug, Strict


class Ratio(Strict):
    hits: float = Field(ge=0)
    n: float = Field(ge=0)
    value: float | None = Field(default=None, ge=0, le=1)  # hits / n; None when n is 0


class AnswerKeyScores(Strict):
    video: Slug
    events: int = Field(ge=0)
    box_precision: Ratio  # chosen elements that are a real tween target (of those the key can judge)
    box_unjudged: int = Field(ge=0)  # chosen elements where the key animates nothing (text swaps, captions)
    box_recall: Ratio  # real tween targets some chosen element covers
    change_types: Ratio  # true changes (fade, slide direction, scale...) the labels name
    change_types_with_measured: Ratio  # same, with the record's measured changes added (S7 channels)
    sfx_classifier: Ratio  # S3 label alone, on the SFX Claude reviewed
    sfx_after_review: Ratio  # final label after Claude's review, same SFX
    estimate_easing: Ratio  # Claude's easing guesses (model_estimate) against the true ease
    measured_easing: Ratio  # S7's fitted class against the true ease


class ConsistencyScores(Strict):
    run: str
    events: list[str]  # <video>/<eid>
    missing: list[str]  # sampled events with no re-annotation yet
    boxes: Ratio  # candidate box ids: intersection over union, summed
    pattern: Ratio
    role: Ratio  # on boxes both picked
    change_types: Ratio  # intersection over union on boxes both picked
    sfx_label: Ratio


class MeasuredShare(Strict):
    tier: str
    events: int = Field(ge=0)  # annotated events
    measured: int = Field(ge=0)  # with at least one element timed by S7
    share: float | None
    target: float
    ok: bool


class EvalFile(Strict):
    provenance: Provenance
    hash: Sha256
    answer_key: AnswerKeyScores | None
    consistency: ConsistencyScores | None
    measured: MeasuredShare
