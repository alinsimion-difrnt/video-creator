"""F1 ingest and F6 edit: ffmpeg/ffprobe wrappers for presenter footage (local tools only)."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from lens.schemas.config import CreateFootage, FootageVoice
from lens.schemas.create import Crop, EdlSegment

HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}  # PQ (HDR10, Dolby Vision base) and HLG (iPhone default HDR)
# HDR -> SDR Rec.709 (zimg + tonemap; research §3.3). Hable keeps highlights; desat=0 keeps skin tones.
TONEMAP = (
    "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
    "zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
)


def probe(path: Path) -> dict[str, Any]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout  # fmt: skip
    data: dict[str, Any] = json.loads(out)
    return data


def video_stream(info: dict[str, Any]) -> dict[str, Any]:
    stream: dict[str, Any] = next(s for s in info["streams"] if s["codec_type"] == "video")
    return stream


def rotation(stream: dict[str, Any]) -> int:
    for side in stream.get("side_data_list", []):
        if "rotation" in side:
            return int(side["rotation"]) % 360
    return int(stream.get("tags", {}).get("rotate", 0)) % 360


def is_hdr(stream: dict[str, Any]) -> bool:
    return stream.get("color_transfer") in HDR_TRANSFERS


def is_vfr(stream: dict[str, Any]) -> bool:
    return stream.get("r_frame_rate") != stream.get("avg_frame_rate")


def display_size(stream: dict[str, Any]) -> tuple[int, int]:
    w, h = int(stream["width"]), int(stream["height"])
    return (h, w) if rotation(stream) in (90, 270) else (w, h)


def master_size(w: int, h: int, max_height: int) -> tuple[int, int]:
    """Scaled down so the shorter side fits `max_height` (4K keeps 2160), even sizes."""
    short = min(w, h)
    scale = min(1.0, max_height / short)
    return int(round(w * scale / 2) * 2), int(round(h * scale / 2) * 2)


def conform(raw: Path, master: Path, audio: Path, cfg: CreateFootage) -> dict[str, Any]:
    """A constant-fps, SDR Rec.709, short-GOP master with PCM audio, and a 16 kHz mono wav for STT."""
    info = probe(raw)
    v = video_stream(info)
    hdr = is_hdr(v)
    w, h = master_size(*display_size(v), cfg.max_height)
    chain = [TONEMAP] if hdr else []
    chain += [f"fps={cfg.fps}", f"scale={w}:{h}:flags=lanczos", "setsar=1", "format=yuv420p"]
    master.parent.mkdir(parents=True, exist_ok=True)
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-vf", ",".join(chain), "-fps_mode", "cfr",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(cfg.master_crf), "-g", str(cfg.gop),
           "-keyint_min", str(cfg.gop), "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
           "-color_trc", "bt709", "-colorspace", "bt709"]  # fmt: skip
    cmd += ["-c:a", "pcm_s16le", "-ar", "48000"] if has_audio else ["-an"]
    subprocess.run([*cmd, str(master)], check=True)
    if not has_audio:
        raise ValueError(f"{raw.name} has no audio track")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(master), "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "pcm_s16le", str(audio)], check=True,
    )  # fmt: skip
    mv = video_stream(probe(master))
    frames = int(mv.get("nb_frames") or 0) or count_frames(master)
    return {
        "width": w, "height": h, "frames": frames, "duration_s": round(frames / cfg.fps, 3),
        "source_fps": "vfr" if is_vfr(v) else str(v.get("r_frame_rate")), "hdr": hdr,
    }  # fmt: skip


def count_frames(path: Path) -> int:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
         "stream=nb_read_packets", "-of", "csv=p=0", str(path)], check=True, capture_output=True, text=True,
    ).stdout  # fmt: skip
    return int(out.strip())


def render_edit(
    segments: list[EdlSegment],
    masters: dict[str, Path],
    fps: int,
    crossfade_ms: float,
    out: Path,
    size: tuple[int, int],
    crops: list[Crop] | None = None,
) -> Path:
    """The edited presenter video at `size`: every kept segment frame-exact, cut to its crop (F5 framing) or,
    without one, scaled to cover the frame and centre-cropped; short audio fades at each cut."""
    w, h = size
    fit = f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h},setsar=1"
    # one input per segment, seeked to it: one decoded master split 40 ways made ffmpeg queue 4K frames for
    # the later segments until it was killed (take 1's TikTok cut, 15 GB)
    inputs: list[str] = []
    for s in segments:
        inputs += ["-ss", f"{s.src_in / fps:.6f}", "-i", str(masters[s.take])]
    fade = crossfade_ms / 1000
    parts = []
    for n, s in enumerate(segments):
        k = n
        dur = (s.src_out - s.src_in) / fps
        shape = fit
        if crops is not None:
            c = crops[n]
            shape = f"crop={c.w}:{c.h}:{c.x}:{c.y},scale={w}:{h}:flags=lanczos,setsar=1"
        parts.append(f"[{k}:v]trim=end_frame={s.src_out - s.src_in},setpts=PTS-STARTPTS,{shape}[v{n}]")
        prev_joined = n > 0 and segments[n - 1].take == s.take and segments[n - 1].src_out == s.src_in
        next_joined = (
            n + 1 < len(segments) and segments[n + 1].take == s.take and segments[n + 1].src_in == s.src_out
        )
        afade = ""  # fades only at real cuts: a punch-in split keeps the sound continuous
        if fade and not prev_joined:
            afade += f",afade=t=in:d={fade:g}"
        if fade and not next_joined:
            afade += f",afade=t=out:st={max(0.0, dur - fade):.6f}:d={fade:g}"
        parts.append(
            f"[{k}:a]atrim=end={dur:.6f},"
            f"asetpts=PTS-STARTPTS,apad=whole_dur={dur:.6f}{afade}[a{n}]"  # audio as long as the video
        )
    joined = "".join(f"[v{n}][a{n}]" for n in range(len(segments)))
    graph = ";".join(parts) + f";{joined}concat=n={len(segments)}:v=1:a=1[v][a]"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
         "-r", str(fps), "-fps_mode", "cfr", "-c:v", "libx264", "-crf", "16", "-g", str(fps),
         "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True,
    )  # fmt: skip
    return out


def loudness(path: Path) -> dict[str, float]:
    """Integrated loudness (LUFS), true peak (dBTP) and loudness range of a file's audio (ffmpeg ebur128)."""
    res = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
         "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    summary = res.stderr[res.stderr.rfind("Summary:") :]

    def grab(label: str) -> float:
        m = re.search(label + r":\s+(-?[\d.]+|-inf)", summary)
        return float(m.group(1)) if m and m.group(1) != "-inf" else float("-inf")

    return {"lufs": grab("I"), "true_peak": grab("Peak"), "lra": grab("LRA")}


