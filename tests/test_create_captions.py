"""C11 captions: narration words grouped into burned-in captions, per frame (config design.captions)."""

import json

import pytest

from create.captions import group_words
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import Timeline

CFG = load_config(REPO_ROOT / "config" / "lens.yaml").create.design
TIMELINE = Timeline.model_validate(json.loads((REPO_ROOT / "projects/acme-v2/timeline.json").read_text()))


def _w(i: int, text: str, t: float, scene: str = "s01", d: float = 0.25) -> dict:
    return {"i": i, "text": text, "start_s": t, "end_s": t + d, "scene": scene}


def _words(spec: str, step: float = 0.3) -> list:
    from lens.schemas.create import TimelineWord

    return [TimelineWord(**_w(i, w, 1 + i * step)) for i, w in enumerate(spec.split())]


def test_sentences_end_groups():
    groups = group_words(_words("Is yours there? It is."), CFG.captions["landscape"])
    assert [" ".join(w.w for w in g.words) for g in groups] == ["Is yours there?", "It is."]


def test_long_sentences_split_balanced_and_prefer_a_comma():
    text = "It tracks which brands AI recommends, in ChatGPT, Gemini and Perplexity."
    groups = group_words(_words(text), CFG.captions["landscape"])
    lines = [" ".join(w.w for w in g.words) for g in groups]
    assert all(len(line) <= 32 for line in lines) and " ".join(lines) == text
    assert any(line.endswith(",") for line in lines[:-1])


def test_vertical_groups_are_short():
    groups = group_words(_words("Here is how it works for your small agency."), CFG.captions["vertical"])
    assert all(len(g.words) <= 3 and len(" ".join(w.w for w in g.words)) <= 16 for g in groups)


def test_a_pause_starts_a_new_group_and_timing_follows_the_words():
    from lens.schemas.create import TimelineWord

    rules = CFG.captions["landscape"]
    ws = [TimelineWord(**_w(0, "First", 1.0)), TimelineWord(**_w(1, "then", 2.5))]
    a, b = group_words(ws, rules)
    assert a.start == pytest.approx(1.0 - rules.lead_s) and a.end == pytest.approx(1.25 + rules.hold_s)
    assert b.start == pytest.approx(2.5 - rules.lead_s)


def test_groups_never_overlap_and_hand_over_at_a_seam():
    rules = CFG.captions["landscape"]
    groups = group_words(_words("One two. Three four.", step=0.2), rules)
    assert groups[0].end == pytest.approx(groups[1].start - rules.seam_s)


def test_acme_v2_grouping_is_close_to_the_hand_made_captions():
    groups = group_words(TIMELINE.words, CFG.captions["landscape"])
    assert sum(len(g.words) for g in groups) == len(TIMELINE.words) == 252
    assert 55 <= len(groups) <= 75  # the hand-made v2 file has 65 groups of 1-6 words
    assert all(len(g.words) <= 6 for g in groups)


def _tokens(**captions):
    from lens.schemas.create import Tokens

    t = json.loads((REPO_ROOT / "projects/acme-v2/tokens.json").read_text())
    if captions:
        t["captions"] = {**t["captions"], **captions}
    return Tokens.model_validate(t)


def test_acme_caption_style_is_the_v2_pill_and_passes():
    from create.tokens import caption_errors

    tokens = _tokens()
    assert tokens.captions is not None and tokens.captions.kind == "pill" and tokens.captions.size_px == 44
    assert caption_errors(tokens, CFG) == []


def test_caption_style_checks_size_width_and_contrast():
    from create.tokens import caption_errors

    tokens = _tokens(size_px=20, max_width_px=3000, text="ink_muted", background="canvas")
    errors = caption_errors(tokens, CFG)
    assert any("under the 24px" in e for e in errors) and any("wider than" in e for e in errors)
    assert not any("contrast" in e for e in errors)  # contrast is checked once size and roles are right
    errors = caption_errors(_tokens(text="accent"), CFG)
    assert any("accent on surface" in e for e in errors)


