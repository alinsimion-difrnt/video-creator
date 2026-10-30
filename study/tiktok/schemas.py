"""Notes on one TikTok, written by a Claude subagent (studies/tiktok/notes/<id>.json). Names only: every
time in a note is one of the times the packet gave (sheet frames, hook frames, measured cuts/events)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from lens.schemas.common import Provenance, Strict

Format = Literal[
    "talking_head",
    "green_screen",
    "split_screen",
    "screen_recording",
    "voiceover_broll",
    "skit",
    "podcast_clip",
    "interview",
    "listicle_text",
    "tutorial_demo",
    "news_reaction",
    "product_demo",
    "animation",
    "other",
]
HookType = Literal[
    "question",
    "bold_claim",
    "result_first",
    "curiosity_gap",
    "pattern_interrupt",
    "problem",
    "news",
    "demo_first",
    "list_promise",
    "story",
    "callout",
    "other",
]
Captions = Literal["none", "word_by_word", "sentence", "native_tiktok", "title_only"]
Position = Literal["top", "middle", "bottom", "mixed", "none"]
Device = Literal[
    "screen_recording",
    "screenshot",
    "arrow_or_circle",
    "zoom_punch",
    "sticker_emoji",
    "meme_cutaway",
    "b_roll",
    "title_text",
    "progress_bar",
    "split_screen",
    "green_screen_bg",
    "product_ui",
    "chart_or_number",
    "mascot",
    "prop",
    "sound_effect",
    "music_bed",
    "jump_cut",
    "camera_move",
    "costume_or_skit",
    "none",
]
Density = Literal["minimal", "moderate", "heavy"]
CtaKind = Literal["follow", "comment", "link_in_bio", "product", "save_or_share", "none", "other"]


class Hook(Strict):
    type: HookType
    line: str = Field(max_length=140)  # the opening line, paraphrased or quoted in under 20 words
    visual: str = Field(max_length=200)  # what the first frames show


class Beat(Strict):
    t: float = Field(ge=0)
    what: str = Field(max_length=160)


class Graphics(Strict):
    captions: Captions
    caption_position: Position
    devices: list[Device]
    density: Density
    per_minute_estimate: float | None = Field(default=None, ge=0)  # graphic changes a minute (model estimate)


class Character(Strict):
    who: str = Field(max_length=80)
    enters: str = Field(max_length=120)
    acts: str = Field(max_length=160)
    exits: str = Field(max_length=120)
    comes_back: bool


class Cta(Strict):
    kind: CtaKind
    t: float | None = Field(default=None, ge=0)


class TikTokNote(Strict):
    provenance: Provenance
    id: str
    format: Format
    hook: Hook
    beats: list[Beat] = Field(max_length=10)
    graphics: Graphics
    characters: list[Character] = Field(default_factory=list)
    cta: Cta
    why_it_works: list[str] = Field(min_length=1, max_length=4)
    weaknesses: list[str] = Field(default_factory=list, max_length=4)
    for_robert: str = Field(max_length=300)  # what Robert's reels can take from it
