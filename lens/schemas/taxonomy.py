"""`taxonomy/v1.yaml`: controlled vocabularies used by annotators and stats."""

from __future__ import annotations

from pydantic import Field, model_validator

from lens.schemas.common import Slug, Strict

Enum = list[Slug]


class Taxonomy(Strict):
    format: Enum
    shot_type: Enum
    composition: Enum
    transition: Enum
    element_role: Enum
    change_type: Enum
    easing_class: Enum
    camera_move: Enum
    sfx: Enum
    music_event: Enum
    depth_cue: Enum
    hook_technique: Enum
    beat: Enum
    patterns: Enum
    scene_archetype: Enum = Field(default_factory=list)  # BUILD_PLAN 8.5; A3 sorts shots into these
    pattern_aliases: dict[Slug, list[str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _consistent(self) -> Taxonomy:
        for name in type(self).model_fields:
            value = getattr(self, name)
            if isinstance(value, list) and len(set(value)) != len(value):
                raise ValueError(f"{name}: duplicate values")
        unknown = set(self.pattern_aliases) - set(self.patterns)
        if unknown:
            raise ValueError(f"pattern_aliases for unknown patterns: {sorted(unknown)}")
        return self
