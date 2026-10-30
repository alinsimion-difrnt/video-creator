"""`config/lens.yaml`: thresholds, budgets and targets. Code reads numbers from here, never literals."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from lens.schemas.common import Slug, Strict


class Analysis(Strict):
    max_minutes: float = Field(gt=0)
    proxy_max_width: int = Field(gt=0)
    base_fps: float = Field(gt=0)
    base_frame_width: int = Field(gt=0)
    jpeg_quality: int = Field(ge=1, le=100)
    palette_colors: int = Field(ge=1, le=16)
    palette_pixels_per_frame: int = Field(ge=100)
    proxy_crf: int = Field(ge=0, le=51)
    proxy_duration_tolerance_s: float = Field(gt=0)
    audio_sample_rate: int = Field(gt=0)
    phash_frames: int = Field(ge=1)
    duplicate_max_distance: float = Field(ge=0, le=64)


class Originals(Strict):
    lifecycle_days: int = Field(ge=0)
    keep_tiers: list[Slug]


class Batch(Strict):
    fetch_max_seconds: int = Field(gt=0)
    per_run: int = Field(gt=0)
    max_parallel: int = Field(gt=0)


class VideoSignalsConfig(Strict):
    analysis_width: int = Field(gt=0)
    mask_threshold: int = Field(ge=1, le=255)  # per-pixel |diff| (0-255) counted as changed
    cut_min_diff: float = Field(gt=0, le=1)
    cut_ratio: float = Field(gt=1)
    transition_min_diff: float = Field(gt=0, le=1)
    transition_min_frames: int = Field(ge=2)
    transition_min_change: float = Field(gt=0, le=1)
    crossfade_max_residual: float = Field(gt=0, le=1)
    push_min_shift: float = Field(gt=0, le=1)  # fraction of width per frame
    zoom_min_scale_step: float = Field(gt=0)
    event_abs_min_diff: float = Field(gt=0)
    event_noise_k: float = Field(gt=0)
    motion_gap_merge_s: float = Field(ge=0)
    motion_min_s: float = Field(gt=0)
    continuous_min_s: float = Field(gt=0)
    camera_min_zoom: float = Field(gt=0)
    camera_min_pan: float = Field(gt=0)
    camera_min_area: float = Field(gt=0, le=1)  # changed area (fraction of frame) for a camera move
    phase_min_response: float = Field(gt=0, le=1)
    empty_max_edge_density: float = Field(ge=0, le=1)
    ignore_bottom_fraction: float = Field(ge=0, lt=1)  # caption band, left out of layout comparisons
    dissolve_baseline_s: float = Field(gt=0)
    dissolve_min_change: float = Field(gt=0, le=1)
    dissolve_max_retention: float = Field(gt=0, le=1)
    dissolve_max_residual: float = Field(gt=0)
    dissolve_max_s: float = Field(gt=0)
    min_shot_s: float = Field(gt=0)
    push_min_total: float = Field(gt=0)  # cumulative shift (frame widths) that makes a slow transition a push
    zoom_min_frames: int = Field(ge=1)


class AudioSignalsConfig(Strict):
    beat_grid_tolerance_ms: float = Field(ge=0)
    beat_min_confidence: float = Field(ge=0, le=1)
    sfx_decay_db: float = Field(gt=0)
    repet_periods: int = Field(ge=1)
    repet_margin: float = Field(gt=0)
    sfx_backtrack_s: float = Field(ge=0)
    sfx_edge_guard_s: float = Field(ge=0)
    sfx_min_gap_s: float = Field(gt=0)
    sfx_max_below_loudest_db: float = Field(gt=0)
    click_max_ms: float = Field(gt=0)
    impact_min_low_ratio: float = Field(ge=0, le=1)
    impact_max_attack_ms: float = Field(gt=0)
    swell_min_attack_ms: float = Field(gt=0)
    riser_min_attack_ms: float = Field(gt=0)
    noise_min_flatness: float = Field(ge=0, le=1)


class SpeechConfig(Strict):
    whisper_model: str
    whisper_compute_type: str
    language: str | None
    pause_min_ms: float = Field(gt=0)
    pause_medium_ms: float = Field(gt=0)
    pause_long_ms: float = Field(gt=0)
    phrase_split_ms: float = Field(gt=0)
    pitch_fmin_hz: float = Field(gt=0)
    pitch_fmax_hz: float = Field(gt=0)
    voice_floor_db: float = Field(gt=0)
    voice_range_db: float = Field(gt=0)


class StemsConfig(Strict):
    enabled: bool
    model: str
    ducking_guard_s: float = Field(ge=0)


class CaptionsConfig(Strict):
    enabled: bool
    band_fraction: float = Field(gt=0, le=1)
    analysis_width: int = Field(gt=0)
    band_change_min: float = Field(gt=0, le=1)
    band_ratio: float = Field(gt=1)
    min_group_frames: int = Field(ge=1)
    ocr_min_score: float = Field(ge=0, le=1)
    min_groups: int = Field(ge=1)
    sync_tolerance_frames: int = Field(ge=0)


class ClapConfig(Strict):
    enabled: bool
    model: str
    min_score: float = Field(ge=0, le=1)  # CLAP may replace an "unsure" rule label above this
    pre_s: float = Field(ge=0)
    post_s: float = Field(ge=0)
    min_clip_s: float = Field(gt=0)
    batch_size: int = Field(ge=1)


class Signals(Strict):
    stems: StemsConfig
    clap: ClapConfig
    captions: CaptionsConfig
    video: VideoSignalsConfig
    audio: AudioSignalsConfig
    speech: SpeechConfig
    cut_on_beat_tolerance_frames: int = Field(ge=0)
    scene_start_tolerance_frames: int = Field(ge=0)
    sfx_reveal_window_s: float = Field(gt=0)
    speech_min_words: int = Field(ge=1)
    dead_hold_min_s: float = Field(gt=0)


class Evidence(Strict):
    burst_pad_s: float = Field(ge=0)
    filmstrip_quantiles: list[float] = Field(min_length=2, max_length=15)  # of cumulative motion energy
    crop_margin: float = Field(ge=0)  # crop = bbox_union grown by this fraction of its size per side
    crop_min_px: int = Field(gt=0)  # ...and at least this many proxy pixels wide and high
    context_thumb_px: int = Field(gt=0)
    image_long_edge_px: int = Field(gt=0, le=2000)
    max_candidate_boxes: int = Field(ge=1)
    box_min_area: float = Field(gt=0, lt=1)  # fraction of the frame
    box_merge_px: int = Field(ge=0)
    box_nms_iou: float = Field(gt=0, le=1)
    ocr_min_score: float = Field(ge=0, le=1)
    ocr_min_changed: float = Field(ge=0, le=1)  # OCR line kept if this share of it changed
    spectrogram_window_s: float = Field(gt=0)
    spectrogram_width_px: int = Field(gt=0)
    spectrogram_height_px: int = Field(gt=0)
    sheet_cols: int = Field(ge=1)
    sheet_max_tiles: int = Field(ge=1)

    @model_validator(mode="after")
    def _quantiles(self) -> Evidence:
        q = self.filmstrip_quantiles
        if any(not 0 <= v <= 1 for v in q) or q != sorted(q):
            raise ValueError("filmstrip_quantiles must be ascending values in [0, 1]")
        return self


class Packets(Strict):
    min_event_energy: float = Field(ge=0)  # triage: smaller events are skipped
    min_event_area: float = Field(ge=0, lt=1)  # ...as are events whose bbox covers less of the frame
    skip_caption_band: bool  # events entirely inside the caption band are captions (S3 measures them)
    dedupe_max_distance: int = Field(ge=0, le=64)  # dHash bits: repeated events share one task...
    dedupe_duration_ratio: float = Field(ge=0)  # ...if their durations also agree within this ratio
    words_window_s: float = Field(ge=0)  # facts.json lists words spoken this close to the event
    overlap_merge_min: float = Field(gt=0, le=1)  # burst overlap (share of the shorter) that merges events


class Annotate(Strict):
    videos_per_run: int = Field(ge=1)
    max_turns: int = Field(ge=1)
    max_images_per_task: int = Field(ge=1)
    event_images: int = Field(ge=1)
    events_per_subagent: int = Field(ge=1)
    validate_retries: int = Field(ge=0)
    task_retries: int = Field(ge=0)
    a2_tiers: list[Slug]
    spot_review_fraction: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def _budget(self) -> Annotate:
        if self.event_images > self.max_images_per_task:
            raise ValueError("event_images exceeds max_images_per_task")
        return self


class Measure(Strict):
    progress_end_tolerance: float = Field(gt=0, lt=1)
    min_fit_quality: float = Field(ge=0, le=1)
    model_selection_margin: float = Field(ge=0)
    gsap_class_ratio: float = Field(ge=1)  # a named ease within this factor of the bezier RMSE sets the class
    track_margin_px: int = Field(ge=0)  # search this far around the event crop
    track_scale_steps: list[float] = Field(min_length=1)  # per-frame scale changes tried while tracking
    track_min_confidence: float = Field(ge=0, le=1)  # NCC below this: position not trusted
    track_coarse_px: int = Field(ge=16)  # larger search areas are first searched shrunk to this size
    track_coarse_min_template_px: int = Field(ge=4)  # never shrink the template below this
    min_position_change_px: float = Field(ge=0)  # channels that change less are static
    min_scale_change: float = Field(ge=0)
    min_opacity_change: float = Field(ge=0, le=1)
    min_alpha_contrast: float = Field(ge=0)  # mean |end - background| (0-255) needed for an opacity curve
    opacity_hold_max_travel: float = Field(ge=0)  # in element sizes; see lens.measure._channels
    stagger_reveal_alpha: float = Field(gt=0, lt=1)  # a word is revealed when its opacity passes this


class Gold(Strict):
    videos: list[Slug] = Field(min_length=1)  # the G2 gold set (BUILD_PLAN 11.2)
    max_events_per_video: int = Field(ge=1)  # events sampled evenly per video, to fit about 2 hours


class AnswerKeyEval(Strict):
    video: Slug  # our own render with a HyperFrames answer key
    path: str  # repo-relative answer key JSON
    min_iou: float = Field(gt=0, le=1)  # a chosen box is a tween target at this overlap
    event_pad_s: float = Field(ge=0)  # tweens this close to an event's window belong to it
    sfx_window_s: tuple[float, float]  # detected onset minus clip start that counts as that clip
    sfx_labels: dict[str, list[Slug]]  # clip file -> accepted taxonomy labels


class ConsistencyEval(Strict):
    videos: list[Slug] = Field(min_length=1)
    events: int = Field(ge=1)  # blind re-annotations, spread evenly


class Eval(Strict):
    answer_key: AnswerKeyEval
    consistency: ConsistencyEval
    measured_tier: str
    min_measured_share: float = Field(ge=0, le=1)  # M6 accept: annotated reference events measured


class SynthWeights(Strict):
    tier: dict[str, float]
    score_from: str
    score_missing: float = Field(ge=0, le=1)
    quality: bool


class Cluster(Strict):
    model: str
    revision: str
    threshold: float = Field(gt=0, le=1)
    merge_similarity: float = Field(gt=0, le=1)
    min_members: int = Field(ge=1)
    min_brands: int = Field(ge=1)


class Synth(Strict):
    weights: SynthWeights
    min_n: int = Field(ge=1)
    bootstrap: int = Field(ge=100)
    ci: float = Field(gt=0, lt=1)
    seed: int
    spring_clusters: int = Field(ge=1)
    max_examples: int = Field(ge=1)
    scene_batch: int = Field(ge=1)
    card_members: int = Field(ge=1)
    g4_hold: dict[str, str] = Field(default_factory=dict)  # pattern id -> plain reason
    g4_hold_archetypes: dict[str, str] = Field(default_factory=dict)  # archetype id -> plain reason
    export_word_brands: list[str] = Field(default_factory=list)  # brands that are also common words
    cluster: Cluster


class CorpusMetric(Strict):
    id: Slug  # an extractor in lens.compare.corpus.EXTRACT
    section: Literal["voice", "sound", "motion", "rhythm"]
    unit: str
    weight: float = Field(gt=0)
    effort: Literal["S", "M", "L"]


class Compare(Strict):
    min_cohort: int = Field(ge=2)  # fewer cohort videos with the metric: n/a
    max_gap: float = Field(gt=0)
    corpus_metrics: list[CorpusMetric] = Field(min_length=1)


class Reconcile(Strict):
    shot_tolerance_frames: int = Field(ge=0)  # an event may overhang its shot by this many frames


class LoudnessTarget(Strict):
    min_lufs: float
    max_lufs: float
    max_true_peak_dbtp: float
    source: str  # "house" = commonly cited convention, not a published platform spec

    @model_validator(mode="after")
    def _range(self) -> LoudnessTarget:
        if self.min_lufs > self.max_lufs:
            raise ValueError("min_lufs > max_lufs")
        return self


class MetricTarget(Strict):
    id: Slug
    path: str  # dotted path into signals.summary.json
    min: float | None = None
    max: float | None = None
    unit: str
    weight: float = Field(gt=0)
    effort: str = Field(pattern="^[SML]$")
    requires: list[str]
    source: str

    @model_validator(mode="after")
    def _bounded(self) -> MetricTarget:
        if self.min is None and self.max is None:
            raise ValueError(f"{self.id}: needs min and/or max")
        bad = set(self.requires) - {"voice", "beat", "sfx", "stems", "captions"}
        if bad:
            raise ValueError(f"{self.id}: unknown requires {sorted(bad)}")
        return self


class Targets(Strict):
    loudness: dict[Slug, LoudnessTarget]
    default_destination: Slug
    metrics: list[MetricTarget]

    @model_validator(mode="after")
    def _destination(self) -> Targets:
        if self.default_destination not in self.loudness:
            raise ValueError("default_destination has no loudness target")
        return self


class KnownValue(Strict):
    value: float
    tolerance: float = Field(ge=0)


class Baseline(Strict):
    """Known values of a reference render; `lens compare` must reproduce them (BUILD_PLAN section 9)."""

    video: Slug
    fps: float = Field(gt=0)
    frames: int = Field(gt=0)
    duration_s: KnownValue
    integrated_lufs: KnownValue
    sample_peak_dbfs: KnownValue
    scenes: int = Field(gt=0)
    transitions: int = Field(ge=0)
    transitions_min_detected: int = Field(ge=0)
    transition_tolerance_frames: int = Field(ge=0)
    wpm: KnownValue
    sfx_at_scene_start_min_share: float = Field(ge=0, le=1)


class CreateVoice(Strict):
    """Phase 2 voice (ADR 0018): ElevenLabs REST with-timestamps."""

    provider: Literal["elevenlabs"]
    voice_id: str = Field(min_length=1)
    voice_name: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    output_format: str = Field(min_length=1)
    takes: int = Field(ge=1)
    allowed_tags: list[str] = Field(min_length=1)  # audio tags a script may use, without brackets
    # voice-spec measures a single scene can show; takes are ranked by their distance from these bands
    select_on: list[
        Literal["wpm", "articulation_wpm", "pause_mean_ms", "pitch_std_semitones", "energy_std_db"]
    ] = Field(min_length=1)


class CreateTiming(Strict):
    fps: int = Field(gt=0)
    pre_roll_s: float = Field(ge=0)  # music before the first word
    scene_tail_s: float = Field(ge=0)  # silence after each scene's last word
    close_tail_s: float = Field(ge=0)  # after the last scene


class Rect(Strict):
    """A rectangle in frame pixels."""

    x0: int = Field(ge=0)
    y0: int = Field(ge=0)
    x1: int = Field(gt=0)
    y1: int = Field(gt=0)

    @model_validator(mode="after")
    def _order(self) -> Rect:
        if self.x1 <= self.x0 or self.y1 <= self.y0:
            raise ValueError("a rect needs x0 < x1 and y0 < y1")
        return self

    def contains(self, x0: float, y0: float, x1: float, y1: float, tol: float = 0) -> bool:
        return x0 >= self.x0 - tol and y0 >= self.y0 - tol and x1 <= self.x1 + tol and y1 <= self.y1 + tol


class CreateFrame(Strict):
    """One output frame: size, text minimum, where critical content may go, where captions sit."""

    width: int = Field(gt=0)
    height: int = Field(gt=0)
    min_text_px: float = Field(gt=0)  # nothing smaller on this frame
    safe: list[Rect] = Field(min_length=1)  # critical content must lie fully inside one of these
    caption_band: Rect  # burned-in captions; scene content keeps out of it
    caption_top: Rect | None = None  # presenter videos: captions above the head, clear of face and body
    cover_safe: Rect | None = None  # a cover's title: survives the platforms' grid and profile crops
    source: str = Field(min_length=1)

    @model_validator(mode="after")
    def _inside(self) -> CreateFrame:
        extra = [r for r in (self.caption_top, self.cover_safe) if r is not None]
        for r in [*self.safe, self.caption_band, *extra]:
            if r.x1 > self.width or r.y1 > self.height:
                raise ValueError(f"rect {r.model_dump()} is outside the {self.width}x{self.height} frame")
        return self


class CaptionRules(Strict):
    """How narration words are grouped into burned-in captions on one frame."""

    max_words: int = Field(ge=1)
    max_chars: int = Field(ge=1)  # a group longer than this is split (at a comma or pause if possible)
    lead_s: float = Field(ge=0)  # a group appears this long before its first word
    hold_s: float = Field(ge=0)  # and stays this long after its last word ...
    seam_s: float = Field(ge=0)  # ... unless the next group starts sooner (then it ends this much before)
    gap_split_s: float = Field(gt=0)  # a pause this long always starts a new group


class CreateDesign(Strict):
    """C3 tokens: WCAG 2.1 AA thresholds and the frames (BUILD_PLAN 12b, handoff 7.4, ADR 0022)."""

    contrast_normal: float = Field(gt=1)  # text below the large-text size
    contrast_large: float = Field(gt=1)  # >= large_text_px regular, or >= large_bold_px bold
    large_text_px: float = Field(gt=0)
    large_bold_px: float = Field(gt=0)
    frames: dict[Slug, CreateFrame] = Field(min_length=1)
    destination_frames: dict[Slug, Slug]  # destination -> a key of frames
    captions: dict[Slug, CaptionRules]  # frame -> grouping rules
    caption_seam_gap_px: float = Field(ge=0)  # split scenes: captions end this far above the product's edge
    caption_face_gap: float = Field(ge=0)  # face-heights between the chin and a presenter video's captions
    caption_function_words: dict[str, list[str]]  # language -> words a caption group should not end on
    audit_step_s: float = Field(gt=0)
    audit_tolerance_px: float = Field(ge=0)
    audit_min_opacity: float = Field(ge=0, lt=1)
    audit_min_hold_s: float = Field(ge=0)
    required_glyphs: str = Field(min_length=1)
    google_fonts_css: str = Field(pattern=r"^https://")
    accent_tint_alpha: float = Field(gt=0, lt=1)  # default chip / highlight tint when a brand sets none

    @model_validator(mode="after")
    def _frames(self) -> CreateDesign:
        unknown = sorted(
            {f for f in [*self.destination_frames.values(), *self.captions] if f not in self.frames}
        )
        if unknown:
            raise ValueError(f"destination_frames or captions name unknown frames: {', '.join(unknown)}")
        return self

    def frame_for(self, destination: str) -> tuple[str, CreateFrame]:
        name = self.destination_frames.get(destination)
        if name is None:
            raise ValueError(f"destination {destination!r} has no frame in create.design.destination_frames")
        return name, self.frames[name]


class CreateRender(Strict):
    """HyperFrames (Apache-2.0) runs through npx at a pinned version; its telemetry is switched off first."""

    hyperframes_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    sketch_before_end_s: float = Field(ge=0)  # the sketch frame: this long before the scene ends
    sketch_columns: int = Field(ge=1)
    timeout_s: int = Field(gt=0)


class StyleRule(Strict):
    pattern: str = Field(min_length=1)  # case-insensitive regex on the spoken text, tags removed
    reason: str = Field(min_length=1)


class CreateScript(Strict):
    """C2 style guard (handoff 7.10): plain, specific narration; no slogans or rhetorical devices."""

    banned: list[StyleRule]
    max_tags_per_scene: int = Field(ge=0)
    planning_wpm: float = Field(gt=0)  # to check the script fits the brief's length band before voicing


class FootageCuts(Strict):
    silence_max_s: float = Field(gt=0)
    keep_before_s: float = Field(ge=0)
    keep_after_s: float = Field(ge=0)
    min_cut_s: float = Field(ge=0)
    retake_min_words: int = Field(ge=2)
    retake_window_words: int = Field(ge=2)
    retake_max_tail_words: int = Field(ge=0)
    retake_pause_s: float = Field(ge=0)
    count_in_pause_s: float = Field(ge=0)
    punch_max_s: float = Field(gt=0)
    punch_min_s: float = Field(gt=0)
    punch_hook_s: float = Field(gt=0)


class FootageReframe(Strict):
    model: str = Field(min_length=1)
    model_url: str = Field(pattern=r"^https://")
    model_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    sample_fps: float = Field(gt=0)
    min_score: float = Field(gt=0, lt=1)
    eye_line: float = Field(gt=0, lt=1)
    punch_in: float = Field(ge=1)
    hair_above_face: float = Field(default=0.3, ge=0, le=1)  # head top: this many face-heights above the box
    pip_face_scale: float = Field(gt=1)
    pip_size: dict[str, int]  # frame -> bubble diameter in px
    pip_margin: int = Field(ge=0)
    pip_ring: int = Field(ge=0)
    split_face_offset: int = Field(ge=0)


class FootagePose(Strict):
    """The presenter's pose (create/footage/pose.py, ADR 0030): BlazePose ONNX, run locally."""

    model: str = Field(min_length=1)
    model_url: str = Field(pattern=r"^https://")
    model_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    sample_fps: float = Field(gt=0)
    min_conf: float = Field(gt=0, lt=1)
    body_below_face: float = Field(gt=0)  # first crop: centred this many face-heights below the face
    box_face_heights: float = Field(gt=0)  # ... and this many face-heights wide
    smooth: int = Field(ge=1)  # moving-average window (samples) on keyed points
    hand_model: str = Field(min_length=1)  # the hand landmark model, run on a crop placed from the body pose
    hand_model_url: str = Field(pattern=r"^https://")
    hand_model_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    hand_scale: float = Field(gt=0)  # the hand crop's side, in wrist-to-knuckle lengths
    hand_min_face: float = Field(gt=0)  # ... and at least this many face heights
    hand_min_conf: float = Field(gt=0, lt=1)


