"""`studies/pixel-art/config.yaml`: the pixel-art study's thresholds."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import Field

from lens.schemas.common import Strict

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "studies" / "pixel-art"
MEDIA = ROOT / "data" / "study" / "pixel"


class Measure(Strict):
    max_scale: int = Field(ge=1)
    block_tolerance: int = Field(ge=0)
    block_min_share: float = Field(gt=0, le=1)
    max_palette: int = Field(ge=2)
    min_colour_share: float = Field(ge=0, lt=1)
    ramp_hue_window: float = Field(gt=0, le=180)
    ramp_min_chroma: float = Field(ge=0)
    ramp_min_len: int = Field(ge=2)
    outline_dark_delta: float = Field(gt=0, lt=1)
    outline_black_luma: float = Field(gt=0, lt=1)
    dither_min_share: float = Field(ge=0, lt=1)
    hold_min_frames: int = Field(ge=1)
    video_fps: float = Field(gt=0)
    video_width: int = Field(gt=0)
    change_threshold: float = Field(gt=0, lt=1)
    clip_seconds: float = Field(gt=0)


class StudyConfig(Strict):
    schema_version: int
    measure: Measure


def load(path: Path | None = None) -> StudyConfig:
    return StudyConfig.model_validate(yaml.safe_load((path or STUDY / "config.yaml").read_text()))
