"""Per-video outputs of S2 (normalize): `videos/<id>/meta.json` and `videos/<id>/palette.json`."""

from __future__ import annotations

from pydantic import Field

from lens.schemas.common import Provenance, Sha256, Slug, Strict

HexColor = str


class OriginalInfo(Strict):
    sha256: Sha256
    bytes: int = Field(ge=0)
    container: str
    video_codec: str
    duration_s: float = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    native_fps: float = Field(gt=0)
    vfr: bool
    irregular_frame_share: float = Field(ge=0, le=1)
    has_audio: bool
    audio_codec: str | None
    audio_sample_rate: int | None
    audio_channels: int | None


class Window(Strict):
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)
    capped: bool  # true when analysis.max_minutes cut the video short


class ProxyInfo(Strict):
    sha256: Sha256
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps: float = Field(gt=0)
    duration_s: float = Field(gt=0)
    frames: int = Field(gt=0)
    has_audio: bool


class AudioInfo(Strict):
    sample_rate: int = Field(gt=0)
    channels: int = Field(gt=0)
    duration_s: float = Field(gt=0)


class BaseFrames(Strict):
    fps: float = Field(gt=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    count: int = Field(ge=1)
    naming: str = "t{ms:08d}.jpg"


class VideoMeta(Strict):
    provenance: Provenance
    video: Slug
    original: OriginalInfo
    window: Window
    proxy: ProxyInfo
    audio: AudioInfo | None
    base_frames: BaseFrames
    phash: list[str] = Field(min_length=1)  # 64-bit dHash per sampled frame, hex
    possible_duplicates: list[Slug] = Field(default_factory=list)


class Swatch(Strict):
    hex: HexColor = Field(pattern=r"^#[0-9a-f]{6}$")
    share: float = Field(ge=0, le=1)


class Palette(Strict):
    provenance: Provenance
    video: Slug
    method: str  # how the palette was computed
    video_palette: list[Swatch] = Field(min_length=1)
    # Per-shot palettes are added by S3 once shots exist (M2).
