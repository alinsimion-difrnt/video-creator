"""A note on one pixel-art subject (studies/pixel-art/notes/<id>.json): a game, style, artist, creator,
tutorial or talk from sources.yaml, or a pixel-art TikTok clip (tiktok.yaml). Written by a Claude subagent.
The fields follow Robert's "what to watch for" (palette, lighting, silhouette, motion, texture, camera, sound,
one feel line) plus how characters act in and out of the scene."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from lens.schemas.common import Provenance, Strict

Kind = Literal["game", "style", "artist", "creator", "tutorial", "talk", "clip"]


class Palette(Strict):
    colours_estimate: int | None = Field(default=None, ge=1)  # use the metrics' palette_size when given
    shadows: Literal["cool", "warm", "neutral", "mixed", "unknown"]
    notes: str = Field(max_length=300)


class Motion(Strict):
    timing: str = Field(max_length=300)  # holds, frame counts (from metrics when given), easing
    principles: list[str] = Field(
        default_factory=list, max_length=6
    )  # anticipation, squash, smear, overlap...


class Acting(Strict):
    """How a character performs in a scene (Robert: Fred should go out, come back, do it again, act small in
    the back)."""

    enters: str = Field(default="", max_length=200)
    acts: str = Field(default="", max_length=240)
    exits: str = Field(default="", max_length=200)
    comes_back: bool | None = None
    depth: str = Field(default="", max_length=200)  # foreground/background use, scale changes


class PixelNote(Strict):
    provenance: Provenance
    id: str
    kind: Kind
    palette: Palette
    lighting: str = Field(max_length=300)
    silhouette: str = Field(max_length=300)
    motion: Motion
    texture: str = Field(max_length=300)
    camera: str = Field(max_length=300)
    sound: str = Field(default="", max_length=200)
    acting: Acting
    techniques: list[str] = Field(min_length=2, max_length=8)  # named techniques, one line each
    feel: str = Field(
        max_length=200
    )  # Robert's one line: "low-contrast bg + high-contrast hero + 2-frame idle"
    for_fred: str = Field(max_length=400)  # what Fred and Pixie should take from it
    sources: list[str] = Field(min_length=1)  # the URLs or files the note was written from
