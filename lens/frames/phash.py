"""Perceptual hashes for duplicate detection across sources (BUILD_PLAN 6.3)."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from PIL import Image


def dhash(frame: np.ndarray) -> str:
    """64-bit difference hash of an RGB frame, as 16 hex chars."""
    img = Image.fromarray(frame).convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    px = np.asarray(img, dtype=np.int16)
    bits = (px[:, 1:] > px[:, :-1]).flatten()
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return f"{value:016x}"


def hamming(a: str, b: str) -> int:
    return (int(a, 16) ^ int(b, 16)).bit_count()


def sequence_distance(a: Sequence[str], b: Sequence[str]) -> float:
    """Median of the best per-frame match distances (robust to small trims)."""
    if not a or not b:
        return 64.0
    best = [min(hamming(x, y) for y in b) for x in a]
    return float(np.median(best))
