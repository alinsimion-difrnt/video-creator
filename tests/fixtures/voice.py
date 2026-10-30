"""Spoken fixtures from espeak-ng (offline TTS) with known words and inserted pauses."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

SENTENCES = [
    "Our tool checks how often your brand appears in answers.",
    "It asks the same questions people ask every day.",
    "Then it counts which companies get mentioned.",
    "You see the results in one simple report.",
]
PAUSES_S = [0.3, 0.9, 0.5]  # silences inserted between the sentences


def available() -> bool:
    return shutil.which("espeak-ng") is not None


def _say(text: str, dest: Path, wpm: int, pitch: int) -> np.ndarray:
    subprocess.run(
        ["espeak-ng", "-v", "en-us", "-s", str(wpm), "-p", str(pitch), "-w", str(dest), text], check=True
    )
    y, sr = sf.read(dest)
    assert sr == 22050
    # trim espeak's own leading/trailing silence so inserted pauses are exact
    nz = np.flatnonzero(np.abs(y) > 1e-3)
    return y[nz[0] : nz[-1] + 1]


def narration(dest: Path, wpm: int = 160, pitches: list[int] | None = None) -> dict:
    """Write a narration; returns truth: words, pause positions (s) and lengths."""
    pitches = pitches or [50] * len(SENTENCES)
    sr = 22050
    parts: list[np.ndarray] = [np.zeros(int(0.5 * sr))]
    pause_at: list[tuple[float, float]] = []
    t = 0.5
    for i, (text, pitch) in enumerate(zip(SENTENCES, pitches, strict=True)):
        y = _say(text, dest.with_suffix(f".{i}.wav"), wpm, pitch)
        parts.append(y)
        t += len(y) / sr
        if i < len(PAUSES_S):
            pause_at.append((t, PAUSES_S[i]))
            parts.append(np.zeros(int(PAUSES_S[i] * sr)))
            t += PAUSES_S[i]
    parts.append(np.zeros(int(0.5 * sr)))
    audio = np.concatenate(parts) * 0.8
    sf.write(dest, audio, sr)
    words = " ".join(SENTENCES).replace(".", "").split()
    return {"words": words, "pauses": pause_at, "speech_end_s": t, "speech_start_s": 0.5}
