"""A cover image for a finished video (`create cover <p> --video f.mp4 --title "..."`).

A frame of the video (the presenter, graded like the reel) with the hook as a big title inside the frame's
`cover_safe` rect (config create.design.frames): the platforms crop covers to 1:1, 4:5 or 3:4 in grids and
profiles, so the title sits where every crop keeps it. `**word**` in the title takes the brand accent. The
page is rendered with the brand's fonts and screenshotted at the frame's size (PNG).

`--split` is the cover for a presenter video on a split base (the panel route, ADR 0034): the title on the
brand's paper above the seam, the presenter untouched below it. `--onto` writes it as the video's first frame,
the thumbnail the platforms show by default.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from pathlib import Path

import yaml

from create.bundle import fonts
from lens.schemas.config import LensConfig
from lens.schemas.create import Tokens

KIT = Path(__file__).parent / "kit"


def title_html(title: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(title))


def title_size(title: str, width: int) -> int:
    """A size that fits the longest word on one line and the title on about three lines."""
    plain = re.sub(r"\*\*", "", title)
    longest = max((len(w) for w in plain.split()), default=1)
    by_word = width / (0.62 * max(longest, 1))
    by_lines = (3 * width) / (0.58 * max(len(plain), 1))
    return int(max(64, min(150, by_word, by_lines)))


def title_top(box_y0: int, box_y1: int, chin: float | None, need: int) -> int:
    """Below the chin when the cover-safe rect has room for the title there, else at its top."""
    if chin is not None and chin + 40 + need <= box_y1:
        return int(max(box_y0, chin + 40))
    return box_y0 + 40


def plan_seam(base: Path, plan: Path | None = None) -> int:
    """The split seam of the video's plan (default projects/<p>/reel-base.yaml), else the plan default."""
    from lens.schemas.create import ReelPlan

    path = plan or base / "reel-base.yaml"
    if path.exists():
        return ReelPlan.model_validate(yaml.safe_load(path.read_text())).split_seam
    return int(ReelPlan.model_fields["split_seam"].default)


def split_layout(seam: int, logo_h: int) -> tuple[int, int]:
    """(the logo's top, the bottom of the title block), both above the seam."""
    logo_y = seam - logo_h - 54
    return logo_y, logo_y - 30


# the title shrinks 2 px at a time until the block's top clears the cover-safe rect (never under 72 px)
FIT_JS = """() => { const w = document.getElementById('wrap'), h = w.querySelector('h1');
  const over = () => w.firstElementChild.getBoundingClientRect().top < w.getBoundingClientRect().top - 0.5;
  let s = parseFloat(getComputedStyle(h).fontSize);
  while (s > 72 && over()) { s -= 2; h.style.fontSize = s + 'px'; }
  return over() ? 0 : s; }"""


def _fonts(root: Path, tokens: Tokens, work: Path) -> None:
    (work / "fonts").mkdir(parents=True, exist_ok=True)
    css, files = fonts(root / "data" / "create" / "_cache", tokens.fonts_css)
    for f in files:
        shutil.copy(f, work / "fonts" / f.name)
    (work / "fonts.css").write_text(css)  # its urls point at fonts/<file>


def _grab(video: Path, at: float, out: Path) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", str(video), "-frames:v", "1",
                    "-q:v", "2", str(out)], check=True)  # fmt: skip


def _shoot(page: Path, width: int, height: int, target: Path, fit: str = "") -> Path:
    from playwright.sync_api import sync_playwright

    from create.browser import launch

    with sync_playwright() as pw:
        browser = launch(pw)
        pg = browser.new_page(viewport={"width": width, "height": height})
        pg.goto(page.as_uri())
        pg.evaluate("document.fonts.ready")
        if fit and not pg.evaluate(fit):
            browser.close()
            raise ValueError("the title does not fit above the logo in the cover-safe rect even at 72 px: "
                             "shorten it (write-post: 6 words at most) or drop --sub")  # fmt: skip
        pg.screenshot(path=str(target))
        browser.close()
    return target


