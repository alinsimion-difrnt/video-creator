"""What an annotator sees for one TikTok (studies/README.md, "Annotate"): a contact sheet of evenly spaced
frames, a 0-3 s hook strip, the transcript and the measured numbers, all under data/study/tiktok/work/<id>/
(third-party frames and words: never committed). `allowed_times` is every time a note may use."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from lens.media import probe
from study.tiktok.config import MEDIA, STUDY, StudyConfig

THUMB_W = 216


def sheet_times(duration: float, n: int) -> list[float]:
    """n times spread over the video, the first at 0 and the last just before the end."""
    if n <= 1:
        return [0.0]
    end = max(0.0, duration - 0.1)
    return [round(end * i / (n - 1), 2) for i in range(n)]


def hook_times(window_s: float, n: int) -> list[float]:
    return [round(window_s * i / n, 2) for i in range(n)]


def _frame(src: Path, t: float, w: int, h: int) -> Image.Image:
    import subprocess

    out = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            f"{t:.3f}",
            "-i",
            str(src),
            "-frames:v",
            "1",
            "-vf",
            f"scale={w}:{h}",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        capture_output=True,
        check=False,
    )
    if len(out.stdout) < w * h * 3:
        return Image.new("RGB", (w, h), (40, 40, 40))
    return Image.frombytes("RGB", (w, h), out.stdout[: w * h * 3])


def _strip(src: Path, times: list[float], cols: int, aspect: float) -> Image.Image:
    w, h = THUMB_W, round(THUMB_W * aspect)
    rows = -(-len(times) // cols)
    img = Image.new("RGB", (cols * w, rows * (h + 22)), (18, 18, 22))
    d = ImageDraw.Draw(img)
    for i, t in enumerate(times):
        x, y = (i % cols) * w, (i // cols) * (h + 22)
        img.paste(_frame(src, t, w, h), (x, y + 22))
        d.text((x + 6, y + 4), f"{t:.2f}s", fill=(255, 220, 120))
    return img


def build(vid: str, cfg: StudyConfig) -> Path:
    src = MEDIA / f"{vid}.cut.mp4" if (MEDIA / f"{vid}.cut.mp4").exists() else MEDIA / f"{vid}.mp4"
    work = MEDIA / "work" / vid
    work.mkdir(parents=True, exist_ok=True)
    p = probe(src)
    aspect = (p.height or 1024) / (p.width or 576)
    st = sheet_times(p.duration_s, cfg.notes.sheet_frames)
    ht = hook_times(cfg.measure.hook_window_s, cfg.notes.hook_frames)
    _strip(src, st, 6, aspect).save(work / "sheet.jpg", quality=82)
    _strip(src, ht, 8, aspect).save(work / "hook.jpg", quality=82)
    measure = json.loads((STUDY / "measure" / f"{vid}.json").read_text())
    allowed = sorted(
        {*st, *ht, *measure["times"]["cuts"], *measure["times"]["events"], *measure["times"]["punches"]}
    )
    (work / "packet.json").write_text(
        json.dumps(
            {
                "id": vid,
                "sheet_times": st,
                "hook_times": ht,
                "cut_times": measure["times"]["cuts"],
                "event_times": measure["times"]["events"],
                "punch_times": measure["times"]["punches"],
                "allowed_times": allowed,
            },
            indent=1,
        )
    )
    return work


def allowed_times(vid: str) -> list[float]:
    data: list[float] = json.loads((MEDIA / "work" / vid / "packet.json").read_text())["allowed_times"]
    return data