def test_karaoke_needs_a_surface_or_a_stroke():
    with pytest.raises(ValueError, match="stroke"):
        _tokens(kind="karaoke", background=None)


def test_caption_comp_places_groups_in_the_band_and_carries_the_style():
    from create.burn import caption_comp
    from create.captions import group_words
    from lens.schemas.create import Captions

    tokens = _tokens(kind="karaoke", active="accent", background=None, stroke="ink", stroke_px=6)
    groups = group_words(_words("Here is how it works."), CFG.captions["vertical"])
    caps = Captions.model_validate(
        {"provenance": json.loads((REPO_ROOT / "projects/acme-v2/tokens.json").read_text())["provenance"]
         | {"stage": "c11_assemble"}, "project": "acme-v2", "frame": "vertical",
         "groups": [g.model_dump() for g in groups]}
    )  # fmt: skip
    frame = CFG.frames["vertical"]
    html = caption_comp(tokens, frame, caps, 3.0, "ro")
    band = frame.caption_band
    assert f"--band-cy:{(band.y0 + band.y1) / 2:g}px" in html and 'lang="ro"' in html
    assert 'data-width="1080" data-height="1920"' in html
    assert '"kind": "karaoke"' in html and f'"active": "{tokens.colors["accent"]}"' in html
    assert "{{" not in html


def _browser() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        return False
    from create.browser import available

    return (REPO_ROOT / "data/create/_cache").exists() and available()


@pytest.mark.skipif(
    not _browser(), reason="needs playwright, Chromium and the GSAP cache (uv run --with playwright)"
)
def test_a_single_word_wider_than_the_band_shrinks_instead_of_crashing(tmp_path):
    import shutil

    from playwright.sync_api import sync_playwright

    from create.bundle import gsap
    from create.burn import caption_comp
    from create.captions import group_words
    from lens.schemas.create import Captions

    tokens = _tokens(kind="karaoke", active="accent", background=None, stroke="ink", stroke_px=6, size_px=64,
                     uppercase=True, max_width_px=480)  # fmt: skip
    groups = group_words(_words("Specifically Uncharacteristically."), CFG.captions["vertical"])
    prov = json.loads((REPO_ROOT / "projects/acme-v2/tokens.json").read_text())["provenance"]
    caps = Captions.model_validate(
        {"provenance": prov | {"stage": "c11_assemble"}, "project": "acme-v2", "frame": "vertical",
         "groups": [g.model_dump() for g in groups]}
    )  # fmt: skip
    (tmp_path / "assets").mkdir()
    shutil.copy(gsap(REPO_ROOT / "data/create/_cache"), tmp_path / "assets/gsap.min.js")
    (tmp_path / "index.html").write_text(caption_comp(tokens, CFG.frames["vertical"], caps, 3.0, "en"))
    with sync_playwright() as p:
        from create.browser import launch

        browser = launch(p)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto((tmp_path / "index.html").as_uri())
        assert errors == [] and page.evaluate("!!window.__timelines.captions")
        widths = page.evaluate("[...document.querySelectorAll('.cap')].map(e => e.scrollWidth)")
        browser.close()
    assert all(w <= 480 + 1 for w in widths)


