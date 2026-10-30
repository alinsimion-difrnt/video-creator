"""Screenshots of a rendered reel for a review round: a contact sheet and motion strips.

    uv run python scripts/reel_shots.py --project <p> --video data/.../rNN.mp4 --out data/.../rNN
        [--every 1.5]

Writes `<out>-sheet.jpg` (a frame every `--every` s, stamped with its time and the word being said) and
`<out>-study*.jpg` (create/lab.py's motion strips: 8 frames 0.1 s apart around every prop beat, cropped to the
prop). The reel data is the last `create reel` build of the project (data/create/<p>/render/reel/).
    Media: data/.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from create import lab
from lens.config import REPO_ROOT


def sheet(video: Path, words: list[dict], out: Path, every: float, cols: int = 10, tile_w: int = 216) -> Path:
    dur = float(
        subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        str(video)], capture_output=True, text=True, check=True).stdout
    )  # fmt: skip
    tmp = out.parent / ".sheet"
    tmp.mkdir(parents=True, exist_ok=True)
    tiles = []
    t = 0.2
    while t < dur:
        png = tmp / f"t{t:07.2f}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                        "-vf", f"scale={tile_w}:-2", str(png)], check=False)  # fmt: skip
        if png.exists():
            im = Image.open(png).convert("RGB")
            said = next((w["text"] for w in words if w["start_s"] <= t <= w["end_s"] + 0.15), "")
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, tile_w, 16), fill=(0, 0, 0))
            d.text((3, 2), f"{t:5.1f}s {said}"[:34], fill=(255, 210, 0))
            tiles.append(im)
        t += every
    th = tiles[0].height
    rows = (len(tiles) + cols - 1) // cols
    img = Image.new("RGB", (cols * tile_w, rows * th), (20, 20, 20))
    for k, im in enumerate(tiles):
        img.paste(im, ((k % cols) * tile_w, (k // cols) * th))
    img.save(out, quality=88)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True, help="path prefix for the images")
    ap.add_argument("--every", type=float, default=1.5)
    a = ap.parse_args()
    video, out = Path(a.video), Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    words = json.loads((REPO_ROOT / "projects" / a.project / "timeline.json").read_text())["words"]
    print(sheet(video, words, Path(f"{out}-sheet.jpg"), a.every))
    data = json.loads((REPO_ROOT / "data/create" / a.project / "render/reel/reel-data.json").read_text())
    probe = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width",
        "-of",
        "csv=p=0",
    ]
    w = int(subprocess.run([*probe, str(video)], capture_output=True, text=True, check=True).stdout)
    print(lab.study(video, data, Path(f"{out}-study.jpg"), scale=w / 1080))


if __name__ == "__main__":
    main()
