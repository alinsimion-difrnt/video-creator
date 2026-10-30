"""create reel end to end on a synthetic 4 s take: build, plan checks, layout checks, and the render gate."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from create.captions import group_words
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import TimelineWord

CFG = load_config(REPO_ROOT / "config" / "lens.yaml")
PROV = json.loads((REPO_ROOT / "projects/acme-v2/tokens.json").read_text())["provenance"]
GSAP = sorted((REPO_ROOT / "data" / "create" / "_cache").glob("gsap-*.min.js"))
TEXT = "Ask ChatGPT for the best restaurant in Budapest and check the sources today."


@pytest.fixture
def take(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A presenter project: a 4 s plate, its timeline, captions, edit, framing and vertical tokens."""
    if not GSAP:
        pytest.skip("needs the GSAP cache (data/create/_cache)")
    monkeypatch.setattr("create.footage.reel.fonts", lambda cache, url: ("", []))  # no network in tests
    base = tmp_path / "projects" / "demo"
    base.mkdir(parents=True)
    cache = tmp_path / "data" / "create" / "_cache"
    cache.mkdir(parents=True)
    shutil.copy(GSAP[-1], cache / GSAP[-1].name)
    plate = tmp_path / "data" / "create" / "demo" / "footage" / "edited" / "demo-edited.mp4"
    plate.parent.mkdir(parents=True)
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x6699cc:s=108x192:r=30:d=4",
            "-f",
            "lavfi",
            "-i",
            "sine=f=220:d=4",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(plate),
        ],
        check=True,
    )
    words = [
        {
            "i": i,
            "text": w,
            "start_s": round(0.2 + i * 0.28, 3),
            "end_s": round(0.42 + i * 0.28, 3),
            "scene": "s01",
        }
        for i, w in enumerate(TEXT.split())
    ]
    tl = {
        "provenance": PROV,
        "project": "demo",
        "fps": 30,
        "total_s": 4.0,
        "words": words,
        "scenes": [{"scene": "s01", "start_s": 0, "end_s": 4.0, "voice_start_s": 0.2, "voice_end_s": 3.9}],
    }
    (base / "timeline.json").write_text(json.dumps(tl))
    groups = group_words([TimelineWord(**w) for w in words], CFG.create.design.captions["vertical"])
    caps = {
        "provenance": PROV,
        "project": "demo",
        "frame": "vertical",
        "groups": [g.model_dump() for g in groups],
    }
    (base / "captions.json").write_text(json.dumps(caps))
    edl = {
        "provenance": PROV,
        "project": "demo",
        "fps": 30,
        "applied": [],
        "duration_frames": 120,
        "segments": [
            {"take": "t", "src_in": 0, "src_out": 60, "rec_in": 0},
            {"take": "t", "src_in": 60, "src_out": 120, "rec_in": 60},
        ],
    }
    (base / "edl.json").write_text(json.dumps(edl))
    seg = {
        "take": "t",
        "face": [430, 640, 220, 260],
        "zoom": 1.0,
        "full": {"x": 0, "y": 0, "w": 1080, "h": 1920},
        "pip": {"x": 0, "y": 0, "w": 9, "h": 9},
    }
    framing = {
        "provenance": PROV,
        "project": "demo",
        "frame": "vertical",
        "width": 1080,
        "height": 1920,
        "segments": [seg | {"segment": 0}, seg | {"segment": 1}],
    }
    (base / "framing.json").write_text(json.dumps(framing))
    tokens = json.loads((REPO_ROOT / "projects/acme-v2/tokens.json").read_text())
    tokens["frame"] = "vertical"
    tokens["captions"] = {
        **tokens["captions"],
        "kind": "karaoke",
        "size_px": 64,
        "max_width_px": 480,
        "background": None,
        "stroke": "ink",
        "stroke_px": 7,
        "uppercase": True,
        "padding_px": [0, 0],
        "text": "surface",
        "active": "accent",
    }
    (base / "tokens.json").write_text(json.dumps(tokens))
    (base / "brief.yaml").write_text("brand: acme\nlanguage: en\n")
    return tmp_path


def _plan(root: Path, items: list[dict], layout: str = "split") -> Path:
    p = root / "projects" / "demo" / "reel.yaml"
    p.write_text(
        yaml.safe_dump({"layout": [{"word": 0, "layout": layout}], "product_bg": "ink", "items": items})
    )
    return p


GOOD = {
    "word": 0,
    "until": 12,
    "kind": "chat",
    "where": "product",
    "marks": [0, 6, 7, 12],
    "spec": {"app": "ChatGPT", "prompt": "Best restaurant in Budapest", "answer": ["1. **Jade Garden**"]},
}


def test_build_writes_the_composition_and_its_data(take: Path):
    from create.footage.reel import build

    comp, meta = build(take, "demo", CFG, _plan(take, [GOOD]))
    data = json.loads((comp / "reel-data.json").read_text())
    assert (comp / "index.html").exists() and (comp / "assets" / "motion.js").exists()
    assert data["items"][0]["box"][3] < 1040 and meta["product"]["items"][0]["kind"] == "chat"
    assert all(c["zone"] == "seam" for c in meta["captions"])  # split: captions above the seam