@pytest.mark.skipif(
    not _browser(), reason="needs playwright, Chromium and the GSAP cache (uv run --with playwright)"
)
def test_a_pill_lights_the_spoken_word_when_active_differs(tmp_path):
    """acme vertical: a paper pill (reads on any footage) with the spoken word in the accent."""
    import shutil

    from playwright.sync_api import sync_playwright

    from create.bundle import gsap
    from create.burn import caption_comp
    from create.captions import group_words
    from lens.schemas.create import Captions

    tokens = _tokens(kind="pill", active="accent", text="ink", background="surface", size_px=56,
                     max_width_px=480)  # fmt: skip
    groups = group_words(_words("Paid is re-earned."), CFG.captions["vertical"])
    prov = json.loads((REPO_ROOT / "projects/acme-v2/tokens.json").read_text())["provenance"]
    caps = Captions.model_validate(
        {"provenance": prov | {"stage": "c11_assemble"}, "project": "acme-v2", "frame": "vertical",
         "groups": [g.model_dump() for g in groups]}
    )  # fmt: skip
    (tmp_path / "assets").mkdir()
    shutil.copy(gsap(REPO_ROOT / "data/create/_cache"), tmp_path / "assets/gsap.min.js")
    (tmp_path / "index.html").write_text(caption_comp(tokens, CFG.frames["vertical"], caps, 3.0, "en"))
    first = groups[0].words[0]
    with sync_playwright() as p:
        from create.browser import launch

        browser = launch(p)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.goto((tmp_path / "index.html").as_uri())
        page.evaluate(f"window.__timelines.captions.seek({first.t + 0.05}); 0")
        colour = page.evaluate("getComputedStyle(document.querySelector('.w')).color")
        browser.close()
    r, g, b = (int(tokens.colors["accent"][i : i + 2], 16) for i in (1, 3, 5))
    assert colour == f"rgb({r}, {g}, {b})"


def test_vertical_groups_do_not_end_on_function_words():
    words = _words("Go on to ChatGPT and search for the type of restaurant that you have.")
    groups = group_words(words, CFG.captions["vertical"], CFG.caption_function_words["en"])
    ends = [g.words[-1].w.lower().strip(".,") for g in groups]
    assert not set(ends[:-1]) & set(CFG.caption_function_words["en"]), ends
    assert all(len(g.words) <= CFG.captions["vertical"].max_words for g in groups)


def test_presenter_captions_sit_below_the_chin():
    from create.burn import group_centres
    from lens.schemas.create import Captions, Edl, Framing

    prov = json.loads((REPO_ROOT / "projects/acme-v2/tokens.json").read_text())["provenance"]
    tokens = _tokens(kind="karaoke", active="accent", background=None, stroke="ink", stroke_px=6, size_px=64,
                     max_width_px=480, padding_px=[0, 0])  # fmt: skip
    groups = group_words(_words("Look for context in reviews.", step=0.3), CFG.captions["vertical"])
    caps = Captions.model_validate(
        {
            "provenance": prov,
            "project": "acme-v2",
            "frame": "vertical",
            "groups": [g.model_dump() for g in groups],
        }
    )
    seg = {"take": "t", "src_in": 0, "src_out": 300, "rec_in": 0}
    edl = Edl.model_validate(
        {
            "provenance": prov,
            "project": "acme-v2",
            "fps": 30,
            "applied": [],
            "duration_frames": 300,
            "segments": [seg],
        }
    )
    framing = Framing.model_validate({
        "provenance": prov, "project": "acme-v2", "frame": "vertical", "width": 1080, "height": 1920,
        "segments": [{"segment": 0, "take": "t", "face": [400, 700, 280, 380], "zoom": 1.12,
                      "full": {"x": 0, "y": 0, "w": 1080, "h": 1920},
                      "pip": {"x": 0, "y": 0, "w": 9, "h": 9}}],
    })  # fmt: skip
    v = CFG.frames["vertical"]
    centres = group_centres(caps, tokens, v, edl, framing, CFG.caption_face_gap)
    chin, face_h = 700 + 380, 380
    half = 64 * tokens.captions.line_height / 2
    for y in centres:
        lowest = v.caption_band.y1 - half  # as low as the band allows
        assert y - half >= chin + CFG.caption_face_gap * face_h - 0.5 or y == pytest.approx(lowest, abs=0.1)
    assert all(v.caption_band.y0 <= y <= v.caption_band.y1 for y in centres)
    # split scenes: every caption ends above the product's bottom edge, clear of the presenter below
    scenes = [{"start_s": 0.0, "end_s": 1e9, "layout": "split"}]
    seam = 830.0
    split = group_centres(caps, tokens, v, edl, framing, CFG.caption_face_gap, scenes, seam, 16)
    assert all(y + half == pytest.approx(seam - 16, abs=0.1) for y in split)
