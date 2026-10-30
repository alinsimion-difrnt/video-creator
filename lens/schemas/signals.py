"""`videos/<id>/signals.summary.json`: compact, committed S3 output (full curves stay in data/ + R2)."""

from __future__ import annotations

from pydantic import Field

from lens.schemas.common import Provenance, Slug, Strict


class TransitionOut(Strict):
    kind: str
    start_s: float
    duration_s: float = Field(ge=0)
    direction: str | None = None


class ShotOut(Strict):
    id: str
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)
    transition_in: TransitionOut | None
    motion_energy: float = Field(ge=0)
    events_per_s: float = Field(ge=0)
    wpm: float | None = None


class EventOut(Strict):
    id: str
    shot: str
    kind: str
    start_s: float
    end_s: float
    bbox: tuple[float, float, float, float] | None
    camera_move: str


class HoldOut(Strict):
    shot: str
    start_s: float
    end_s: float
    dead: bool


class VideoSummary(Strict):
    fps: float = Field(gt=0)
    duration_s: float = Field(gt=0)
    shots: list[ShotOut]
    transitions_by_kind: dict[str, int]
    mean_shot_s: float
    events: list[EventOut]
    camera_moves: dict[str, int]
    holds: list[HoldOut]
    dead_hold_count: int = Field(ge=0)
    dead_hold_s: float = Field(ge=0)
    pace_cv: float = Field(ge=0)  # variation of motion energy across shots; low = uniform pacing


class LoudnessOut(Strict):
    integrated_lufs: float
    short_term_max_lufs: float
    lra_lu: float
    sample_peak_dbfs: float
    true_peak_dbtp: float


class SfxOut(Strict):
    id: str
    sync_s: float
    label: str
    label_source: str
    rules_label: str
    clap_label: str | None
    clap_score: float | None
    agreement: bool | None  # rules vs CLAP (same label family); None without CLAP
    on_beat: bool
    reveal_offset_ms: float | None  # sync minus nearest reveal start/landing; negative = sound leads
    scene_start_offset_ms: float  # sync minus nearest scene change (0 inside a transition span)
    at_scene_start: bool


class AudioSummary(Strict):
    stems: bool  # False: beats/SFX/speech were measured on the full mix (low confidence)
    ducking_db: float | None  # bed level away from speech minus under speech
    loudness: LoudnessOut
    bpm: float
    beat_confidence: float
    sfx: list[SfxOut]
    sfx_per_min: float
    label_agreement_share: float | None
    sfx_at_scene_start_share: float | None
    sfx_near_reveal_share: float | None
    cuts_on_beat_share: float | None  # None when there is no steady beat


class SpeechSummary(Strict):
    words: int
    speech_span_s: float
    wpm: float
    articulation_wpm: float
    pause_count: int
    pause_mean_ms: float
    pause_p90_ms: float
    pause_cv: float
    pauses_by_length: dict[str, int]
    phrase_rate_cv: float
    pitch_median_hz: float | None
    pitch_std_semitones: float | None
    energy_std_db: float | None
    perceived_emotion: None = None
    wpm_cv_across_shots: float | None


class CaptionSummary(Strict):
    groups: int
    words_per_group_mean: float
    words_per_group_median: float
    group_duration_mean_s: float
    changes_per_min: float
    coverage: float
    word_synced_share: float | None


class SignalsSummary(Strict):
    provenance: Provenance
    video_id: Slug
    video: VideoSummary
    audio: AudioSummary | None
    speech: SpeechSummary | None
    captions: CaptionSummary | None  # None: no burned-in captions found (or disabled)
