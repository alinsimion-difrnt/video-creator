"""Safe-zone checks (M-C): where critical text and logos may sit on a frame.

Pure functions over measured boxes (`create.audit` measures them in a browser). A box is a problem when it
is on screen and not fully inside one of the frame's safe rectangles, or when scene content (not a caption)
overlaps the caption band. Rectangles and tolerances come from config `create.design` (frames, audit_*).
"""

from __future__ import annotations

from dataclasses import dataclass

from lens.schemas.config import CreateFrame, Rect
from lens.schemas.create import Box, SafeZoneIssue

__all__ = ["Box", "Hit", "persistent", "violations"]


@dataclass(frozen=True)
class Hit:
    scene: str
    t: float
    element: str
    text: str
    problem: str  # outside_safe | in_caption_band
    box: tuple[float, float, float, float]


def _overlaps(r: Rect, b: Box, tol: float) -> bool:
    return b.x0 < r.x1 - tol and b.x1 > r.x0 + tol and b.y0 < r.y1 - tol and b.y1 > r.y0 + tol


def _on_screen(frame: CreateFrame, b: Box) -> bool:
    return b.x1 > 0 and b.y1 > 0 and b.x0 < frame.width and b.y0 < frame.height


def violations(boxes: list[Box], frame: CreateFrame, tol: float) -> list[Hit]:
    """Every sampled box that breaks the frame's rules, one hit per box and problem."""
    hits = []
    for b in boxes:
        if not _on_screen(frame, b):
            continue  # entirely outside the frame: not seen
        coords = (b.x0, b.y0, b.x1, b.y1)
        if not any(r.contains(*coords, tol=tol) for r in frame.safe):
            hits.append(Hit(b.scene, b.t, b.element, b.text, "outside_safe", coords))
        if b.kind != "caption" and _overlaps(frame.caption_band, b, tol):
            hits.append(Hit(b.scene, b.t, b.element, b.text, "in_caption_band", coords))
    return hits


def persistent(hits: list[Hit], step_s: float, min_hold_s: float) -> list[SafeZoneIssue]:
    """Hits grouped into time ranges per element and problem; ranges held shorter than `min_hold_s` dropped.

    A range spans consecutive samples (gaps up to 1.5 steps); its length is t1 - t0 plus one step.
    """
    groups: dict[tuple[str, str, str], list[Hit]] = {}
    for h in sorted(hits, key=lambda h: (h.scene, h.element, h.problem, h.t)):
        groups.setdefault((h.scene, h.element, h.problem), []).append(h)
    issues = []
    for (scene, element, problem), hs in groups.items():
        runs: list[list[Hit]] = [[hs[0]]]
        for h in hs[1:]:
            if h.t - runs[-1][-1].t <= 1.5 * step_s + 1e-9:
                runs[-1].append(h)
            else:
                runs.append([h])
        for run in runs:
            first, last = run[0], run[-1]
            if last.t - first.t + step_s < min_hold_s - 1e-9:
                continue
            issues.append(
                SafeZoneIssue(
                    scene=scene,
                    element=element,
                    text=first.text,
                    problem="outside_safe" if problem == "outside_safe" else "in_caption_band",
                    t0=round(first.t, 3),
                    t1=round(last.t, 3),
                    box=[round(v, 1) for v in first.box],
                )
            )
    return issues