class FootageOverlays(Strict):
    margin: int = Field(ge=0)
    max_width: int = Field(gt=0)
    gap: float = Field(ge=0)


class FootageMusic(Strict):
    """A music bed under the presenter (plan `music`, tournament n06): Eleven Music, its beats measured."""

    model: str  # Eleven Music model id (external-facts section 10 g)
    snap_s: float = Field(
        ge=0, le=0.5
    )  # hits (punches, flashes, shakes, bursts) this close to a beat land on it
    pulse_scale: float = Field(ge=1, le=1.1)  # the zoom pulse on each bar's first beat


class FootageSfx(Strict):
    """Soft UI sounds under the voice (create/footage/sfx.py)."""

    level_db: float = Field(le=0)  # gain of every sound before its trim
    trim_db: dict[str, float] = Field(default_factory=dict)  # per sound (pop, whoosh, click)
    pop_offset_s: float = 0.0  # a pop lands this long after a widget starts entering
    whoosh_lead_s: float = Field(ge=0)  # a whoosh starts this long before the layout move's midpoint
    min_gap_s: float = Field(ge=0)  # two sounds never closer than this


class CaptionPlate(Strict):
    """create reel, plan `caption_plate`: captions on a white plate (Robert, seo-budget)."""

    color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    alpha: float = Field(ge=0.9, le=1)
    size_px: int = Field(ge=56)  # the caption's font size on a plate (at least the brand's)
    pad_y: int = Field(ge=0)
    pad_x: int = Field(ge=0)
    radius_px: int = Field(ge=0)
    max_width_px: int = Field(ge=300)  # one line for a group of up to ~20 characters
    shadow: str  # CSS box-shadow: reads on paper and on footage


