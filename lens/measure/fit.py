"""Fit a measured progress curve (BUILD_PLAN 7.5 step 4): linear, cubic-bezier, damped spring and the
nearest GSAP ease; choose with AIC and a margin.

Input is progress p (0 at the first observed value, 1 at rest) sampled at times t in seconds. Each
model has a free start `t0`; eases and beziers also a free duration, because "within 2% of final" ends
an expo.out at ~56% of its real duration. Springs carry their own duration (time to settle within 2%).

When the start of the motion was not visible (an element fading in while it moves cannot be placed
until it is visible), `free_amplitude` adds A >= 1: the model is p = 1 - A * (1 - curve), i.e. the
observed travel is the last 1/A of the real one.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import least_squares

from lens.measure.curves import Curve, Spring, bezier_class, cubic_bezier, gsap_candidates, gsap_ease

MAX_AMPLITUDE = 6.0  # observed travel is at least 1/6 of the real one


@dataclass(frozen=True)
class EaseFit:
    name: str
    t0: float
    duration_s: float
    rmse: float
    amplitude: float = 1.0


@dataclass(frozen=True)
class BezierFit:
    x1: float
    y1: float
    x2: float
    y2: float
    t0: float
    duration_s: float
    rmse: float
    amplitude: float = 1.0

    @property
    def css(self) -> str:
        return f"cubic-bezier({self.x1:.3f}, {self.y1:.3f}, {self.x2:.3f}, {self.y2:.3f})"


@dataclass(frozen=True)
class SpringFit:
    spring: Spring
    t0: float
    rmse: float
    amplitude: float = 1.0


@dataclass(frozen=True)
class FitResult:
    cls: str  # linear | ease_in | ease_out | ease_in_out | spring | ambiguous
    linear: EaseFit
    bezier: BezierFit
    spring: SpringFit
    gsap: EaseFit
    aic: dict[str, float] = field(default_factory=dict)
    overshoot_pct: float = 0.0
    duration_ms: float = 0.0
    fit_quality: float = 0.0  # R^2 of the chosen model


def _rmse(r: np.ndarray) -> float:
    return float(np.sqrt(np.mean(r**2)))


def _guess(t: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    """Start and duration guesses: first move and first arrival near 1."""
    moving = np.flatnonzero(np.abs(p - p[0]) > 0.02)
    t0 = float(t[max(moving[0] - 1, 0)]) if moving.size else float(t[0])
    near = np.flatnonzero((np.abs(p - 1) < 0.02) & (t > t0))
    t1 = float(t[near[0]]) if near.size else float(t[-1])
    return t0, max(t1 - t0, (t[1] - t[0]) if t.size > 1 else 0.01)


Model = Callable[[np.ndarray, np.ndarray], np.ndarray]  # (params, t) -> curve value (0 -> 1)


def _solve(
    model: Model,
    t: np.ndarray,
    p: np.ndarray,
    inits: list[list[float]],
    lo: list[float],
    hi: list[float],
    free_amplitude: bool,
) -> tuple[np.ndarray, float, float]:
    """Least squares from each init; returns (params, amplitude, rmse) of the best."""
    best: tuple[np.ndarray, float, float] | None = None
    for x0 in inits:
        if free_amplitude:

            def resid(x: np.ndarray) -> np.ndarray:
                return np.asarray(1 - x[-1] * (1 - model(x[:-1], t)) - p)

            starts = [[*x0, a] for a in (1.0, 2.0)]
            bounds = ([*lo, 1.0], [*hi, MAX_AMPLITUDE])
        else:

            def resid(x: np.ndarray) -> np.ndarray:
                return np.asarray(model(x, t) - p)

            starts = [x0]
            bounds = (lo, hi)
        for s in starts:
            r = least_squares(resid, s, bounds=bounds)
            amp = float(r.x[-1]) if free_amplitude else 1.0
            params = r.x[:-1] if free_amplitude else r.x
            cand = (np.asarray(params), amp, _rmse(r.fun))
            if best is None or cand[2] < best[2]:
                best = cand
    assert best is not None
    return best


def _bounds_t(t: np.ndarray, free_amplitude: bool) -> tuple[float, float, float]:
    dt = float(t[1] - t[0]) if t.size > 1 else 0.01
    span = float(t[-1] - t[0])
    # With an unseen start, the motion may have begun well before the first observed frame.
    earliest = float(t[0] - (span if free_amplitude else 2 * dt))
    return dt, span, earliest


def fit_ease(
    curve: Curve, t: np.ndarray, p: np.ndarray, name: str = "", free_amplitude: bool = False
) -> EaseFit:
    t0, dur = _guess(t, p)
    dt, span, earliest = _bounds_t(t, free_amplitude)

    def model(x: np.ndarray, tt: np.ndarray) -> np.ndarray:
        return curve(np.clip((tt - x[0]) / max(x[1], 1e-6), 0.0, 1.0))

    inits = [[t0, min(dur * s, span)] for s in (1.0, 2.2)]  # slow-tailed eases end long after they look done
    x, amp, rmse = _solve(model, t, p, inits, [earliest, dt], [float(t[-1]), span + 4 * dt], free_amplitude)
    return EaseFit(name, float(x[0]), float(x[1]), rmse, amp)


def fit_bezier(t: np.ndarray, p: np.ndarray, free_amplitude: bool = False) -> BezierFit:
    t0, dur = _guess(t, p)
    dt, span, earliest = _bounds_t(t, free_amplitude)

    def model(x: np.ndarray, tt: np.ndarray) -> np.ndarray:
        return cubic_bezier(x[0], x[1], x[2], x[3])(np.clip((tt - x[4]) / max(x[5], 1e-6), 0.0, 1.0))

    shapes = [
        (0.25, 0.1, 0.25, 1.0),
        (0.42, 0.0, 0.58, 1.0),
        (0.0, 0.0, 0.58, 1.0),
        (0.42, 0.0, 1.0, 1.0),
        (0.3, 1.4, 0.6, 1.0),
    ]
    inits = [[*sh, t0, min(dur * s, span)] for sh in shapes for s in (1.0, 1.8)]
    lo = [0.0, -1.0, 0.0, -1.0, earliest, dt]
    hi = [1.0, 2.5, 1.0, 2.5, float(t[-1]), span + 4 * dt]
    x, amp, rmse = _solve(model, t, p, inits, lo, hi, free_amplitude)
    v = [float(a) for a in x]
    return BezierFit(v[0], v[1], v[2], v[3], v[4], v[5], rmse=rmse, amplitude=amp)


def fit_spring(t: np.ndarray, p: np.ndarray, free_amplitude: bool = False) -> SpringFit:
    t0, dur = _guess(t, p)
    dt, _span, earliest = _bounds_t(t, free_amplitude)

    def model(x: np.ndarray, tt: np.ndarray) -> np.ndarray:
        return np.where(tt > x[0], Spring(x[1], x[2])(np.maximum(tt - x[0], 0.0)), 0.0)

    inits = [[t0, z, 4.0 / max(dur, dt) / max(z, 0.5)] for z in (0.3, 0.6, 1.0, 1.5)]
    lo, hi = [earliest, 0.05, 0.5], [float(t[-1]), 3.0, 300.0]
    x, amp, rmse = _solve(model, t, p, inits, lo, hi, free_amplitude)
    return SpringFit(Spring(float(x[1]), float(x[2])), float(x[0]), rmse, amp)


def nearest_gsap(t: np.ndarray, p: np.ndarray, free_amplitude: bool = False) -> EaseFit:
    fits = [fit_ease(gsap_ease(n), t, p, n, free_amplitude) for n in gsap_candidates()]
    return min(fits, key=lambda f: f.rmse)


def gsap_direction(name: str) -> str:
    if name in ("none", "linear", "power0"):
        return "linear"
    if ".inOut" in name:
        return "ease_in_out"
    if ".in" in name:
        return "ease_in"
    return "ease_out"


def _aic(rmse: float, n: int, k: int) -> float:
    return n * math.log(max(rmse, 1e-6) ** 2) + 2 * k


def fit_progress(
    t: np.ndarray,
    p: np.ndarray,
    *,
    margin: float,
    end_tolerance: float,
    gsap_class_ratio: float,
    free_amplitude: bool = False,
) -> FitResult:
    t = np.asarray(t, dtype=np.float64)
    p = np.asarray(p, dtype=np.float64)
    n = len(t)
    extra = 1 if free_amplitude else 0
    lin = fit_ease(gsap_ease("none"), t, p, "none", free_amplitude)
    bez = fit_bezier(t, p, free_amplitude)
    spr = fit_spring(t, p, free_amplitude)
    gs = nearest_gsap(t, p, free_amplitude)
    aic = {
        "linear": _aic(lin.rmse, n, 2 + extra),
        "bezier": _aic(bez.rmse, n, 6 + extra),
        "spring": _aic(spr.rmse, n, 3 + extra),
    }
    bcls = bezier_class(bez.x1, bez.y1, bez.x2, bez.y2)
    if gs.rmse <= bez.rmse * gsap_class_ratio + 1e-4:
        bcls = gsap_direction(gs.name)  # a named ease that fits as well is the more robust reading
    if aic["linear"] <= min(aic["bezier"], aic["spring"]) + margin and bcls == "linear":
        cls = "linear"
    elif abs(aic["bezier"] - aic["spring"]) < margin:
        cls = "ambiguous"
    elif aic["spring"] < aic["bezier"]:
        cls = "spring"
    else:
        cls = bcls
    chosen = {"spring": spr.rmse, "linear": lin.rmse}.get(cls, bez.rmse)
    tss = float(np.sum((p - p.mean()) ** 2)) or 1e-12
    quality = max(0.0, 1 - chosen**2 * n / tss)
    overshoot = max(0.0, float(p.max()) - 1.0) / gs.amplitude
    if cls == "spring":
        duration = spr.spring.settle_s(end_tolerance)
    elif cls == "linear":
        duration = lin.duration_s
    else:
        duration = bez.duration_s
    return FitResult(
        cls=cls,
        linear=lin,
        bezier=bez,
        spring=spr,
        gsap=gs,
        aic={k: round(v, 2) for k, v in aic.items()},
        overshoot_pct=round(100 * overshoot, 2),
        duration_ms=round(1000 * duration, 1),
        fit_quality=round(quality, 4),
    )


@dataclass(frozen=True)
class JointFit:
    """One ease and timing shared by several channels of the same element (one GSAP tween usually
    moves and fades an element together); each channel keeps its own amplitude."""

    name: str
    t0: float  # absolute seconds
    duration_s: float
    rmse: float
    amplitudes: tuple[float, ...]


def fit_joint(
    series: list[tuple[np.ndarray, np.ndarray, bool, bool]], names: list[str] | None = None
) -> JointFit:
    """`series`: (absolute t, progress, free_amplitude, clamped) per channel; best named GSAP ease
    overall. `clamped` channels (opacity) cannot pass 1: the browser caps an overshooting ease."""
    t_all = np.concatenate([s[0] for s in series])
    t_lo, t_hi = float(t_all.min()), float(t_all.max())
    dt = min(float(np.min(np.diff(s[0]))) for s in series if len(s[0]) > 1)
    span = t_hi - t_lo
    guesses = [_guess(t, p) for t, p, _, _ in series]
    t0g = min(g[0] for g in guesses)
    durg = max(g[1] for g in guesses)
    free = [f for _, _, f, _ in series]
    nfree = sum(free)
    best: JointFit | None = None
    for name in names or gsap_candidates():
        curve = gsap_ease(name)

        def resid(x: np.ndarray, curve: Curve = curve) -> np.ndarray:
            out, k = [], 2
            for t, p, f, clamped in series:
                c = curve(np.clip((t - x[0]) / max(x[1], 1e-6), 0.0, 1.0))
                if clamped:
                    c = np.clip(c, 0.0, 1.0)
                if f:
                    c = 1 - x[k] * (1 - c)
                    k += 1
                out.append(c - p)
            return np.concatenate(out)

        lo = [t_lo - (span if nfree else 2 * dt), dt] + [1.0] * nfree
        hi = [t_hi, span + 4 * dt] + [MAX_AMPLITUDE] * nfree
        for scale in (1.0, 2.2):
            x0 = [t0g, min(durg * scale, span)] + [1.5] * nfree
            r = least_squares(resid, x0, bounds=(lo, hi))
            amps, k = [], 2
            for f in free:
                amps.append(float(r.x[k]) if f else 1.0)
                k += f
            cand = JointFit(name, float(r.x[0]), float(r.x[1]), _rmse(r.fun), tuple(amps))
            if best is None or cand.rmse < best.rmse:
                best = cand
    assert best is not None
    return best
