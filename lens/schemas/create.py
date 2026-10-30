"""Phase 2 project files under `projects/<project>/` (docs/phase2-plan.md section 3).

Cross-file rules (facts exist in the brief, scenes match the script, the timeline is contiguous) are
checked in `lens.validate`; these models check each file on its own.
"""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from lens.schemas.common import Provenance, Sha256, Slug, Strict
from lens.schemas.config import Rect, ReelEntrance, ReelHandover

_TAG = re.compile(r"\[([^\]]+)\]")
_SCENE_ID = r"^s\d{2}$"


def audio_tags(text: str) -> list[str]:
    """The audio tags in a spoken line, without brackets (`[short pause]` -> `short pause`)."""
    return [m.strip().lower() for m in _TAG.findall(text)]


class Product(Strict):
    name: str = Field(min_length=1)  # as written on screen, e.g. "Acme"
    spoken: str = Field(min_length=1)  # as the voice must say it, e.g. "Ack-me"
    url: str = Field(pattern=r"^https://")
    one_liner: str = Field(min_length=1)


class LengthBand(Strict):
    min_s: float = Field(gt=0)
    max_s: float = Field(gt=0)

    @model_validator(mode="after")
    def _order(self) -> LengthBand:
        if self.min_s > self.max_s:
            raise ValueError("min_s must not exceed max_s")
        return self


class Fact(Strict):
    """A claim the video may make, with where it comes from (honesty guard, handoff 7.9)."""

    id: Slug
    claim: str = Field(min_length=1)
    source: str = Field(min_length=1)  # a URL or a named document


class Brief(Strict):
    """C1: what the video is for. Written by Claude from a short interview with Robert."""

    provenance: Provenance
    project: Slug
    brand: Slug  # the shared hand-off in brands/<brand>/ (ADR 0022)
    language: str = Field(default="en", pattern=r"^[a-z]{2}$")  # ISO 639-1, spoken and on screen
    voice: Literal["tts", "presenter"] = "tts"  # presenter: Robert's own footage (F1-F6, ADR 0025)
    # motion: Claude directs one composition inside direction.md (ADR 0032); templates: storyboard + C8
    build: Literal["motion", "templates"] = "motion"
    cut_s: float | None = Field(
        default=None, gt=0
    )  # film length when shorter than the timeline (cuts the tail)
    product: Product
    audience: str = Field(min_length=1)
    destination: Slug  # a key of config targets.loudness
    format: Slug  # a taxonomy format
    length: LengthBand
    tone: str = Field(min_length=1)
    message: str = Field(min_length=1)  # the one thing a viewer should remember
    facts: list[Fact] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_facts(self) -> Brief:
        ids = [f.id for f in self.facts]
        if len(ids) != len(set(ids)):
            raise ValueError("fact ids must be unique")
        return self


class ScriptScene(Strict):
    id: str = Field(pattern=_SCENE_ID)
    beat: Slug  # a taxonomy beat
    spoken: str = Field(min_length=1)  # the narration, with audio tags such as [chuckles]
    on_screen: list[str] = Field(default_factory=list)
    facts: list[Slug] = Field(default_factory=list)  # brief fact ids this scene relies on
    notes: str | None = None


class Script(Strict):
    """C2: one spoken line (or short paragraph) per scene, in order."""

    provenance: Provenance
    project: Slug
    scenes: list[ScriptScene] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_scenes(self) -> Script:
        ids = [s.id for s in self.scenes]
        if len(ids) != len(set(ids)):
            raise ValueError("scene ids must be unique")
        return self


class TimedWord(Strict):
    i: int = Field(ge=0)
    text: str = Field(min_length=1)
    start_s: float = Field(ge=0)
    end_s: float = Field(ge=0)

    @model_validator(mode="after")
    def _order(self) -> TimedWord:
        if self.end_s < self.start_s:
            raise ValueError("end_s must not be before start_s")
        return self


class TakeProsody(Strict):
    """lens speech measures of one take (whisper words, as the corpus was measured)."""

    wpm: float = Field(ge=0)
    articulation_wpm: float = Field(ge=0)
    pause_mean_ms: float = Field(ge=0)
    pitch_std_semitones: float | None = None
    energy_std_db: float | None = None
    in_range: int = Field(ge=0)  # how many voice-spec measures fall inside the premium band
    band_distance: float = Field(ge=0)  # summed distance outside the bands it was chosen on (0 = inside)
    brand_heard: bool | None = None  # the brand name came back in the transcript (None: not spoken)


class VoiceScene(Strict):
    scene: str = Field(pattern=_SCENE_ID)
    text_hash: Sha256  # hash of the spoken text + voice + model; a change means regenerate
    take: int = Field(ge=1)  # the chosen take
    takes: int = Field(ge=1)
    audio: str  # data/create/<project>/voice/<scene>-t<n>.mp3 (never committed)
    duration_s: float = Field(gt=0)
    words: list[TimedWord] = Field(min_length=1)  # from the ElevenLabs character alignment
    prosody: TakeProsody
    credits: int | None = Field(default=None, ge=0)  # spent on this scene's takes, when known

    @model_validator(mode="after")
    def _check(self) -> VoiceScene:
        if self.take > self.takes:
            raise ValueError("take must be one of the generated takes")
        if any(b.start_s < a.start_s for a, b in zip(self.words, self.words[1:], strict=False)):
            raise ValueError("words must be in time order")
        if self.words[-1].end_s > self.duration_s + 0.05:
            raise ValueError("words run past the audio")
        return self


class Voice(Strict):
    """C4: the chosen take per scene, with word timings."""

    provenance: Provenance
    project: Slug
    voice_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    scenes: list[VoiceScene] = Field(min_length=1)
    credits_used: int | None = Field(default=None, ge=0)


class TimelineScene(Strict):
    scene: str = Field(pattern=_SCENE_ID)
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)
    voice_start_s: float = Field(ge=0)
    voice_end_s: float = Field(gt=0)

    @model_validator(mode="after")
    def _inside(self) -> TimelineScene:
        if not self.start_s <= self.voice_start_s <= self.voice_end_s <= self.end_s:
            raise ValueError("the voice must sit inside the scene")
        return self


