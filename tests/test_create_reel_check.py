"""create reel --check: the plan and layout checks catch what reviews of Robert's first take kept finding."""

import json

from create.footage.reel_check import judge, kit_names, plan_findings, sample_times, spoken_names
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import Timeline

CFG = load_config(REPO_ROOT / "config" / "lens.yaml")
CHK = CFG.create.footage.reel.check
V = CFG.create.design.frames["vertical"]
PROV = json.loads((REPO_ROOT / "projects/acme-v2/tokens.json").read_text())["provenance"]


def _timeline(text: str, step: float = 0.5) -> Timeline:
    words = [{"i": i, "text": w, "start_s": i * step, "end_s": i * step + 0.4, "scene": "s01"}
             for i, w in enumerate(text.split())]  # fmt: skip
    total = len(words) * step + 1
    return Timeline.model_validate({
        "provenance": PROV, "project": "demo", "fps": 30, "total_s": total,
        "scenes": [{"scene": "s01", "start_s": 0, "end_s": total, "voice_start_s": 0, "voice_end_s": total}],
        "words": words,
    })  # fmt: skip


def _data(items, layout="full", duration=20.0):
    return {"duration": duration, "transition": 0.6, "punches": [],
            "poses": [{"t": 0.0, "layout": layout}], "items": items}  # fmt: skip


def _item(**kw):
    return {"kind": "chat", "where": "overlay", "title": "chat", "t0": 0.0, "t1": 3.0, "marks": [],
            "spec": {"prompt": "x"}} | kw  # fmt: skip


def test_names_said_but_not_shown_are_flagged():
    tl = _timeline(
        'Type it in, like "Best Chinese restaurant in Budapest," or in Bucharest, or even New York.'
    )
    assert spoken_names(tl, 0, 20) == ["Best", "Chinese", "Budapest", "Bucharest", "New", "York"]
    item = _item(t1=8.0, marks=[1.0, 2.0, 3.0], spec={"prompt": "Best Chinese restaurant in Budapest"})
    msgs = [f.message for f in plan_findings(_data([item]), tl, CHK) if f.rule == "names"]
    assert msgs and "Bucharest" in msgs[0] and "Budapest" not in msgs[0]


def test_long_holds_empty_product_and_missing_fields_are_found():
    tl = _timeline("one two three four five six seven eight nine ten eleven twelve")
    hold = _item(t0=0.0, t1=CHK.max_beat_gap_s + 3)  # one card, no beats, too long
    bare = _item(kind="cta", t0=1.0, t1=2.0, spec={"text": "Start"})  # no url
    found = plan_findings(_data([hold, bare]), tl, CHK)
    assert {"long-hold", "spec"} <= {f.rule for f in found}
    split = _data(
        [_item(where="product", t0=0.3, t1=2.0), _item(where="product", t0=5.0, t1=9.0)], "split", 9.0
    )
    empty = [f for f in plan_findings(split, tl, CHK) if f.rule == "empty-product"]
    assert empty and abs(empty[0].at_s - 2.0) < 1e-6


def test_layout_judge_flags_rail_face_captions_and_tiny_text():
    items = [_item(where="overlay", t0=0.0, t1=4.0)]
    face = (400.0, 600.0, 700.0, 900.0)
    measures = [
        {
            "item": 0,
            "t": 1.0,
            "rect": [600, 1000, 900, 1200],
            "min_text": 20,
            "captions": [],
        },  # under the rail
        {"item": 0, "t": 2.0, "rect": [200, 850, 600, 1100], "min_text": 40, "captions": []},  # on the chin
        {
            "item": 0,
            "t": 3.0,
            "rect": [200, 300, 700, 500],
            "min_text": 40,
            "captions": [[250, 350, 650, 450]],
        },
    ]
    rules = [(f.rule, f.at_s) for f in judge(measures, items, V, CHK, {1.0: face, 2.0: face, 3.0: face})]
    assert ("safe-area", 1.0) in rules and ("small-text", 1.0) in rules
    assert ("on-face", 2.0) in rules and ("on-captions", 3.0) in rules
    ok = [{"item": 0, "t": 1.0, "rect": [140, 1000, 700, 1200], "min_text": 40, "captions": []}]
    assert judge(ok, items, V, CHK, {1.0: face}) == []


