"""The numpy beat tracker (tournament n06) on a synthetic click track."""

import numpy as np

from create.footage.beatgrid import track


def _clicks(bpm: float, offset: float, seconds: float, sr: int = 22050) -> np.ndarray:
    y = np.random.default_rng(0).normal(0, 0.01, int(seconds * sr))
    t = offset
    while t < seconds - 0.05:
        k = int(t * sr)
        n = int(0.03 * sr)
        y[k : k + n] += np.sin(2 * np.pi * 80 * np.arange(n) / sr) * np.exp(-np.arange(n) / (0.006 * sr))
        t += 60 / bpm
    return y.astype(np.float32)


def test_tempo_and_beats_of_a_steady_kick() -> None:
    sr = 22050
    g = track(_clicks(110, 0.37, 20, sr), sr)
    assert abs(g.bpm - 110) < 1.0
    want = 0.37 + np.arange(30) * 60 / 110
    got = np.array(g.times[:30])
    assert np.max(np.abs(got - want)) < 0.03  # within about a frame of each hit
    assert g.confidence > 0.3
