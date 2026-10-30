"""`sources/sources.yaml`: what goes into the corpus."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, RootModel, model_validator

from lens.schemas.common import Slug, Strict


class Tier(StrEnum):
    REFERENCE = "reference"
    AVERAGE = "average"
    OWN = "own"
    COMPETITOR = "competitor"


class Media(StrEnum):
    FULL = "full"
    FRAMES_ONLY = "frames_only"
    AUDIO_ONLY = "audio_only"


class Status(StrEnum):
    READY = "ready"
    DRAFT = "draft"  # e.g. URL still to be supplied; skipped by the pipeline


class Segment(Strict):
    start: float = Field(ge=0)
    end: float = Field(gt=0)

    @model_validator(mode="after")
    def _ordered(self) -> Segment:
        if self.end <= self.start:
            raise ValueError("segment.end must be after segment.start")
        return self


URL_PATTERN = r"^(https://|r2://inbox/|file://)\S+$"


class SourceEntry(Strict):
    id: Slug
    url: str | None = Field(default=None, pattern=URL_PATTERN)
    # Public page a local machine fetches into `url` (YouTube/X/LinkedIn block cloud runners);
    # used by scripts/fetch_batch.py.
    page_url: str | None = Field(default=None, pattern=r"^https://\S+$")
    brand: str
    title: str
    format: str  # checked against taxonomy.format by `lens validate`
    tier: Tier
    why: str
    tags: list[Slug] = Field(default_factory=list)
    segment: Segment | None = None
    media: Media = Media.FULL
    refetchable: bool = True
    status: Status = Status.READY
    transcript_hint: str | None = None

    @model_validator(mode="after")
    def _ready_needs_url(self) -> SourceEntry:
        if self.status is Status.READY and self.url is None:
            raise ValueError(f"{self.id}: status 'ready' needs a url (use status: draft until it has one)")
        return self


class SourcesFile(RootModel[list[SourceEntry]]):
    @model_validator(mode="after")
    def _unique_ids(self) -> SourcesFile:
        seen: set[str] = set()
        for entry in self.root:
            key = entry.id.lower()
            if key in seen:
                raise ValueError(f"duplicate source id {entry.id!r}")
            seen.add(key)
        return self
