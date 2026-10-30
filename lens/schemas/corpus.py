"""`corpus/stats/*.json` (S9, BUILD_PLAN 8): weighted corpus statistics, and the `other`-pattern clusters
in taxonomy/proposals.yaml.

Every value is weighted (config `synth.weights`): tier x overall score, and for measured motion also the
fit quality. A `Stat` gives the weighted median with a bootstrap interval, so a card can say
"median 420 ms (380-470, n=37)". Only code-measured numbers feed the motion and sound stats; the
annotators' estimates never do. Shares are weighted fractions.
"""

from __future__ import annotations

from pydantic import Field

from lens.schemas.common import Provenance, Slug, Strict


class Stat(Strict):
    n: int = Field(ge=0)  # observations
    videos: int = Field(ge=0)  # distinct videos they come from
    weight: float = Field(ge=0)
    median: float | None
    p25: float | None
    p75: float | None
    ci: tuple[float, float] | None  # bootstrap interval of the median; None below synth.min_n


Shares = dict[str, float]  # label -> weighted share (sums to 1)


class Weighting(Strict):
    tier: dict[str, float]
    score_from: str  # summary.scores.<this>.score / 5
    score_missing: float
    quality: bool  # measured values also weighted by fit quality


class SpringCluster(Strict):
    n: int = Field(ge=0)
    zeta: Stat  # damping ratio
    settle_ms: Stat
    remotion: dict[str, float]  # {mass, stiffness, damping} at the cluster medians, mass 1


class MotionStats(Strict):
    provenance: Provenance
    weighting: Weighting
    videos: int
    elements: int  # measured elements used
    duration_ms_by_role: dict[str, Stat]
    duration_ms_by_change: dict[str, Stat]
    easing_mix: Shares
    easing_by_role: dict[str, Shares]
    ease_mix: Shares  # GSAP ease names of the joint fits
    ease_by_class: dict[str, str] = Field(default_factory=dict)  # most weighted GSAP ease in each class
    bezier_by_class: dict[str, str] = Field(
        default_factory=dict
    )  # weighted-median CSS cubic-bezier per class
    overshoot_share: float | None  # measured elements with overshoot
    overshoot_pct: Stat  # among those
    springs: list[SpringCluster]
    stagger_ms_by_unit: dict[str, Stat]


class SoundStats(Strict):
    provenance: Provenance
    weighting: Weighting
    videos: int
    sfx_per_min: Stat
    sfx_label_mix: Shares  # final labels (claude-reviewed or code)
    reveal_offset_ms_by_label: dict[str, Stat]  # SFX onset minus the nearest reveal landing
    sfx_on_beat_share: float | None
    integrated_lufs: Stat
    true_peak_dbtp: Stat
    lra_lu: Stat
    ducking_db: Stat


class PacingStats(Strict):
    provenance: Provenance
    weighting: Weighting
    videos: int
    shot_s_by_format: dict[str, Stat]
    shot_s: Stat
    pace_cv: Stat
    cuts_on_beat_share: Stat
    time_to_first_ui_s: Stat  # start of the first shot A1 calls ui_*
    wpm: Stat
    pitch_std_semitones: Stat
    pause_mean_ms: Stat
    articulation_wpm: Stat | None = None  # speaking rate without pauses
    pause_p90_ms: Stat | None = None
    energy_std_db: Stat | None = None  # loudness variation of the voice
    phrase_rate_cv: Stat | None = None  # how much the speaking rate varies between phrases
    pause_length_mix: Shares = Field(default_factory=dict)  # short / medium / long pauses
    caption_words_per_group: Stat
    duration_s_by_format: dict[str, Stat]


class PatternExample(Strict):
    video: Slug
    event: str
    score: float | None  # the video's overall score


class PatternStats(Strict):
    id: Slug
    events: int = Field(ge=0)
    videos: int = Field(ge=0)
    weight: float = Field(ge=0)
    duration_ms: Stat  # measured elements of its events
    easing_mix: Shares
    change_mix: Shares
    role_mix: Shares
    sfx_label_mix: Shares
    sfx_offset_ms: Stat
    examples: list[PatternExample]  # best-weighted first


class PatternsFile(Strict):
    provenance: Provenance
    weighting: Weighting
    patterns: list[PatternStats]
    other_events: int  # annotated as "other"; clustered into taxonomy/proposals.yaml


class Proposal(Strict):
    """A cluster of `other` patterns: a candidate for the taxonomy (gate G4)."""

    id: Slug  # suggested pattern id
    name: str  # the most common proposed name in the cluster
    members: list[str]  # <video>/<event>
    videos: int = Field(ge=1)
    names: list[str]  # every proposed name in the cluster, most common first
    nearest_pattern: str | None  # closest existing taxonomy pattern
    similarity: float  # cosine to it
    suggestion: str  # "new" | "merge:<pattern id>"
    plain: str | None = None  # what it is, in plain words (Claude, for G4)
    recommendation: str | None = None  # "add" | "merge:<pattern id>" | "reject", with `why` (Claude)
    why: str | None = None
    status: str = "proposed"  # G4: approved | merged:<id> | rejected (from Robert's verdict)