class TimelineWord(TimedWord):
    scene: str = Field(pattern=_SCENE_ID)


class Timeline(Strict):
    """C5: scene bounds and every word on one clock (seconds from the start of the video)."""

    provenance: Provenance
    project: Slug
    fps: int = Field(gt=0)
    total_s: float = Field(gt=0)
    scenes: list[TimelineScene] = Field(min_length=1)
    words: list[TimelineWord] = Field(min_length=1)

    @model_validator(mode="after")
    def _check(self) -> Timeline:
        for a, b in zip(self.scenes, self.scenes[1:], strict=False):
            if abs(b.start_s - a.end_s) > 1e-6:
                raise ValueError(f"{b.scene} must start where {a.scene} ends")
        if abs(self.scenes[-1].end_s - self.total_s) > 1e-6:
            raise ValueError("total_s must equal the last scene's end")
        bounds = {s.scene: s for s in self.scenes}
        for w in self.words:
            s = bounds.get(w.scene)
            if s is None:
                raise ValueError(f"word {w.i} belongs to unknown scene {w.scene}")
            if not s.voice_start_s - 1e-6 <= w.start_s <= w.end_s <= s.voice_end_s + 1e-6:
                raise ValueError(f"word {w.i} lies outside {w.scene}'s voice")
        if any(b.start_s < a.start_s for a, b in zip(self.words, self.words[1:], strict=False)):
            raise ValueError("words must be in time order")
        return self


Hex = Annotated[str, Field(pattern=r"^#[0-9A-F]{6}$")]
SizeClass = Literal["normal", "large", "display"]


class ContrastPair(Strict):
    text: Slug  # a colour role
    bg: Slug
    size: SizeClass
    use: str = Field(min_length=1)
    ratio: float = Field(ge=1)
    required: float = Field(ge=1)
    passes: bool
    exception: str | None = None  # why a failing pair is allowed (brand rule)


class TypeStyle(Strict):
    family: str = Field(min_length=1)
    weight: int = Field(ge=100, le=900)
    size_px: float = Field(gt=0)
    line_height: float = Field(gt=0)
    tracking_em: float
    uppercase: bool = False
    override: str | None = None  # where a hand-off value was changed for video, and why


class GlyphCoverage(Strict):
    family: str
    source: str  # where the checked font file came from
    has: dict[str, bool]


class Layout(Strict):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    safe_margin: int = Field(ge=0)
    section_gap: int = Field(ge=0)
    stack_gap: int = Field(ge=0)
    card_padding: int = Field(ge=0)
    card_radius: int = Field(ge=0)
    chip_radius: int = Field(ge=0)
    hairline_width: int = Field(ge=1)
    card_shadow: str
    caption_keepout_px: int = Field(ge=0)  # from the caption band's top to the frame's bottom
    safe: list[Rect] = Field(min_length=1)  # where critical content may go (config frame)
    caption_band: Rect


class Logo(Strict):
    """Logo files by use, relative to the brand folder (owner-supplied SVGs, ADR 0019/0022)."""

    primary: str  # on light backgrounds; the one templates use by default
    on_dark: str | None = None
    mono: str | None = None  # single-colour version
    min_height_corner: int = Field(gt=0)
    min_height_hero: int = Field(gt=0)

    def files(self) -> dict[str, str]:
        """Variant -> file, for the variants the brand has."""
        return {
            k: v for k, v in (("primary", self.primary), ("on_dark", self.on_dark), ("mono", self.mono)) if v
        }


class FontFamily(Strict):
    family: str = Field(min_length=1)  # as Google Fonts names it, e.g. "Space Grotesk"
    weights: str = Field(default="400..700", pattern=r"^\d{3}(\.\.\d{3})?$")  # a variable range or one weight
    source: Literal["google"] = "google"  # OFL fonts from Google Fonts (other licences: docs/research, B2)
    fallback: str = "system-ui, sans-serif"  # CSS stack after the family


class BrandType(Strict):
    families: dict[Slug, FontFamily]  # role -> family; needs `heading` and `body`
    sizes: Slug = "video1920"  # which size set of the hand-off's type styles to use
    overrides: dict[Slug, dict[str, float]] = Field(default_factory=dict)  # style -> {size: px}
    glyph_fallback: dict[str, str] = Field(default_factory=dict)  # glyph -> family to set it in
    extra_glyphs: str = ""  # glyphs this brand's copy needs beyond the house set (e.g. Romanian ăâîșț)

    @model_validator(mode="after")
    def _roles(self) -> BrandType:
        missing = {"heading", "body"} - set(self.families)
        if missing:
            raise ValueError(f"type.families needs {', '.join(sorted(missing))}")
        return self


class BrandPairSpec(Strict):
    text: Slug
    bg: Slug
    size: SizeClass
    use: str = Field(min_length=1)
    exception: str | None = None


class BrandLayout(Strict):
    """Token paths ("group.name") into the hand-off's tokens.json, or literal values."""

    safe_margin: str | int
    section_gap: str | int
    stack_gap: str | int
    card_padding: str | int
    card_radius: str | int
    chip_radius: str | int
    card_shadow: str
    hairline_width: int = Field(ge=1)


class CaptionStyle(Strict):
    """How burned-in captions look on one frame (brand video.yaml `captions.<frame>`)."""

    kind: Literal[
        "pill", "karaoke"
    ]  # pill: words on a soft surface (v2); karaoke: bold words, spoken one lit
    family: Slug = "body"  # a font family role
    weight: int = Field(ge=100, le=900)
    size_px: float = Field(gt=0)
    line_height: float = Field(gt=0)
    tracking_em: float = 0
    uppercase: bool = False
    text: Slug  # colour role of the words
    active: Slug  # colour role of the word being spoken
    dim_opacity: float = Field(default=1.0, ge=0, le=1)  # words not yet spoken
    background: Slug | None = None  # pill surface colour role
    background_alpha: float = Field(default=1.0, gt=0, le=1)
    stroke: Slug | None = None  # outline colour role (karaoke over footage)
    stroke_px: float = Field(default=0, ge=0)
    max_width_px: int = Field(gt=0)
    radius_px: int = Field(default=999, ge=0)
    padding_px: tuple[int, int] = (13, 30)  # vertical, horizontal

    @model_validator(mode="after")
    def _legible(self) -> CaptionStyle:
        if self.kind == "pill" and self.background is None:
            raise ValueError("a pill caption needs a background role")
        if (
            self.kind == "karaoke"
            and self.background is None
            and (self.stroke is None or self.stroke_px <= 0)
        ):
            raise ValueError("a karaoke caption over footage needs a background or a stroke")
        return self