class FootagePanel(Strict):
    """create panel (ADR 0034): a bespoke HTML panel stepped frame by frame and laid over a reel render."""

    jpeg_quality: int = Field(ge=50, le=100)  # each frame's screenshot (camera-free graphics: 90+ is clean)
    crf: int = Field(ge=0, le=51)  # the panel's own MP4 (re-encoded once more by the composite)
    composite_crf: int = Field(ge=0, le=51)
    settle_ms: int = Field(ge=0)  # after load, before the first frame (fonts, images)
    review_sheets: int = Field(ge=1)  # images a lab-reviewer gets per stills run (Claude usage)
    max_stills: int = Field(ge=1)  # stills on one sheet: more and each tile is too small to judge
    caption_clear_px: int = Field(ge=0)  # the panel ends this far above the seam (the captions sit there)


# Reel motion (ADR 0033): entrance styles the kit knows (create/kit/motion.js MOTIONS) and the hand-over
# between two product cards: morph (one surface changes shape into the next card), push (the deck scrolls),
# stack (the next card lands on the last), cut (the last leaves, then the next enters: the first take's look).
ReelEntrance = Literal["rise", "pop", "slide", "flip", "focus", "pixel", "wipe", "unfold"]
ReelHandover = Literal["morph", "push", "stack", "cut"]


