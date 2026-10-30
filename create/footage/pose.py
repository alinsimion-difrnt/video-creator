"""The presenter's pose on a take (ADR 0030): 33 body points per sampled frame, from MediaPipe BlazePose.

The model is the BlazePose full-body landmark model as ONNX from the OpenCV zoo
(`pose_estimation_mediapipe_2023mar`, Apache-2.0, external-facts §19), run locally with `cv2.dnn`: no API. It
needs a square crop around the person. The zoo's demo gets it from a person detector; a seated presenter is
upright, still and found by the face model already, so the crop is one fixed square around the chair
from the median face (`box_face_heights`). Each hand is then found again at full resolution by the hand model,
tracking itself from its last points and seeded by the body pose.

Points are BlazePose's (0 nose ... 11/12 shoulders, 13/14 elbows, 15/16 wrists, 17-22 hand points, 23/24 hips,
25/26 knees, 27/28 ankles; odd = the person's left, which is the right of the screen when they face us),
in master pixels, with a visibility in 0..1. Tracks are cached by master, span and model
(data/create/_cache/pose/).

Uses: a prop that follows the presenter's hands (`follow: hand`), and effects drawn on a limb (`automail`).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from create.footage.reframe import ensure_model
from lens.schemas.config import FootagePose

INPUT = 256
# BlazePose indices by the person's side
LIMBS = {  # root joint, middle joint, end joint, tip (index finger, toe)
    "right_arm": (12, 14, 16, 20),
    "left_arm": (11, 13, 15, 19),
    "right_leg": (24, 26, 28, 32),
    "left_leg": (23, 25, 27, 31),
}
HAND = {"right": (16, 18, 20), "left": (15, 17, 19)}  # wrist, pinky, index: the palm is their mean

Points = list[list[float]]  # 33 x [x, y, visibility]


def _net(model: Path) -> Any:
    import cv2

    return cv2.dnn.readNet(str(model))


def landmarks(net: Any, img: np.ndarray, box: tuple[float, float, float]) -> tuple[Points, float] | None:
    """Pose in a square crop (centre x, centre y, side) of `img` (BGR): 33 points in image pixels and the
    model's confidence, or None when the crop is empty."""
    import cv2

    cx, cy, side = box
    h, w = img.shape[:2]
    x0, y0 = round(cx - side / 2), round(cy - side / 2)
    s = max(8, round(side))
    crop = np.zeros((s, s, 3), dtype=img.dtype)  # padded with black where the square leaves the frame
    sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(w, x0 + s), min(h, y0 + s)
    if sx1 <= sx0 or sy1 <= sy0:
        return None
    crop[sy0 - y0 : sy1 - y0, sx0 - x0 : sx1 - x0] = img[sy0:sy1, sx0:sx1]
    blob = cv2.cvtColor(cv2.resize(crop, (INPUT, INPUT), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
    net.setInput((blob.astype(np.float32) / 255.0)[None])
    out = net.forward(net.getUnconnectedOutLayersNames())
    pts, conf = out[0][0].reshape(-1, 5), float(np.asarray(out[1]).ravel()[0])
    k = s / INPUT
    vis = 1 / (1 + np.exp(-pts[:33, 3]))
    xy = pts[:33, :2] * k + np.array([x0, y0])
    return [
        [round(float(x), 1), round(float(y), 1), round(float(v), 3)]
        for (x, y), v in zip(xy, vis, strict=True)
    ], conf


HAND_IN = 224
PALM_IDS = (0, 5, 9, 13, 17)  # the hand model's wrist and finger roots: their mean is the palm's centre
PALM_INDEX = {"right": 33, "left": 34}  # where `track` stores the refined palms after the 33 body points


def hand_crop(centre: tuple[float, float], angle: float, side: float) -> np.ndarray:
    """The affine map from the frame to the hand model's 224 x 224 input: a square of `side` around
    `centre`, turned by `angle` degrees so the hand points up (the hand ROI, as MediaPipe Holistic does)."""
    import cv2

    cx, cy = centre
    m = cv2.getRotationMatrix2D((cx, cy), angle, HAND_IN / side)
    m[0, 2] += HAND_IN / 2 - cx
    m[1, 2] += HAND_IN / 2 - cy
    return m


def hand_landmarks(
    net: Any, img: np.ndarray, centre: tuple[float, float], angle: float, side: float
) -> tuple[list[list[float]], float]:
    """21 hand points (frame pixels) and the model's confidence, in one crop."""
    import cv2

    m = hand_crop(centre, angle, side)
    crop = cv2.warpAffine(img, m, (HAND_IN, HAND_IN), flags=cv2.INTER_AREA, borderValue=(0, 0, 0))
    blob = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    net.setInput(blob[None])
    out = net.forward(net.getUnconnectedOutLayersNames())
    pts = np.asarray(out[0]).reshape(-1, 3)[:, :2]
    conf = float(np.asarray(out[1]).ravel()[0])
    inv = cv2.invertAffineTransform(m)
    xy = pts @ inv[:, :2].T + inv[:, 2]
    return [[round(float(x), 1), round(float(y), 1)] for x, y in xy], conf


def hand_seeds(
    wrist: tuple[float, float], knuckles: tuple[float, float], min_side: float, scale: float
) -> list[tuple[tuple[float, float], float, float]]:
    """Crops to try for a hand (centre, angle, side): along wrist -> knuckles when they are far enough apart
    to give a direction; a palm-up or end-on hand bunches them together (v22: 15 px apart, a 60 px crop
    that saw nothing), so the crop is at least `min_side` and four turns are tried."""
    wx, wy = wrist
    kx, ky = knuckles
    d = math.hypot(kx - wx, ky - wy)
    side = max(d * scale, min_side)
    if d * scale >= min_side:
        angle = math.degrees(math.atan2(kx - wx, -(ky - wy)))
        return [((wx + (kx - wx) * 0.9, wy + (ky - wy) * 0.9), angle, side)]
    base = math.degrees(math.atan2(kx - wx, -(ky - wy))) if d > 1 else 0.0
    centre = ((wx + kx) / 2, (wy + ky) / 2)
    return [(centre, base + turn, side) for turn in (0, 180, 90, -90)]


def refine_hands(
    hnet: Any,
    img: np.ndarray,
    pts: Points | None,
    prev: dict[str, list[list[float]] | None],
    cfg: FootagePose,
    face_h: float,
) -> dict[str, list[list[float]] | None]:
    """Each hand's 21 points where the hand model is sure (`hand_min_conf`), else None.

    The body model sees a hand as ~10 px of its 256 px crop (v22: a palm ~250 px off on 4K); the hand model
    sees it at 224 px. Its crop comes first from the hand's own last points (it tracks itself, as MediaPipe's
    hand tracker does: the body pose broke down in a deep lean while both hands stayed in plain sight), then
    from the body's wrist and knuckles."""
    min_side = cfg.hand_min_face * face_h
    out: dict[str, list[list[float]] | None] = {}
    for side, (w, p, i) in HAND.items():
        seeds = []
        last = prev.get(side)
        if last is not None:  # wrist and the middle of the finger roots of the last hand
            kn = ((last[5][0] + last[17][0]) / 2, (last[5][1] + last[17][1]) / 2)
            seeds += hand_seeds((last[0][0], last[0][1]), kn, min_side, cfg.hand_scale)[:1]
        if pts is not None and min(pts[w][2], pts[p][2], pts[i][2]) >= 0.3:
            kn = ((pts[p][0] + pts[i][0]) / 2, (pts[p][1] + pts[i][1]) / 2)
            seeds += hand_seeds((pts[w][0], pts[w][1]), kn, min_side, cfg.hand_scale)
        out[side] = None
        best = 0.0
        for centre, angle, sz in seeds:
            lm, conf = hand_landmarks(hnet, img, centre, angle, sz)
            if conf >= cfg.hand_min_conf and conf > best:
                out[side], best = lm, conf
                if conf > 0.9:  # sure enough: skip the other turns
                    break
    return out


def fixed_box(face: tuple[float, float, float, float], cfg: FootagePose) -> tuple[float, float, float]:
    """A seated presenter in a static shot stays in one place: one generous square around the chair, from
    the median face. A crop that follows the last pose shrank with a bad pose and lost him in a lean (v22)."""
    cx, cy, _, fh = face
    return (cx, cy + cfg.body_below_face * fh, cfg.box_face_heights * fh)


def track(
    master: Path,
    t0: float,
    t1: float,
    face: tuple[float, float, float, float],
    root: Path,
    cfg: FootagePose,
) -> list[tuple[float, Points | None]]:
    """(source time, 33 points or None) every 1/sample_fps s of `master` from t0 to t1 (cached)."""
    import cv2

    model = ensure_model(root, cfg)
    hand = {"model": cfg.hand_model, "model_url": cfg.hand_model_url, "model_sha256": cfg.hand_model_sha256}
    hmodel = ensure_model(root, cfg.model_copy(update=hand))
    st = master.stat()
    key = hashlib.sha256(
        json.dumps([str(master), st.st_size, st.st_mtime, t0, t1, face, cfg.model_dump()]).encode()
    ).hexdigest()[:16]
    cache = root / "data" / "create" / "_cache" / "pose" / f"{key}.json"
    if cache.exists():
        return [(t, p) for t, p in json.loads(cache.read_text())]
    net, hnet = _net(model), _net(hmodel)
    cap = cv2.VideoCapture(str(master))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, round(fps / cfg.sample_fps))
    f0, f1 = math.floor(t0 * fps), math.ceil(t1 * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, f0)
    box = fixed_box(face, cfg)
    out: list[tuple[float, Points | None]] = []
    last_hands: dict[str, list[list[float]] | None] = {}
    last_body: Points | None = None
    for i in range(f0, f1 + 1):
        if not cap.grab():
            break
        if (i - f0) % step:
            continue
        _, img = cap.retrieve()
        got = landmarks(net, img, box)
        body = got[0] if got is not None and got[1] >= cfg.min_conf else None
        hands = refine_hands(hnet, img, body, last_hands, cfg, face[3])
        last_hands = hands
        if body is None:  # the body is lost: keep its last pose (invisible) so the hands can still be used
            if last_body is None or not any(hands.values()):
                out.append((round(i / fps, 3), None))
                continue
            body = [[x, y, 0.0] for x, y, _ in last_body[:33]]
        last_body = body
        pts = [list(q) for q in body[:33]]
        for side in PALM_INDEX:  # the hand model's palm (visibility 1) or the body's guess (at most 0.5)
            lm = hands[side]
            if lm is not None:
                px = sum(lm[j][0] for j in PALM_IDS) / 5
                py = sum(lm[j][1] for j in PALM_IDS) / 5
                pts.append([round(px, 1), round(py, 1), 1.0])
            else:
                x, y, v = palm(pts, side)
                pts.append([round(x, 1), round(y, 1), round(min(v, 0.5), 3)])
        out.append((round(i / fps, 3), pts))
    cap.release()
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_suffix(".tmp")
    tmp.write_text(json.dumps(out))
    tmp.replace(cache)
    return out


def palm(pts: Points, side: str) -> tuple[float, float, float]:
    """A hand's palm: the hand model's palm centre when `track` stored one (points 33, 34), else the mean of
    the body model's wrist, pinky and index; and its visibility."""
    if len(pts) > PALM_INDEX[side]:
        x, y, v = pts[PALM_INDEX[side]]
        return (x, y, v)
    ids = HAND[side]
    return (
        sum(pts[i][0] for i in ids) / 3,
        sum(pts[i][1] for i in ids) / 3,
        min(pts[i][2] for i in ids),
    )


def smooth(xs: list[float], window: int) -> list[float]:
    """A centred median of 5 (one wrong frame in a fast lean is dropped, v22: a palm jumped 500 px and
    back), then a moving average of `window` samples (no jitter frame to frame)."""
    if len(xs) < 3:
        return list(xs)
    med = [sorted(xs[max(0, k - 2) : k + 3])[len(xs[max(0, k - 2) : k + 3]) // 2] for k in range(len(xs))]
    if window <= 1:
        return med
    h = window // 2
    return [
        sum(med[max(0, k - h) : k + h + 1]) / len(med[max(0, k - h) : k + h + 1]) for k in range(len(med))
    ]


def lead_path(
    samples: list[tuple[float, Points | None]], left: bool, window: int = 5
) -> list[tuple[float, float]]:
    """The leading hand's x over the samples: the palm furthest toward `left` (or right), median-filtered over
    `window` samples so one wrong frame cannot throw a fleeing prop; gaps hold the last value."""
    xs: list[tuple[float, float]] = []
    last: float | None = None
    for t, p in samples:
        if p is not None:
            seen = [palm(p, s)[0] for s in ("left", "right") if palm(p, s)[2] > 0.2]
            if seen:
                last = min(seen) if left else max(seen)
        if last is not None:
            xs.append((t, last))
    h = window // 2
    vals = [x for _, x in xs]
    return [
        (t, sorted(vals[max(0, k - h) : k + h + 1])[len(vals[max(0, k - h) : k + h + 1]) // 2])
        for k, (t, _) in enumerate(xs)
    ]


def hand_path(
    samples: list[tuple[float, Points | None]], start: tuple[float, float], window: int, pick: str = "lowest"
) -> tuple[str, list[tuple[float, float, float]]]:
    """The hand that puts the prop down: the one that reaches lowest in the span (v22: the nearest hand at
    the start went to his knee while the other set Fred on the floor); on a tie, the one nearest `start`.
    Its palm (time, x, y) over the samples, smoothed; gaps (lost frames, a hidden hand) hold."""
    first = next((p for _, p in samples if p is not None), None)
    if first is None:
        return "right", []

    def lowest(s: str) -> float:  # the mean of its three lowest points: one wrong frame cannot decide it
        ys = sorted(
            (palm(p, s)[1] for _, p in samples if p is not None and palm(p, s)[2] > 0.2), reverse=True
        )
        return sum(ys[:3]) / max(1, len(ys[:3]))

    def mean_y(s: str) -> float:  # the lower hand on average: the one held out palm up (`follow: palm`)
        ys = [palm(p, s)[1] for _, p in samples if p is not None and palm(p, s)[2] > 0.2]
        return sum(ys) / max(1, len(ys))

    measure = mean_y if pick == "lower" else lowest
    side = max(
        ("right", "left"), key=lambda s: (round(measure(s) / 20), -math.dist(palm(first, s)[:2], start))
    )
    path: list[tuple[float, float, float]] = []
    last: tuple[float, float] | None = None
    for t, p in samples:
        if p is not None and palm(p, side)[2] > 0.2:
            last = palm(p, side)[:2]
        if last is not None:
            path.append((t, last[0], last[1]))
    xs, ys = smooth([p[1] for p in path], window), smooth([p[2] for p in path], window)
    return side, [(t, round(x, 1), round(y, 1)) for (t, _, _), x, y in zip(path, xs, ys, strict=True)]


def limb_path(
    samples: list[tuple[float, Points | None]], limb: str, window: int
) -> list[tuple[float, list[tuple[float, float]]]]:
    """A limb's joints (shoulder/hip, elbow/knee, wrist/ankle, finger/toe) over the samples, smoothed; gaps
    hold the last pose."""
    ids = LIMBS[limb]
    rows: list[tuple[float, list[tuple[float, float]]]] = []
    last: list[tuple[float, float]] | None = None
    for t, p in samples:
        if p is not None and min(p[i][2] for i in ids[:3]) > 0.2:
            last = [(p[i][0], p[i][1]) for i in ids]
        if last is not None:
            rows.append((t, last))
    n = len(ids)
    cols = [smooth([r[1][j][c] for r in rows], window) for j in range(n) for c in range(2)]
    return [
        (t, [(round(cols[2 * j][k], 1), round(cols[2 * j + 1][k], 1)) for j in range(n)])
        for k, (t, _) in enumerate(rows)
    ]