class BrandFrame(Strict):
    """Per-frame type sizes and layout for frames other than landscape (e.g. vertical)."""

    sizes: Slug  # the size set in tokens.json type styles, e.g. video1080x1920
    overrides: dict[Slug, dict[str, float]] = Field(default_factory=dict)  # replaces type.overrides
    layout: dict[str, str | int] = Field(default_factory=dict)  # BrandLayout fields to change


class BrandVideo(Strict):
    """brands/<brand>/video.yaml: how a brand hand-off maps to video roles (input to C3, ADR 0022)."""

    colors: dict[Slug, str]  # role -> token path into tokens.json `color`
    pairs: list[BrandPairSpec] = Field(min_length=1)
    type: BrandType
    layout: BrandLayout
    logo: Logo
    accent_tint_alpha: float | None = Field(default=None, gt=0, lt=1)  # None: the config default
    strings: dict[Slug, str] = Field(default_factory=dict)  # template UI copy in the brand's language
    frames: dict[Slug, BrandFrame] = Field(default_factory=dict)  # type.sizes and layout serve landscape
    captions: dict[Slug, CaptionStyle] = Field(default_factory=dict)  # frame -> burned-in caption style


class Tokens(Strict):
    """C3: the brand hand-off made ready for the video frame, with contrast and glyphs checked."""

    provenance: Provenance
    project: Slug
    frame: Slug = "landscape"  # a key of config create.design.frames (from the brief's destination)
    colors: dict[Slug, Hex]
    contrast: list[ContrastPair] = Field(min_length=1)
    type: dict[Slug, TypeStyle]
    families: dict[Slug, FontFamily]  # role (heading, body, ...) -> family
    fonts_css: str = Field(pattern=r"^https://")
    glyphs: list[GlyphCoverage]
    glyph_fallback: dict[str, str]  # glyph -> family to set it in
    layout: Layout
    logo: Logo
    accent_tint_alpha: float = Field(gt=0, lt=1)  # accent at this alpha for chip and highlight backgrounds
    strings: dict[Slug, str] = Field(default_factory=dict)  # template UI copy (labels, chips)
    captions: CaptionStyle | None = None  # the brand's caption style for this frame (None: not defined)


class Cue(Strict):
    """An action that starts when a word of the narration starts (a timeline word index; never a time)."""

    word: int = Field(ge=0)
    do: str = Field(min_length=1)  # what happens, in plain words
    target: str | None = None  # the slot it acts on


class StoryScene(Strict):
    scene: str = Field(pattern=_SCENE_ID)
    archetype: Slug  # an id from exports/archetypes.json, or "freeform"
    freeform_reason: str | None = None
    canvas: Literal["marketing", "product"]  # brand DESIGN.md §3: do not mix registers within a scene
    title: str | None = None  # an on-screen step heading, when the archetype has no slot for one
    slots: dict[Slug, Any]
    accent: str | None = None  # the one orange moment in the scene
    example_data: bool = False  # on-screen numbers or brands that are illustrative, marked on screen
    cues: list[Cue] = Field(min_length=1)

    @model_validator(mode="after")
    def _check(self) -> StoryScene:
        if (self.archetype == "freeform") != bool(self.freeform_reason):
            raise ValueError("a freeform scene needs freeform_reason, and only a freeform scene has one")
        if any(b.word < a.word for a, b in zip(self.cues, self.cues[1:], strict=False)):
            raise ValueError("cues must follow the narration in order")
        return self


class Storyboard(Strict):
    """C6: an archetype per scene, its slots filled, every motion cue tied to a spoken word."""

    provenance: Provenance
    project: Slug
    scenes: list[StoryScene] = Field(min_length=1)


class Box(Strict):
    """A critical element's on-screen box at one sample time (measured in a browser by `create audit`)."""

    scene: str = Field(pattern=_SCENE_ID)
    t: float = Field(ge=0)  # seconds from the scene's start
    element: str  # a CSS path to the element
    kind: Literal["text", "logo", "caption"]
    text: str  # the element's text (first 60 characters), "" for a logo
    x0: float
    y0: float
    x1: float
    y1: float
    opacity: float = Field(ge=0, le=1)  # effective, with every ancestor's opacity


class SafeZoneIssue(Strict):
    scene: str = Field(pattern=_SCENE_ID)
    element: str
    text: str
    problem: Literal["outside_safe", "in_caption_band"]
    t0: float = Field(ge=0)  # first and last sample time with the problem
    t1: float = Field(ge=0)
    box: list[float]  # [x0, y0, x1, y1] at t0


class SafeZoneReport(Strict):
    """C8 audit: critical text and logos against the frame's safe area and caption band (config frames)."""

    provenance: Provenance
    project: Slug
    frame: Slug
    step_s: float = Field(gt=0)
    min_hold_s: float = Field(ge=0)  # problems shorter than this (motion entering or leaving) are not issues
    scenes: list[str]
    boxes_checked: int = Field(ge=0)
    issues: list[SafeZoneIssue]
    ok: bool

    @model_validator(mode="after")
    def _ok(self) -> SafeZoneReport:
        if self.ok != (not self.issues):
            raise ValueError("ok must be true exactly when there are no issues")
        return self


class GradeFinding(Strict):
    level: Literal["fail", "warn"]  # fail: must be fixed before the mix; warn: advisory
    area: Literal[
        "layout", "contrast", "brand", "motion", "pacing", "timing", "sound", "text", "accent", "overlap"
    ]
    msg: str = Field(min_length=1)
    t: float | None = Field(default=None, ge=0)  # when it happens, if it has a time