class ReelStyle(Strict):
    """A motion style for a whole reel (ADR 0033): a plan names one (`motion: {style: paper}`) and code
    applies it, so two videos of one brand move differently and every video moves as one piece."""

    cards: ReelEntrance  # chat, search, sources, review, queries, chart, bars, pins, code, bucket, agents
    stickers: ReelEntrance  # sticker, tiles, logo, cta
    numbers: ReelEntrance  # counter
    handover: ReelHandover  # between two product cards in one layout block
    bg: Literal["none", "drift"]  # drift: soft brand-tinted shapes move slowly behind the cards
    kicker: Literal["each", "run"]  # run: cards in a row with one kicker share one step label
    push_alternate: bool  # shots push in and out in turn, so the scale is continuous across a cut
    cut_nudge: bool  # the product area reacts to each cut (background shift, a small settle)
    snap_cuts: bool  # a card whose word starts just after a cut enters on the cut
    note: str = ""  # when it fits


class FootageReel(Strict):
    """create reel: how widgets fill their boxes, and how a reel moves as a whole (ADR 0033)."""

    styles: dict[str, ReelStyle] = Field(default_factory=dict)  # named motion styles; `classic` = ADR 0026
    handover_s: float = Field(default=0.55, gt=0, le=1.5)  # a hand-over between product cards
    kicker_h: int = Field(default=104, ge=0, le=200)  # a shared step label takes this much of the cards' box
    snap_cuts_s: float = Field(default=0.3, ge=0, le=1)  # enter on the cut when the word starts this close
    bg_drift_s: float = Field(default=18.0, gt=0)  # one loop of the drifting product background
    cut_nudge_px: int = Field(default=14, ge=0, le=60)  # the product background shifts this much on a cut

    fit_up: float = Field(ge=1, le=3)  # a widget may grow to this scale to fill its box
    # chest overlays start this many face-heights under the chin (a beard and the zoom reach below the box)
    chest_chin_gap: float = Field(default=0.0, ge=0, le=1)
    held_w: int = Field(default=520, ge=200, le=1080)  # a card held on the palm: its box width, frame px
    held_h: int = Field(default=340, ge=100, le=1000)  # ...and at most this tall
    # a held card's bottom sits this share of its width over the palm, its top never above chin + gap px
    held_lift: float = Field(default=0.08, ge=0, le=0.5)
    held_chin_gap: int = Field(default=30, ge=0)
    held_tilt: float = Field(default=8.0, ge=0, le=30)  # a held card tilts at most this many degrees...
    held_tilt_k: float = Field(
        default=0.02, ge=0
    )  # ...this many degrees per px/s of the hand's sideways speed
    overlay_aspect: dict[str, float]  # widget kind -> expected height / width, to pick the roomiest zone
    caption_dim: float = Field(ge=0, le=1)  # karaoke words not yet spoken: at least this opaque
    punch_scale: float = Field(ge=1, le=1.3)  # a key-word punch-in
    frame_format: Literal["png", "jpg"]  # how HyperFrames extracts the presenter's frames
    draft_scale: float = Field(default=0.5, gt=0, le=1)  # `create reel --draft`: output size for reviews
    caption_plate: CaptionPlate
    check: ReelCheck
    props: ReelProps


