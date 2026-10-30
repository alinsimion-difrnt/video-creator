"""Check the presenter's pose on real frames: skeleton, hand points and palms drawn on a contact sheet.

    uv run python scripts/pose_check.py --master data/create/<p>/footage/master/take1.mov \
        --from 104.0 --to 106.6 --face 2138,822,153,184 --out data/pose-check.jpg [--every 4]
        [--crop x0,y0,x1,y1]

Each tile is a sampled frame (time stamped): the body model's limbs in white, the hand model's 21 points in
cyan (a sure hand) and each palm as a disc: green from the hand model, orange when it fell back to the body
model's guess. Tracking bugs are judged here, on the frames, not on a render (ADR 0030). Media: data/ only.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from create.footage import pose as ps
from lens.config import REPO_ROOT, load_config

BONES = [(11, 13), (13, 15), (12, 14), (14, 16), (11, 12), (11, 23), (12, 24), (23, 24), (23, 25), (25, 27),
         (24, 26), (26, 28)]  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--from", dest="t0", type=float, required=True)
    ap.add_argument("--to", dest="t1", type=float, required=True)
    ap.add_argument("--face", required=True, help="centre x, centre y, width, height on the master")
    ap.add_argument("--out", required=True)
    ap.add_argument("--every", type=int, default=4, help="draw every n-th sample")
    ap.add_argument("--crop", help="x0,y0,x1,y1 of the master to show (default: a box around the body)")
    ap.add_argument("--cols", type=int, default=6)
    a = ap.parse_args()
    cfg = load_config().create.footage.pose
    face = tuple(float(v) for v in a.face.split(","))
    master = Path(a.master)
    samples = ps.track(master, a.t0, a.t1, face, REPO_ROOT, cfg)  # type: ignore[arg-type]
    cap = cv2.VideoCapture(str(master))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    tiles = []
    for t, pts in samples[:: a.every]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, round(t * fps))
        ok, img = cap.read()
        if not ok:
            continue
        if pts is not None:
            for i, j in BONES:
                p, q = pts[i], pts[j]
                cv2.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), (255, 255, 255), 6)
            for side in ("right", "left"):
                x, y, v = ps.palm(pts, side)
                col = (0, 200, 0) if v >= 1 else (0, 140, 255)
                cv2.circle(img, (int(x), int(y)), 22, col, -1)
                cv2.putText(img, side[0].upper(), (int(x) + 26, int(y)), 0, 2.0, col, 5)
        if a.crop:
            x0, y0, x1, y1 = (int(v) for v in a.crop.split(","))
        else:
            cx, cy, _, fh = face
            x0, x1 = int(cx - 5 * fh), int(cx + 5 * fh)
            y0, y1 = int(cy - 1.5 * fh), int(cy + 8 * fh)
        h, w = img.shape[:2]
        tile = img[max(0, y0) : min(h, y1), max(0, x0) : min(w, x1)]
        tile = cv2.resize(tile, (360, round(360 * tile.shape[0] / tile.shape[1])))
        cv2.putText(tile, f"{t:.2f}", (8, 30), 0, 0.9, (0, 0, 255), 2)
        if pts is None:
            cv2.putText(tile, "LOST", (8, 64), 0, 1.0, (0, 0, 255), 2)
        tiles.append(tile)
    cap.release()
    th = max(t.shape[0] for t in tiles)
    rows = [tiles[k : k + a.cols] for k in range(0, len(tiles), a.cols)]
    sheet = np.vstack(
        [
            np.hstack([cv2.copyMakeBorder(t, 0, th - t.shape[0], 0, 0, cv2.BORDER_CONSTANT) for t in r]
                      + [np.zeros((th, 360, 3), np.uint8)] * (a.cols - len(r)))
            for r in rows
        ]
    )  # fmt: skip
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(a.out, sheet)
    print(a.out)


if __name__ == "__main__":
    main()