class GradeMeasures(Strict):
    transitions: list[str]  # lens kind@seconds; empty = one continuous shot
    events: int = Field(ge=0)
    motion_share: float = Field(ge=0, le=1)
    moves: int = Field(ge=0)  # timeline tweens shorter than ambient_min_s
    sfx: int = Field(ge=0)
    dead_hold_s: float = Field(ge=0)
    longest_idle_s: float = Field(ge=0)
    min_text_px: float | None = Field(default=None, ge=0)  # smallest rendered text seen
    max_accent_moments: float = Field(ge=0)


class MotionGrade(Strict):
    """C8 grade: the checks code can make on a motion build (ADR 0032)."""

    provenance: Provenance
    project: Slug
    duration_s: float = Field(gt=0)
    measures: GradeMeasures
    findings: list[GradeFinding]
    fails: int = Field(ge=0)
    warns: int = Field(ge=0)
    ok: bool

    @model_validator(mode="after")
    def _counts(self) -> MotionGrade:
        fails = sum(f.level == "fail" for f in self.findings)
        if self.fails != fails or self.warns != len(self.findings) - fails:
            raise ValueError("fails and warns must count the findings")
        if self.ok != (fails == 0):
            raise ValueError("ok must be true exactly when there are no fails")
        return self


class SfxCue(Strict):
    t: float = Field(ge=0)  # seconds on the film clock
    sfx: Slug  # a name from config create.motion.sfx
    gain_db: float = Field(le=0)
    x: float | None = Field(default=None, ge=0, le=1)  # the reveal's centre, share of frame width; panned


class CaptionWord(Strict):
    i: int = Field(ge=0)  # timeline word index
    w: str = Field(min_length=1)
    t: float = Field(ge=0)  # the word's start on the video clock
    end: float = Field(ge=0)


class CaptionGroup(Strict):
    start: float = Field(ge=0)  # the group shows from here ...
    end: float = Field(gt=0)  # ... to here
    words: list[CaptionWord] = Field(min_length=1)

    @model_validator(mode="after")
    def _inside(self) -> CaptionGroup:
        if not self.start <= self.words[0].t + 1e-6 or self.end <= self.start:
            raise ValueError("a group must start by its first word and end after it starts")
        return self


class Captions(Strict):
    """C11: burned-in caption groups from the narration's word timings (one clock with the timeline)."""

    provenance: Provenance
    project: Slug
    frame: Slug
    groups: list[CaptionGroup] = Field(min_length=1)

    @model_validator(mode="after")
    def _order(self) -> Captions:
        for a, b in zip(self.groups, self.groups[1:], strict=False):
            if b.start < a.end - 1e-6:
                raise ValueError(f"groups overlap at {b.start}s")
        idx = [w.i for g in self.groups for w in g.words]
        if idx != sorted(set(idx)):
            raise ValueError("every word appears once, in order")
        return self


class FootageTake(Strict):
    id: Slug  # the raw file's stem, slugged
    raw: str  # data/create/<p>/footage/raw/<file>
    master: str  # data/create/<p>/footage/master/<id>.mov
    audio: str  # data/create/<p>/footage/master/<id>.wav (16 kHz mono, for speech-to-text)
    width: int = Field(gt=0)  # master size (rotation applied)
    height: int = Field(gt=0)
    frames: int = Field(gt=0)
    duration_s: float = Field(gt=0)
    source_fps: str  # as probed, e.g. "30000/1001" or "vfr"
    hdr: bool  # the raw file was HDR (tone-mapped to SDR Rec.709)


class Footage(Strict):
    """F1: conformed masters of Robert's raw takes (constant fps, SDR, short GOP)."""

    provenance: Provenance
    project: Slug
    fps: int = Field(gt=0)
    takes: list[FootageTake] = Field(min_length=1)


class TranscriptWord(Strict):
    i: int = Field(ge=0)
    take: Slug
    text: str = Field(min_length=1)
    kind: Literal["word", "filler", "event"]
    start_s: float = Field(ge=0)  # on the take's master clock
    end_s: float = Field(ge=0)
    logprob: float | None = None


class Transcript(Strict):
    """F2: every word of every take, verbatim (fillers kept), on the masters' clocks."""

    provenance: Provenance
    project: Slug
    engine: Literal["elevenlabs", "whisper"]
    model: str
    language: str
    words: list[TranscriptWord] = Field(min_length=1)

    @model_validator(mode="after")
    def _order(self) -> Transcript:
        if [w.i for w in self.words] != list(range(len(self.words))):
            raise ValueError("word indexes must be 0..n-1 in order")
        return self


class CutProposal(Strict):
    id: str = Field(pattern=r"^c\d{3,}$")
    kind: Literal["silence", "filler", "retake", "cue", "count_in"]
    take: Slug
    start_s: float = Field(ge=0)  # removed range on the take's master clock
    end_s: float = Field(gt=0)
    words: list[int] = Field(default_factory=list)  # transcript words removed
    reason: str = Field(min_length=1)


class CutRange(Strict):
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)
    reason: str = "Robert's note"

    @model_validator(mode="after")
    def _order(self) -> CutRange:
        if self.end_s <= self.start_s:
            raise ValueError("end_s must be after start_s")
        return self


class CutNotes(Strict):
    """Robert's own cut instructions for a take (projects/<p>/cut-notes.yaml, optional F3 input), applied over
    the proposals: where the video starts and ends, spans that must stay whole (a silence that carries an
    effect), and extra cuts. Times are on the take's master clock."""

    take: Slug
    start_s: float | None = Field(default=None, ge=0)  # cut everything before (notes to Claude, a count-in)
    end_s: float | None = Field(default=None, gt=0)  # cut everything after
    keep: list[CutRange] = Field(default_factory=list)  # never cut inside these
    cut: list[CutRange] = Field(default_factory=list)  # extra cuts (a false start the proposer missed)
    # a short version: only these spans stay (everything between them is cut); proposals apply inside them
    keep_only: list[CutRange] = Field(default_factory=list)
    open_with: CutRange | None = None  # a flash-forward: this span plays first, then the video from its start
    close_with: CutRange | None = (
        None  # a span played again at the end (a still empty chair: time for a card)
    )