class ReelProps(Strict):
    """create reel props (characters in the room): where named spots are and how big a beat moves."""

    # spot -> (dx in face widths, dy in face heights) from the face centre, for the prop's bottom centre
    anchors: dict[str, tuple[float, float]]
    pixel_cells: int = Field(ge=8, le=128)  # pixel style: cells across the prop
    move_s: float = Field(gt=0)  # a `move` beat travels this long (ending as its word ends, at least)
    exit_s: float = Field(gt=0)  # a run / swim / fall exit takes this long
    path_leg_s: float = Field(gt=0)  # a `path` beat spends this long on each leg (at least)
    speeds: dict[str, float]  # gait -> body widths a second (walk, run, hop, boat, swim, slide)
    peek_share: float = Field(gt=0, le=1)  # a prop behind the presenter shows at least this much of itself
    min_exit_s: float = Field(gt=0)  # a shorter exit reads as a glitch: the prop stays instead
    min_travel_s: float = Field(gt=0)  # no move is quicker than this (a snap reads as a cut)
    jump_rise: float = Field(gt=0)  # a walker's move up or down more than this many prop heights is a jump
    approach: tuple[float, float]  # a carrier stops this many of its widths and its prey's widths away
    carry_max: float = Field(gt=0, le=1)  # a carried prop is at most this share of the carrier's width
    tag_s: float = Field(gt=0)  # a name tag stays up this long
    # a tag or bubble ends at the next cut once up this long
    tag_cut_least_s: float = Field(default=0.8, ge=0)
    # follow: flee keeps this many of its own widths ahead of the leading hand
    flee_gap: float = Field(default=0.3, ge=0)
    flee_chase_s: float = Field(default=1.5, gt=0)  # ...for this long, then its exit
    flee_bolt: float = Field(default=0.25, ge=0)  # its own pace meanwhile, a share of its run speed
    max_travel_s: float = Field(gt=0)  # no single move takes longer than this
    lead_s: float = Field(ge=0, le=0.2)  # visuals lead their word by this much (they read as in sync)
    safe_bottom: float = Field(gt=0)  # frame px: a prop's feet stay above this (the platform's bottom UI)
    safe_right: float = Field(default=1e9, gt=0)  # frame px: a prop stays left of this (the action rail)
    tag_side_above: float = Field(default=0.0, ge=0)  # frame y: tags beside the head above this (captions)
    gag_scale: float = Field(default=1.0, gt=0)  # gag items over Fred's pixel size (create/pixel/items.py)
    min_visible: float = Field(ge=0, le=1)  # create reel --check: share of a prop that must stay on screen


