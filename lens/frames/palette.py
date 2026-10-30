"""Palette by k-means in code: hex values come from code, never from Claude (BUILD_PLAN 6.3)."""

from __future__ import annotations

import numpy as np

MERGE_DISTANCE = 12.0  # RGB distance under which two centroids are the same colour


def sample_pixels(frame: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    flat = frame.reshape(-1, 3)
    idx = rng.choice(flat.shape[0], size=min(n, flat.shape[0]), replace=False)
    return flat[idx].astype(np.float64)


def kmeans(pixels: np.ndarray, k: int, seed: int = 0, iterations: int = 30) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic k-means++ in RGB. Returns (centroids kx3, counts k)."""
    rng = np.random.default_rng(seed)
    k = min(k, len(pixels))
    centroids = [pixels[rng.integers(len(pixels))]]
    for _ in range(1, k):
        d2 = np.min(((pixels[:, None, :] - np.asarray(centroids)[None]) ** 2).sum(-1), axis=1)
        total = d2.sum()
        if total == 0:
            break
        centroids.append(pixels[rng.choice(len(pixels), p=d2 / total)])
    c = np.asarray(centroids)
    labels = np.zeros(len(pixels), dtype=int)
    for _ in range(iterations):
        labels = ((pixels[:, None, :] - c[None]) ** 2).sum(-1).argmin(1)
        new = np.asarray(
            [pixels[labels == j].mean(0) if np.any(labels == j) else c[j] for j in range(len(c))]
        )
        if np.allclose(new, c, atol=0.5):
            c = new
            break
        c = new
    counts = np.bincount(labels, minlength=len(c))
    return c, counts


def merge_close(centroids: np.ndarray, counts: np.ndarray) -> list[tuple[np.ndarray, int]]:
    """Merge centroids closer than MERGE_DISTANCE (k larger than the true number of colours)."""
    order = np.argsort(-counts)
    merged: list[tuple[np.ndarray, int]] = []
    for j in order:
        if counts[j] == 0:
            continue
        for i, (c, n) in enumerate(merged):
            if np.linalg.norm(c - centroids[j]) < MERGE_DISTANCE:
                total = n + int(counts[j])
                merged[i] = ((c * n + centroids[j] * counts[j]) / total, total)
                break
        else:
            merged.append((centroids[j].astype(np.float64), int(counts[j])))
    return sorted(merged, key=lambda cn: -cn[1])


def to_hex(rgb: np.ndarray) -> str:
    r, g, b = (round(float(v)) for v in np.clip(rgb, 0, 255))
    return f"#{r:02x}{g:02x}{b:02x}"


def palette(pixels: np.ndarray, k: int, seed: int = 0) -> list[tuple[str, float]]:
    centroids, counts = kmeans(pixels, k, seed)
    merged = merge_close(centroids, counts)
    total = sum(n for _, n in merged)
    return [(to_hex(c), round(n / total, 4)) for c, n in merged]
