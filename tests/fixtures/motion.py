"""M4 measurement fixtures (BUILD_PLAN 11.1): a UI card animated with known eases, springs, fades and
scale-pops, plus a per-word text reveal with a known stagger. Rendered in memory with subpixel
placement (bilinear warp), so every answer is exact; `encode` runs it through ffmpeg when a test needs
real compression.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from lens.measure.curves import Spring, gsap_ease

W, H = 640, 360
BG = (245, 247, 250)
GRID = (232, 236, 241)


def canvas() -> np.ndarray:
    img = np.empty((H, W, 3), np.float32)
    img[:] = BG
    img[::40, :] = GRID
    img[:, ::40] = GRID
    return img


def card(w: int = 120, h: int = 80) -> np.ndarray:
    """RGBA sprite: white card, navy border, an orange chip and grey text stripes."""
    s = np.zeros((h, w, 4), np.float32)
    s[..., :3], s[..., 3] = (255, 255, 255), 1
    s[:2, :, :3] = s[-2:, :, :3] = s[:, :2, :3] = s[:, -2:, :3] = (30, 42, 59)
    s[10:22, 10:34, :3] = (228, 87, 46)
    for k, y in enumerate((32, 46, 60)):
        s[y : y + 6, 10 : w - 10 - 20 * k, :3] = (150, 160, 175)
    return s


def composite(base: np.ndarray, sprite: np.ndarray, cx: float, cy: float, scale: float, alpha: float) -> None:
    """Draw `sprite` centred at (cx, cy), scaled, with opacity, onto `base` (in place)."""
    h, w = sprite.shape[:2]
    m = np.float32([[scale, 0, cx - scale * w / 2], [0, scale, cy - scale * h / 2]])
    warped = cv2.warpAffine(sprite, m, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    a = warped[..., 3:4] * alpha
    base[:] = base * (1 - a) + warped[..., :3] * a


Progress = Callable[[float], float]


def ease_progress(name: str, t0: float, dur: float) -> Progress:
    f = gsap_ease(name)
    return lambda t: float(f(np.asarray(min(max((t - t0) / dur, 0.0), 1.0))))


def spring_progress(spring: Spring, t0: float) -> Progress:
    return lambda t: float(spring(np.asarray(max(t - t0, 0.0)))) if t > t0 else 0.0


@dataclass(frozen=True)
class Anim:
    """One card: positions/scale/opacity interpolated by `progress` between start and end values."""

    progress: Progress
    start_xy: tuple[float, float]
    end_xy: tuple[float, float]
    start_scale: float = 1.0
    start_alpha: float = 1.0


def render(anim: Anim, fps: float, duration_s: float) -> tuple[list[np.ndarray], tuple[int, int, int, int]]:
    """Frames (uint8 RGB) and the card's box on the last frame."""
    sprite = card()
    frames = []
    for i in range(round(duration_s * fps)):
        p = anim.progress(i / fps)
        x = anim.start_xy[0] + (anim.end_xy[0] - anim.start_xy[0]) * p
        y = anim.start_xy[1] + (anim.end_xy[1] - anim.start_xy[1]) * p
        s = anim.start_scale + (1 - anim.start_scale) * p
        a = float(np.clip(anim.start_alpha + (1 - anim.start_alpha) * p, 0, 1))
        img = canvas()
        composite(img, sprite, x, y, s, a)
        frames.append(np.clip(img + 0.5, 0, 255).astype(np.uint8))
    h, w = sprite.shape[:2]
    ex, ey = anim.end_xy
    return frames, (round(ex - w / 2), round(ey - h / 2), round(ex + w / 2), round(ey + h / 2))


WORDS = ["Every", "answer", "counts", "toward", "visibility"]


def word_reveal(
    fps: float, stagger_frames: int, fade_frames: int = 4, first: int = 6, duration_s: float = 1.6
) -> tuple[list[np.ndarray], list[tuple[int, int, int, int]], list[int]]:
    """Five words fading in one after another. Returns frames, word boxes, and each word's reveal
    frame (where its opacity passes 50%)."""
    font = ImageFont.load_default(size=28)
    probe = ImageDraw.Draw(Image.new("RGB", (W, H)))
    x, y, boxes = 40.0, 160.0, []
    for wd in WORDS:
        left, top, right, bottom = probe.textbbox((x, y), wd, font=font)
        boxes.append((int(left) - 2, int(top) - 2, int(right) + 2, int(bottom) + 2))
        x = right + 14
    starts = [first + k * stagger_frames for k in range(len(WORDS))]
    frames = []
    for i in range(round(duration_s * fps)):
        img = Image.fromarray(canvas().astype(np.uint8))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for wd, box, s in zip(WORDS, boxes, starts, strict=True):
            a = min(max((i - s) / fade_frames, 0.0), 1.0)
            if a > 0:
                d.text((box[0] + 2, box[1] + 2 - (probe.textbbox((0, 0), wd, font=font)[1])),
                       wd, font=font, fill=(30, 42, 59, round(255 * a)))  # fmt: skip
        img.paste(layer, (0, 0), layer)
        frames.append(np.asarray(img.convert("RGB")))
    reveal = [s + fade_frames // 2 for s in starts]
    return frames, boxes, reveal