class FootageSurface(Strict):
    """Words painted on a room surface (fx wall, tournament n08): what counts as wood in the master frame."""

    hue: tuple[float, float]  # degrees
    sat_min: float = Field(ge=0, le=1)
    val: tuple[float, float]  # value (max channel), 0-1: neither black nor blown
    rows: tuple[float, float]  # default band of the surface's height the words are painted in
    card_aspect: float = Field(gt=0)  # the flat card's height over its width before it is mapped on


class FootageDepth(Strict):
    """Bullet time (fx freeze, tournament n05): Depth Anything V2 Small as ONNX, run locally."""

    model: str  # file name under data/create/_cache/depth/
    url: str
    sha256: str
    side: int = Field(ge=140, le=1036)  # the width the model sees (its patch is 14 px)
    fps: int = Field(ge=12, le=60)
    amp: float = Field(ge=0, le=200)  # the orbit's swing for the nearest pixels, frame px
    push: float = Field(ge=0, le=0.5)  # how far it pushes in over the move


class FootageMatte(Strict):
    """create matte: the presenter cut out of the edited video (HyperFrames remove-background, local model)
    only where a reel plan needs it (props behind the presenter, anime backgrounds), ADR 0027."""

    pad_s: float = Field(ge=0)  # cut out this much before and after each span
    device: Literal["auto", "cpu", "coreml", "cuda"]
    quality: Literal["fast", "balanced", "best"]
    timeout_s: int = Field(gt=0)


