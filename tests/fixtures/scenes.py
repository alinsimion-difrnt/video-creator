"""Frame-exact synthetic explainers with known answers (BUILD_PLAN 11.1).

A fixture is a list of scenes joined by transitions. Each scene has a background and animated
rectangles; every motion's start/end frame, easing and the transitions' frames are known, and
`render()` returns them as ground truth alongside the encoded MP4.
"""

from __future__ import annotations

import math
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

Ease = Callable[[float], float]


def linear(t: float) -> float:
    return t


def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def spring(zeta: float = 0.5, omega: float = 12.0, duration_s: float = 1.0) -> Ease:
    """Underdamped spring from 0 to 1 over a normalised time t in [0, 1] (mass = 1)."""

    def f(t: float) -> float:
        x = t * duration_s
        wd = omega * math.sqrt(1 - zeta**2)
        return 1 - math.exp(-zeta * omega * x) * (math.cos(wd * x) + zeta * omega / wd * math.sin(wd * x))

    f.__name__ = "spring"
    return f


@dataclass
class Motion:
    """Move a box from `start_xy` to `end_xy` (pixels, top-left) between frames [f0, f1]."""

    f0: int
    f1: int
    start_xy: tuple[int, int]
    end_xy: tuple[int, int]
    ease: Ease = ease_out_cubic
    fade_in: bool = False


@dataclass
class Box:
    size: tuple[int, int]
    color: tuple[int, int, int]
    motion: Motion | None = None
    at: tuple[int, int] = (0, 0)  # static position when there is no motion
    appear: int = 0  # frame (within the scene) the box appears


@dataclass
class Scene:
    frames: int
    background: tuple[int, int, int]
    boxes: list[Box] = field(default_factory=list)


@dataclass
class Transition:
    kind: str  # hard_cut | crossfade | push | zoom_through
    frames: int = 0  # 0 for hard cuts


W, H = 640, 360


def _draw_scene(scene: Scene, f: int) -> np.ndarray:
    img = np.empty((H, W, 3), dtype=np.float32)
    img[:] = scene.background
    for box in scene.boxes:
        if f < box.appear:
            continue
        w, h = box.size
        alpha = 1.0
        if box.motion is None:
            x, y = box.at
        else:
            m = box.motion
            t = 0.0 if f <= m.f0 else 1.0 if f >= m.f1 else (f - m.f0) / (m.f1 - m.f0)
            p = m.ease(t)
            x = m.start_xy[0] + (m.end_xy[0] - m.start_xy[0]) * p
            y = m.start_xy[1] + (m.end_xy[1] - m.start_xy[1]) * p
            if m.fade_in:
                alpha = min(1.0, max(0.0, t))
        x0, y0 = round(x), round(y)
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
        if xa < xb and ya < yb:
            region = img[ya:yb, xa:xb]
            region[:] = region * (1 - alpha) + np.asarray(box.color, dtype=np.float32) * alpha
    return img


def _zoom(img: np.ndarray, scale: float) -> np.ndarray:
    """Centre zoom by `scale` (> 1 zooms in), nearest-neighbour, same size."""
    ys = ((np.arange(H) - H / 2) / scale + H / 2).clip(0, H - 1).astype(int)
    xs = ((np.arange(W) - W / 2) / scale + W / 2).clip(0, W - 1).astype(int)
    return img[ys][:, xs]


def frames_of(scenes: list[Scene], transitions: list[Transition]) -> tuple[list[np.ndarray], dict]:
    """Render all frames; returns (frames, truth). Transitions overlap the end of the outgoing scene."""
    assert len(transitions) == len(scenes) - 1
    out: list[np.ndarray] = []
    truth: dict = {"scene_starts": [], "transitions": [], "motions": []}
    for i, scene in enumerate(scenes):
        incoming = transitions[i - 1] if i > 0 else None
        skip = incoming.frames if incoming else 0  # frames already shown inside the transition
        start = len(out) - skip
        truth["scene_starts"].append(start)
        for box in scene.boxes:
            if box.motion:
                truth["motions"].append(
                    {
                        "scene": i,
                        "f0": start + box.motion.f0,
                        "f1": start + box.motion.f1,
                        "ease": box.motion.ease.__name__
                        if hasattr(box.motion.ease, "__name__")
                        else "custom",
                    }
                )
        outgoing = transitions[i] if i < len(transitions) else None
        own_frames = scene.frames - (outgoing.frames if outgoing else 0)
        for f in range(skip, own_frames):
            out.append(_draw_scene(scene, f))
        if outgoing is None:
            continue
        nxt = scenes[i + 1]
        t0 = len(out)
        truth["transitions"].append({"kind": outgoing.kind, "start": t0, "frames": outgoing.frames})
        for k in range(outgoing.frames):
            a = _draw_scene(scene, own_frames + k)
            b = _draw_scene(nxt, k)
            p = (k + 1) / (outgoing.frames + 1)
            if outgoing.kind == "crossfade":
                frame = a * (1 - p) + b * p
            elif outgoing.kind == "push":
                shift = round(W * p)
                frame = np.concatenate([a[:, shift:], b[:, :shift]], axis=1) if shift else a
            elif outgoing.kind == "zoom_through":
                frame = _zoom(a, 1 + 3 * p) if p < 0.5 else _zoom(b, 1 + 3 * (1 - p))
            else:
                raise ValueError(outgoing.kind)
            out.append(frame)
    truth["frames"] = len(out)
    return out, truth


