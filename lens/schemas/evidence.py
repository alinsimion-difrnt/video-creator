"""`candidates.json`: the candidate boxes an event annotator may refer to (by id only)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from lens.schemas.common import Provenance, Slug, Strict


class BoxOut(Strict):
    id: str = Field(pattern=r"^b\d{2}$")
    source: Literal["diff", "ocr", "union"]
    xyxy: tuple[int, int, int, int]  # proxy pixels, x1/y1 exclusive
    norm: tuple[float, float, float, float]  # the same in 0..1
    changed_share: float = Field(ge=0, le=1)  # share of the box that changed start -> end
    text: str | None = None  # OCR line text (source "ocr")

    @model_validator(mode="after")
    def _ordered(self) -> BoxOut:
        x0, y0, x1, y1 = self.xyxy
        if x1 <= x0 or y1 <= y0:
            raise ValueError(f"{self.id}: empty box {self.xyxy}")
        return self


class CandidatesFile(Strict):
    provenance: Provenance
    video: Slug
    event: str = Field(pattern=r"^e\d{3,}$")
    frame_size: tuple[int, int]
    start_frame: int = Field(ge=0)  # burst start (diff baseline)
    end_frame: int = Field(ge=0)  # settled end frame (the marked image)
    boxes: list[BoxOut] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique(self) -> CandidatesFile:
        ids = [b.id for b in self.boxes]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate box ids")
        return self