class Cuts(Strict):
    """F3: proposed cuts. Robert approves them in projects/<p>/cuts-approved.yaml (a human gate)."""

    provenance: Provenance
    project: Slug
    proposals: list[CutProposal]


class CutApprovals(Strict):
    """projects/<p>/cuts-approved.yaml: Robert's decisions (written by him or by `create cuts --approve`)."""

    approve: list[str] | Literal["all"] = Field(default_factory=list)
    reject: list[str] = Field(default_factory=list)


class ShotEdit(Strict):
    """One shot's crop as Robert set it on the edit page. Matched by take and first master frame, so a shot
    keeps its edit when a cut change renumbers the segments."""

    take: Slug
    src_in: int = Field(ge=0)
    zoom: float = Field(ge=1, le=3)  # 1 = the widest crop of the output's aspect (F5 fill_crop)
    dx: float = Field(default=0.0, ge=-1, le=1)  # shift from the face-placed crop, a share of its width
    dy: float = Field(default=0.0, ge=-1, le=1)  # ...and of its height (+ = down)


class HeldZoomEdit(Strict):
    word: int = Field(ge=0)  # the held zoom that starts on this word (ReelZoom.word)
    scale: float = Field(ge=1, le=2)  # 1 removes it


class PlanEdit(Strict):
    """Robert's changes to one reel plan's zooms; `create reel` applies them over the plan file."""

    push: float | None = Field(default=None, ge=1.0, le=1.15)
    drop_punches: list[int] = Field(default_factory=list)  # word indexes of quick zooms to remove
    zooms: list[HeldZoomEdit] = Field(default_factory=list)


class EditNote(Strict):
    t: float = Field(ge=0)  # seconds on the video's clock
    text: str = Field(min_length=1, max_length=2000)
    plan: str | None = None  # the plan file of the version he watched
    done: bool = False  # set once Claude has acted on it


class Edits(Strict):
    """projects/<p>/edits.yaml: Robert's corrections from the edit page (`create edits <p> --page`). Values,
    not wishes: F5 uses the shot crops as given and `create reel` the plan changes; notes are for Claude."""

    shots: list[ShotEdit] = Field(default_factory=list)
    plans: dict[str, PlanEdit] = Field(default_factory=dict)  # keyed by plan file name (reel-overlay.yaml)
    notes: list[EditNote] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique(self) -> Edits:
        keys = [(s.take, s.src_in) for s in self.shots]
        if len(keys) != len(set(keys)):
            raise ValueError("one edit per shot (take, src_in)")
        return self


class EdlSegment(Strict):
    take: Slug
    src_in: int = Field(ge=0)  # frames on the take's master (inclusive)
    src_out: int = Field(gt=0)  # exclusive
    rec_in: int = Field(ge=0)  # frames on the edited clock
    cold_open: bool = False  # a flash-forward shown first: its words are not on the timeline (ADR 0030)


class Edl(Strict):
    """F4: the edit, in integer frames; words are remapped by C5 (presenter mode)."""

    provenance: Provenance
    project: Slug
    fps: int = Field(gt=0)
    segments: list[EdlSegment] = Field(min_length=1)
    applied: list[str]  # approved cut ids
    duration_frames: int = Field(gt=0)

    @model_validator(mode="after")
    def _contiguous(self) -> Edl:
        rec = 0
        for s in self.segments:
            if s.src_out <= s.src_in:
                raise ValueError("segments need src_in < src_out")
            if s.rec_in != rec:
                raise ValueError(f"segment at {s.rec_in} must start at {rec}")
            rec += s.src_out - s.src_in
        if rec != self.duration_frames:
            raise ValueError("duration_frames must equal the segments' total")
        return self


class Crop(Strict):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(gt=0)
    h: int = Field(gt=0)


class SegmentFraming(Strict):
    segment: int = Field(ge=0)  # index into edl.segments
    take: Slug
    face: list[float] | None  # median face box [x, y, w, h] on the master, None when no face was found
    full: Crop  # the crop that fills the output frame
    zoom: float = Field(ge=1)  # punch-in applied to `full`
    pip: Crop  # a square around the face for the corner bubble


class Framing(Strict):
    """F5: one steady crop per edited segment (face-aware), for the full frame and for the corner bubble."""

    provenance: Provenance
    project: Slug
    frame: Slug
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    segments: list[SegmentFraming] = Field(min_length=1)


PresenterLayout = Literal["full", "pip", "split", "off"]


class LayoutPlan(Strict):
    """projects/<p>/layout.yaml: where the presenter is, per timeline scene (written by Robert or Claude).

    full: the presenter fills the frame; pip: the presenter shrinks into a corner bubble over the background;
    split: the product (background) whole on top, the presenter moved lower beneath it;
    off: only the background shows (the presenter's voice continues)."""

    default: PresenterLayout = "full"
    corner: Literal["br", "bl", "tr", "tl"] = "br"
    transition_s: float = Field(default=0.6, ge=0, le=2)
    scenes: dict[str, PresenterLayout] = Field(default_factory=dict)  # scene id -> layout


class OverlayItem(Strict):
    """One graphic over the presenter, timed to their words (timeline word indexes, never times)."""

    word: int = Field(ge=0)  # appears as this word starts
    until: int | None = Field(default=None, ge=0)  # leaves as this word ends (default: after duration_s)
    duration_s: float = Field(default=2.6, gt=0)
    kind: Literal["keyword", "card", "stat", "list"]
    title: str = Field(min_length=1)  # keyword text, card heading, the stat's number, or the list heading
    lines: list[str] = Field(default_factory=list, max_length=4)  # card lines, the stat's label, list rows
    position: Literal["auto", "top", "left", "right"] = "auto"
    accent: bool = False  # the one accent moment: title in the brand accent

    @model_validator(mode="after")
    def _order(self) -> OverlayItem:
        if self.until is not None and self.until < self.word:
            raise ValueError("until must not come before word")
        return self


class OverlayPlan(Strict):
    """projects/<p>/overlays.yaml: graphics over the presenter's own video (written by Claude or Robert)."""

    items: list[OverlayItem] = Field(min_length=1)