def test_plan_checks_find_unshown_names_and_the_render_refuses_errors(take: Path):
    from create.footage.reel import run_reel
    from create.footage.reel_check import run_check

    found = run_check(take, "demo", CFG, _plan(take, [GOOD]), browser=False)
    assert [f.rule for f in found if f.level == "error"] == []
    bad = GOOD | {"kind": "cta", "spec": {"text": "Start"}, "marks": []}  # no url, and the names go unshown
    found = run_check(take, "demo", CFG, _plan(take, [bad]), browser=False)
    assert {"spec", "names"} <= {f.rule for f in found}
    with pytest.raises(ValueError, match="check errors"):
        run_reel(take, "demo", CFG, _plan(take, [bad]))  # refused before a render


def test_layout_checks_measure_the_page(take: Path):
    from create.browser import available

    if not available():
        pytest.skip("needs playwright and Chromium")
    from create.footage.reel_check import run_check

    found = run_check(take, "demo", CFG, _plan(take, [GOOD]), browser=True)
    assert [f for f in found if f.level == "error"] == []
    on_face = {
        "word": 0,
        "until": 12,
        "kind": "review",
        "position": "chest",
        "w": 1000,
        "spec": {"text": "Great view and the duck was really good.", "stars": 5},
    }
    rules = {f.rule for f in run_check(take, "demo", CFG, _plan(take, [on_face], "full"), browser=True)}
    assert rules & {"safe-area", "on-face", "on-captions", "small-text", "names"}


def test_props_and_effects_build_into_the_page(take: Path):
    """ADR 0027: a drawn fish and cat with styles, accessories and a carry, and effects, in room space."""
    from create.footage.reel import build

    p = take / "projects" / "demo" / "reel.yaml"
    p.write_text(
        yaml.safe_dump(
            {
                "layout": [{"word": 0, "layout": "full"}],
                "props": [
                    {
                        "id": "fred",
                        "art": "fish",
                        "word": 1,
                        "until": 12,
                        "at": "lap",
                        "style": "photo",
                        "beats": [
                            {"word": 3, "style": "pixel"},
                            {"word": 4, "add": ["top_hat"], "tag": "Fred"},
                        ],
                    },
                    {
                        "id": "pixie",
                        "art": "cat",
                        "word": 6,
                        "until": 12,
                        "enter": "walk_left",
                        "exit": "run_right",
                        "beats": [{"word": 9, "carry": "fred"}],
                    },
                ],
                "fx": [{"word": 2, "until": 4, "kind": "anime"}, {"word": 11, "kind": "fade_black"}],
            }
        )
    )
    comp, _ = build(take, "demo", CFG, p)
    data = json.loads((comp / "reel-data.json").read_text())
    assert [t["id"] for t in data["props"]] == ["fred", "pixie"]
    assert (comp / "assets" / "props" / "fred-pixel.png").exists() and (comp / "assets" / "props.js").exists()
    assert data["props"][1]["carry"]["acc"] == ["top_hat"] and data["matte"] is False  # anime falls back
    html = (comp / "index.html").read_text()
    assert 'id="room"' in html and "{{" not in html


def test_a_motion_style_carries_cards_into_each_other_under_one_step_label(take: Path):
    """ADR 0033: `motion: {style: paper}` makes the second card take over from the first (morph), the two
    share one step label, the shots push in and out in turn, and the page still passes the layout checks."""
    from create.footage.reel import build
    from create.footage.reel_check import run_check

    first = {
        **GOOD,
        "until": 5,
        "marks": [0, 2, 3, 5],
        "spec": {**GOOD["spec"], "kicker": "Ask", "step": "1/2"},
    }
    second = {
        "word": 6, "until": 12, "kind": "sources", "where": "product", "marks": [7, 9],
        "spec": {"title": "Sources", "items": [{"name": "Maps"}, {"name": "Blog"}], "kicker": "Ask",
                 "step": "2/2"},
    }  # fmt: skip
    p = take / "projects" / "demo" / "reel.yaml"
    p.write_text(yaml.safe_dump({"layout": [{"word": 0, "layout": "split"}], "product_bg": "canvas",
                                 "motion": {"style": "paper"}, "items": [first, second]}))  # fmt: skip
    comp, meta = build(take, "demo", CFG, p)
    data = json.loads((comp / "reel-data.json").read_text())
    assert data["motion"]["style"] == "paper" and data["motion"]["handover"] == "morph"
    assert data["motion"]["push_alternate"] is True and data["cuts"] == [2.0]
    a, b = data["items"]
    assert b["handover"] == "morph" and b["prev"] == 0 and a["handover_out"] == "morph"
    assert a["t1"] == pytest.approx(b["t0"] + CFG.create.footage.reel.handover_s, abs=0.06)
    assert a["spec"]["motion"] == "rise" and "kicker" not in a["spec"] and a["align"] == "top"
    (run,) = data["kickers"]
    assert run["text"] == "Ask" and [s[1] for s in run["steps"]] == ["1/2", "2/2"]
    assert run["box"][3] - run["box"][1] == CFG.create.footage.reel.kicker_h
    assert a["box"][1] == run["box"][3]
    assert meta["product"]["items"][1]["handover"] == "morph"
    html = (comp / "index.html").read_text()
    assert 'id="pbg"' in html and 'id="pwidgets"' in html
    found = run_check(take, "demo", CFG, p, browser=True)
    assert [f for f in found if f.level == "error"] == []
