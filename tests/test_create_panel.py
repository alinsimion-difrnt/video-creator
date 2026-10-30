"""create panel (ADR 0034): the panel's clock, its asset base and the plan that hands it the product area."""

import json
import shutil
from urllib.error import HTTPError

import pytest
import yaml

from create.browser import HINT, available
from create.footage.panel import frame_times, panel_paths, render_panel, seek_js, stills_sheet, with_base
from create.footage.reel_check import plan_findings
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import ReelPlan, Timeline

CHK = load_config(REPO_ROOT / "config" / "lens.yaml").create.footage.reel.check
PROV = json.loads((REPO_ROOT / "projects/acme-v2/tokens.json").read_text())["provenance"]


def test_frame_times_cover_the_video_on_its_own_clock():
    t = frame_times(2.0, 30)
    assert len(t) == 60 and t[0] == 0 and t[-1] == pytest.approx(59 / 30)


def test_seeking_never_hands_the_timeline_back():
    assert seek_js(12.5) == "void seek(12.5)"  # a returned GSAP timeline hangs Playwright's serialiser


def test_stills_go_to_the_reviewer_as_one_stamped_sheet(tmp_path):
    from PIL import Image

    times = [1.0, 2.5, 4.0, 7.25, 9.0]
    paths = []
    for k, t in enumerate(times):
        paths.append(tmp_path / f"t{t:06.2f}.png")
        Image.new("RGB", (1080, 840), (40 * k, 120, 200)).save(paths[-1])
    sheet = Image.open(stills_sheet(paths, times, tmp_path / "sheet.png", cols=4, tile_w=360))
    assert sheet.size == (4 * 360, 2 * 280)
    assert sheet.getpixel((360 + 200, 200)) == (40, 120, 200)  # the second still, scaled into its tile
    assert sheet.getpixel((10, 12)) != (0, 120, 200)  # its time stamp in the corner


def test_the_page_resolves_its_assets_from_the_work_folder(tmp_path):
    html = with_base("<html><head><title>x</title></head></html>", tmp_path)
    assert f'<base href="{tmp_path.resolve().as_uri()}/">' in html and html.count("<base") == 1
    with pytest.raises(ValueError):
        with_base("<html></html>", tmp_path)


def test_a_panel_plan_needs_no_widgets_and_owns_the_product_area():
    plan = ReelPlan.model_validate({"layout": [{"word": 0, "layout": "split"}], "panel": True})
    assert plan.panel and plan.items == []
    words = [{"i": i, "text": w, "start_s": i * 0.5, "end_s": i * 0.5 + 0.4, "scene": "s01"}
             for i, w in enumerate(["one", "two", "three", "four", "five", "six"])]  # fmt: skip
    tl = Timeline.model_validate({
        "provenance": PROV, "project": "demo", "fps": 30, "total_s": 4.0,
        "scenes": [{"scene": "s01", "start_s": 0, "end_s": 4.0, "voice_start_s": 0, "voice_end_s": 4.0}],
        "words": words,
    })  # fmt: skip
    data = {"duration": 20.0, "transition": 0.6, "punches": [], "poses": [{"t": 0.0, "layout": "split"}],
            "items": []}  # fmt: skip
    assert {"empty-product", "static"} <= {f.rule for f in plan_findings(data, tl, CHK)}
    assert not plan_findings(data | {"panel": True}, tl, CHK)


@pytest.mark.skipif(not available(), reason=HINT)
def test_stills_render_on_the_pages_own_clock_and_land_on_one_sheet(tmp_path):
    from PIL import Image

    page, work = panel_paths(tmp_path, "demo")
    page.parent.mkdir(parents=True)
    (work / "assets").mkdir(parents=True)
    page.write_text(
        "<html><head><style>html,body{margin:0;width:1080px;height:840px}</style></head><body>"
        "<script>const tl = {t: 0, seek(t) { this.t = t; document.body.style.background ="
        " t < 2 ? 'rgb(255,0,0)' : 'rgb(0,0,255)'; return this; }};"
        "window.seek = (t) => tl.seek(t);</script></body></html>"
    )  # seek returns the timeline, as GSAP's does
    pc = load_config(REPO_ROOT / "config" / "lens.yaml").create.footage.panel
    folder = render_panel(tmp_path, "demo", pc, 30, 0, [1.0, 3.0])
    assert Image.open(folder / "t001.000.png").getpixel((500, 400))[:3] == (255, 0, 0)
    assert Image.open(folder / "t003.000.png").getpixel((500, 400))[:3] == (0, 0, 255)
    assert Image.open(folder / "sheet.png").size == (4 * 360, 280)


