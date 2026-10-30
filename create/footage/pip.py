"""Where the presenter's corner bubble goes (used by create/footage/layout.py).

The bubble sits as far into its corner as the frame's safe rects allow (config frames) and stays above the
caption band, so captions burned later never collide with it.
"""

from __future__ import annotations

from typing import Literal

from lens.schemas.config import CreateFrame

Corner = Literal["br", "bl", "tr", "tl"]


def bubble_position(
    frame: CreateFrame, d: int, margin: int, corner: Corner, avoid_band: bool = True
) -> tuple[int, int]:
    """Top-left of a `d`-pixel bubble as far into `corner` as the frame's safe rects allow, above the caption
    band (a vertical frame's upper extension lets a bubble sit further right, above the action rail).
    `avoid_band=False`: as low as the safe rect allows (just above the description zone); the captions then
    go elsewhere."""
    band = frame.caption_band
    best: tuple[float, tuple[int, int]] | None = None
    for r in frame.safe:
        bottom = r.y1 - margin
        if avoid_band and band.x0 < r.x1 and band.x1 > r.x0 and band.y0 < bottom:
            bottom = band.y0 - margin
        x = r.x1 - margin - d if corner in ("br", "tr") else r.x0 + margin
        y = r.y0 + margin if corner in ("tr", "tl") else bottom - d
        if x < r.x0 or y < r.y0 or x + d > r.x1 or y + d > r.y1:
            continue  # the bubble does not fit in this rect
        sx = x if corner in ("br", "tr") else -x
        sy = y if corner in ("br", "bl") else -y
        if best is None or sx + sy > best[0]:
            best = (sx + sy, (x, y))
    if best is None:
        raise ValueError(f"a {d}px bubble fits in none of the frame's safe rects")
    return best[1]