def encode(frames: list[np.ndarray], fps: float, dest: Path, audio: Path | None = None) -> Path:
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{W}x{H}",
        "-r",
        str(fps),
        "-i",
        "-",
    ]
    if audio is not None:
        cmd += ["-i", str(audio), "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(fps), str(dest)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    for frame in frames:
        proc.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(proc.stderr.read().decode() if proc.stderr else "ffmpeg failed")
    return dest


# ---------------------------------------------------------------------------------------------
# Canonical fixture: four scenes, three transition types, three easings, a dead hold.


def explainer(fps: float = 30.0) -> tuple[list[Scene], list[Transition]]:
    s = lambda sec: round(sec * fps)  # noqa: E731
    navy, cream, orange, white = (30, 42, 59), (245, 247, 250), (228, 87, 46), (255, 255, 255)
    sky = (205, 222, 250)
    scenes = [
        # Scene 0: a box slides in with easeOutCubic (0.5 s -> 1.2 s).
        Scene(
            s(2.0),
            cream,
            [Box((120, 80), orange, Motion(s(0.5), s(1.2), (-130, 140), (260, 140), ease_out_cubic))],
        ),
        # Scene 1: a spring with overshoot, then a linear move.
        Scene(
            s(2.5),
            navy,
            [
                Box(
                    (100, 100), orange, Motion(s(0.3), s(1.3), (60, 130), (300, 130), spring(0.45, 14.0, 1.0))
                ),
                Box((80, 40), white, Motion(s(1.5), s(2.0), (60, 280), (480, 280), linear)),
            ],
        ),
        # Scene 2: DEAD HOLD. An empty card sits from the end of the crossfade (0.4 s) until its
        # content fades in at 1.6 s: a 1.2 s hold on an empty placeholder (handoff section 6).
        Scene(
            s(2.8),
            cream,
            [
                Box((300, 160), white, at=(170, 100)),
                Box((200, 40), navy, Motion(s(1.6), s(2.0), (220, 160), (220, 160), linear, fade_in=True)),
            ],
        ),
        # Scene 3: a box drops in (easeOutCubic) next to a static label; ends with a zoom-through.
        Scene(
            s(2.0),
            sky,
            [
                Box((220, 50), navy, at=(60, 60)),
                Box((140, 90), orange, Motion(s(0.5), s(1.0), (420, -100), (420, 200), ease_out_cubic)),
            ],
        ),
        # Scene 4: static logo close.
        Scene(s(1.5), navy, [Box((160, 60), orange, at=(240, 150))]),
    ]
    transitions = [
        Transition("hard_cut", 0),
        Transition("crossfade", s(0.4)),
        Transition("push", s(0.3)),
        Transition("zoom_through", s(0.3)),
    ]
    return scenes, transitions


# Dead hold in scene 2, relative to the scene start: from the end of the crossfade to the reveal.
EXPLAINER_DEAD_HOLD = {"scene": 2, "start_s": 0.4, "end_s": 1.6}


def explainer_with_sound(dest_dir: Path, fps: float = 30.0, voice: bool = True) -> tuple[Path, dict]:
    """The canonical explainer muxed with its soundtrack (and optionally a narration).

    Returns (mp4 path, truth) where truth adds the SFX list and narration words to the scene truth.
    """
    import soundfile as sf

    from tests.fixtures import sounds
    from tests.fixtures import voice as voice_fx

    frames, truth = frames_of(*explainer(fps))
    duration = len(frames) / fps
    track = sounds.explainer_soundtrack(
        dest_dir / "bed.wav",
        duration,
        landing_s=truth["motions"][0]["f1"] / fps,
        impact_beat_s=4.5,
        click_s=truth["motions"][3]["f0"] / fps,
        riser_end_s=truth["transitions"][3]["start"] / fps,
    )
    mix, sr = sf.read(track.path)
    truth["sfx"] = track.sfx
    truth["bpm"] = sounds.BPM
    if voice and voice_fx.available():
        v = voice_fx.narration(dest_dir / "vo.wav")
        y, vsr = sf.read(dest_dir / "vo.wav")
        import librosa

        y = librosa.resample(y, orig_sr=vsr, target_sr=sr)[: len(mix)]
        mix[: len(y)] += np.stack([y, y], axis=1) * 0.5
        truth["words"] = [w for w in v["words"]]
    sf.write(dest_dir / "mix.wav", mix, sr)
    return encode(frames, fps, dest_dir / "explainer.mp4", audio=dest_dir / "mix.wav"), truth


CAPTION_GROUPS = ["Every answer", "counts toward", "your visibility", "score", "This group has five words"]


def captioned_clip(fps: float = 30.0, group_s: float = 1.0) -> tuple[list[np.ndarray], dict]:
    """A moving box with burned-in captions switching every `group_s` (2-word groups, then 1, then 5)."""
    import cv2

    per = round(group_s * fps)
    total = per * len(CAPTION_GROUPS)
    scene = Scene(
        total,
        (245, 247, 250),
        [Box((90, 60), (228, 87, 46), Motion(0, total - 1, (20, 60), (520, 120), linear))],
    )
    frames, _ = frames_of([scene], [])
    for i, frame in enumerate(frames):
        text = CAPTION_GROUPS[min(i // per, len(CAPTION_GROUPS) - 1)]
        (tw, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        img = frame.astype(np.uint8).copy()
        cv2.rectangle(img, ((W - tw) // 2 - 10, 300), ((W + tw) // 2 + 10, 340), (30, 42, 59), -1)
        cv2.putText(
            img, text, ((W - tw) // 2, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA
        )
        frames[i] = img.astype(np.float32)
    truth = {
        "switch_frames": [per * k for k in range(1, len(CAPTION_GROUPS))],
        "words": [len(g.split()) for g in CAPTION_GROUPS],
        "texts": CAPTION_GROUPS,
        "frames": total,
    }
    return frames, truth
