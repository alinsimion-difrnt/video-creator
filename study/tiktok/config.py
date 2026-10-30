"""`studies/tiktok/config.yaml`: the TikTok study's thresholds (the study code reads numbers from here)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import Field

from lens.schemas.common import Strict

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "studies" / "tiktok"
MEDIA = ROOT / "data" / "study" / "tiktok"


class Select(Strict):
    total: int = Field(gt=0)
    per_topic: int = Field(gt=0)
    max_per_creator: int = Field(gt=0)
    min_seconds: float = Field(gt=0)
    max_seconds: float = Field(gt=0)
    max_age_days: int = Field(gt=0)
    min_likes: int = Field(ge=0)
    exclude: str
    topic_keywords: dict[str, str]


class Measure(Strict):
    scan_fps: float = Field(gt=0)
    sample_fps: float = Field(gt=0)
    sample_width: int = Field(gt=0)
    ocr_min_score: float = Field(ge=0, le=1)
    ocr_min_chars: int = Field(ge=1)
    caption_min_height: float = Field(gt=0, lt=1)
    face_min_height: float = Field(gt=0, lt=1)
    face_model: str
    face_min_score: float = Field(gt=0, lt=1)
    hook_window_s: float = Field(gt=0)
    end_slack_s: float = Field(ge=0)
    punch_min_step: float = Field(gt=0)
    punch_min_total: float = Field(gt=0)
    punch_max_gap_frames: int = Field(ge=0)
    music_guard_s: float = Field(ge=0)
    music_min_gap_s: float = Field(gt=0)
    music_bed_floor_db: float
    safe_core: tuple[float, float, float, float]
    thirds: tuple[float, float]


class Notes(Strict):
    videos_per_agent: int = Field(gt=0)
    sheet_frames: int = Field(gt=0)
    hook_frames: int = Field(gt=0)


class StudyConfig(Strict):
    schema_version: int
    select: Select
    measure: Measure
    notes: Notes


def load(path: Path | None = None) -> StudyConfig:
    return StudyConfig.model_validate(yaml.safe_load((path or STUDY / "config.yaml").read_text()))
