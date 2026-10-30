"""Thin ffprobe/ffmpeg wrappers. All timing facts about a file come from here."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Snap measured rates to these when within 0.5% (NTSC rates included).
COMMON_FPS: tuple[float, ...] = (23.976, 24.0, 25.0, 29.97, 30.0, 48.0, 50.0, 59.94, 60.0, 120.0)


class MediaError(RuntimeError):
    pass


def run(cmd: Sequence[str]) -> str:
    proc = subprocess.run(list(cmd), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-8:])
        raise MediaError(f"{cmd[0]} failed ({proc.returncode}): {tail}")
    return proc.stdout


@dataclass(frozen=True)
class Probe:
    duration_s: float  # the container: the longest stream
    video_end_s: float  # where the picture ends (an audio tail can run past it)
    width: int
    height: int
    video_codec: str
    avg_fps: float
    has_audio: bool
    audio_codec: str | None
    audio_sample_rate: int | None
    audio_channels: int | None
    container: str


def _rate(value: str | None) -> float:
    if not value or value in {"0/0", "N/A"}:
        return 0.0
    num, _, den = value.partition("/")
    return float(num) / float(den or 1)


def probe(path: Path) -> Probe:
    out = json.loads(
        run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)])
    )
    streams = out.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise MediaError(f"{path}: no video stream")
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = out.get("format", {})
    duration = float(fmt.get("duration") or video.get("duration") or 0.0)
    video_end = duration
    if video.get("duration") not in (None, "N/A"):
        offset = float(video.get("start_time") or 0.0) - float(fmt.get("start_time") or 0.0)
        end = offset + float(video["duration"])
        video_end = min(duration, end) if duration else end
    return Probe(
        duration_s=duration,
        video_end_s=round(video_end, 6),
        width=int(video["width"]),
        height=int(video["height"]),
        video_codec=str(video.get("codec_name", "")),
        avg_fps=_rate(video.get("avg_frame_rate")),
        has_audio=audio is not None,
        audio_codec=str(audio["codec_name"]) if audio else None,
        audio_sample_rate=int(audio["sample_rate"]) if audio and audio.get("sample_rate") else None,
        audio_channels=int(audio["channels"]) if audio and audio.get("channels") else None,
        container=str(fmt.get("format_name", "")),
    )


def packet_times(path: Path, max_packets: int | None = 5000) -> list[float]:
    """Presentation times of video packets (no decoding); the first `max_packets`, or all if None."""
    limit = ["-read_intervals", f"%+#{max_packets}"] if max_packets else []
    raw = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "packet=pts_time",
            *limit,
            "-of",
            "csv=p=0",
            str(path),
        ]
    )
    times = sorted(float(t) for t in raw.split() if t and t != "N/A")
    return times


@dataclass(frozen=True)
class FrameRate:
    native_fps: float
    vfr: bool
    irregular_share: float


def native_frame_rate(times: Sequence[float], fallback: float = 0.0) -> FrameRate:
    """Native fps = 1 / mode of frame durations, snapped to a common rate (BUILD_PLAN 6.3).

    A file is VFR when more than 1% of frame durations differ from the mode by over 10%.
    """
    deltas = np.diff(np.asarray(times, dtype=float))
    deltas = deltas[deltas > 1e-6]
    if deltas.size == 0:
        if fallback <= 0:
            raise MediaError("cannot determine frame rate")
        return FrameRate(snap_fps(fallback), False, 0.0)
    binned = np.round(deltas, 4)
    counts = Counter(binned.tolist())
    mode_bin = max(counts.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    # Average the exact durations in the modal bin: rounding 1/30 to 0.0333 would read as 30.03 fps.
    mode = float(np.mean(deltas[binned == mode_bin]))
    irregular = float(np.mean(np.abs(deltas - mode) > 0.1 * mode))
    return FrameRate(snap_fps(1.0 / mode), irregular > 0.01, round(irregular, 4))


def snap_fps(fps: float) -> float:
    """Snap to the nearest common rate within 0.5% (nearest, so 30.0 never becomes 29.97)."""
    nearest = min(COMMON_FPS, key=lambda c: abs(fps - c) / c)
    if abs(fps - nearest) / nearest <= 0.005:
        return nearest
    return round(fps, 3)


def even(n: float) -> int:
    return max(2, round(n / 2.0) * 2)


def scaled_size(width: int, height: int, max_width: int) -> tuple[int, int]:
    """Fit within max_width keeping aspect; even dimensions for H.264."""
    if width <= max_width:
        return even(width), even(height)
    return even(max_width), even(height * max_width / width)


def iter_frames_rgb(path: Path, fps: float, width: int, height: int) -> Iterator[tuple[int, np.ndarray]]:
    """Decode `path` at `fps`, scaled to width x height, yielding (index, HxWx3 uint8)."""
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(path),
        "-vf",
        f"fps={fps},scale={width}:{height}:flags=area",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    ]
    frame_bytes = width * height * 3
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None
    index = 0
    finished = False
    try:
        while True:
            buf = proc.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            yield index, np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 3)
            index += 1
        finished = True
    finally:
        if not finished:  # the consumer stopped early: not an error
            proc.kill()
        proc.stdout.close()
        stderr = proc.stderr.read().decode() if proc.stderr else ""
        if proc.wait() != 0 and finished:
            raise MediaError(f"ffmpeg frame decode failed: {stderr[-500:]}")
