"""Synthetic soundtracks with known answers, aligned to `scenes.explainer()` (BUILD_PLAN 11.1).

Levels follow typical explainer mixes: SFX sit clearly above a soft music bed.

Music: 120 BPM kick + hat + pad (a repeating pattern the SFX detector must ignore).
SFX (each exactly once): a whoosh peaking 60 ms before a visual landing, an impact exactly on a
beat, a click on a reveal, and a riser ending on a scene start. The mix is normalised to a known
integrated loudness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf

SR = 48_000
BPM = 120.0


def _env(n: int, attack: int, decay_tau: float) -> np.ndarray:
    t = np.arange(n)
    env = np.exp(-np.maximum(t - attack, 0) / decay_tau)
    if attack > 0:
        env[:attack] = np.linspace(0, 1, attack)
    return env


def _noise(n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.standard_normal(n)


def _bandpass_sweep(x: np.ndarray, f0: float, f1: float) -> np.ndarray:
    """Noise band sweeping from f0 to f1: difference of two stable one-pole low-passes."""
    out = np.empty_like(x)
    fast = slow = 0.0
    freqs = np.linspace(f0, f1, len(x))
    a_fast = np.exp(-2 * np.pi * freqs / SR)
    a_slow = np.exp(-2 * np.pi * (freqs / 4) / SR)
    for i, v in enumerate(x):
        fast = (1 - a_fast[i]) * v + a_fast[i] * fast
        slow = (1 - a_slow[i]) * v + a_slow[i] * slow
        out[i] = fast - slow
    return out


def kick(rng: np.random.Generator) -> np.ndarray:
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    freq = 50 + 70 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(freq) / SR) * _env(n, 30, 0.06 * SR)


def hat(rng: np.random.Generator) -> np.ndarray:
    n = int(0.04 * SR)
    return np.diff(_noise(n + 1, rng)) * _env(n, 5, 0.008 * SR) * 0.3


def whoosh(rng: np.random.Generator, dur: float = 0.45) -> tuple[np.ndarray, float]:
    """Returns (signal, peak offset in seconds from its start)."""
    n = int(dur * SR)
    peak = int(n * 0.7)
    env = np.concatenate([np.linspace(0, 1, peak) ** 2, np.linspace(1, 0, n - peak) ** 1.5])
    sig = _bandpass_sweep(_noise(n, rng), 300, 4000) * env
    return sig / np.max(np.abs(sig)), peak / SR


def impact(rng: np.random.Generator) -> np.ndarray:
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 45 * t) * _env(n, 10, 0.18 * SR)
    crack = _noise(n, rng) * _env(n, 5, 0.03 * SR) * 0.6
    return body + crack


def click() -> np.ndarray:
    n = int(0.012 * SR)
    return np.sign(np.sin(np.linspace(0, 6 * np.pi, n))) * _env(n, 2, 0.002 * SR)


def riser(rng: np.random.Generator, dur: float = 1.5) -> np.ndarray:
    n = int(dur * SR)
    env = np.linspace(0.02, 1, n) ** 2
    return _bandpass_sweep(_noise(n, rng), 200, 6000) * env


@dataclass
class Soundtrack:
    path: Path
    duration_s: float
    integrated_lufs: float
    beats: list[float]
    sfx: list[dict[str, float | str]] = field(default_factory=list)


def explainer_soundtrack(
    dest: Path,
    duration_s: float,
    landing_s: float,
    impact_beat_s: float,
    click_s: float,
    riser_end_s: float,
    target_lufs: float = -20.9,
    seed: int = 7,
) -> Soundtrack:
    rng = np.random.default_rng(seed)
    n = int(duration_s * SR)
    music = np.zeros(n)
    beat = 60.0 / BPM
    beats = [round(i * beat, 6) for i in range(int(duration_s / beat) + 1) if i * beat < duration_s - 0.3]
    k, h = kick(rng), hat(rng)
    for b in beats:
        i = int(b * SR)
        music[i : i + len(k)] += k[: n - i] * 0.35
        j = int((b + beat / 2) * SR)
        if j < n:
            music[j : j + len(h)] += h[: n - j] * 0.5
    t = np.arange(n) / SR
    pad = sum(np.sin(2 * np.pi * f * t) for f in (220.0, 277.2, 329.6)) * 0.08
    music += pad

    sfx = np.zeros(n)
    events: list[dict[str, float | str]] = []
    w, peak_off = whoosh(rng)
    start = landing_s - 0.060 - peak_off
    i = int(start * SR)
    sfx[i : i + len(w)] += w * 0.6
    events.append({"label": "whoosh", "sync_s": round(landing_s - 0.060, 4), "onset_s": round(start, 4)})

    im = impact(rng)
    i = int(impact_beat_s * SR)
    sfx[i : i + len(im)] += im[: n - i] * 0.6
    events.append({"label": "impact", "sync_s": impact_beat_s, "onset_s": impact_beat_s})

    c = click()
    i = int(click_s * SR)
    sfx[i : i + len(c)] += c * 0.5
    events.append({"label": "click", "sync_s": click_s, "onset_s": click_s})

    r = riser(rng)
    i = int((riser_end_s - len(r) / SR) * SR)
    sfx[i : i + len(r)] += r / np.max(np.abs(r)) * 0.5
    events.append({"label": "riser", "sync_s": riser_end_s, "onset_s": round(riser_end_s - len(r) / SR, 4)})

    mix = music + sfx
    stereo = np.stack([mix, mix * 0.98], axis=1)
    meter = pyln.Meter(SR)
    stereo = pyln.normalize.loudness(stereo, meter.integrated_loudness(stereo), target_lufs)
    peak = np.max(np.abs(stereo))
    if peak > 0.98:
        raise ValueError("fixture clips; lower the target loudness")
    sf.write(dest, stereo.astype(np.float32), SR, subtype="PCM_24")
    return Soundtrack(dest, duration_s, target_lufs, beats, events)
