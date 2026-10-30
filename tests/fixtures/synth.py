"""Synthetic videos with known answers (BUILD_PLAN 11.1). Generated on demand, never committed.

M1 fixtures cover normalization; M2 adds motion, transitions, captions and audio fixtures.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

# Known palette colours for the two-colour fixture (left/right halves, 50/50).
TWO_COLOURS = ("#e4572e", "#1e2a3b")


def _ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def cfr30_1080p(dest: Path, seconds: float = 4.0) -> Path:
    """1920x1080, 30 fps CFR, stereo 48 kHz tone. Proxy must downscale to 1280x720."""
    _ffmpeg(
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size=1920x1080:rate=30:duration={seconds}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:sample_rate=48000:duration={seconds}",
        "-ac",
        "2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(dest),
    )
    return dest


def vfr_from30(dest: Path, seconds: float = 4.0) -> Path:
    """640x360, every 5th frame dropped with VFR timestamps, no audio. Native fps is still 30."""
    _ffmpeg(
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size=640x360:rate=30:duration={seconds}",
        "-vf",
        "select='not(eq(mod(n\\,5)\\,4))'",
        "-fps_mode",
        "vfr",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-an",
        str(dest),
    )
    return dest


def two_colour_25(dest: Path, seconds: float = 3.0) -> Path:
    """640x360 at 25 fps: left half TWO_COLOURS[0], right half TWO_COLOURS[1], 48 kHz mono silence."""
    a, b = (c.replace("#", "0x") for c in TWO_COLOURS)
    _ffmpeg(
        "-f",
        "lavfi",
        "-i",
        f"color=c={a}:size=320x360:rate=25:duration={seconds}",
        "-f",
        "lavfi",
        "-i",
        f"color=c={b}:size=320x360:rate=25:duration={seconds}",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=mono:sample_rate=48000",
        "-filter_complex",
        "[0:v][1:v]hstack=inputs=2[v]",
        "-map",
        "[v]",
        "-map",
        "2:a",
        "-t",
        str(seconds),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        str(dest),
    )
    return dest


def audio_outlasts_video(dest: Path, seconds: float = 3.0, extra_audio: float = 0.3) -> Path:
    """640x360 at 30 fps for `seconds`; the audio runs `extra_audio` s longer, so the container is longer
    than the picture (seen in a real upload: the video stream ended 0.12 s before the audio)."""
    _ffmpeg(
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size=640x360:rate=30:duration={seconds}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:sample_rate=48000:duration={seconds + extra_audio}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        str(dest),
    )
    return dest


ALL = {
    "cfr30-1080p": cfr30_1080p,
    "vfr-from30": vfr_from30,
    "two-colour-25": two_colour_25,
    "audio-outlasts-video": audio_outlasts_video,
}