ReelWidget = Literal[
    "chat",
    "search",
    "sources",
    "review",
    "counter",
    "pins",
    "chart",
    "cta",
    "sticker",
    "queries",
    "tiles",
    "logo",
    "shredder",
    "code",
    "bucket",
    "agents",
    "pixel",
    "bars",
    "handoff",
]


class ReelLayoutAt(Strict):
    """From this word on, the presenter is in this layout (see LayoutPlan for the four layouts)."""

    word: int = Field(ge=0)
    layout: PresenterLayout


class ReelItem(Strict):
    """One animated widget (create/kit/motion.js), timed to the presenter's words (never times).

    product: drawn in the product area (the top half in split, the frame above the captions in pip/off);
    overlay: over the presenter's own video, in a zone clear of the face and the captions."""

    word: int = Field(ge=0)  # enters as this word starts
    until: int = Field(ge=0)  # has left by the end of this word
    kind: ReelWidget
    where: Literal["product", "overlay"] = "overlay"
    position: Literal["auto", "top", "chest", "left"] = "auto"  # overlays only
    marks: list[int] = Field(
        default_factory=list
    )  # word indexes of the widget's beats (typing, rows, clicks)
    w: int | None = Field(default=None, ge=200, le=1080)  # layout width before fitting (default per kind)
    # palm: the card rides on the presenter's lower palm (pose-tracked), like a tray (tournament n04)
    hold: Literal["palm"] | None = None
    # product cards: how this card takes over from the one before it (default: the plan's motion style)
    handover: ReelHandover | None = None
    spec: dict[str, Any] = Field(default_factory=dict)  # the widget's own fields (motion.js)

    @model_validator(mode="after")
    def _order(self) -> ReelItem:
        if self.until < self.word:
            raise ValueError("until must not come before word")
        if any(m < self.word or m > self.until for m in self.marks):
            raise ValueError("marks must lie between word and until")
        return self


# image: projects/<p>/assets/<image>; fish, cat, fred: drawn in code. fred: an upright cartoon fish rigged in
# SVG (stands on his tail, fins as arms); his `photo` style is the image
PropArt = Literal["image", "fish", "cat", "fred"]
PropStyle = Literal["photo", "illustrated", "pixel", "toon3d"]
PropAnchor = Literal[
    "lap", "left", "right", "shoulder_left", "shoulder_right", "floor_left", "floor_right", "above", "centre"
]  # fmt: skip
PropEnter = Literal["pop", "drop", "fade", "slide_left", "slide_right", "walk_left", "walk_right", "none"]
PropExit = Literal["pop", "fade", "fall", "run_left", "run_right", "swim_left", "swim_right", "none"]
PropAction = Literal["jump", "spin", "wiggle", "blink", "flip", "squash", "look", "wave", "clap", "dance"]
PropHold = Literal["book", "pencil", "phone", "hammer", "none"]  # fred: what his fins hold (and do)
PropRide = Literal["boat", "none"]  # fred: rows a little boat through the air
# automail: fred's steel fin and tail
# shock ... angry: pixel Fred's expressions (create/pixel/fred.py EXPRESSIONS), worn like accessories
Accessory = Literal[
    "top_hat", "moustache", "sunglasses", "crown", "bow_tie", "automail",
    "shock", "smug", "terror", "happy", "angry",
]  # fmt: skip


class FramePlace(Strict):
    """(x, y) as shares of the shot on screen at that moment (the shot's crop of the master): for cameos at a
    frame edge whatever the crop (r03: master shares fell off a face-following crop)."""

    frame: tuple[float, float]


# a named spot by the presenter, (x, y) as shares of the master, or {frame: [x, y]}: shares of the shot
# on screen
Place = PropAnchor | tuple[float, float] | FramePlace


class ReelPropBeat(Strict):
    """Something a prop does on a word: change style, put on or take off accessories, move, act, carry."""

    word: int = Field(ge=0)
    style: PropStyle | None = None
    add: list[Accessory] = Field(default_factory=list)
    remove: list[Accessory] = Field(default_factory=list)
    move: Place | None = None  # travel here (bottom centre of the prop), arriving by the end of the word
    do: PropAction | None = None
    tag: str | None = Field(default=None, max_length=24)  # a name tag pops up under it ("Fred")
    say: str | None = Field(default=None, max_length=24)  # a small speech bubble ("blub")
    emote: str | None = Field(default=None, max_length=4)  # a big symbol pops over its head ("!", "💢")
    carry: Slug | None = None  # picks up this other prop (mouth or hands) and takes it along until its exit
    hold: PropHold | None = None  # fred: starts reading, writing, texting or hammering (none: puts it away)
    ride: PropRide | None = None  # fred: gets into the boat (none: hops out)
    path: list[Place] = Field(default_factory=list, max_length=8)  # travels through these spots in turn
    # hand: from this word the prop rides the hand that goes lowest (pose, create/footage/pose.py) until the
    # next beat, and stays where it is let go (the hand's lowest point): put down by hand.
    # palm: it stands on the lower hand's palm (held out, palm up) until the next beat that moves it
    follow: Literal["hand", "palm", "flee"] | None = None  # flee: runs ahead of the leading hand (r11)
    # a pixel gag item beside it (create/pixel/items.py: popcorn tv camera bucket free dog bird censor), for
    # `gag_s` (default: until its next gag beat, at most 3 s); dog and bird stand in for it (a transformation)
    gag: str | None = None
    gag_s: float | None = Field(default=None, gt=0, le=10)