class ReelCheck(Strict):
    """`create reel --check`: what the reviews of Robert's first take kept finding, caught before a render."""

    max_beat_gap_s: float = Field(gt=0)  # a card that shows nothing new for longer reads as dead
    max_static_s: float = Field(gt=0)  # nothing new on screen (no widget, beat, layout move or punch-in)
    max_product_empty_s: float = Field(ge=0)  # an empty product area in split / off
    max_sticker_chars: int = Field(gt=0)  # longer stickers wrap and read as broken
    min_card_text_px: float = Field(gt=0)  # the smallest text a card may show on screen (after fitting)
    edge_tol_px: float = Field(ge=0)  # a rendered rect may pass a safe edge by this much (springs, drift)


class FootageVoice(Strict):
    highpass_hz: float = Field(gt=0)
    denoise_nf_db: float = Field(lt=0)
    compressor: str = Field(min_length=1)  # ffmpeg acompressor options
    true_peak_db: float = Field(lt=0)
    lra: float = Field(gt=0)


class SkinMask(Strict):
    """Which pixels inside a face box count as skin (Oklab)."""

    min_l: float = Field(ge=0, le=1)
    min_chroma: float = Field(ge=0)
    hue: tuple[float, float]


class FootageResolve(Strict):
    """Skill resolve-fix-take: grade and skin targets for a raw take fixed in DaVinci Resolve."""

    black: float = Field(ge=0, lt=0.5)
    white: float = Field(gt=0.5, le=1)
    white_rg: float = Field(gt=0)
    white_bg: float = Field(gt=0)
    saturation: float = Field(gt=0, le=2)
    skin_hue: float = Field(ge=0, lt=360)
    skin_chroma: float = Field(gt=0)
    skin_hue_tol: float = Field(gt=0)
    skin_chroma_tol: float = Field(gt=0)
    skin_window: tuple[float, float]  # Oklab hue centre, half-width (deg)
    skin_hue_to: float = Field(ge=0, lt=360)  # the LUT's aim; skin_hue is the checked target
    skin_hue_pull: float = Field(ge=0, le=1)
    skin_chroma_mul: float = Field(gt=0, le=1)
    skin_lift: float = Field(ge=0, le=0.2)
    skin_neutral: tuple[float, float]  # Oklab chroma ramp in: untouched below, full above
    skin_saturated: tuple[float, float]  # Oklab chroma ramp out: full below, untouched above
    skin_shadow: tuple[float, float]  # Oklab L ramp in
    skin_mask: SkinMask
    lut_size: int = Field(ge=9, le=65)
    regions: dict[str, tuple[float, float, float, float]]  # name -> x0, x1, y0, y1 (frame fractions)


class FootageEditPage(Strict):
    """create edits --page: the phone page where Robert sets crops, zooms and notes himself."""

    still_width: int = Field(ge=120, le=1920)
    still_quality: int = Field(ge=2, le=31)
    video_height: int = Field(ge=240, le=1920)
    video_crf: int = Field(ge=18, le=45)
    audio_kbps: int = Field(ge=16, le=256)
    max_mb: float = Field(gt=0)
    zoom_step: float = Field(gt=0, le=0.5)
    max_zoom: float = Field(gt=1, le=3)
    nudge: float = Field(gt=0, le=0.5)


class CreateFootage(Strict):
    """Presenter footage: conform, transcribe, cut proposals, edit (ADR 0025)."""

    fps: int = Field(gt=0)
    max_height: int = Field(gt=0)
    master_crf: int = Field(ge=0, le=51)
    gop: int = Field(ge=1)
    stt_engine: Literal["elevenlabs", "whisper"]
    stt_model: str = Field(min_length=1)
    whisper_model: str = Field(min_length=1)
    fillers: dict[str, list[str]]  # language -> filler tokens
    retake_cues: dict[str, list[str]]  # language -> cue words or phrases
    count_in: dict[str, list[str]]  # language -> count words said before speaking
    keep_pad_s: float = Field(
        default=1.0, ge=0
    )  # `create take --keep m:ss`: a cut this close to the time stays
    conjunctions: dict[str, list[str]]  # language -> words that join a list (a repeat after one is no retake)
    cuts: FootageCuts
    crossfade_ms: float = Field(ge=0)
    voice: FootageVoice
    resolve: FootageResolve
    reframe: FootageReframe
    pose: FootagePose
    overlays: FootageOverlays
    sfx: FootageSfx
    music: FootageMusic
    reel: FootageReel
    panel: FootagePanel
    matte: FootageMatte
    surface: FootageSurface
    depth: FootageDepth
    edit_page: FootageEditPage
    scene_target_s: float = Field(gt=0)


class CreateQa(Strict):
    max_duration_s: float = Field(gt=0)
    first_word_max_s: float = Field(ge=0)
    first_visual_max_s: float = Field(ge=0)
    max_static_s: float = Field(gt=0)
    max_word_gap_s: float = Field(gt=0)
    max_tail_s: float = Field(ge=0)
    true_peak_max_db: float


class CreateLab(Strict):
    """`create lab` (ADR 0029): test reels from a stand-in photo and an ElevenLabs voice."""

    pre_s: float = Field(ge=0)  # silence before the voice
    tail_s: float = Field(ge=0)  # after the last word
    fps: int = Field(gt=0)
    breathe: tuple[float, float, float]  # plate zoom = base + amp * sin(2 pi t / period); base - amp >= 1
    punch: float = Field(ge=1)  # the jump cut's punch-in on the face (`cut_at`)
    brand_project: str  # tokens (fonts, colours) and provenance borrowed from this project
    study_rows: int = Field(gt=0)  # motion-strip rows per study page
    review_images: int = Field(gt=0)  # images the lab-reviewer subagent reads per version (usage budget)

    @model_validator(mode="after")
    def _zoom(self) -> CreateLab:
        base, amp, _ = self.breathe
        if base - amp < 1:  # below 1 the crop asks for more pixels than the frame has: green edges (v06)
            raise ValueError("breathe: base - amp must stay >= 1")
        return self


