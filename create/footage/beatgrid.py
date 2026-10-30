"""A small beat tracker in numpy only (tournament n06): onset envelope, tempo by autocorrelation, phase by
the grid that collects the most onset energy. librosa's `beat_track` is compiled with numba, which crashes
(SIGSEGV) in the cloud sandbox; a generated bed has one steady tempo, which this measures well."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Grid:
    bpm: float
    times: list[float]
    confidence: float  # autocorrelation at the beat lag over lag 0: 0 none, 1 a perfect pulse


def onset_envelope(mono: np.ndarray, sr: int, hop: int = 512, n_fft: int = 2048) -> np.ndarray:
    """Spectral flux: the summed rise in log magnitude from one frame to the next, one value per hop."""
    n = 1 + max(0, (len(mono) - n_fft) // hop)
    idx = np.arange(n_fft)[None, :] + hop * np.arange(n)[:, None]
    frames = mono[idx] * np.hanning(n_fft)[None, :]
    mag = np.log1p(100 * np.abs(np.fft.rfft(frames, axis=1)))
    flux = np.maximum(0.0, np.diff(mag, axis=0)).sum(axis=1)
    env = np.concatenate([[0.0], flux])
    return env - np.convolve(env, np.ones(16) / 16, mode="same")  # the local mean off: hits stand out


def _hit(mono: np.ndarray, sr: int, t: float, search_s: float = 0.08) -> float:
    """The hit's own start near `t`: the first sample whose 5 ms energy reaches half the window's peak (the
    flux frame says only which hop the hit is in, up to a window late or early)."""
    a, b = max(0, int((t - search_s) * sr)), min(len(mono), int((t + search_s) * sr))
    seg = mono[a:b].astype(np.float64)
    if seg.size == 0:
        return round(t, 4)
    win = max(1, int(0.005 * sr))
    env = np.sqrt(np.convolve(seg**2, np.ones(win) / win, mode="same"))
    if env.max() <= 4 * np.median(np.abs(mono)) + 1e-9:
        return round(t, 4)  # no clear hit: keep the grid time
    k = int(np.flatnonzero(env >= 0.5 * env.max())[0])
    return round((a + max(0, k - win // 2)) / sr, 4)


def track(mono: np.ndarray, sr: int, bpm_range: tuple[float, float] = (70, 180), hop: int = 512) -> Grid:
    env = onset_envelope(mono, sr, hop)
    e = env - env.mean()
    ac = np.correlate(e, e, mode="full")[len(e) - 1 :]
    fps = sr / hop
    lo, hi = int(fps * 60 / bpm_range[1]), int(fps * 60 / bpm_range[0]) + 1
    lag = lo + int(np.argmax(ac[lo:hi]))
    # sub-frame period: a parabola through the peak and its neighbours
    a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
    period = lag + (0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0)
    phases = np.arange(0, period, 0.25)
    pos = np.clip(env, 0, None)

    def energy(o: float) -> float:
        k = np.arange(o, len(pos) - 1, period).round().astype(int)
        return float(pos[k].mean())

    o = float(max(phases, key=energy))
    times = [_hit(mono, sr, (t * hop + 1024) / sr) for t in np.arange(o, len(pos) - 1, period)]
    conf = float(ac[lag] / ac[0]) if ac[0] > 0 else 0.0
    return Grid(round(60 * fps / period, 2), times, round(max(0.0, min(1.0, conf)), 3))
