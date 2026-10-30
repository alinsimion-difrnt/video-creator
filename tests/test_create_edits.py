"""create edits: Robert's own crops, zoom changes and notes land exactly as he set them."""

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from create.browser import available, launch
from create.footage.editpage import run_edit_page
from create.footage.edits import apply_plan, load_plan, merge, read_answer, write_edits
from create.footage.reframe import fill_crop, plan
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import Edits, Edl, PlanEdit, ReelPlan, ShotEdit
from lens.validate import validate_file

CFG = load_config(REPO_ROOT / "config" / "lens.yaml")
R = CFG.create.footage.reframe
PROV = json.loads((REPO_ROOT / "projects/acme-v2/tokens.json").read_text())["provenance"]
FACE = [860.0, 300.0, 200.0, 260.0]


def _edl(segs: list[tuple[str, int, int]], fps: int = 30) -> Edl:
    rec, out = 0, []
    for take, a, b in segs:
        out.append({"take": take, "src_in": a, "src_out": b, "rec_in": rec})
        rec += b - a
    return Edl.model_validate(
        {
            "provenance": PROV,
            "project": "demo",
            "fps": fps,
            "segments": out,
            "applied": [],
            "duration_frames": rec,
        }
    )


def _plan(**kw: object) -> ReelPlan:
    return ReelPlan.model_validate({"layout": [{"word": 0, "layout": "full"}], **kw})


def test_shift_moves_the_crop_by_a_share_of_its_size_and_stays_inside():
    a = fill_crop(1920, 1080, 1080, 1920, FACE, 1.0, R.eye_line)
    b = fill_crop(1920, 1080, 1080, 1920, FACE, 1.0, R.eye_line, (0.1, 0.0))
    assert b.x - a.x == pytest.approx(0.1 * a.w, abs=1) and b.y == a.y
    edge = fill_crop(1920, 1080, 1080, 1920, [1500, 300, 200, 260], 1.0, R.eye_line, (1.0, 1.0))
    assert edge.x + edge.w == 1920 and edge.y + edge.h == 1080  # pushed past the master: held at its edge


def test_an_edited_shot_takes_his_zoom_and_the_others_keep_alternating():
    edl = _edl([("t", 0, 30), ("t", 40, 70), ("t", 80, 110)])
    tracks = {"t": [(0.5, FACE), (1.5, FACE), (3.0, FACE)]}
    sizes = {"t": (1920, 1080)}
    auto = plan(edl, sizes, tracks, 1080, 1920, R)
    assert [s.zoom for s in auto] == [1.0, R.punch_in, 1.0]
    edits = {("t", 40): ShotEdit(take="t", src_in=40, zoom=1.0, dx=0.0, dy=-0.05)}
    got = plan(edl, sizes, tracks, 1080, 1920, R, edits)
    assert [s.zoom for s in got] == [1.0, 1.0, 1.0]  # his 1.0 on shot 2; shot 3 still the auto 1.0
    assert got[1].full == fill_crop(1920, 1080, 1080, 1920, FACE, 1.0, R.eye_line, (0.0, -0.05))
    assert got[0] == auto[0] and got[2] == auto[2]


def test_plan_edits_set_the_push_drop_quick_zooms_and_rescale_or_remove_held_ones():
    p = _plan(push=1.05, punches=[3, 7], zooms=[{"word": 10, "until": 12}, {"word": 20, "until": 22}])
    e = PlanEdit(
        push=1.0, drop_punches=[7, 99], zooms=[{"word": 10, "scale": 1.1}, {"word": 20, "scale": 1.0}]
    )
    got = apply_plan(p, e)
    assert got.push == 1.0 and got.punches == [3]
    assert [(z.word, z.scale) for z in got.zooms] == [(10, 1.1)]
    assert apply_plan(p, None) is p


def test_answers_merge_into_the_edits_file():
    head = {"edits": "demo", "plan": "reel-overlay.yaml"}
    first = merge(
        Edits(),
        {
            **head,
            "shots": [{"take": "t", "src_in": 40, "zoom": 1.2, "dx": 0, "dy": 0}],
            "drop_punches": [7],
            "notes": [{"t": 3.2, "text": "sticker on my face"}],
        },
    )
    second = merge(
        first,
        {
            **head,
            "shots": [{"take": "t", "src_in": 40, "zoom": 1.05, "dx": 0.1, "dy": 0}],
            "push": 1.02,
            "drop_punches": [3],
            "zooms": [{"word": 10, "scale": 1}],
        },
    )
    assert [(s.src_in, s.zoom, s.dx) for s in second.shots] == [(40, 1.05, 0.1)]
    pe = second.plans["reel-overlay.yaml"]
    assert (
        pe.push == 1.02 and pe.drop_punches == [3, 7] and [(z.word, z.scale) for z in pe.zooms] == [(10, 1.0)]
    )
    assert [(n.t, n.plan) for n in second.notes] == [(3.2, "reel-overlay.yaml")]


def test_the_answer_is_found_in_pasted_text():
    assert read_answer('here:\n```json\n{"edits": "demo", "plan": null}\n```')["edits"] == "demo"
    with pytest.raises(ValueError):
        read_answer("too zoomed in at 0:32")
    with pytest.raises(ValueError):
        Edits.model_validate({"shots": [{"take": "t", "src_in": 1, "zoom": 1}] * 2})


