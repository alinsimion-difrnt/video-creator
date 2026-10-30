"""create cover: the title fits and sits below the chin inside the cover-safe rect when there is room; the
split cover keeps the title above the seam and lands on the video's first frame."""

import shutil
import subprocess

import pytest

from create.browser import HINT, available
from create.cover import title_html, title_size, title_top
from lens.config import REPO_ROOT, load_config

CFG = load_config(REPO_ROOT / "config" / "lens.yaml")
BASE_PLAN = "layout: [{word: 0, layout: split}]\nsplit_seam: 980\npanel: true\n"


def test_the_title_goes_below_the_chin_when_it_fits():
    assert title_top(420, 1500, chin=900, need=400) == 940
    assert title_top(420, 1500, chin=1300, need=400) == 460  # no room below: top of the safe rect
    assert title_top(420, 1500, chin=None, need=400) == 460


def test_long_words_shrink_the_title_and_bold_takes_the_accent():
    assert title_size("Hi", 840) == 150 and title_size("Internationalisation everywhere", 840) < 90
    assert title_html("Get **cited** <now>") == "Get <b>cited</b> &lt;now&gt;"


def test_the_split_cover_takes_the_base_plans_seam_and_keeps_the_logo_above_it(tmp_path):
    from create.cover import plan_seam, split_layout

    assert plan_seam(tmp_path) == 1040  # no base plan: the plan default
    (tmp_path / "reel-base.yaml").write_text(BASE_PLAN)
    assert plan_seam(tmp_path) == 980
    logo_y, title_h = split_layout(980, 56)
    assert logo_y + 56 < 980 and title_h < logo_y


@pytest.mark.skipif(not available(), reason=HINT)
def test_the_split_cover_leaves_him_untouched_and_becomes_the_first_frame(tmp_path, monkeypatch):
    from PIL import Image

    import create.cover as cover

    monkeypatch.setattr(cover, "fonts", lambda cache, url: ("", []))  # no network: system fonts
    p = "demo"
    base = tmp_path / "projects" / p
    base.mkdir(parents=True)
    shutil.copy(REPO_ROOT / "projects/acme-reel/tokens.json", base / "tokens.json")
    (base / "brief.yaml").write_text("brand: acme\nlanguage: en\n")
    (base / "reel-base.yaml").write_text(BASE_PLAN)
    shutil.copytree(REPO_ROOT / "brands/acme/logo", tmp_path / "brands/acme/logo")
    video = tmp_path / "base.mp4"
    red = "color=c=0xC81E1E:s=1080x1920:r=30:d=1"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", red, "-f", "lavfi", "-i", "sine=d=1",
                    "-shortest", "-pix_fmt", "yuv420p", str(video)], check=True)  # fmt: skip
    png = cover.run_split_cover(tmp_path, p, video, "Vague site, **vague ad.**", CFG, at=0.5, kicker="new",
                                sub="X writes your ads.")  # fmt: skip
    img = Image.open(png).convert("RGB")
    assert img.size == (1080, 1920)
    from playwright.sync_api import sync_playwright

    from create.browser import launch

    box = CFG.create.design.frames["vertical"].cover_safe
    with sync_playwright() as pw:  # the block sits inside the rect the grid crops keep, above the logo
        browser = launch(pw)
        pg = browser.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto((tmp_path / "data/create/demo/render/cover-split/index.html").as_uri())
        pg.evaluate(cover.FIT_JS)
        top, left, right, bottom, logo = pg.evaluate(
            "(() => { const r = (s) => document.querySelector(s).getBoundingClientRect(); const h = r('h1');"
            " return [r('.kick').top, h.left, h.right, h.bottom, r('#logo').top]; })()"
        )
        browser.close()
    assert box is not None and top >= box.y0 - 1 and left >= box.x0 and right <= box.x1 and bottom < logo
    assert img.getpixel((1060, 20)) == (255, 255, 255)  # paper above the seam
    r, g, b = img.getpixel((540, 1600))
    assert r > 150 and g < 80 and b < 80  # his frame below the seam, as rendered
    with pytest.raises(ValueError, match="does not fit"):
        cover.run_split_cover(
            tmp_path, p, video, " ".join(["Internationalisation"] * 9), CFG, kicker="k", sub="s"
        )
    out = cover.onto_first_frame(png, video, 18)
    probe = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries",
                            "stream=codec_type,nb_read_frames", "-of", "csv=p=0", str(out)],
                           capture_output=True, text=True, check=True).stdout.split()  # fmt: skip
    assert "video,30" in probe and any(s.startswith("audio") for s in probe)
    frames = tmp_path / "f%d.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-vf", "select='lte(n,1)'",
                    "-vsync", "vfr", str(frames)], check=True)  # fmt: skip
    first, second = (Image.open(tmp_path / f"f{i}.png").convert("RGB") for i in (1, 2))
    assert first.getpixel((1060, 20))[1] > 200  # frame 0 is the cover
    assert second.getpixel((1060, 20))[1] < 80  # and only frame 0