def test_widgets_are_measured_once_landed_and_once_built():
    times = sample_times([_item(t0=0.0, t1=6.0, marks=[1.0, 3.0])])
    assert [t for _, t in times] == [0.8, 3.45]


def test_review_brief_names_the_files_zones_and_notes(tmp_path):
    from create.footage.review import RUBRIC, brief, entrance_times

    meta = {"overlays": {"items": [{"t0": t} for t in (1.0, 9.0, 4.0)]}, "product": {"items": [{"t0": 12.0}]}}
    assert entrance_times(meta) == [4.0, 9.0, 12.0]  # second, middle, last
    files = {"sheet": tmp_path / "sheet.png", "motion": tmp_path / "motion.png"}
    text = brief(tmp_path / "v.mp4", files, V, "Captions never on my face.", 2.5)
    assert str(files["sheet"]) in text and str(files["motion"]) in text
    assert "Captions never on my face." in text and all(r in text for r in RUBRIC)
    assert f"x {V.safe[0].x0}-{V.safe[0].x1}" in text


def test_settled_frames_are_frame_exact_and_named_in_the_brief(tmp_path):
    import subprocess

    from PIL import Image

    from create.footage.review import brief, settled

    video = tmp_path / "v.mp4"  # red for one second, then blue: a frame on each side of the change
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=108x192:r=30:d=1",
                    "-f", "lavfi", "-i", "color=c=blue:s=108x192:r=30:d=1", "-filter_complex",
                    "[0:v][1:v]concat=n=2:v=1[v]", "-map", "[v]", "-pix_fmt", "yuv420p", str(video)],
                   check=True)  # fmt: skip
    sheet = Image.open(settled(video, [29 / 30, 1.0], tmp_path)).convert("RGB")
    left, right = sheet.getpixel((300, 400)), sheet.getpixel((660, 400))
    assert left[0] > 200 > left[2] and right[2] > 200 > right[0]  # the last red frame, the first blue one
    files = {
        "sheet": tmp_path / "sheet.png",
        "motion": tmp_path / "m.png",
        "settled": tmp_path / "settled.png",
    }
    assert str(files["settled"]) in brief(tmp_path / "v.mp4", files, V, "", 2.5)


def test_unknown_pixel_sprites_and_motions_fail_the_check():
    sprites, motions = kit_names()
    assert {"robot", "trophy", "heart"} <= sprites and {"rise", "pop", "flip", "pixel"} <= motions
    tl = _timeline("one two three four five six")
    ok = _item(kind="pixel", spec={"sprite": "robot", "motion": "flip"})
    bad = _item(kind="pixel", spec={"sprite": "unicorn", "motion": "wobble"})
    icon = _item(kind="sticker", spec={"text": "Top", "icon": "px:nope"})
    assert not [f for f in plan_findings(_data([ok]), tl, CHK) if f.rule == "spec"]
    msgs = [f.message for f in plan_findings(_data([bad, icon]), tl, CHK) if f.rule == "spec"]
    assert (
        any("unicorn" in m for m in msgs)
        and any("wobble" in m for m in msgs)
        and any("nope" in m for m in msgs)
    )


def test_pixel_sprites_and_font_are_well_formed():
    import re

    js = (REPO_ROOT / "create" / "kit" / "motion.js").read_text()
    letters = set(re.findall(r"\b([a-z]): \"", re.search(r"const PAL = \{(.*?)\};", js, re.S).group(1)))
    block = js[js.index("const PX = {") : js.index("};", js.index("const PX = {"))]
    for name, body in re.findall(r"(\w+): \[(.*?)\]", block, re.S):
        rows = re.findall(r'"([^"]*)"', body)
        assert rows and len({len(r) for r in rows}) == 1, f"{name}: rows of different widths"
        assert set("".join(rows)) <= letters | {"."}, f"{name}: a colour outside the palette"
        assert len(rows[0]) <= 16 and len(rows) <= 16  # pixel art stays chunky enough to read on a phone
    font = js[js.index("const FONT = {") : js.index("};", js.index("const FONT = {"))]
    glyphs = re.findall(r':\s*"([01]+)"', font)
    assert len(glyphs) >= 36 and all(len(g) == 15 for g in glyphs)  # 3x5