def finish_voice(video: Path, out: Path, voice: FootageVoice, lufs: float) -> Path:
    """The edited video with its voice cleaned and levelled: high-pass, light denoise, compression, then a
    two-pass loudnorm to `lufs` (linear, so the dynamics the compressor left are kept) and a true-peak
    limiter. Video is copied."""
    pre = f"highpass=f={voice.highpass_hz:g},afftdn=nf={voice.denoise_nf_db:g},acompressor={voice.compressor}"
    target = f"I={lufs:g}:TP={voice.true_peak_db:g}:LRA={voice.lra:g}"
    probe_run = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(video),
         "-af", f"{pre},loudnorm={target}:print_format=json",
         "-f", "null", "-"], capture_output=True, text=True, check=True,
    )  # fmt: skip
    m = json.loads(probe_run.stderr[probe_run.stderr.rfind("{") :])
    second = (
        f"{pre},loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
        f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
        # linear loudnorm can still overshoot: a 4x oversampled limiter holds the true peak (the AAC encode
        # adds a little, hence the margin in config)
        f",aresample=192000,alimiter=limit={10 ** (voice.true_peak_db / 20):.4f}"
        ":level=false:attack=1:release=50"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(video), "-map", "0:v", "-map", "0:a", "-c:v", "copy",
         "-af", second + ",aresample=48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
         str(out)],
        check=True,
    )  # fmt: skip
    return out
