"""`videos/<id>/measure/<eid>.json`: S7 measurements of the elements chosen in an event (BUILD_PLAN 7.5).

Numbers here come from code (`source: measured`). Renderer-agnostic: every timing has a GSAP ease
(primary, HyperFrames), a CSS cubic-bezier and a Remotion spring config.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from lens.schemas.common import Provenance, Slug, Strict, ValueSource


class GsapOut(Strict):
    ease: str  # e.g. "power3.out", "back.out(1.4)"
    duration_ms: float = Field(ge=0)
    rmse: float = Field(ge=0)


class SpringOut(Strict):
    zeta: float = Field(gt=0)
    omega0: float = Field(gt=0)  # rad/s, mass 1
    settle_ms: float = Field(ge=0)  # within the end tolerance
    remotion: dict[str, float]  # {mass, stiffness, damping}
    remotion_exact: bool  # False when overdamped: Remotion draws zeta >= 1 as critically damped
    rmse: float = Field(ge=0)


class ChannelOut(Strict):
    name: Literal["x", "y", "scale", "opacity"]
    start_f: int = Field(ge=0)
    end_f: int = Field(ge=0)
    start_value: float
    end_value: float
    observed_start: bool  # False: the element became measurable mid-motion (e.g. fading in)
    cls: Literal["linear", "ease_in", "ease_out", "ease_in_out", "spring", "ambiguous"]
    gsap: GsapOut
    bezier: str  # CSS cubic-bezier(...), also usable by GSAP CustomEase
    bezier_rmse: float = Field(ge=0)
    spring: SpringOut
    overshoot_pct: float = Field(ge=0)
    duration_ms: float = Field(ge=0)
    fit_quality: float = Field(ge=0, le=1)


class TimingOut(Strict):
    """One ease and timing shared by all channels of the element (one tween moving and fading it)."""

    ease: str
    start_s: float
    duration_ms: float = Field(ge=0)
    rmse: float = Field(ge=0)


class StaggerOut(Strict):
    unit: Literal["word", "all", "none"]
    stagger_ms: float | None
    reveal_frames: list[int | None]


class ElementOut(Strict):
    box: str = Field(pattern=r"^[bm]\d{2}$")  # candidate box id, or m<element index> for an A2 manual box
    xyxy: tuple[int, int, int, int] | None = None  # the box measured, proxy pixels
    method: Literal["ncc"]
    mean_confidence: float = Field(ge=-1, le=1)
    channels: list[ChannelOut]
    timing: TimingOut | None
    stagger: StaggerOut | None = None
    sfx_offset_ms: dict[str, float] = Field(default_factory=dict)  # SFX id -> onset minus landing
    source: ValueSource
    quality: float = Field(ge=0, le=1)  # best channel fit quality; below the threshold -> model_estimate


class MeasureFile(Strict):
    provenance: Provenance
    video: Slug
    event: str = Field(pattern=r"^e\d{3,}$")
    fps: float = Field(gt=0)
    elements: list[ElementOut]
    failed: dict[str, str] = Field(default_factory=dict)  # box id -> why it could not be measured
