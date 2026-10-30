"""Fred's design sheet: his three styles side by side (illustrated rig, 3D, pixel), beside a reference photo.

    uv run python scripts/fred_sheet.py --out data/fred/sheet.png [--photo f] [--sets none,top_hat+moustache]

One row per accessory set. The rig is drawn by create/kit/fred.js in headless Chromium, 3D by
create/render3d/fred3d.py, pixel by create/pixel/fred.py at an integer upscale. The output is media: keep it
in data/ (never committed).
"""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw

from create.browser import launch
from create.bundle import gsap
from create.pixel import fred as pfred
from create.render3d import fred3d

ROOT = Path(__file__).resolve().parents[1]
CELL_W, CELL_H = 300, 435  # the rig's box (aspect 1.45)


def rig_images(sets: list[list[str]], pose: str) -> list[Image.Image]:
    from playwright.sync_api import sync_playwright

    js = (ROOT / "create/kit/fred.js").read_text()
    lib = gsap(ROOT / "data/create/_cache").read_text()
    page_html = f"""<!doctype html><html><body style="margin:0;background:transparent">
<div id="row" style="display:flex"></div><script>{lib}</script><script>{js}</script><script>
const sets = {json.dumps(sets)}, pose = {json.dumps(pose)};
sets.forEach(function (acc, k) {{
  const box = document.createElement("div");
  box.style.cssText = "width:{CELL_W}px;height:{CELL_H}px;padding:0;";
  document.getElementById("row").appendChild(box);
  const R = FRED.build("s" + k, {CELL_W});
  box.appendChild(R.svg);
  const tl = gsap.timeline({{ paused: true }});
  acc.forEach(function (a) {{ FRED.accessory(tl, R, a, true, 0, false); }});
  if (pose !== "rest") FRED.act(tl, R, pose, 0.1);
  tl.seek(pose === "wave" ? 0.45 : pose === "clap" ? 0.3 : 0.01);
}});
</script></body></html>"""
    with sync_playwright() as pw:
        b = launch(pw)
        pg = b.new_page(viewport={"width": CELL_W * len(sets), "height": CELL_H})
        pg.set_content(page_html)
        png = pg.screenshot(omit_background=True)
        b.close()
    strip = Image.open(io.BytesIO(png)).convert("RGBA")
    return [strip.crop((k * CELL_W, 0, (k + 1) * CELL_W, CELL_H)) for k in range(len(sets))]


def fit(img: Image.Image, w: int, h: int, nearest: bool = False) -> Image.Image:
    box = img.getbbox() or (0, 0, *img.size)
    img = img.crop(box)
    s = min(w / img.width, h / img.height)
    if nearest:
        s = max(1, int(s))
    rs = Image.Resampling.NEAREST if nearest else Image.Resampling.LANCZOS
    img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), rs)
    out = Image.new("RGBA", (w, h))
    out.alpha_composite(img, ((w - img.width) // 2, h - img.height))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--photo")
    ap.add_argument("--sets", default="none,top_hat+moustache,automail")
    ap.add_argument("--pose", default="rest", help="rest | wave | clap (rig and 3D/pixel equivalents)")
    a = ap.parse_args()
    sets = [[] if s == "none" else s.split("+") for s in a.sets.split(",")]
    rigs = rig_images(sets, a.pose)
    anim3d = {"rest": "idle", "wave": "wave", "clap": "idle"}[a.pose]
    animpx = {"rest": "idle", "wave": "wave", "clap": "clap"}[a.pose]
    pad, label_h = 24, 40
    cols = 3 + (1 if a.photo else 0)
    sheet = Image.new(
        "RGBA", (cols * (CELL_W + pad) + pad, len(sets) * (CELL_H + pad) + label_h + pad), "#f2efe8"
    )
    d = ImageDraw.Draw(sheet)
    heads = (["photo"] if a.photo else []) + ["illustrated (rig)", "3D (toon3d)", "pixel"]
    for c, t in enumerate(heads):
        d.text((pad + c * (CELL_W + pad) + 8, 12), t, fill="#333")
    for r, acc in enumerate(sets):
        y = label_h + r * (CELL_H + pad)
        cells = []
        if a.photo:
            cells.append(fit(Image.open(a.photo).convert("RGBA"), CELL_W, CELL_H // 2) if r == 0 else None)
        cells.append(fit(rigs[r], CELL_W, CELL_H))
        cells.append(fit(fred3d.frames(anim3d, frozenset(acc))[1 if anim3d == "wave" else 0], CELL_W, CELL_H))
        px = pfred.frames(animpx, set(acc))
        cells.append(fit(px[1 if animpx != "idle" else 0], CELL_W, CELL_H, nearest=True))
        for c, im in enumerate(cells):
            if im is not None:
                sheet.alpha_composite(im, (pad + c * (CELL_W + pad), y))
        d.text((6, y + 4), "+".join(acc) or "plain", fill="#888")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(a.out)
    print(a.out)


if __name__ == "__main__":
    main()
