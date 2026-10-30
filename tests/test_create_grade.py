"""C8 grade (ADR 0032): the checks code makes on a motion build, on synthetic inputs."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from create import browser
from create.grade import (
    BudgetError,
    browse,
    colour_findings,
    decoration_findings,
    dom_findings,
    duration_findings,
    ease_family,
    ease_findings,
    hold_findings,
    move_findings,
    new_round,
    seam_findings,
    sfx_findings,
    spend,
)
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import MotionGrade, TimelineScene

CFG = load_config()
G = CFG.create.motion.grade
COLORS = {
    "canvas": "#F5F7FA",
    "surface": "#FFFFFF",
    "ink": "#3E0863",
    "accent": "#00AA90",
    "hairline": "#E5E7EB",
}


def _levels(findings, area=None):
    return [f.level for f in findings if area is None or f.area == area]


def test_colours_allow_tokens_and_their_tints_only():
    ok = '<div style="color:#3E0863;background:#E6F6F4"></div>'  # ink; accent at ~10% over white
    assert colour_findings(ok, COLORS, G) == []
    bad = colour_findings('<i style="color:#B6BDC8"></i>', COLORS, G)
    assert _levels(bad) == ["fail"] and "#B6BDC8" in bad[0].msg


@pytest.mark.parametrize(
    "css",
    [
        "background:linear-gradient(#fff,#000)",
        "text-decoration: underline",
        "backdrop-filter: saturate(1.2)",
        "filter: blur(12px)",
    ],
)
def test_banned_decoration_fails(css):
    assert _levels(decoration_findings(f"<style>.a{{{css}}}</style>", G)) == ["fail"]


def test_small_blur_and_plain_css_pass_but_em_dash_warns():
    assert decoration_findings("<style>.a{filter:blur(1px)}</style><p>ok</p>", G) == []
    assert _levels(decoration_findings("<p>fast — and clear</p>", G)) == ["warn"]


def test_long_moves_warn_and_ambient_drift_is_not_a_move():
    tweens = [{"d": 0.6, "s": 1.0}, {"d": 1.5, "s": 2.0}, {"d": 15.0, "s": 0.0}, {"d": 0.0, "s": 3.0}]
    findings, moves = move_findings(tweens, G)
    assert moves == 2
    assert _levels(findings) == ["warn"] and "1.50" in findings[0].msg


@pytest.mark.parametrize(
    ("ease", "family"),
    [
        ("power3.out", "ease_out"),
        ("power2", "ease_out"),
        ("expo.inOut", "ease_in_out"),
        ("circ.in", "ease_in"),
        ("back.out(1.7)", "spring_overshoot"),
        ("elastic.out(1, 0.3)", "spring_overshoot"),
        ("none", "linear"),
        ("steps(12)", "linear"),
        ("custom", None),
    ],
)
def test_gsap_eases_map_to_corpus_families(ease, family):
    assert ease_family(ease) == family


def _moves(*eases, a=0.01):
    return [{"d": 0.5, "s": float(i), "e": e, "a": a} for i, e in enumerate(eases)]


def test_one_ease_everywhere_warns_and_a_mix_passes():
    flat = ease_findings(_moves(*["power3.out"] * 10), 0.14, G)
    assert _levels(flat) == ["warn"] and "1 ease families" in flat[0].msg
    mixed = _moves(*["power3.out"] * 6, "power2.inOut", "power2.inOut", "none", "back.out(2)")
    assert ease_findings(mixed, 0.14, G) == []
    assert ease_findings(_moves("power3.out", "power3.out"), 0.14, G) == []  # too few moves to count


def test_overshoot_past_its_share_or_on_a_large_element_warns():
    many = _moves(*["back.out"] * 5, "power3.out", "power2.inOut", "none")
    assert any("overshoot on 5 of 8" in f.msg for f in ease_findings(many, 0.14, G))
    card = [
        *_moves("power3.out", "power2.inOut", "none", "power3.out"),
        {"d": 0.5, "s": 4.0, "e": "back.out", "a": 0.2},
    ]
    found = ease_findings(card, 0.14, G)
    assert len(found) == 1 and "large elements" in found[0].msg and found[0].t == 4.0


def _scene(sid, a, b):
    return TimelineScene(scene=sid, start_s=a, end_s=b, voice_start_s=a + 0.2, voice_end_s=b - 0.5)


def test_the_frame_must_keep_moving_through_a_handover():
    scenes = [_scene("s01", 0.0, 4.0), _scene("s02", 4.0, 8.0)]  # handover window 3.5-4.5 s
    carried = [{"d": 1.0, "s": 3.4, "e": "power2.inOut"}, {"d": 0.5, "s": 4.3, "e": "power3.out"}]
    assert seam_findings(carried, scenes, 8.0, G) == []
    settled = [{"d": 0.5, "s": 2.5, "e": "power3.out"}, {"d": 0.5, "s": 4.2, "e": "power3.out"}]
    found = seam_findings(settled, scenes, 8.0, G)
    assert _levels(found) == ["warn"] and found[0].t == 3.5 and "s02" in found[0].msg
    drift = [{"d": 12.0, "s": 0.0, "e": "sine.inOut"}]  # ambient drift is not a move
    assert _levels(seam_findings(drift, scenes, 8.0, G)) == ["warn"]


def test_holds_cuts_and_idle():
    fps, dur, high = 30.0, 25.0, 4.5
    holds = [(30, 60, True), (90, 300, False), (600, 750, False)]  # dead; 7 s idle; the final hold
    findings = hold_findings(holds, [("hard_cut", 400), ("crossfade", 500)], fps, dur, high)
    assert sorted((f.area, f.level) for f in findings) == [
        ("pacing", "fail"),
        ("pacing", "fail"),
        ("pacing", "warn"),
        ("pacing", "warn"),
    ]
    assert any("crossfades at 16.67" in f.msg for f in findings)
    assert any("hard cut" in f.msg for f in findings) and any("dead hold" in f.msg for f in findings)


def test_sfx_count_names_and_times(tmp_path: Path):
    lib = tmp_path / "sfx"
    lib.mkdir()
    (lib / "pop.mp3").write_bytes(b"x")
    cues = [{"t": 1.0, "sfx": "pop", "gain_db": -6}] * 3
    per_min = {"median": 38.0, "low": 13.4, "high": 57.0}
    assert _levels(sfx_findings(cues, 25.0, per_min, lib)) == ["warn"]  # 3 < 6
    cues = [{"t": 1.0 + i, "sfx": "pop", "gain_db": -6} for i in range(10)]
    assert sfx_findings(cues, 25.0, per_min, lib) == []
    bad = [*cues, {"t": 30.0, "sfx": "pop", "gain_db": -6}, {"t": 2.0, "sfx": "boing", "gain_db": -6}]
    assert _levels(sfx_findings(bad, 25.0, per_min, lib)) == ["fail", "fail"]


CORNER_LOGO = {"box": [1760, 990, 1880, 1040], "covered": False}  # clear of every test box


def _sample(t, texts=(), logos=(CORNER_LOGO,), accent=0.0):
    return {"t": t, "texts": list(texts), "logos": list(logos), "accent": accent}


def test_small_text_fails_only_when_it_stays_small():
    step = G.sample_step_s
    tiny = {"text": "Example data", "px": 14.0, "box": [0, 0, 100, 20]}
    entering = {"text": "Headline", "px": 10.0, "box": [0, 100, 400, 140]}
    samples = [_sample(i * step, [tiny] + ([entering] if i == 0 else [])) for i in range(8)]
    findings, measures = dom_findings(samples, 24.0, G)
    assert [(f.area, f.level) for f in findings] == [("text", "fail")]
    assert "Example data" in findings[0].msg and measures["min_text_px"] == 14.0


def test_accent_overspend_warns():
    samples = [_sample(i * G.sample_step_s, accent=2.5) for i in range(8)]
    findings, measures = dom_findings(samples, 24.0, G)
    assert _levels(findings, "accent") == ["warn"] and measures["max_accent_moments"] == 2.5


def test_lasting_overlaps_fail_and_fly_throughs_pass():
    step = G.sample_step_s
    a = {"text": "Ask ChatGPT", "px": 72.0, "box": [100, 100, 700, 180]}
    b = {"text": "Your brand", "px": 32.0, "box": [400, 150, 800, 200]}
    logo = {"box": [450, 120, 650, 170], "covered": False}
    lasting = [_sample(i * step, [a, b]) for i in range(6)]
    assert _levels(dom_findings(lasting, 24.0, G)[0], "overlap") == ["fail"]
    passing = [_sample(0.0, [a, b])] + [_sample(i * step, [a]) for i in range(1, 6)]
    assert dom_findings(passing, 24.0, G)[0] == []
    on_logo = [_sample(i * step, [a], [logo]) for i in range(6)]
    assert _levels(dom_findings(on_logo, 24.0, G)[0], "overlap") == ["fail"]


def test_the_close_needs_a_visible_logo():
    logo = {"box": [700, 400, 1200, 550], "covered": False}
    hidden = {**logo, "covered": True}  # a card grew over it
    url = {"text": "acme.example", "px": 40.0, "box": [800, 600, 1100, 650]}
    ok = [_sample(i * G.sample_step_s, [url], [logo]) for i in range(8)]
    assert _levels(dom_findings(ok, 24.0, G)[0], "brand") == []
    covered = [_sample(i * G.sample_step_s, [url], [hidden]) for i in range(8)]
    assert _levels(dom_findings(covered, 24.0, G)[0], "brand") == ["fail"]
    gone = [_sample(i * G.sample_step_s, [url], []) for i in range(8)]
    assert _levels(dom_findings(gone, 24.0, G)[0], "brand") == ["fail"]


def test_pieces_of_one_line_never_overlap_each_other():
    num = {"text": "38", "px": 40.0, "box": [100, 100, 160, 150], "group": 7}
    unit = {"text": "%", "px": 40.0, "box": [150, 100, 180, 150], "group": 7}
    samples = [_sample(i * G.sample_step_s, [num, unit]) for i in range(6)]
    assert dom_findings(samples, 24.0, G)[0] == []


def test_the_budget_stops_a_round_and_a_new_round_resets_it(tmp_path: Path):
    assert spend(tmp_path, "demo", "grades", 1, 2) == 1
    assert spend(tmp_path, "demo", "grades", 1, 2) == 0
    with pytest.raises(BudgetError, match="2 of 2 grades"):
        spend(tmp_path, "demo", "grades", 1, 2)
    assert spend(tmp_path, "demo", "frames", 6, 6) == 0  # counted separately
    new_round(tmp_path, "demo")
    assert spend(tmp_path, "demo", "grades", 1, 2) == 1


def test_duration_must_match_the_film():
    assert duration_findings('<div id="main" data-duration="25">', 25.0) == []
    assert _levels(duration_findings('<div id="main" data-duration="27.18">', 25.0)) == ["fail"]
    assert _levels(duration_findings("<div id='main'>", 25.0)) == ["fail"]


# --- end to end: a 2 s build in a temporary project (needs Chromium, npx and the GSAP cache) ---------------

GSAP = sorted((REPO_ROOT / "data" / "create" / "_cache").glob("gsap-*.min.js"))
BUILD = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="assets/fonts.css">
<script src="assets/gsap.min.js"></script>
<style>#main{position:relative;width:1920px;height:1080px;overflow:hidden;background:#F5F7FA}
h1{position:absolute;left:160px;top:420px;margin:0;font:700 120px sans-serif;color:#3E0863}
.box{position:absolute;left:160px;top:640px;width:600px;height:120px;background:#FFFFFF;
border:1px solid #E5E7EB}
</style></head><body>
<div id="main" data-composition-id="main" data-width="1920" data-height="1080" data-start="0"
 data-duration="2">
<h1 id="hl">Hello there</h1><div class="box" id="bx"></div>
<img id="logo" src="assets/logo.svg" alt="Acme"
 style="position:absolute;left:1500px;top:900px;height:96px"></div>
<script>const tl = gsap.timeline({paused: true});
tl.from("#hl", {y: 60, opacity: 0, duration: 0.5, ease: "circ.out"}, 0.1);
tl.from("#bx", {scaleX: 0, duration: 0.6, ease: "circ.out"}, 0.4);
tl.to("#bx", {x: 300, duration: 0.6, ease: "circ.inOut"}, 1.0);
tl.set({}, {}, 2);
window.__timelines = {main: tl};</script></body></html>"""


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    if not GSAP or not browser.available() or shutil.which("npx") is None:
        pytest.skip("needs the GSAP cache, Playwright + Chromium and npx")
    monkeypatch.setattr("create.grade.fonts", lambda cache, url: ("", []))  # no network in tests
    for rel in (
        "config/lens.yaml",
        "exports/pacing.json",
        "exports/sound-spec.json",
        "exports/motion-tokens.json",
    ):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, tmp_path / rel)
    shutil.copytree(REPO_ROOT / "brands" / "acme", tmp_path / "brands" / "acme")
    cache = tmp_path / "data" / "create" / "_cache"
    cache.mkdir(parents=True)
    shutil.copy(GSAP[-1], cache / GSAP[-1].name)
    sfx = cache / "sfx"
    sfx.mkdir()
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=f=880:d=0.1", str(sfx / "pop.mp3")], check=True
    )
    monkeypatch.setattr("create.grade.sfx_library", lambda cache, render: sfx)
    base = tmp_path / "projects" / "demo"
    shutil.copytree(REPO_ROOT / "projects" / "demo25", base)
    brief = yaml.safe_load((base / "brief.yaml").read_text())
    brief.update(project="demo", cut_s=None)
    (base / "brief.yaml").write_text(yaml.safe_dump(brief, sort_keys=False))
    tl = json.loads((base / "timeline.json").read_text())
    tl.update(
        project="demo",
        total_s=2.0,
        scenes=[{**tl["scenes"][0], "start_s": 0.0, "end_s": 2.0, "voice_start_s": 0.2, "voice_end_s": 1.5}],
        words=[{**tl["words"][0], "start_s": 0.2, "end_s": 0.5}],
    )
    (base / "timeline.json").write_text(json.dumps(tl))
    (base / "motion").mkdir(exist_ok=True)
    (base / "motion" / "index.html").write_text(BUILD)
    (base / "motion" / "sfx.json").write_text(json.dumps([{"t": 0.1, "sfx": "pop", "gain_db": -9}]))
    return tmp_path


def test_grade_end_to_end(project: Path):
    from create.grade import run_grade

    grade = run_grade(project, "demo", load_config(project / "config" / "lens.yaml"))
    path = project / "projects" / "demo" / "motion" / "grade.json"
    assert MotionGrade.model_validate_json(path.read_text()) == grade
    assert grade.duration_s == 2.0 and grade.measures.moves == 3 and grade.measures.sfx == 1
    assert grade.measures.min_text_px == pytest.approx(120.0)
    assert not [f for f in grade.findings if f.area in ("text", "brand", "overlap", "timing")]
    _, tweens = browse(project / "data/create/demo/motion/render/index.html", 2.0, "#00AA90", G)
    moves = sorted((t["s"], t["e"]) for t in tweens if t["d"] > 0)
    assert moves == [(0.1, "circ.out"), (0.4, "circ.out"), (1.0, "circ.inOut")]
    assert all(0 < t["a"] < 1 for t in tweens if t["d"] > 0)
    video = project / "data" / "create" / "demo" / "motion" / "render" / "video.mp4"
    frames = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v",
            "-show_entries",
            "stream=nb_read_frames",
            "-of",
            "csv=p=0",
            str(video),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert int(frames) == 60