def run_split_cover(
    root: Path, project: str, video: Path | None, title: str, cfg: LensConfig, at: float = 1.0,
    kicker: str = "", sub: str = "", icon: Path | None = None, out: Path | None = None,
    plan: Path | None = None,
) -> Path:  # fmt: skip
    """The title above the seam of a split render (the panel's base, or a kit plan's split layout via `plan`),
    the presenter as he is below it."""
    base = root / "projects" / project
    video = video or root / "data" / "create" / project / "render" / f"{project}-base.mp4"
    if not video.exists():
        raise FileNotFoundError(f"{video}: render the split base first, or pass --video")
    tokens = Tokens.model_validate(json.loads((base / "tokens.json").read_text()))
    brand = str((yaml.safe_load((base / "brief.yaml").read_text()) or {}).get("brand", ""))
    frame = cfg.create.design.frames[tokens.frame]
    work = root / "data" / "create" / project / "render" / "cover-split"
    _fonts(root, tokens, work)
    _grab(video, at, work / "frame.png")
    shutil.copy(root / "brands" / brand / tokens.logo.primary, work / "logo.svg")
    kick = html.escape(kicker)
    if icon is not None:
        shutil.copy(icon, work / f"icon{icon.suffix}")
        kick = f'<img src="icon{icon.suffix}" alt="">{kick}'
    seam = plan_seam(base, plan)
    logo_y, bottom = split_layout(seam, tokens.logo.min_height_corner)
    box = frame.cover_safe or frame.safe[0]  # the grid crops keep only this: the block grows up from the logo
    c, fam = tokens.colors, tokens.families
    size = title_size(title, box.x1 - box.x0)  # the start; FIT_JS shrinks it to the band
    v = {
        "--w": f"{frame.width}px", "--h": f"{frame.height}px", "--seam": f"{seam}px", "--x0": f"{box.x0}px",
        "--tw": f"{box.x1 - box.x0}px", "--y0": f"{box.y0}px", "--band": f"{bottom - box.y0}px",
        "--logo-y": f"{logo_y}px", "--size": f"{size}px",
        "--logo-h": f"{tokens.logo.min_height_corner}px", "--paper": c["canvas"], "--dots": c["hairline"],
        "--ink": c["ink"], "--accent": c["accent"], "--lede": c.get("ink_lede", c["ink_muted"]),
        "--heading": f'"{fam["heading"].family}", {fam["heading"].fallback}',
        "--body": f'"{fam["body"].family}", {fam["body"].fallback}',
    }  # fmt: skip
    page = (KIT / "cover-split.html").read_text()
    for key, val in {
        "{{LANG}}": str((yaml.safe_load((base / "brief.yaml").read_text()) or {}).get("language", "en")),
        "{{TITLE}}": title_html(title),
        "{{KICK}}": f'<span class="kick">{kick}</span>' if kick else "",
        "{{SUB}}": f'<p class="sub">{html.escape(sub)}</p>' if sub else "",
        "{{CSS_VARS}}": ":root{" + ";".join(f"{k}:{x}" for k, x in v.items()) + "}",
    }.items():  # fmt: skip
        page = page.replace(key, val)
    (work / "index.html").write_text(page)
    target = out or root / "data" / "create" / project / f"{project}-cover.png"
    return _shoot(work / "index.html", frame.width, frame.height, target, FIT_JS)


def onto_first_frame(cover: Path, video: Path, crf: int) -> Path:
    """<video>-cover.mp4: the video with the cover as its first frame, the thumbnail the platforms show by
    default; same length and sound (the cover replaces frame 0, nothing is inserted)."""
    out = video.with_name(f"{video.stem}-cover.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(cover),
         "-filter_complex", "[0:v][1:v]overlay=0:0:enable='eq(n,0)'[v]",
         "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
         "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(out)],
        check=True,
    )  # fmt: skip
    meta = video.with_suffix(".meta.json")
    if meta.exists():
        shutil.copy(meta, out.with_suffix(".meta.json"))
    return out


def run_cover(
    root: Path, project: str, video: Path | None, title: str, cfg: LensConfig, at: float = 1.0, tag: str = "",
    out: Path | None = None,
) -> Path:  # fmt: skip
    base = root / "projects" / project
    clean = root / "data" / "create" / project / "footage" / "edited" / f"{project}-edited.mp4"
    video = video or clean  # the edit without captions or graphics: a cover has its own title
    tokens = Tokens.model_validate(json.loads((base / "tokens.json").read_text()))
    frame = cfg.create.design.frames[tokens.frame]
    box = frame.cover_safe or frame.safe[0]
    work = root / "data" / "create" / project / "render" / "cover"
    _fonts(root, tokens, work)
    _grab(video, at, work / "frame.jpg")
    c, fam = tokens.colors, tokens.families
    tw = box.x1 - box.x0
    size = title_size(title, tw)
    lines = max(1, round(len(re.sub(r"\*\*", "", title)) * 0.58 * size / tw + 0.5))
    need = int(lines * size * 1.05 + (80 if tag else 0))
    chin = None
    edl_p, fr_p = base / "edl.json", base / "framing.json"
    if video == clean and edl_p.exists() and fr_p.exists():
        from create.footage.framing import face_box
        from lens.schemas.create import Edl, Framing

        edl = Edl.model_validate_json(edl_p.read_text())
        fb = face_box(at, edl, Framing.model_validate_json(fr_p.read_text()), frame.width)
        chin = fb[3] if fb else None
    y0 = title_top(box.y0, box.y1, chin, need)
    v = {
        "--w": f"{frame.width}px", "--h": f"{frame.height}px", "--x0": f"{box.x0}px", "--tw": f"{tw}px",
        "--y0": f"{y0}px", "--size": f"{size}px", "--ink": c["ink"],
        "--accent": c["accent"], "--fade0": f"{(y0 + need / 2) / frame.height:.0%}",
        "--fade1": f"{min(1.0, (y0 + need + 300) / frame.height):.0%}",
        "--heading": f'"{fam["heading"].family}", {fam["heading"].fallback}',
        "--body": f'"{fam["body"].family}", {fam["body"].fallback}',
        "--grade": "contrast(1.08) saturate(1.14) brightness(1.01) sepia(0.05)",
    }  # fmt: skip
    page = (KIT / "cover.html").read_text()
    for key, val in {
        "{{LANG}}": "en", "{{TITLE}}": title_html(title),
        "{{TAG}}": f'<div class="tag">{html.escape(tag)}</div>' if tag else "",
        "{{CSS_VARS}}": ":root{" + ";".join(f"{k}:{x}" for k, x in v.items()) + "}",
    }.items():  # fmt: skip
        page = page.replace(key, val)
    (work / "index.html").write_text(page)
    target = out or root / "data" / "create" / project / f"{video.stem}-cover.png"
    return _shoot(work / "index.html", frame.width, frame.height, target)
