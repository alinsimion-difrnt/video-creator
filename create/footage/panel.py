"""create panel (ADR 0034): a bespoke animated panel laid over a presenter reel.

The panel is one hand-built HTML page per project (projects/<p>/panel/index.html, committed) with one paused
GSAP timeline and a global `seek(t)`; its assets (logos, team photos, 3D icons, fonts) sit in
data/create/<p>/panel/assets/ and are never committed (third-party media). The page is stepped frame by frame
in Chromium, encoded, and composited at (0, 0) over a reel render whose plan says `panel: true` (the plan
places the presenter below the seam, the captions and the audio; the panel owns the product area above).
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote

from lens.schemas.config import FootagePanel


def frame_times(duration: float, fps: int) -> list[float]:
    """Every frame start on the video's clock, 0 included, the frame at `duration` not."""
    return [i / fps for i in range(round(duration * fps))]


def with_base(html: str, assets: Path) -> str:
    """The page with a <base> at its assets folder, so its relative URLs (logos/x.svg) resolve there."""
    if "<head>" not in html:
        raise ValueError("panel page has no <head>")
    return html.replace("<head>", f'<head><base href="{assets.resolve().as_uri()}/">', 1)


def seek_js(t: float) -> str:
    """The page call that shows time t; `void`: a GSAP timeline handed back hangs Playwright's serialiser."""
    return f"void seek({t})"


def still_name(t: float) -> str:
    return f"t{t:07.3f}.png"


