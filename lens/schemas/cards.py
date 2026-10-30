"""`corpus/patterns/<pid>.json` (A3, BUILD_PLAN 8.3): one pattern card, written by the pattern-card
writer from `lens status --card <pid>`.

Claude writes the words: what the pattern is, when to use it, how to build it. Every number on the card
is the `numbers` block, copied verbatim from the S9 stats (validation checks it), so prose never
carries a number of its own. `lens cards render` turns the JSON into the .md next to it.
"""

from __future__ import annotations

from pydantic import Field

from lens.schemas.common import Provenance, Slug, Strict
from lens.schemas.corpus import PatternExample, PatternStats
from lens.schemas.scenes import ArchetypeStats, SceneExample


class Build(Strict):
    gsap: str = Field(min_length=1)  # HyperFrames/GSAP phrasing first
    remotion: str = Field(min_length=1)


class PatternCard(Strict):
    provenance: Provenance
    id: Slug
    name: str = Field(min_length=2, max_length=60)  # plain words, title case
    summary: str = Field(min_length=10, max_length=300)  # one or two sentences anyone can follow
    when_to_use: list[str] = Field(min_length=1, max_length=4)
    avoid_when: list[str] = Field(default_factory=list, max_length=3)
    steps: list[str] = Field(min_length=2, max_length=7)  # how to build it, in order, no numbers
    build: Build
    sound: str  # how sound is used with it (from the SFX mix and offsets), or "no typical sound"
    why_premium: str = Field(min_length=10)
    numbers: PatternStats  # verbatim from corpus/stats/patterns.json
    examples: list[PatternExample]  # a subset of numbers.examples
    caveats: list[str] = Field(default_factory=list, max_length=3)  # e.g. few videos, few measurements


class Slot(Strict):
    name: Slug  # e.g. headline, metric, items, logo
    what: str = Field(min_length=3)  # what goes in it, plain words
    required: bool = True


class ArchetypeCard(Strict):
    """`corpus/archetypes/<aid>.json`: one scene archetype, a template a builder fills with content."""

    provenance: Provenance
    id: Slug
    name: str = Field(min_length=2, max_length=60)
    summary: str = Field(min_length=10, max_length=300)
    when_to_use: list[str] = Field(min_length=1, max_length=4)
    slots: list[Slot] = Field(min_length=1, max_length=8)  # the content the scene takes
    steps: list[str] = Field(min_length=2, max_length=8)  # the scene's beats in order, no numbers
    patterns: list[Slug]  # pattern ids it uses, from numbers.pattern_mix
    build: Build
    sound: str
    numbers: ArchetypeStats  # verbatim from corpus/stats/scenes.json
    examples: list[SceneExample]
    caveats: list[str] = Field(default_factory=list, max_length=3)
