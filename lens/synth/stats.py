"""Weighted statistics for S9: weighted quantiles, bootstrap interval of the median, shares, k-means."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence

import numpy as np

from lens.schemas.corpus import Shares, Stat


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    """Quantile of the weighted distribution (midpoint rule, linear between points)."""
    order = np.argsort(values, kind="stable")
    v, w = values[order], weights[order]
    cum = np.cumsum(w) - 0.5 * w
    return float(np.interp(q * w.sum(), cum, v))


def stat(
    values: Sequence[float],
    weights: Sequence[float],
    videos: Iterable[str],
    *,
    min_n: int,
    bootstrap: int,
    ci: float,
    seed: int,
) -> Stat:
    """Weighted median, quartiles and (from `min_n` observations) a bootstrap interval of the median."""
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    keep = np.isfinite(v) & (w > 0)
    v, w = v[keep], w[keep]
    vids = {x for x, k in zip(videos, keep, strict=True) if k}
    if v.size == 0:
        return Stat(n=0, videos=0, weight=0.0, median=None, p25=None, p75=None, ci=None)
    med = weighted_quantile(v, w, 0.5)
    interval = None
    if v.size >= min_n:
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, v.size, size=(bootstrap, v.size))
        meds = np.array([weighted_quantile(v[i], w[i], 0.5) for i in idx])
        lo, hi = np.quantile(meds, [(1 - ci) / 2, 1 - (1 - ci) / 2])
        interval = (round(float(lo), 3), round(float(hi), 3))
    return Stat(
        n=int(v.size),
        videos=len(vids),
        weight=round(float(w.sum()), 4),
        median=round(med, 3),
        p25=round(weighted_quantile(v, w, 0.25), 3),
        p75=round(weighted_quantile(v, w, 0.75), 3),
        ci=interval,
    )


def shares(pairs: Iterable[tuple[str, float]]) -> Shares:
    """Weighted share of each label, largest first."""
    tot: dict[str, float] = defaultdict(float)
    for label, w in pairs:
        if w > 0:
            tot[label] += w
    s = sum(tot.values())
    if not s:
        return {}
    return {k: round(v / s, 4) for k, v in sorted(tot.items(), key=lambda kv: (-kv[1], kv[0]))}


def kmeans(points: np.ndarray, k: int, iters: int = 50) -> np.ndarray:
    """Labels of a deterministic k-means on standardized points (initial centres at quantiles of the
    first coordinate), ordered by that coordinate's centre."""
    n = points.shape[0]
    k = min(k, n)
    if k <= 1:
        return np.zeros(n, dtype=int)
    z = (points - points.mean(0)) / np.where(points.std(0) > 0, points.std(0), 1)
    order = np.argsort(z[:, 0], kind="stable")
    centres = z[order[np.linspace(0, n - 1, k).round().astype(int)]]
    labels = np.zeros(n, dtype=int)
    for _ in range(iters):
        d = ((z[:, None, :] - centres[None]) ** 2).sum(-1)
        new = d.argmin(1)
        if (new == labels).all() and _ > 0:
            break
        labels = new
        for j in range(k):
            if (labels == j).any():
                centres[j] = z[labels == j].mean(0)
    rank = np.argsort(np.argsort(centres[:, 0]))
    return np.asarray(rank[labels], dtype=int)
