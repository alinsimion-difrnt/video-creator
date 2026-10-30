"""Shared building blocks for every output JSON."""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

SCHEMA_VERSION = 1

_SLUG = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")


def _check_slug(value: str) -> str:
    if not _SLUG.fullmatch(value):
        raise ValueError(f"{value!r} is not a lowercase slug (a-z, 0-9, '-' or '_')")
    return value


Slug = Annotated[str, AfterValidator(_check_slug)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Annotator(StrEnum):
    CODE = "code"
    CLAUDE_CODE = "claude-code"
    HUMAN = "human"


class ValueSource(StrEnum):
    MEASURED = "measured"
    MODEL_ESTIMATE = "model_estimate"
    HUMAN = "human"


class Provenance(Strict):
    """Carried by every output JSON (BUILD_PLAN section 2.7)."""

    schema_version: int = SCHEMA_VERSION
    tool_version: str
    stage: Slug
    annotator: Annotator
    skill: str | None = Field(default=None, pattern=r"^[a-z0-9-]+@[0-9a-f]{8,64}$")
    model: str | None = None
    input_hash: Sha256
    created_at: datetime
