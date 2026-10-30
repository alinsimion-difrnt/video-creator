"""Bullet time from one frame (tournament n05): a depth map of a still (Depth Anything V2 Small, ONNX,
Apache-2.0, run locally) and a 2.5D camera move rendered from it: near pixels shift more than far ones, so a
small orbit and push read as a camera moving round a frozen moment."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np

MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def depth(rgb: np.ndarray, model: Path, side: int) -> np.ndarray:
    """Relative nearness of each pixel (0 far .. 1 near), the image's size. The model runs on a `side` px
    wide copy (heights a multiple of its 14 px patch) and the map is resized back."""
    import cv2
    import onnxruntime as ort

    h, w = rgb.shape[:2]
    sh = max(14, round(side * h / w / 14) * 14)
    x = cv2.resize(rgb, (side, sh), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255.0
    x = ((x - MEAN) / STD).transpose(2, 0, 1)[None].astype(np.float32)
    sess = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
    d = sess.run(None, {sess.get_inputs()[0].name: x})[0][0]
    d = (d - d.min()) / max(1e-6, float(d.max() - d.min()))
    return np.asarray(cv2.resize(d.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR))


def warp(rgb: np.ndarray, near: np.ndarray, dx: float, dy: float, zoom: float) -> np.ndarray:
    """The image seen from a camera moved by (dx, dy) px for the nearest pixels (farther ones less, by
    `near`) and pushed in by `zoom` about the centre. Backward mapping: each output pixel samples the image
    where it came from; the stretch at depth edges hides the missing background."""
    import cv2

    h, w = near.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    sx = cx + (xx - cx) / zoom - dx * near
    sy = cy + (yy - cy) / zoom - dy * near
    return cv2.remap(rgb, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def orbit(n: int, amp: float, push: float) -> list[tuple[float, float, float]]:
    """(dx, dy, zoom) for n frames: an arc that eases out and back (the camera swings round and settles)
    while it pushes in a little."""
    out = []
    for k in range(n):
        u = k / max(1, n - 1)
        s = math.sin(math.pi * u)
        out.append(
            (
                amp * math.sin(math.pi * (u - 0.5)),
                -0.25 * amp * s,
                1 + push * (0.5 - 0.5 * math.cos(math.pi * u)),
            )
        )
    return out


def time_look(rgb: np.ndarray, drain: float, cool: float, vignette: float) -> np.ndarray:
    """Frozen time looks unlike live time: colour drained toward grey by `drain`, a cool cast, a vignette."""
    x = rgb.astype(np.float32)
    grey = x.mean(axis=2, keepdims=True)
    x = x * (1 - drain) + grey * drain
    x[..., 2] *= 1 + cool
    x[..., 0] *= 1 - cool * 0.6
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
    x *= (1 - vignette * np.clip(r - 0.35, 0, 1) / 0.65)[..., None]
    return np.clip(x, 0, 255).astype(np.uint8)
