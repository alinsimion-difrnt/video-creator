"""`exports/*.json` (S10, BUILD_PLAN 8.6): the corpus findings in the shape Phase 2 builds from.

Self-contained and brand-free: no video ids, no examples, no third-party text. Every timing number
comes from the S9 stats; the words come from the approved A3 cards. Held-back cards (gate G4) are left
out.
"""

from __future__ import annotations

from pydantic import Field

from lens.schemas.cards import Build, Slot
from lens.schemas.common import Provenance, Slug, Strict
from lens.schemas.corpus import Shares


class Range(Strict):
    """A measured value for building: the weighted median and the typical (25-75%) range."""

    median: float | None
    low: float | None  # 25th percentile
    high: float | None  # 75th percentile
    n: int = Field(ge=0)
    videos: int = Field(ge=0)


class EasingClass(Strict):
    gsap: str  # most used GSAP ease of the class in the corpus
    css: str  # CSS easing (cubic-bezier, or "linear")
    share: float  # of measured elements


class SpringPreset(Strict):
    name: Slug  # snappy | smooth | bouncy (by damping ratio)
    remotion: dict[str, float]  # {mass, stiffness, damping}
    zeta: float | None
    settle_ms: Range
    share: float


class MotionTokens(Strict):
    provenance: Provenance
    duration_ms_by_role: dict[str, Range]
    duration_ms_by_change: dict[str, Range]
    easing: dict[str, EasingClass]
    easing_by_role: dict[str, Shares]
    springs: list[SpringPreset]
    overshoot_share: float | None
    overshoot_pct: Range
    word_stagger_ms: Range
    all_at_once_share: float | None  # text reveals that appear in one go rather than word by word


class LoudnessSpec(Strict):
    destination: Slug
    min_lufs: float
    max_lufs: float
    max_true_peak_dbtp: float
    source: str


class SoundSpec(Strict):
    provenance: Provenance
    sfx_per_min: Range
    sfx_mix: Shares
    sfx_offset_ms_to_reveal: dict[str, Range]  # SFX onset minus the reveal landing, by type
    sfx_on_beat_share: float | None
    corpus_lufs: Range
    corpus_true_peak_dbtp: Range
    corpus_lra_lu: Range
    ducking_db: Range
    targets: list[LoudnessSpec]


class PacingSpec(Strict):
    provenance: Provenance
    shot_s: Range
    shot_s_by_format: dict[str, Range]
    duration_s_by_format: dict[str, Range]
    scene_s_by_archetype: dict[str, Range]
    pace_cv: Range
    cuts_on_beat_share: Range
    time_to_first_ui_s: Range
    caption_words_per_group: Range


class VoiceSpec(Strict):
    provenance: Provenance
    wpm: Range
    articulation_wpm: Range
    pause_mean_ms: Range
    pause_p90_ms: Range
    pause_length_mix: Shares
    pitch_std_semitones: Range
    energy_std_db: Range
    phrase_rate_cv: Range
    brief: list[str]  # plain instructions for the voice, built from the ranges


class ExportPattern(Strict):
    id: Slug
    name: str
    summary: str
    when_to_use: list[str]
    avoid_when: list[str]
    steps: list[str]
    build: Build
    sound: str
    why_premium: str
    duration_ms: Range
    easing_mix: Shares
    change_mix: Shares
    sfx_offset_ms: Range
    videos: int
    caveats: list[str]


class ExportArchetype(Strict):
    id: Slug
    name: str
    summary: str
    when_to_use: list[str]
    slots: list[Slot]
    steps: list[str]
    patterns: list[Slug]
    build: Build
    sound: str
    duration_s: Range
    first_motion_s: Range
    events_per_scene: Range
    way_in: Shares
    beats: Shares
    sfx_cues_s: dict[str, Range]  # SFX onset after the scene starts, by type
    videos: int
    caveats: list[str]


class ArchetypesExport(Strict):
    provenance: Provenance
    archetypes: list[ExportArchetype]


class PatternsExport(Strict):
    provenance: Provenance
    patterns: list[ExportPattern]
