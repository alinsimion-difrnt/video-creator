"""Mel spectrogram around an event with SFX candidates marked (evidence for Claude, not truth)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

from lens.evidence.draw import BG, FG, MARK_COLOURS, font


@dataclass(frozen=True)
class Mark:
    t_s: float
    label: str  # e.g. "x003 whoosh"


def _colormap(v: np.ndarray) -> np.ndarray:
    """0..1 → RGB (dark blue → teal → yellow), a small perceptual ramp without matplotlib."""
    stops = np.array(
        [
            [13, 8, 135],
            [84, 2, 163],
            [139, 10, 165],
            [185, 50, 137],
            [219, 92, 104],
            [244, 136, 73],
            [254, 188, 43],
            [240, 249, 33],
        ],
        dtype=np.float64,
    )
    x = np.clip(v, 0, 1) * (len(stops) - 1)
    i = np.minimum(x.astype(int), len(stops) - 2)
    f = (x - i)[..., None]
    rgb: np.ndarray = (stops[i] * (1 - f) + stops[i + 1] * f).astype(np.uint8)
    return rgb


def render(
    y: np.ndarray,
    sr: int,
    t0: float,
    marks: Sequence[Mark],
    span: tuple[float, float],
    size: tuple[int, int],
    title: str,
) -> Image.Image:
    """`y` is the mono audio starting at `t0`; `span` is the event (shaded); marks are SFX syncs."""
    import librosa

    w, h = size
    head, axis = 24, 20
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    d.text((6, 4), title, fill=FG, font=font(14))
    plot_h = h - head - axis
    dur = len(y) / sr if len(y) else 0.0
    if dur > 0:
        mel = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=256, n_mels=128)
        db = librosa.power_to_db(mel, ref=np.max(mel) if mel.max() > 0 else 1.0, top_db=80)
        v = (db + 80) / 80
        rgb = _colormap(v[::-1])  # low frequencies at the bottom
        spec = Image.fromarray(rgb).resize((w, plot_h), Image.Resampling.BILINEAR)
        img.paste(spec, (0, head))

    def x_of(t: float) -> int:
        return round((t - t0) / dur * (w - 1)) if dur else 0

    a, b = x_of(span[0]), x_of(span[1])
    d.rectangle((a, head, max(a + 1, b), head + plot_h - 1), outline=FG, width=1)
    for k, m in enumerate(marks):
        x = x_of(m.t_s)
        col = MARK_COLOURS[k % len(MARK_COLOURS)]
        d.line((x, head, x, head + plot_h), fill=col, width=2)
        d.rectangle((x + 2, head + 2 + 18 * k, x + 4 + 9 * len(m.label), head + 18 + 18 * k), fill=col)
        d.text((x + 4, head + 3 + 18 * k), m.label, fill=(255, 255, 255), font=font(13))
    # time axis: ticks every 0.25 s
    if dur:
        t = np.ceil(t0 * 4) / 4
        while t <= t0 + dur:
            x = x_of(float(t))
            d.line((x, head + plot_h, x, head + plot_h + 4), fill=FG)
            d.text((x + 2, head + plot_h + 3), f"{t:.2f}s", fill=FG, font=font(11))
            t += 0.25
    return img