class ReelProp(Strict):
    """A character or object in the room with the presenter (create/kit/props.js), timed to words.

    It lives in room space: placed on the take's master (a spot by the presenter's face, or shares of the
    master), so it moves with the push-in, punch-ins and layout moves and stays put across jump cuts."""

    id: Slug
    art: PropArt = "image"
    image: str | None = None  # file name in projects/<p>/assets/ (Robert's media, never committed)
    word: int = Field(ge=0)  # enters as this word starts
    until: int = Field(ge=0)  # has left by the end of this word
    at: Place = "lap"
    size: float = Field(default=0.22, gt=0.02, le=1.0)  # width as a share of the master's width
    flip: bool = False  # faces the other way (code-drawn art faces right)
    from_start: bool = False  # there from the video's first frame (a loop's cold open: tournament n09)
    to_end: bool = False  # stays to the video's last frame (a loop's end)
    style: PropStyle = "photo"
    accessories: list[Accessory] = Field(default_factory=list)
    enter: PropEnter = "pop"
    exit: PropExit = "pop"
    idle: Literal["bob", "breathe", "swim", "none"] = "bob"
    behind: bool = False  # behind the presenter (needs `create matte`)
    points: dict[str, tuple[float, float]] = Field(default_factory=dict)  # head, mouth: shares of its box
    colors: dict[str, str] = Field(default_factory=dict)  # cat: fur stripe belly nose eyes iris bandana
    beats: list[ReelPropBeat] = Field(default_factory=list)

    @model_validator(mode="after")
    def _order(self) -> ReelProp:
        if self.until < self.word:
            raise ValueError("until must not come before word")
        bad = [c for c in self.colors.values() if not re.fullmatch(r"#[0-9a-fA-F]{6}", c)]
        if bad or set(self.colors) - {"fur", "stripe", "belly", "nose", "eyes", "iris", "bandana"}:
            raise ValueError("colors: fur, stripe, belly, nose, eyes, iris, bandana as #rrggbb")
        if self.art == "image" and not self.image:
            raise ValueError("art: image needs `image` (a file in projects/<p>/assets/)")
        words = [b.word for b in self.beats]
        if words != sorted(words) or any(w < self.word or w > self.until for w in words):
            raise ValueError("beats must go forward between word and until")
        return self


FxKind = Literal[
    "shake", "flash", "fade_black", "grade", "caption_font", "anime", "blocky", "glitch", "alchemy",
    "automail", "blackhole", "endcard", "rewind", "look", "hud", "comic", "burst", "panels", "wall", "clone",
    "freeze",
]  # fmt: skip


class ReelMotion(Strict):
    """How the video moves as a whole (ADR 0033): a style from config `create.footage.reel.styles`, chosen
    for the topic (say why in the plan's `# look:` comment), with any of its parts overridden. Code applies
    it: an entrance per kind of widget, the hand-over between product cards (morph | push | stack | cut),
    a shared step label over a run of cards, a drifting background, the push-in continuing across cuts,
    cards entering on the cut. Without `motion:` a plan moves as the first take did (`classic`)."""

    style: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    cards: ReelEntrance | None = None
    stickers: ReelEntrance | None = None
    numbers: ReelEntrance | None = None
    handover: ReelHandover | None = None
    bg: Literal["none", "drift"] | None = None
    kicker: Literal["each", "run"] | None = None
    push_alternate: bool | None = None
    cut_nudge: bool | None = None
    snap_cuts: bool | None = None


class ReelZoom(Strict):
    """A held zoom on the face: in as `word` starts, out as `until` starts ("the zoom in, the zoom out")."""

    word: int = Field(ge=0)
    until: int = Field(ge=0)
    scale: float = Field(default=1.25, gt=1, le=2)


class ReelSound(Strict):
    """A sound on a word (ADR 0030): a formula sound (`sound`, create/footage/sfx.py RECIPES), an ElevenLabs
    sound effect from a prompt (`prompt`, cached by prompt and length), or a narrated line (`say`, an
    ElevenLabs voice: the black-hole explainer). Effects sit `create.footage.sfx.level_db` under the voice
    plus `gain_db`; narration plays at `gain_db`."""

    word: int = Field(ge=0)
    sound: str | None = None
    prompt: str | None = Field(default=None, max_length=300)
    duration_s: float | None = Field(default=None, ge=0.5, le=30)
    say: str | None = Field(default=None, max_length=600)
    voice: str | None = None  # an ElevenLabs voice id for `say` (default: config create.voice)
    gain_db: float = Field(default=0.0, ge=-30, le=12)
    offset_s: float = Field(default=0.0, ge=-2, le=10)  # from the word's start

    @model_validator(mode="after")
    def _one(self) -> ReelSound:
        if sum(x is not None for x in (self.sound, self.prompt, self.say)) != 1:
            raise ValueError("a sound needs exactly one of sound, prompt or say")
        return self


class ReelFx(Strict):
    """An effect on the presenter or the whole frame, timed to words.

    shake, flash, glitch: one hit on the word. fade_black: to black from the word, by the end of `until`
    (or the video), and stays black. alchemy: a transmutation circle lights up under a prop or a spot
    (spec at: a prop id or a spot; size) with sparks and a flash, for 2.4 s (or until `until`).
    grade (spec hue, saturate, contrast, brightness), caption_font (spec
    family: heading, body, mono; color), anime (spec hair, eyes) and blocky (spec block px): from the word
    until the end of `until`. automail: the presenter's limbs turn to steel (spec limbs: right_arm,
    right_leg ... from the pose, create/footage/pose.py), from the word until `until` (or the video's end).
    blackhole: a full-frame space cutaway (spec labels: [[share of the span, text]], victim: a prop id
    pulled in) in the silence from the END of `word` to the START of `until`. endcard: a closing card
    (spec title, sub, credit, cta: a follow line, cat: a prop id shown happy) from `delay_s` after the word to
    the end.
    look: a film look over the whole frame from the word to `until` (or the end): spec letterbox (bar px),
    vignette, grain, flicker (0-1) and tint (a CSS colour, multiplied). hud: a game-style counter in the top
    left (spec label, steps: [[word, text]]: the text changes with a pop on each word).
    comic: the presenter drawn as a comic (flat colour, ink lines) with halftone dots, from the word to
    `until`. burst: a comic sound word in a starburst on the word (spec text, at: [x, y] frame shares, color).
    panels: a comic-page recap from the word to `until` (or the end): freeze-frames of the presenter's own
    video at spec words (offset_s each) slam in as tilted panels, spec captions per panel.
    wall: words painted on a room surface (the wood of a slatted wall), from the word to `until` (or the
    end): spec steps [[word, text]] (each replaces the last, painted letter by letter), columns [x0, x1]
    (master px where the surface is free), rows [top, bottom] (shares of its height), frame_s (the master
    time to measure it on), color.
    clone: a second presenter (his own cut-out from the moment at spec from_word, delayed by delay_s) from
    the word to `until`, shifted by spec dx (a share of the frame's width), scaled, mirrored (flip) and
    tinted (hue degrees, saturate); spec label shows a tag over it.
    freeze: bullet time: the frame as the viewer sees it at the word (+ spec offset_s) freezes and the camera
    swings round it in 2.5D (a depth map of that still) for spec dur seconds, then the video goes on."""

    word: int = Field(ge=0)
    until: int | None = Field(default=None, ge=0)
    kind: FxKind
    spec: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _order(self) -> ReelFx:
        if self.until is not None and self.until < self.word:
            raise ValueError("until must not come before word")
        if self.kind in ("grade", "caption_font", "anime", "blocky", "comic") and self.until is None:
            raise ValueError(f"{self.kind} needs until (where the effect ends)")
        return self


