"""Images for Claude: filmstrips, set-of-marks overlays, contact sheets (BUILD_PLAN 7.2).

Every image keeps its long edge within `evidence.image_long_edge_px`.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from lens.evidence.boxes import Box

# High-contrast outline colours, cycled by box rank (colour-blind safe order first).
MARK_COLOURS = [
    (230, 25, 75),
    (0, 130, 200),
    (245, 130, 48),
    (60, 180, 75),
    (145, 30, 180),
    (240, 50, 230),
    (0, 128, 128),
    (128, 0, 0),
    (0, 0, 128),
    (128, 128, 0),
]
BG = (24, 24, 27)
FG = (250, 250, 250)


@cache
def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except (TypeError, OSError):  # Pillow without FreeType
        return ImageFont.load_default()


def fit(img: Image.Image, long_edge: int) -> Image.Image:
    w, h = img.size
    s = long_edge / max(w, h)
    if s >= 1:
        return img
    return img.resize((max(1, round(w * s)), max(1, round(h * s))), Image.Resampling.LANCZOS)


def stamp(t_s: float) -> str:
    m, s = divmod(t_s, 60)
    return f"{int(m)}:{s:06.3f}"


def _text_size(d: ImageDraw.ImageDraw, text: str, size: int) -> tuple[int, int]:
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=font(size))
    return int(x1 - x0), int(y1 - y0)


def grid(
    tiles: Sequence[Image.Image],
    captions: Sequence[str],
    cols: int,
    long_edge: int,
    header: str | None = None,
    gap: int = 6,
    caption_px: int = 16,
) -> Image.Image:
    """Tiles of equal size in a grid, a caption bar under each, an optional header, scaled to fit."""
    if not tiles:
        raise ValueError("no tiles")
    rows = -(-len(tiles) // cols)
    cols = min(cols, len(tiles))
    tw, th = tiles[0].size
    cap_h = caption_px + 6
    head_h = caption_px + 12 if header else 0
    # Gaps, caption bars and the header keep their size; only the tiles scale.
    fixed_w = (cols + 1) * gap
    fixed_h = head_h + rows * cap_h + (rows + 1) * gap
    scale = min(1.0, (long_edge - fixed_w) / (cols * tw), (long_edge - fixed_h) / (rows * th))
    # Lay out at the final scale so text stays crisp.
    tw2, th2 = max(1, int(tw * scale)), max(1, int(th * scale))
    W = cols * tw2 + (cols + 1) * gap
    H = head_h + rows * (th2 + cap_h) + (rows + 1) * gap
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    if header:
        d.text((gap, gap), header, fill=FG, font=font(caption_px))
    for i, (tile, cap) in enumerate(zip(tiles, captions, strict=True)):
        r, c = divmod(i, cols)
        x = gap + c * (tw2 + gap)
        y = head_h + gap + r * (th2 + cap_h + gap)
        sheet.paste(tile.resize((tw2, th2), Image.Resampling.LANCZOS), (x, y))
        d.text((x + 2, y + th2 + 3), cap, fill=FG, font=font(caption_px - 2))
    return sheet


def context_thumb(frame: np.ndarray, crop: Box, size: tuple[int, int]) -> Image.Image:
    """The full frame, small, with the crop outlined: where in the frame the filmstrip looks."""
    img = Image.fromarray(frame)
    d = ImageDraw.Draw(img)
    w = max(2, img.width // 240)
    d.rectangle((crop[0], crop[1], crop[2] - 1, crop[3] - 1), outline=MARK_COLOURS[0], width=w)
    img.thumbnail(size, Image.Resampling.LANCZOS)
    tile = Image.new("RGB", size, BG)
    tile.paste(img, ((size[0] - img.width) // 2, (size[1] - img.height) // 2))
    return tile


def _overlaps(a: Box, b: Box) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def place_labels(
    boxes: Sequence[Box], sizes: Sequence[tuple[int, int]], width: int, height: int
) -> list[Box]:
    """Label rectangles placed outside their box where possible (above, below, left, right),
    avoiding other labels and other boxes; inside the box's top-left corner as a last resort."""
    placed: list[Box] = []
    for i, (b, (lw, lh)) in enumerate(zip(boxes, sizes, strict=True)):
        x0, y0, x1, y1 = b
        options = [
            (x0, y0 - lh - 2),
            (x0, y1 + 2),
            (x0 - lw - 2, y0),
            (x1 + 2, y0),
            (x1 - lw, y0 - lh - 2),
            (x1 - lw, y1 + 2),
        ]
        others = [o for j, o in enumerate(boxes) if j != i]
        chosen: Box | None = None
        for ox, oy in options:
            r = (int(ox), int(oy), int(ox + lw), int(oy + lh))
            if r[0] < 0 or r[1] < 0 or r[2] > width or r[3] > height:
                continue
            if any(_overlaps(r, p) for p in placed) or any(_overlaps(r, o) for o in others):
                continue
            chosen = r
            break
        if chosen is None:  # crowded: first in-frame option that avoids other labels, else inside
            for ox, oy in options:
                r = (int(ox), int(oy), int(ox + lw), int(oy + lh))
                inside = r[0] >= 0 and r[1] >= 0 and r[2] <= width and r[3] <= height
                if inside and not any(_overlaps(r, p) for p in placed):
                    chosen = r
                    break
        placed.append(chosen or (x0 + 1, y0 + 1, x0 + 1 + lw, y0 + 1 + lh))
    return placed


def set_of_marks(frame: np.ndarray, boxes: Sequence[Box], ids: Sequence[str], long_edge: int) -> Image.Image:
    """Thin numbered outlines; labels outside the boxes with a leader line to the box edge."""
    img = Image.fromarray(frame).convert("RGB")
    s = min(1.0, long_edge / max(img.size))
    if s < 1:
        img = img.resize((round(img.width * s), round(img.height * s)), Image.Resampling.LANCZOS)
    scaled = [tuple(round(v * s) for v in b) for b in boxes]
    d = ImageDraw.Draw(img)
    size = max(12, img.height // 45)
    sizes = [(_text_size(d, t, size)[0] + 6, _text_size(d, t, size)[1] + 6) for t in ids]
    labels = place_labels(scaled, sizes, img.width, img.height)  # type: ignore[arg-type]
    line = max(1, img.width // 640)
    for k, (b, lab, text) in enumerate(zip(scaled, labels, ids, strict=True)):
        col = MARK_COLOURS[k % len(MARK_COLOURS)]
        d.rectangle((b[0], b[1], b[2] - 1, b[3] - 1), outline=col, width=line)
        # leader line: label centre to the nearest point on the box outline
        cx, cy = (lab[0] + lab[2]) / 2, (lab[1] + lab[3]) / 2
        px, py = min(max(cx, b[0]), b[2] - 1), min(max(cy, b[1]), b[3] - 1)
        if not (b[0] <= cx < b[2] and b[1] <= cy < b[3]):
            d.line((cx, cy, px, py), fill=col, width=line)
        d.rectangle(lab, fill=col)
        d.text((lab[0] + 3, lab[1] + 2), text, fill=(255, 255, 255), font=font(size))
    return img