GSAP = sorted((REPO_ROOT / "data/create/_cache").glob("gsap-*.min.js"))


@pytest.mark.skipif(not available() or not GSAP, reason="needs Chromium and the GSAP cache (make setup)")
def test_the_starter_page_runs_and_its_example_scene_shows(tmp_path):
    from PIL import Image

    page, work = panel_paths(tmp_path, "demo")
    page.parent.mkdir(parents=True)
    (work / "assets").mkdir(parents=True)
    shutil.copy(GSAP[-1], work / "assets" / "gsap.min.js")
    shutil.copy(REPO_ROOT / "create/kit/panel-starter.html", page)
    pc = load_config(REPO_ROOT / "config" / "lens.yaml").create.footage.panel
    with pytest.raises(RuntimeError, match=r"missing .*fonts\.css"):  # an asset that never loads: no render
        render_panel(tmp_path, "demo", pc, 30, 0, [0.0])
    (work / "assets/fonts").mkdir()
    (work / "assets/fonts/fonts.css").write_text("")
    (work / "assets/logos").mkdir()
    (work / "assets/logos/x.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"/>')
    folder = render_panel(tmp_path, "demo", pc, 30, 0, [0.0, 2.0])  # raises on any page error
    blank, shown = (Image.open(folder / n).convert("L") for n in ("t000.000.png", "t002.000.png"))
    assert shown.crop((80, 220, 700, 360)).getextrema()[0] < 60  # the headline is on screen at 2 s
    assert blank.crop((80, 220, 700, 360)).getextrema()[0] > 150  # and not before its scene starts


def test_init_sets_up_the_starter_and_assets_once(tmp_path, monkeypatch):
    import create.bundle as bundle
    from create.footage.panel import google_css, init_panel

    woff, js = tmp_path / "a.woff2", tmp_path / "gsap.js"
    woff.write_bytes(b"w")
    js.write_text("gsap")
    seen: list[str] = []
    monkeypatch.setattr(bundle, "gsap", lambda cache: js)
    monkeypatch.setattr(
        bundle, "fonts", lambda cache, url: (seen.append(url) or "url(fonts/a.woff2)", [woff])
    )
    base = tmp_path / "projects" / "demo"
    base.mkdir(parents=True)
    shutil.copy(REPO_ROOT / "projects/acme-reel/tokens.json", base / "tokens.json")
    (base / "brief.yaml").write_text("brand: acme\n")
    shutil.copytree(REPO_ROOT / "brands/acme/logo", tmp_path / "brands/acme/logo")
    lines = init_panel(tmp_path, "demo", ["Space Grotesk"])
    page, work = panel_paths(tmp_path, "demo")
    assert "starter" in lines[0] and "window.seek" in page.read_text()
    plan = ReelPlan.model_validate(yaml.safe_load((base / "reel-base.yaml").read_text()))
    assert plan.panel and plan.split_seam == 980 and plan.items == [] and "split base" in lines[1]
    assert (work / "assets/gsap.min.js").read_text() == "gsap"
    assert (work / "assets/fonts/fonts.css").read_text().count("url(a.woff2)") == 2
    assert (work / "assets/logos/acme-primary.svg").exists()
    assert seen[1] == google_css(["Space Grotesk"]) and "family=Space%20Grotesk:wght@400;700" in seen[1]
    assert "family=Inter:wght@400..800&" in google_css(["Inter:wght@400..800"])
    page.write_text("<html><head></head>mine</html>")
    assert not any("starter" in x or "split base" in x for x in init_panel(tmp_path, "demo", []))
    assert page.read_text().endswith("mine</html>")  # never over a page in progress
    assert seen[-1] == google_css(["Space Grotesk"])  # a rerun without --font keeps the family
    monkeypatch.setattr(
        bundle, "fonts", lambda cache, url: (_ for _ in ()).throw(HTTPError(url, 400, "", {}, None))
    )
    with pytest.raises(HTTPError):
        init_panel(tmp_path, "demo", ["Nope Sans"])
    assert "Nope Sans" not in (work / "assets/fonts/extra.txt").read_text()  # a failed family is not kept


@pytest.mark.skipif(not available() or not GSAP, reason="needs Chromium and the GSAP cache (make setup)")
def test_the_starters_typing_and_counting_survive_seeks_in_any_order(tmp_path):
    from playwright.sync_api import sync_playwright

    from create.browser import launch

    page = tmp_path / "page.html"
    shutil.copy(GSAP[-1], tmp_path / "gsap.min.js")
    html = (REPO_ROOT / "create/kit/panel-starter.html").read_text()
    html = html.replace('<div id="fade">', '<div id="n"></div><div id="q"></div><div id="fade">')
    uses = 'count("#n", 1000000, 1, 2); type("#q", "Which agency?", 1, 2);'
    html = html.replace("tl.set({}, {}, DUR);", uses + "\ntl.set({}, {}, DUR);")
    page.write_text(with_base(html, tmp_path))
    want = {3.0: ("1,000,000", "Which agency?"), 0.5: ("0", ""), 1.5: (None, "Which a")}
    with sync_playwright() as pw:
        browser = launch(pw)
        tab = browser.new_page()
        tab.goto(page.as_uri())
        for t in [3.0, 0.5, 1.5, 3.0, 0.5]:  # forwards, back, middle, forwards, back
            tab.evaluate(seek_js(t))
            n, q = tab.evaluate(
                "[document.querySelector('#n').textContent, document.querySelector('#q').textContent]"
            )
            assert (want[t][0] in (None, n)) and q == want[t][1], (t, n, q)
        mid = tab.evaluate("seek(1.5), document.querySelector('#n').textContent")
        browser.close()
    assert 0 < int(mid.replace(",", "")) < 1000000


def test_the_asset_list_says_what_file_cannot(tmp_path):
    from PIL import Image

    from create.footage.panel import asset_lines, caption_clearance

    Image.new("RGBA", (300, 80), (255, 255, 255, 255)).save(tmp_path / "white.png")
    Image.new("RGBA", (64, 64), (0, 0, 0, 0)).save(tmp_path / "clear.png")
    (tmp_path / "logo.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"/>')
    (tmp_path / "wlogo.svg").write_text('<svg viewBox="0 0 9 9"><path fill="#FFF" d="M0 0h9v9z"/></svg>')
    (tmp_path / "page.svg").write_text("<html>Access denied</html>")
    (tmp_path / "oops.webp").write_text("<html>404 Not Found</html>")  # an error page saved as an image
    lines = {line.split()[0]: line for line in asset_lines(tmp_path)}
    assert "300x80 light" in lines["white.png"] and "transparent" in lines["clear.png"]
    assert "viewBox 0 0 24 24 dark (no fill" in lines["logo.svg"] and "light" in lines["wlogo.svg"]
    assert "NOT AN SVG" in lines["page.svg"] and "NOT AN IMAGE" in lines["oops.webp"]
    assert caption_clearance(840, 980, 140) is None
    assert "740 px" in (caption_clearance(840, 880, 140) or "")  # a close take: the captions move up


@pytest.mark.skipif(not available(), reason=HINT)
def test_a_panel_that_would_cover_the_captions_is_refused(tmp_path):
    page, work = panel_paths(tmp_path, "demo")
    page.parent.mkdir(parents=True)
    (work / "assets").mkdir(parents=True)
    (tmp_path / "projects/demo/reel-base.yaml").write_text(
        "layout: [{word: 0, layout: split}]\nsplit_seam: 880\n"
    )
    page.write_text("<html><head><style>html,body{margin:0;width:1080px;height:840px}</style></head><body>"
                    "<script>window.seek = (t) => {};</script></body></html>")  # fmt: skip
    pc = load_config(REPO_ROOT / "config" / "lens.yaml").create.footage.panel
    with pytest.raises(ValueError, match="740 px"):  # a close take: seam 880 - 140
        render_panel(tmp_path, "demo", pc, 30, 0, [0.0])