class MotionRule(Strict):
    rule: str = Field(min_length=1)
    source: str = Field(min_length=1)  # where it was learned


class MotionBuild(Strict):
    grades: int = Field(ge=1)  # create grade runs per build (each renders the film)
    snapshot_frames: int = Field(ge=0)  # frames the builder may look at in total (Claude usage budget)


class MotionGradeConfig(Strict):
    max_move_s: float = Field(gt=0)  # a move longer than this needs a reason
    ambient_min_s: float = Field(gt=0)  # tweens at least this long are ambient drift, not moves
    min_blur_px: float = Field(gt=0)  # blur() at or above this is decoration
    sample_step_s: float = Field(gt=0)  # DOM sampling step for text size, accents and overlaps
    max_accent_moments: float = Field(gt=0)  # accent moments per frame (the orange logo counts 0.5)
    overlap_min_px: float = Field(ge=0)
    persist_s: float = Field(ge=0)  # a DOM finding counts when it lasts this long
    min_visible_opacity: float = Field(ge=0, le=1)  # fainter text is mid-fade, not read
    logo_at_close: bool  # the end card must show a logo nothing covers
    tint_tokens: list[str] = Field(min_length=1)  # colour roles that may appear as light tints
    tint_max_alpha: float = Field(gt=0, le=1)
    tint_tolerance: int = Field(ge=0, le=255)
    tint_alpha_spread: float = Field(ge=0, le=1)
    min_ease_families: int = Field(ge=1)  # corpus easing classes a film should mix
    ease_min_moves: int = Field(ge=1)  # films with fewer moves skip the family count
    overshoot_factor: float = Field(gt=0)  # overshoot share past the corpus share times this warns
    overshoot_max_area: float = Field(gt=0, le=1)  # overshoot on a larger target (share of frame) warns
    seam_s: float = Field(ge=0)  # a handover window runs to this long after the next scene's first word
    seam_rest_s: float = Field(gt=0)  # the frame at rest this long inside a handover window warns

    @model_validator(mode="after")
    def _ambient(self) -> MotionGradeConfig:
        if self.ambient_min_s <= self.max_move_s:
            raise ValueError("ambient_min_s must be longer than max_move_s")
        return self


class CreateMotion(Strict):
    """c6_direction, c8_motion, c8_grade (ADR 0032): Claude directs the motion inside our learnings."""

    patterns: list[str] = Field(min_length=1)  # recipe menu (exports/patterns.json ids)
    pattern_steps: int = Field(ge=1)
    design_sections: list[str] = Field(min_length=1)  # DESIGN.md "## N." sections copied verbatim
    rules: list[MotionRule] = Field(min_length=1)
    final_hold_s: float = Field(ge=0)
    sfx: list[str] = Field(min_length=1)  # the SFX library a build may cue
    sfx_gain_db: tuple[float, float]
    build: MotionBuild
    grade: MotionGradeConfig

    @model_validator(mode="after")
    def _gain(self) -> CreateMotion:
        if self.sfx_gain_db[0] > self.sfx_gain_db[1]:
            raise ValueError("sfx_gain_db must be [low, high]")
        return self


class CreateMix(Strict):
    """c12_mix: narration + ducked music bed + the build's SFX, at the destination's loudness."""

    bed_db: float = Field(le=0)
    duck: str = Field(min_length=1)  # ffmpeg sidechaincompress options
    bed_fade_s: float = Field(ge=0)
    lra: float = Field(gt=0)
    true_peak_margin_db: float = Field(ge=0)
    audio_kbps: int = Field(gt=0)
    sfx_pan_width: float = Field(ge=0, le=1)  # a cue at the frame edge pans this far (1 = hard left/right)


class MusicSections(Strict):
    first: str = Field(min_length=1)
    middle: str = Field(min_length=1)
    last: str = Field(min_length=1)


class CreateMusic(Strict):
    """c10_music: a bed built for the video (Eleven Music composition plan, one chunk per scene)."""

    model_id: str = Field(min_length=1)
    output_format: str = Field(min_length=1)
    min_chunk_ms: int = Field(gt=0)
    max_chunk_ms: int = Field(gt=0)
    dropout_db: float = Field(lt=0)
    ending_s: float = Field(ge=0)
    credits_per_s: float = Field(gt=0)  # dry-run estimate only
    positive_styles: list[str] = Field(min_length=1)
    negative_styles: list[str] = Field(default_factory=list)
    sections: MusicSections


class Create(Strict):
    """Phase 2 (`create`): defaults every project uses unless its brief says otherwise."""

    voice: CreateVoice
    footage: CreateFootage
    timing: CreateTiming
    design: CreateDesign
    script: CreateScript
    qa: CreateQa
    render: CreateRender
    lab: CreateLab
    motion: CreateMotion
    mix: CreateMix
    music: CreateMusic


class LensConfig(Strict):
    schema_version: int
    analysis: Analysis
    originals: Originals
    batch: Batch
    signals: Signals
    evidence: Evidence
    packets: Packets
    annotate: Annotate
    measure: Measure
    reconcile: Reconcile
    synth: Synth
    gold: Gold
    eval: Eval
    compare: Compare
    targets: Targets
    baselines: list[Baseline]
    create: Create