class ReelGrade(Strict):
    """A light look on the presenter's video (CSS filters; 1 / 0 = unchanged)."""

    contrast: float = Field(default=1.0, ge=0.8, le=1.3)
    saturate: float = Field(default=1.0, ge=0.7, le=1.4)
    brightness: float = Field(default=1.0, ge=0.85, le=1.15)
    warmth: float = Field(default=0.0, ge=0, le=0.2)  # a little sepia warms skin and light


class ReelMusic(Strict):
    """A music bed for the whole video (tournament n06): Eleven Music from a prompt (instrumental, the video's
    length, cached), its beats measured (lens.signals.audio.beats); `snap` moves hits onto the nearest beat,
    `pulse` gives each bar's first beat a small zoom."""

    prompt: str = Field(max_length=400)
    gain_db: float = Field(default=-16.0, ge=-40, le=0)
    snap: bool = True
    pulse: bool = True


class ReelPlan(Strict):
    """projects/<p>/reel.yaml: the whole presenter video in one composition (`create reel`): where the
    presenter is, the widgets on their words, where the captions go, a push-in per shot and a grade."""

    layout: list[ReelLayoutAt] = Field(min_length=1)
    corner: Literal["br", "bl", "tr", "tl"] = "br"
    transition_s: float = Field(default=0.6, ge=0, le=2)
    split_seam: int = Field(default=1040, ge=600, le=1300)  # split: the product area's bottom edge
    captions: Literal["top", "band"] = "top"  # full layout: above the head, or the frame's caption band
    # the spoken word: in the accent colour, or white on an accent pill (reads on a bright wall: reviews)
    caption_style: Literal["color", "pill"] = "color"
    # captions on a white plate from config (create.footage.reel.caption_plate): ink words, the spoken one in
    # the accent; one line at a time. With `pill`, the spoken word is coloured, not boxed.
    caption_plate: bool = False
    # pip: the bubble sits low in its corner, just above the platform's description zone, and the captions sit
    # above it with the product above them (default: above the caption band, mid-frame)
    pip_low: bool = False
    # split: the whole head clears the seam by this many px, per shot (default: the face sits
    # split_face_offset below the seam, which clips the hair)
    split_head_gap: int | None = Field(default=None, ge=0, le=400)
    push: float = Field(default=1.05, ge=1.0, le=1.15)  # each shot slowly scales to this (1 = still)
    grade: ReelGrade = Field(default_factory=ReelGrade)
    product_bg: Literal["canvas", "grid", "glow", "ink"] = "grid"  # ink: dark, captions stay light
    punches: list[int] = Field(default_factory=list)  # word indexes: a quick zoom on the face (full shots)
    zooms: list[ReelZoom] = Field(default_factory=list)  # held zooms between two words (ADR 0030)
    overlay_zone: Literal["auto", "left", "chest"] = "auto"  # left: beside the face, off the chest and logo
    # full shots with no clear air above the head: the caption moves to the shirt (the caption band, below the
    # chin) instead of grazing the hair (Robert, ai-picks: "above, inside animations, or over my shirt")
    caption_shirt: bool = False
    sounds: bool = True  # soft UI sounds under the voice (create/footage/sfx.py)
    # the product area is a bespoke panel (projects/<p>/panel/index.html, `create panel`, ADR 0034) composited
    # over this render: the plan only places the presenter, the captions and the audio; items may be empty
    panel: bool = False
    items: list[ReelItem] = Field(default_factory=list)
    props: list[ReelProp] = Field(default_factory=list)  # characters in the room (create/kit/props.js)
    fx: list[ReelFx] = Field(default_factory=list)
    audio: list[ReelSound] = Field(default_factory=list)  # gag sounds and narration on words (ADR 0030)
    music: ReelMusic | None = None  # a beat-measured bed under everything (tournament n06)
    motion: ReelMotion | None = None  # the video's motion style (ADR 0033); None: classic
    # Fred's items beside him ("left", "above") pop at this frame spot instead, `scale` times bigger: at his
    # feet they sat under the platform's description and buttons (r15 reviews). {frame: [x, y], scale: k}
    gag_spot: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _starts(self) -> ReelPlan:
        words = [b.word for b in self.layout]
        if words[0] != 0 or words != sorted(words):
            raise ValueError("layout must start at word 0 and go forward")
        ids = [p.id for p in self.props]
        if len(ids) != len(set(ids)):
            raise ValueError("prop ids must be unique")
        for p in self.props:
            for b in p.beats:
                if b.carry is not None and (b.carry not in ids or b.carry == p.id):
                    raise ValueError(f"prop {p.id}: carry {b.carry!r} is not another prop")
        return self


class QaCheck(Strict):
    id: Slug
    ok: bool
    value: str  # what was measured
    target: str  # what it should be (config create.qa, targets.loudness, frames)
    note: str = ""


class QaReport(Strict):
    """C13: a finished video checked against the destination's rules (`create qa`)."""

    provenance: Provenance
    project: Slug
    video: str  # the checked file, relative to the repo or absolute
    destination: Slug
    checks: list[QaCheck] = Field(min_length=1)
    ok: bool

    @model_validator(mode="after")
    def _ok(self) -> QaReport:
        if self.ok != all(c.ok for c in self.checks):
            raise ValueError("ok must be true exactly when every check passes")
        return self