def stills_sheet(stills: list[Path], times: list[float], out: Path, cols: int = 4, tile_w: int = 360) -> Path:
    """The stills on one sheet, each stamped with its time: one image for a reviewer instead of many."""
    from PIL import Image, ImageDraw, ImageFont

    first = Image.open(stills[0])
    tile_h = round(first.height * tile_w / first.width)
    rows = -(-len(stills) // cols)
    sheet = Image.new("RGB", (cols * tile_w, rows * tile_h), "white")
    font = ImageFont.load_default(size=22)
    for k, (path, t) in enumerate(zip(stills, times, strict=True)):
        tile = Image.open(path).convert("RGB").resize((tile_w, tile_h))
        draw = ImageDraw.Draw(tile)
        label = f"{t:.2f}s"
        x1, y1 = draw.textbbox((8, 6), label, font=font)[2:]
        draw.rectangle((4, 4, x1 + 4, y1 + 4), fill="black")
        draw.text((8, 6), label, fill="white", font=font)
        sheet.paste(tile, ((k % cols) * tile_w, (k // cols) * tile_h))
    sheet.save(out)
    return out


def panel_paths(root: Path, project: str) -> tuple[Path, Path]:
    """(the committed page, the uncommitted work folder holding assets/, frames/ and panel.mp4)."""
    return root / "projects" / project / "panel" / "index.html", root / "data" / "create" / project / "panel"


def google_css(families: list[str]) -> str:
    """The Google Fonts CSS URL for extra families a beat borrows (e.g. a product's look): weights 400 and 700
    unless the family names its own axes ("Inter:wght@400..800"); a weight the family lacks is a 400 error."""
    q = "&".join(
        "family=" + (quote(f.rstrip(":"), safe=":@;.,") if ":" in f else f"{quote(f)}:wght@400;700")
        for f in families
    )
    return f"https://fonts.googleapis.com/css2?{q}&display=swap"


def init_panel(root: Path, project: str, extra_fonts: list[str]) -> list[str]:
    """Set up a panel: the starter page and the split base plan (never over existing ones) and the assets
    every panel needs (GSAP, the brand's fonts and logos, any extra font families). Returns what it wrote."""
    import json

    import yaml

    from create.bundle import fonts, gsap
    from lens.schemas.create import Tokens

    page, work = panel_paths(root, project)
    assets = work / "assets"
    done: list[str] = []
    if not page.exists():
        page.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(Path(__file__).parent.parent / "kit" / "panel-starter.html", page)
        done.append(f"{page.relative_to(root)} (the starter: replace its example scene)")
    plan = root / "projects" / project / "reel-base.yaml"
    if not plan.exists():
        shutil.copy(Path(__file__).parent.parent / "kit" / "panel-base.yaml", plan)
        done.append(f"{plan.relative_to(root)} (the split base: `create reel --plan` it, then render it)")
    cache = root / "data" / "create" / "_cache"
    (assets / "fonts").mkdir(parents=True, exist_ok=True)
    shutil.copy(gsap(cache), assets / "gsap.min.js")
    base = root / "projects" / project
    tokens = Tokens.model_validate(json.loads((base / "tokens.json").read_text()))
    kept = assets / "fonts" / "extra.txt"  # families an earlier --init added: a rerun keeps them
    extra_fonts = list(dict.fromkeys((kept.read_text().split("\n") if kept.exists() else []) + extra_fonts))
    extra_fonts = [f for f in extra_fonts if f]
    sheets = []
    for url, fallback in [(tokens.fonts_css, "")] + [
        (google_css([f]), google_css([f.split(":")[0] + ":"])) for f in extra_fonts
    ]:
        try:
            css, files = fonts(cache, url)
        except HTTPError:  # a weight the family does not have: its default weight only
            if not fallback:
                raise
            css, files = fonts(cache, fallback)
        for f in files:
            shutil.copy(f, assets / "fonts" / f.name)
        sheets.append(css)
    (assets / "fonts" / "fonts.css").write_text("\n".join(sheets).replace("url(fonts/", "url("))
    kept.write_text("\n".join(extra_fonts))  # only once every family loaded
    brand = str((yaml.safe_load((base / "brief.yaml").read_text()) or {}).get("brand", ""))
    (assets / "logos").mkdir(exist_ok=True)
    (assets / "emoji").mkdir(exist_ok=True)
    logos = sorted((root / "brands" / brand / "logo").glob("*.svg"))
    for f in logos:
        shutil.copy(f, assets / "logos" / f.name)
    families = ", ".join(dict.fromkeys([f.family for f in tokens.families.values()] + extra_fonts))
    done += [
        f"{assets.relative_to(root)}/gsap.min.js",
        f"{assets.relative_to(root)}/fonts/fonts.css ({families})",
        f"{assets.relative_to(root)}/logos/ ({len(logos)} {brand} logos)",
    ]
    return done


def asset_lines(assets: Path) -> list[str]:
    """Every asset with its size and, for images, whether it is light or dark (a white logo needs a dark
    tile): what `file` cannot tell about webp, png or svg."""
    from PIL import Image, ImageStat

    lines = []
    for f in sorted(x for x in assets.rglob("*") if x.is_file() and x.suffix.lower() != ".woff2"):
        rel, kb = f.relative_to(assets), f.stat().st_size / 1024
        info = ""
        if f.suffix.lower() == ".svg":
            text = f.read_text(errors="ignore")
            box = re.search(r'viewBox="([^"]+)"', text)
            view = f"viewBox {box.group(1)} " if box else ""
            info = f"svg {view}{svg_tone(text)}" if "<svg" in text else "NOT AN SVG"
        elif f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}:
            try:
                with Image.open(f) as im:
                    rgba = im.convert("RGBA")
                    alpha = rgba.getchannel("A")
                    lum = ImageStat.Stat(rgba.convert("L"), mask=alpha.point(lambda a: 255 if a > 32 else 0))
                    tone = "light" if lum.mean[0] > 170 else "dark" if lum.mean[0] < 85 else "mid"
                    low = alpha.getextrema()[0]
                    clear = " transparent bg" if isinstance(low, int | float) and low < 32 else ""
                    info = f"{im.width}x{im.height} {tone}{clear}"
            except OSError as exc:  # an error page saved as an image
                info = f"NOT AN IMAGE ({exc.__class__.__name__})"
        lines.append(f"{rel}  {kb:.0f} KB  {info}".rstrip())
    return lines


def svg_tone(svg: str) -> str:
    """light, dark or mixed from the SVG's fill colours; no fill renders black."""
    named = {"white": "#ffffff", "black": "#000000"}
    fills = [
        named.get(c.lower(), c) for c in re.findall(r'fill[=:]\s*"?(#[0-9a-fA-F]{3,6}|white|black)', svg)
    ]
    lums = []
    for c in fills:
        h = c.lstrip("#")
        h = "".join(ch * 2 for ch in h) if len(h) == 3 else h
        r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
        lums.append(0.299 * r + 0.587 * g + 0.114 * b)
    if not lums:
        return "dark (no fill: black)"
    if all(v > 170 for v in lums):
        return "light"
    return "dark" if all(v < 85 for v in lums) else "mixed"


def caption_clearance(page_height: int, seam: int, clear_px: int) -> str | None:
    """A panel taller than the seam allows covers the captions (they sit just above the seam): the problem,
    or None."""
    if page_height > seam - clear_px:
        return (f"panel page is {page_height} px tall but the base plan's seam is {seam}: the captions above "
                f"the seam would be covered; make html, body {seam - clear_px} px tall")  # fmt: skip
    return None


def render_panel(
    root: Path, project: str, pc: FootagePanel, fps: int, duration: float, stills: list[float] | None = None
) -> Path:
    """Step the page through every frame (or only `stills`, as PNGs plus a stamped sheet.png for a design
    review) and encode it. Returns panel.mp4, or the stills folder."""
    from playwright.sync_api import sync_playwright

    from create.browser import launch

    page_src, work = panel_paths(root, project)
    assets = work / "assets"
    if not assets.is_dir():
        raise FileNotFoundError(f"{assets}: put the panel's logos, photos, icons and fonts there")
    page = work / "page.html"
    page.write_text(with_base(page_src.read_text(), assets))
    out = work / ("stills" if stills is not None else "frames")
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    times = stills if stills is not None else frame_times(duration, fps)
    errors: list[str] = []
    with sync_playwright() as pw:
        browser = launch(pw)
        tab = browser.new_page()
        tab.on("pageerror", lambda e: errors.append(str(e)))
        tab.on("requestfailed", lambda r: errors.append(f"missing {r.url}"))  # a logo that never loaded
        tab.goto(page.as_uri())
        w, h = tab.evaluate("[document.body.offsetWidth, document.body.offsetHeight]")
        plan = root / "projects" / project / "reel-base.yaml"
        if plan.exists():
            from create.cover import plan_seam

            problem = caption_clearance(h, plan_seam(plan.parent), pc.caption_clear_px)
            if problem:
                raise ValueError(problem)
        tab.set_viewport_size({"width": w, "height": h})
        tab.evaluate("document.fonts.ready")
        tab.wait_for_timeout(pc.settle_ms)
        if not tab.evaluate("typeof window.seek === 'function'"):
            raise RuntimeError("panel page must define window.seek(t) over one paused timeline")
        for i, t in enumerate(times):
            tab.evaluate(seek_js(t))
            if stills is not None:
                tab.screenshot(path=str(out / still_name(t)))
            else:
                tab.screenshot(path=str(out / f"f{i:05d}.jpg"), type="jpeg", quality=pc.jpeg_quality)
        browser.close()
    if errors:
        raise RuntimeError(f"panel page errors: {errors[:3]}")
    if stills is not None:
        stills_sheet([out / still_name(t) for t in times], times, out / "sheet.png")
        return out
    target = work / "panel.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-framerate", str(fps), "-i", str(out / "f%05d.jpg"),
         "-c:v", "libx264", "-crf", str(pc.crf), "-pix_fmt", "yuv420p", str(target)],
        check=True,
    )  # fmt: skip
    return target


def composite(base: Path, panel: Path, out: Path, crf: int) -> Path:
    """The panel over the base render at (0, 0); the base's audio and meta (for create qa) carried over."""
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(base), "-i", str(panel),
         "-filter_complex", "[0:v][1:v]overlay=0:0:eof_action=repeat[v]",
         "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
         "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(out)],
        check=True,
    )  # fmt: skip
    meta = base.with_suffix(".meta.json")
    if meta.exists():
        shutil.copy(meta, out.with_suffix(".meta.json"))
    return out
