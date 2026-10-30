"""Pixel gag items for Fred (skill pixel-art; ADR 0030): small sprites drawn at native size in Fred's look (a
warm ink outline, two or three tones a material, one light from the top left), upscaled with Fred's own
pixel size so they read as one set.

`frames(name)` -> frames (RGBA, native pixels); `FPS[name]`; `PLACE[name]`: where the page puts it beside
Fred (left: on the floor to his left, held: at his fin, above: over his head, swap: instead of him, face:
over his eyes). Native heights are 12-34 px against Fred's 64.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from PIL import Image

INK = (43, 29, 20, 255)
RGB = tuple[int, int, int]


def _canvas(w: int, h: int) -> np.ndarray:
    return np.zeros((h, w, 4), np.uint8)


def _rect(a: np.ndarray, x0: int, y0: int, x1: int, y1: int, c: RGB) -> None:
    a[max(0, y0) : max(0, y1), max(0, x0) : max(0, x1)] = (*c, 255)


def _px(a: np.ndarray, pts: list[tuple[int, int]], c: RGB) -> None:
    for x, y in pts:
        if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
            a[y, x] = (*c, 255)


def _ink(a: np.ndarray) -> Image.Image:
    """A one-pixel warm ink outline around everything drawn (the fish-icon look), then an image."""
    solid = a[..., 3] > 0
    grow = solid.copy()
    grow[1:] |= solid[:-1]
    grow[:-1] |= solid[1:]
    grow[:, 1:] |= solid[:, :-1]
    grow[:, :-1] |= solid[:, 1:]
    edge = grow & ~solid
    out = a.copy()
    out[edge] = INK
    return Image.fromarray(out, "RGBA")


GLYPHS = {  # 3 x 5 pixel letters for signs
    "F": ["###", "#..", "##.", "#..", "#.."],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "E": ["###", "#..", "##.", "#..", "###"],
}


def _text(a: np.ndarray, x: int, y: int, word: str, c: RGB) -> None:
    for k, ch in enumerate(word):
        for r, row in enumerate(GLYPHS[ch]):
            for q, v in enumerate(row):
                if v == "#":
                    _px(a, [(x + k * 4 + q, y + r)], c)


def popcorn() -> list[Image.Image]:
    """A striped popcorn box; kernels pop out of it one by one."""
    out = []
    for f in range(4):
        a = _canvas(18, 24)
        for k in range(5):  # red and white stripes, a little wider at the top
            _rect(
                a,
                3 + k * 2 + (k // 3),
                10,
                5 + k * 2 + (k // 3),
                23,
                (214, 40, 52) if k % 2 == 0 else (250, 244, 232),
            )
        _rect(a, 3, 10, 15, 12, (180, 30, 44))
        for x, y in [(4, 8), (7, 7), (10, 8), (13, 7), (6, 9), (11, 9), (9, 6)]:  # the heap of kernels
            _rect(a, x, y, x + 2, y + 2, (255, 236, 170))
        fly = [(8, 3 - f), (12, 4 - (f + 2) % 4)][: 1 + f % 2]  # one or two kernels in the air
        for x, y in fly:
            _rect(a, x, max(0, y), x + 2, max(0, y) + 2, (255, 246, 200))
        out.append(_ink(a))
    return out


def tv() -> list[Image.Image]:
    """A tiny retro screen on legs; the picture flickers (a play button, then frames)."""
    out = []
    for f in range(3):
        a = _canvas(26, 22)
        _rect(a, 1, 1, 25, 17, (70, 72, 84))
        screen = [(84, 170, 255), (110, 200, 255), (96, 186, 240)][f]
        _rect(a, 3, 3, 21, 15, screen)
        _rect(a, 22, 4, 24, 6, (230, 190, 80))
        _rect(a, 22, 9, 24, 11, (200, 60, 60))
        _px(
            a,
            [(10, 6), (10, 7), (11, 7), (10, 8), (11, 8), (12, 8), (10, 9), (11, 9), (10, 10)],
            (255, 255, 255),
        )
        _rect(a, 5, 18, 7, 22, (60, 60, 70))
        _rect(a, 19, 18, 21, 22, (60, 60, 70))
        out.append(_ink(a))
    return out


def camera() -> list[Image.Image]:
    """A little camera; the second frame fires the flash (a white star on the flash window)."""
    out = []
    for f in range(3):
        a = _canvas(22, 18)
        _rect(a, 1, 5, 21, 17, (54, 58, 70))
        _rect(a, 4, 2, 10, 5, (54, 58, 70))
        _rect(a, 1, 8, 21, 10, (90, 96, 112))
        for y in range(8, 16):  # the lens
            for x in range(7, 16):
                if (x - 11) ** 2 + (y - 12) ** 2 <= 12:
                    _px(a, [(x, y)], (30, 34, 46) if (x - 11) ** 2 + (y - 12) ** 2 > 4 else (120, 170, 230))
        _rect(a, 16, 2, 20, 5, (255, 255, 230) if f == 1 else (190, 190, 170))
        img = _ink(a)
        if f == 1:  # the burst, outside the body
            big = _canvas(34, 30)
            big[6:24, 6:28] = np.asarray(img)
            _px(
                big,
                [(24, 0), (24, 1), (24, 2), (30, 5), (31, 5), (32, 5), (29, 1), (28, 2), (31, 9), (32, 10)],
                (255, 255, 210),
            )
            img = Image.fromarray(big, "RGBA")
        else:
            big = _canvas(34, 30)
            big[6:24, 6:28] = np.asarray(img)
            img = Image.fromarray(big, "RGBA")
        out.append(img)
    return out


def bucket() -> list[Image.Image]:
    """An orange pail (the R2 bucket's colour); little blocks drop into it."""
    out = []
    for f in range(4):
        a = _canvas(22, 26)
        for y in range(12, 26):  # the pail narrows to its base
            inset = (y - 12) // 4
            _rect(a, 2 + inset, y, 20 - inset, y + 1, (243, 128, 32) if y % 5 else (214, 98, 20))
        _rect(a, 2, 11, 20, 13, (255, 168, 72))
        for x in range(4, 19):  # the handle
            y = 3 + int(((x - 11) / 7.5) ** 2 * 7)
            _px(a, [(x, y)], (120, 120, 132))
        drop = [(9, 1 + f * 3), (13, -2 + f * 3)]
        for k, (x, y) in enumerate(drop):
            if y < 10:
                _rect(a, x, max(0, y), x + 3, max(0, y) + 3, [(96, 160, 255), (120, 210, 120)][k])
        out.append(_ink(a))
    return out


def sign_free() -> list[Image.Image]:
    """A wooden sign on a stick that says FREE; it wobbles."""
    out = []
    for f in range(2):
        a = _canvas(22, 22)
        _rect(a, 10, 9, 12, 22, (150, 98, 52))
        _rect(a, 1, 1 + f, 21, 11 + f, (236, 196, 120))
        _rect(a, 1, 9 + f, 21, 11 + f, (200, 156, 86))
        _text(a, 3, 3 + f, "FREE", (40, 150, 60))
        out.append(_ink(a))
    return out


def dog() -> list[Image.Image]:
    """A small sitting dog (Fred, transformed); the tail wags."""
    out = []
    for f in range(2):
        a = _canvas(26, 28)
        c, d = (196, 140, 84), (150, 100, 58)
        _rect(a, 6, 12, 18, 26, c)  # body
        _rect(a, 9, 3, 21, 13, c)  # head
        _rect(a, 18, 8, 24, 13, (222, 180, 130))  # muzzle
        _rect(a, 22, 8, 24, 10, (40, 30, 30))  # nose
        _rect(a, 8, 2, 11, 9, d)  # ear
        _px(a, [(16, 7), (16, 8)], (30, 24, 30))  # eye
        _rect(a, 8, 24, 11, 28, d)
        _rect(a, 14, 24, 17, 28, d)
        tail = [(3, 14), (2, 13), (1, 12)] if f == 0 else [(3, 17), (2, 17), (1, 18)]
        for x, y in tail:
            _rect(a, x, y, x + 3, y + 2, d)
        out.append(_ink(a))
    return out


def bird() -> list[Image.Image]:
    """A small round bird (Fred, transformed); it flaps."""
    out = []
    for f in range(2):
        a = _canvas(24, 22)
        for y in range(6, 20):
            for x in range(4, 20):
                if (x - 11.5) ** 2 / 64 + (y - 13) ** 2 / 49 <= 1:
                    _px(a, [(x, y)], (90, 170, 230) if y < 14 else (250, 236, 200))
        _rect(a, 19, 11, 23, 13, (250, 180, 40))  # beak
        _px(a, [(15, 10), (15, 11)], (25, 25, 35))
        wing = (
            [(6, 9), (7, 9), (8, 9), (5, 8), (4, 7)]
            if f == 0
            else [(6, 15), (7, 16), (8, 16), (5, 17), (4, 18)]
        )
        _px(a, wing, (50, 120, 190))
        _rect(a, 9, 19, 10, 22, (250, 180, 40))
        _rect(a, 13, 19, 14, 22, (250, 180, 40))
        out.append(_ink(a))
    return out


def book() -> list[Image.Image]:
    """An open book held up to read; a page turns (the middle frame)."""
    out = []
    for f in range(4):
        a = _canvas(26, 18)
        _rect(a, 1, 3, 25, 17, (58, 104, 190))  # the cover behind the pages
        _rect(a, 2, 2, 12, 15, (250, 247, 238))
        _rect(a, 14, 2, 24, 15, (244, 240, 228))
        _rect(a, 12, 2, 14, 16, (200, 196, 186))  # the spine
        for y in (5, 8, 11):
            _rect(a, 4, y, 11, y + 1, (150, 160, 180))
            _rect(a, 15, y, 22 - (y == 11) * 3, y + 1, (150, 160, 180))
        if f == 2:  # a page mid-turn
            _rect(a, 13, 0, 19, 13, (255, 255, 250))
        out.append(_ink(a))
    return out


def censor() -> list[Image.Image]:
    """A black censor bar with a white outline: slammed over his eyes (the API key he must not see)."""
    a = _canvas(20, 6)
    _rect(a, 0, 0, 20, 6, (245, 245, 245))
    _rect(a, 1, 1, 19, 5, (12, 12, 14))
    return [Image.fromarray(a, "RGBA")]


ITEMS: dict[str, Callable[[], list[Image.Image]]] = {
    "popcorn": popcorn,
    "tv": tv,
    "camera": camera,
    "bucket": bucket,
    "free": sign_free,
    "dog": dog,
    "bird": bird,
    "censor": censor,
    "book": book,
}
# size over Fred's own pixel size, before the reel's gag_scale: the camera's canvas holds its flash burst
SCALE = {"camera": 0.65, "censor": 0.75, "dog": 1.35, "bird": 1.35}  # r06: the swaps read tiny
FPS = {
    "popcorn": 6,
    "tv": 8,
    "camera": 6,
    "bucket": 6,
    "free": 4,
    "dog": 6,
    "bird": 8,
    "censor": 1,
    "book": 3,
}
PLACE = {
    "popcorn": "held",
    "tv": "left",
    "camera": "held",
    "bucket": "left",
    "free": "left",
    "dog": "swap",
    "bird": "swap",
    "censor": "face",
    "book": "held",
}


def frames(name: str) -> list[Image.Image]:
    if name not in ITEMS:
        raise ValueError(f"unknown gag item {name!r} (create/pixel/items.py: {', '.join(ITEMS)})")
    return ITEMS[name]()