def test_create_reel_reads_the_plan_with_his_changes(tmp_path: Path):
    base = tmp_path / "projects" / "demo"
    base.mkdir(parents=True)
    (base / "reel-overlay.yaml").write_text(yaml.safe_dump(_plan(punches=[3, 7]).model_dump(mode="json")))
    write_edits(base, Edits(plans={"reel-overlay.yaml": PlanEdit(drop_punches=[3])}))
    assert load_plan(base, base / "reel-overlay.yaml").punches == [7]
    assert validate_file(base / "edits.yaml", tmp_path).ok


def _ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Two shots of one 640x360 take, framed for a 1080x1920 frame, with a quick zoom and a held zoom."""
    base = tmp_path / "projects" / "demo"
    base.mkdir(parents=True)
    master = tmp_path / "data" / "create" / "demo" / "footage" / "master" / "t.mov"
    master.parent.mkdir(parents=True)
    _ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "testsrc=s=640x360:r=30:d=4",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(master),
    )
    render = tmp_path / "render.mp4"
    _ffmpeg("-f", "lavfi", "-i", "color=c=0x6699cc:s=108x192:r=30:d=3", "-f", "lavfi", "-i", "sine=d=3",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(render))  # fmt: skip
    edl = _edl([("t", 0, 45), ("t", 60, 105)])
    face = [300.0, 100.0, 60.0, 80.0]
    segs = plan(edl, {"t": (640, 360)}, {"t": [(0.5, face), (2.5, face)]}, 1080, 1920, R)
    (base / "edl.json").write_text(edl.model_dump_json())
    (base / "framing.json").write_text(json.dumps({
        "provenance": PROV, "project": "demo", "frame": "vertical", "width": 1080, "height": 1920,
        "segments": [s.model_dump() for s in segs]}))  # fmt: skip
    (base / "footage.json").write_text(json.dumps({"provenance": PROV, "project": "demo", "fps": 30,
        "takes": [
        {"id": "t", "raw": "r", "master": str(master.relative_to(tmp_path)), "audio": "a", "width": 640,
         "height": 360, "frames": 120, "duration_s": 4.0, "source_fps": "30", "hdr": False}]}))  # fmt: skip
    words = ["Ask", "the", "model", "for", "sources", "now."]
    (base / "timeline.json").write_text(json.dumps({
        "provenance": PROV, "project": "demo", "fps": 30, "total_s": 3.0,
        "scenes": [{"scene": "s01", "start_s": 0.0, "end_s": 3.0, "voice_start_s": 0.0, "voice_end_s": 2.9}],
        "words": [{"i": i, "text": w, "start_s": 0.5 * i, "end_s": 0.5 * i + 0.4, "scene": "s01"}
                  for i, w in enumerate(words)]}))  # fmt: skip
    (base / "reel.yaml").write_text(yaml.safe_dump(
        _plan(punches=[2], zooms=[{"word": 4, "until": 5}]).model_dump(mode="json")))  # fmt: skip
    return render


def test_the_page_is_self_contained_and_carries_each_shot(project: Path):
    root = project.parent
    path, warnings = run_edit_page(root, "demo", CFG, video=project)
    html = path.read_text()
    assert warnings == [] and "{{" not in html and "http" not in html.replace("viewport", "")
    data = json.loads(html.split('id="data">')[1].split("</script>")[0])
    assert [s["src_in"] for s in data["shots"]] == [0, 60] and data["video"].startswith("data:video/mp4")
    assert [p["text"] for p in data["punches"]] == ["model"] and data["zooms"][0]["text"] == "sources"
    assert data["shots"][1]["zoom"] == R.punch_in and data["shots"][0]["still"].startswith("data:image/jpeg")


@pytest.mark.skipif(not available(), reason="needs playwright and Chromium")
def test_the_page_draws_the_render_crop_and_answers_with_values(project: Path):
    from playwright.sync_api import sync_playwright

    root = project.parent
    path, _ = run_edit_page(root, "demo", CFG, video=project)
    data = json.loads(path.read_text().split('id="data">')[1].split("</script>")[0])
    with sync_playwright() as pw:
        browser = launch(pw)
        pg = browser.new_page(viewport={"width": 390, "height": 844})
        pg.goto(path.as_uri())
        pg.wait_for_function("document.getElementById('mimg').complete")
        for k, shot in enumerate(data["shots"]):  # the page's crop is F5's crop, to the pixel
            if k:
                pg.click("#nextShot")
            box = pg.eval_on_selector(
                "#box", "b => [b.style.left, b.style.top, b.style.width, b.style.height]"
            )
            c = shot["crop"]
            want = [100 * c["x"] / 640, 100 * c["y"] / 360, 100 * c["w"] / 640, 100 * c["h"] / 360]
            assert [float(v.rstrip("%")) for v in box] == pytest.approx(want, abs=0.2)
        assert pg.text_content("#out") == "Nothing changed yet."
        pg.click("#wider")  # shot 2: 1.12 -> 1.07
        pg.click("#fxList button:has-text('Remove')")  # remove the held zoom shown with shot 2
        pg.fill("#note", "the sticker covers my face")
        pg.click("#addNote")
        sent = read_answer(pg.text_content("#out") or "")
        browser.close()
    assert sent["shots"] == [
        {"take": "t", "src_in": 60, "zoom": round(R.punch_in - 0.05, 2), "dx": 0, "dy": 0}
    ]
    assert (
        sent["zooms"] == [{"word": 4, "scale": 1}]
        and sent["notes"][0]["text"] == "the sticker covers my face"
    )
    edits = merge(Edits(), sent)
    assert edits.shots[0].zoom == pytest.approx(R.punch_in - 0.05)
