"""S2 normalize: meta.json, proxy at native fps, audio.wav, 2 fps base frames, palette (BUILD_PLAN 6.3)."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from PIL import Image

from lens import __version__
from lens.frames.palette import MERGE_DISTANCE, sample_pixels
from lens.frames.palette import palette as compute_palette
from lens.frames.phash import dhash, sequence_distance
from lens.hashing import cache_key, sha256_file
from lens.ingest import read_marker, write_marker
from lens.media import (
    MediaError,
    iter_frames_rgb,
    native_frame_rate,
    packet_times,
    probe,
    run,
    scaled_size,
)
from lens.schemas import LensConfig, SourceEntry
from lens.schemas.common import Annotator, Provenance
from lens.schemas.video import (
    AudioInfo,
    BaseFrames,
    OriginalInfo,
    Palette,
    ProxyInfo,
    Swatch,
    VideoMeta,
    Window,
)

STAGE = "s2_normalize"


class NormalizeError(RuntimeError):
    pass


@dataclass(frozen=True)
class NormalizeResult:
    video: str
    status: str  # "normalized" | "cached" | "skipped"
    detail: str = ""


def frame_name(index: int, fps: float) -> str:
    return f"t{round(index * 1000 / fps):08d}.jpg"


def analysis_window(entry: SourceEntry, duration_s: float, cfg: LensConfig) -> Window:
    cap = cfg.analysis.max_minutes * 60.0
    if entry.segment is not None:
        start, end = entry.segment.start, min(entry.segment.end, duration_s)
    else:
        start, end = 0.0, duration_s
    capped = end - start > cap
    if capped:
        end = start + cap
    if end <= start:
        raise NormalizeError(f"{entry.id}: empty analysis window ({start}-{end}s of {duration_s}s)")
    return Window(start_s=round(start, 3), end_s=round(end, 3), capped=capped)


def _encode_proxy(
    original: Path, dest: Path, window: Window, fps: float, size: tuple[int, int], crf: int, has_audio: bool
) -> None:
    w, h = size
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-ss",
        f"{window.start_s}",
        "-t",
        f"{window.end_s - window.start_s}",
        "-i",
        str(original),
        "-map",
        "0:v:0",
    ]
    if has_audio:
        cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "192k"]
    cmd += [
        "-vf",
        f"fps={fps},scale={w}:{h}:flags=lanczos,setsar=1",
        "-fps_mode",
        "cfr",
        "-r",
        f"{fps}",
        # The fps filter can flush one extra boundary frame; cap at exactly window x fps.
        "-frames:v",
        str(round((window.end_s - window.start_s) * fps)),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    run(cmd)


def _extract_audio(original: Path, dest: Path, window: Window, sample_rate: int) -> None:
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-ss",
            f"{window.start_s}",
            "-t",
            f"{window.end_s - window.start_s}",
            "-i",
            str(original),
            "-vn",
            "-map",
            "0:a:0",
            "-ar",
            str(sample_rate),
            "-c:a",
            "pcm_s16le",
            str(dest),
        ]
    )


def _verify_proxy(proxy: Path, window: Window, fps: float, cfg: LensConfig) -> tuple[float, int]:
    """Check the proxy is CFR at `fps` and covers the window; returns (video duration, frame count).

    Durations come from the video packets: the container duration includes audio priming/padding.
    """
    times = packet_times(proxy, max_packets=None)
    rate = native_frame_rate(times, probe(proxy).avg_fps)
    if rate.vfr or abs(rate.native_fps - fps) / fps > 0.005:
        raise NormalizeError(f"proxy is not CFR at {fps} fps (got {rate.native_fps}, vfr={rate.vfr})")
    frames = len(times)
    duration = frames / fps
    expected = window.end_s - window.start_s
    tolerance = max(cfg.analysis.proxy_duration_tolerance_s, 2.0 / fps)
    if abs(duration - expected) > tolerance:
        raise NormalizeError(
            f"proxy video duration {duration:.3f}s differs from window {expected:.3f}s "
            f"by more than {tolerance:.3f}s"
        )
    return duration, frames


def _base_frames(
    proxy: Path, out_dir: Path, cfg: LensConfig, proxy_size: tuple[int, int], rng: np.random.Generator
) -> tuple[BaseFrames, list[np.ndarray], list[np.ndarray]]:
    """Write timestamped JPEGs; return the frame spec, palette pixel samples and phash frames."""
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    w, h = scaled_size(*proxy_size, cfg.analysis.base_frame_width)
    fps = cfg.analysis.base_fps
    samples: list[np.ndarray] = []
    frames: list[np.ndarray] = []
    count = 0
    for index, frame in iter_frames_rgb(proxy, fps, w, h):
        Image.fromarray(frame).save(out_dir / frame_name(index, fps), quality=cfg.analysis.jpeg_quality)
        samples.append(sample_pixels(frame, cfg.analysis.palette_pixels_per_frame, rng))
        frames.append(frame)
        count += 1
    if count == 0:
        raise NormalizeError("no base frames decoded")
    step = max(1, count // cfg.analysis.phash_frames)
    return (
        BaseFrames(fps=fps, width=w, height=h, count=count),
        samples,
        frames[::step][: cfg.analysis.phash_frames],
    )


def _duplicates(video: str, hashes: list[str], root: Path, cfg: LensConfig) -> list[str]:
    found = []
    for meta_path in sorted((root / "videos").glob("*/meta.json")):
        other = meta_path.parent.name
        if other == video:
            continue
        other_hashes = json.loads(meta_path.read_text(encoding="utf-8")).get("phash", [])
        if sequence_distance(hashes, other_hashes) <= cfg.analysis.duplicate_max_distance:
            found.append(other)
    return found


def _write_json(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(path)


def normalize_one(entry: SourceEntry, root: Path, cfg: LensConfig, force: bool = False) -> NormalizeResult:
    ingest = read_marker(root, entry.id)
    if ingest is None:
        return NormalizeResult(entry.id, "skipped", "not ingested")
    key = cache_key(
        {
            "stage": STAGE,
            "tool": __version__,
            "original": ingest["sha256"],
            "segment": entry.segment.model_dump() if entry.segment else None,
            "analysis": cfg.analysis.model_dump(),
        }
    )
    media = root / "data" / "media" / entry.id
    meta_path = root / "videos" / entry.id / "meta.json"
    marker = read_marker(root, entry.id, STAGE)
    if not force and marker and marker.get("cache_key") == key and meta_path.exists():
        return NormalizeResult(entry.id, "cached")

    original = root / str(ingest["path"])
    if not original.exists():
        raise NormalizeError(f"{entry.id}: original missing at {original}; re-run `lens ingest`")
    if sha256_file(original) != ingest["sha256"]:
        raise NormalizeError(f"{entry.id}: original changed since ingest; re-run `lens ingest --force`")

    src = probe(original)
    rate = native_frame_rate(packet_times(original), src.avg_fps)
    window = analysis_window(entry, src.video_end_s, cfg)
    size = scaled_size(src.width, src.height, cfg.analysis.proxy_max_width)
    has_audio = src.has_audio and entry.media.value != "frames_only"

    media.mkdir(parents=True, exist_ok=True)
    proxy = media / "proxy.mp4"
    _encode_proxy(original, proxy, window, rate.native_fps, size, cfg.analysis.proxy_crf, has_audio)
    try:
        proxy_duration, proxy_frames = _verify_proxy(proxy, window, rate.native_fps, cfg)
    except (NormalizeError, MediaError) as exc:
        proxy.unlink(missing_ok=True)
        raise NormalizeError(f"{entry.id}: proxy verification failed: {exc}") from exc

    audio_info = None
    wav = media / "audio.wav"
    if has_audio:
        _extract_audio(original, wav, window, cfg.analysis.audio_sample_rate)
        a = probe_audio(wav)
        audio_info = AudioInfo(sample_rate=a[0], channels=a[1], duration_s=round(a[2], 3))
    else:
        wav.unlink(missing_ok=True)

    rng = np.random.default_rng(0)
    base, samples, hash_frames = _base_frames(
        proxy, root / "data" / "frames" / entry.id / "base", cfg, size, rng
    )
    hashes = [dhash(f) for f in hash_frames]
    swatches = compute_palette(np.concatenate(samples), cfg.analysis.palette_colors)

    now = datetime.now(UTC)
    prov = Provenance(
        tool_version=__version__, stage=STAGE, annotator=Annotator.CODE, input_hash=key, created_at=now
    )
    meta = VideoMeta(
        provenance=prov,
        video=entry.id,
        original=OriginalInfo(
            sha256=str(ingest["sha256"]),
            bytes=original.stat().st_size,
            container=src.container,
            video_codec=src.video_codec,
            duration_s=round(src.duration_s, 3),
            width=src.width,
            height=src.height,
            native_fps=rate.native_fps,
            vfr=rate.vfr,
            irregular_frame_share=rate.irregular_share,
            has_audio=src.has_audio,
            audio_codec=src.audio_codec,
            audio_sample_rate=src.audio_sample_rate,
            audio_channels=src.audio_channels,
        ),
        window=window,
        proxy=ProxyInfo(
            sha256=sha256_file(proxy),
            width=size[0],
            height=size[1],
            fps=rate.native_fps,
            duration_s=round(proxy_duration, 3),
            frames=proxy_frames,
            has_audio=has_audio,
        ),
        audio=audio_info,
        base_frames=base,
        phash=hashes,
        possible_duplicates=_duplicates(entry.id, hashes, root, cfg),
    )
    pal = Palette(
        provenance=prov,
        video=entry.id,
        method=(
            f"k-means++ (k={cfg.analysis.palette_colors}, RGB, merged < {MERGE_DISTANCE:g}) over base frames"
        ),
        video_palette=[Swatch(hex=h, share=s) for h, s in swatches],
    )
    _write_json(meta_path, meta.model_dump_json(indent=2) + "\n")
    _write_json(root / "videos" / entry.id / "palette.json", pal.model_dump_json(indent=2) + "\n")
    write_marker(
        root, entry.id, STAGE, {"cache_key": key, "tool_version": __version__, "created_at": now.isoformat()}
    )
    return NormalizeResult(entry.id, "normalized")


def probe_audio(path: Path) -> tuple[int, int, float]:
    out = json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=sample_rate,channels:format=duration",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    stream = out["streams"][0]
    return int(stream["sample_rate"]), int(stream["channels"]), float(out["format"]["duration"])
