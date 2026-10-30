"""Timing curves from first principles (BUILD_PLAN 7.5, ADR 0004): GSAP's ease family, the damped
spring and CSS cubic-bezier. Golden-tested against GSAP and Remotion samples
(tests/fixtures/golden-curves.json); no library source is copied.

Every curve maps normalised time t in [0, 1] to progress (0 at the start, 1 at rest; overshoot > 1).
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

Curve = Callable[[np.ndarray], np.ndarray]


# --- GSAP eases --------------------------------------------------------------------------------------
# An "in" ease f; out(t) = 1 - f(1 - t); inOut is f on each half, mirrored.


def _power(n: int) -> Curve:
    return lambda t: t**n


def _sine(t: np.ndarray) -> np.ndarray:
    return 1 - np.cos(t * np.pi / 2)


def _expo(t: np.ndarray) -> np.ndarray:
    # GSAP's variant of 2^(10(t-1)): scaled by t plus a t^6(1-t) term so it starts at exactly 0.
    return np.asarray(2.0 ** (10 * (t - 1)) * t + t**6 * (1 - t))


def _circ(t: np.ndarray) -> np.ndarray:
    return np.asarray(1 - np.sqrt(np.clip(1 - t * t, 0, None)))


def _back(overshoot: float) -> Curve:
    return lambda t: t * t * ((overshoot + 1) * t - overshoot)


def _elastic_out(amplitude: float, period: float) -> Curve:
    """Decaying sine settling at 1 (amplitude >= 1 scales the first swing)."""
    a = max(1.0, amplitude)
    shift = period / (2 * math.pi) * math.asin(1 / a)

    def f(t: np.ndarray) -> np.ndarray:
        return np.where(t >= 1, 1.0, a * 2.0 ** (-10 * t) * np.sin((t - shift) * 2 * math.pi / period) + 1)

    return f


def _direction(base_in: Curve, direction: str) -> Curve:
    if direction == "in":
        return base_in
    if direction == "out":
        return lambda t: 1 - base_in(1 - t)
    return lambda t: np.where(t < 0.5, base_in(2 * t) / 2, 1 - base_in(2 * (1 - t)) / 2)


def _from_out(base_out: Curve, direction: str) -> Curve:
    as_in: Curve = lambda t: 1 - base_out(1 - t)  # noqa: E731
    return _direction(as_in, direction)


GSAP_FAMILIES = ("power1", "power2", "power3", "power4", "sine", "expo", "circ")
_POWERS = {"power0": 1, "power1": 2, "power2": 3, "power3": 4, "power4": 5}
_NAME = re.compile(r"^(?P<family>[a-z]+\d?)(?:\.(?P<dir>in|out|inOut))?(?:\((?P<args>[^)]*)\))?$")


def gsap_ease(name: str) -> Curve:
    """A GSAP ease by name, e.g. "power2.out", "back.out(1.4)", "elastic.out(1,0.3)", "none"."""
    if name in ("none", "linear", "power0"):
        return lambda t: np.asarray(t, dtype=np.float64)
    m = _NAME.match(name)
    if not m:
        raise ValueError(f"unknown ease {name!r}")
    family, direction = m.group("family"), m.group("dir") or "out"
    args = [float(a) for a in (m.group("args") or "").split(",") if a.strip()]
    if family in _POWERS:
        return _direction(_power(_POWERS[family]), direction)
    if family == "sine":
        return _direction(_sine, direction)
    if family == "expo":
        return _direction(_expo, direction)
    if family == "circ":
        return _direction(_circ, direction)
    if family == "back":
        return _direction(_back(args[0] if args else 1.70158), direction)
    if family == "elastic":
        amp, per = (args + [1.0, 0.3][len(args) :])[:2]
        return _from_out(_elastic_out(amp, per), direction)
    raise ValueError(f"unknown ease {name!r}")


def gsap_candidates() -> list[str]:
    """The built-in eases `nearest_gsap` chooses from (back/elastic over a parameter grid)."""
    names = ["none"] + [f"{f}.{d}" for f in GSAP_FAMILIES for d in ("in", "out", "inOut")]
    names += [f"back.out({p:g})" for p in (0.8, 1.0, 1.2, 1.4, 1.7, 2.0, 2.5, 3.0)]
    names += [f"back.inOut({p:g})" for p in (1.2, 1.7, 2.5)]
    names += [f"elastic.out(1,{p:g})" for p in (0.3, 0.4, 0.5, 0.75)]
    return names


# --- cubic-bezier --------------------------------------------------------------------------------------


def cubic_bezier(x1: float, y1: float, x2: float, y2: float) -> Curve:
    """CSS cubic-bezier(x1, y1, x2, y2): solve x(s) = t for s, return y(s). x1, x2 in [0, 1]."""

    def coord(s: np.ndarray, p1: float, p2: float) -> np.ndarray:
        return np.asarray(3 * (1 - s) ** 2 * s * p1 + 3 * (1 - s) * s**2 * p2 + s**3)

    def f(t: np.ndarray) -> np.ndarray:
        t = np.clip(np.asarray(t, dtype=np.float64), 0, 1)
        lo, hi = np.zeros_like(t), np.ones_like(t)
        for _ in range(40):  # x(s) is monotonic for x1, x2 in [0, 1]: bisection is exact enough
            mid = (lo + hi) / 2
            below = coord(mid, x1, x2) < t
            lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
        return coord((lo + hi) / 2, y1, y2)

    return f


def bezier_class(x1: float, y1: float, x2: float, y2: float, tol: float = 0.1) -> str:
    """linear | ease_in | ease_out | ease_in_out, from the start and end slopes."""
    start = y1 / x1 if x1 > 1e-6 else math.inf
    end = (1 - y2) / (1 - x2) if x2 < 1 - 1e-6 else math.inf
    slow_start, slow_end = start < 1 - tol, end < 1 - tol
    if slow_start and slow_end:
        return "ease_in_out"
    if slow_start:
        return "ease_in"
    if slow_end:
        return "ease_out"
    return "linear"


# --- damped spring -------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Spring:
    """Mass-spring-damper from rest at 0 to equilibrium at 1, in seconds; mass fixed at 1."""

    zeta: float  # damping ratio: < 1 overshoots, 1 critical, > 1 overdamped
    omega0: float  # natural frequency, rad/s

    def __call__(self, t_s: np.ndarray) -> np.ndarray:
        t = np.asarray(t_s, dtype=np.float64)
        z, w = self.zeta, self.omega0
        if z < 1 - 1e-9:
            wd = w * math.sqrt(1 - z * z)
            x = np.exp(-z * w * t) * (np.cos(wd * t) + z * w / wd * np.sin(wd * t))
        elif z <= 1 + 1e-9:
            x = (1 + w * t) * np.exp(-w * t)
        else:
            root = math.sqrt(z * z - 1)
            r1, r2 = -w * (z - root), -w * (z + root)
            a = r2 / (r2 - r1)
            x = a * np.exp(r1 * t) + (1 - a) * np.exp(r2 * t)
        return 1 - x

    @classmethod
    def from_physical(cls, mass: float, stiffness: float, damping: float) -> Spring:
        """{mass, stiffness, damping} is over-parameterised; it maps to one (zeta, omega0)."""
        return cls(damping / (2 * math.sqrt(stiffness * mass)), math.sqrt(stiffness / mass))

    def remotion(self) -> dict[str, float]:
        """Remotion's `spring()` config with mass 1 (the same curve as any scaled triple).

        Remotion renders every spring with zeta >= 1 as critically damped at the same omega0
        (verified by sampling, docs/external-facts.md), so an overdamped fit does not reproduce in
        Remotion; `remotion_exact` says whether it does.
        """
        return {
            "mass": 1.0,
            "stiffness": round(self.omega0**2, 3),
            "damping": round(2 * self.zeta * self.omega0, 3),
        }

    @property
    def remotion_exact(self) -> bool:
        return self.zeta <= 1 + 1e-9

    def as_remotion_renders(self) -> Spring:
        """The curve Remotion actually draws for this config."""
        return self if self.remotion_exact else Spring(1.0, self.omega0)

    def overshoot(self) -> float:
        """Peak above 1 as a fraction (0 when critically or overdamped)."""
        if self.zeta >= 1:
            return 0.0
        return math.exp(-math.pi * self.zeta / math.sqrt(1 - self.zeta**2))

    def settle_s(self, tol: float = 0.02, horizon_s: float = 20.0) -> float:
        """Time after which the spring stays within `tol` of rest."""
        t = np.linspace(0, horizon_s, 20001)
        off = np.flatnonzero(np.abs(self(t) - 1) > tol)
        return (
            float(t[off[-1] + 1])
            if off.size and off[-1] + 1 < t.size
            else (0.0 if not off.size else horizon_s)
        )


def ease_class(ease: str | None) -> str:
    """Taxonomy easing class of a GSAP ease name."""
    if not ease:
        return "ease_out"  # GSAP's default ease is power1.out
    if ease in ("none", "linear") or ease.startswith("linear"):
        return "linear"
    if ease.startswith("steps"):
        return "step"
    if ease.startswith("bounce"):
        return "bounce"
    overshoot = ease.startswith(("back", "elastic"))
    if ".inOut" in ease:
        return "ease_in_out"
    if ".in" in ease and ".out" not in ease:
        return "ease_in"
    return "spring_overshoot" if overshoot else "ease_out"
