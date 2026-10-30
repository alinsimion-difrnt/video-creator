"""Reel props and effects (ADR 0027): room space, spots, moves, carries, matte spans and the art."""

import itertools
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from create.footage import props as pr
from create.footage.matte import covering, matte_spans
from create.footage.props_art import Art, cut_out, make_art, pixelate, trim
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import Edl, Framing, ReelFx, ReelPlan, ReelProp, Timeline

CFG = load_config(REPO_ROOT / "config" / "lens.yaml")
FRAME = CFG.create.design.frames["vertical"]
PC = CFG.create.footage.reel.props
PROV = {
    "tool_version": "0",
    "stage": "f4_edl",
    "annotator": "code",
    "input_hash": "0" * 64,
    "created_at": "2026-10-11T00:00:00Z",
}


def _edl() -> Edl:
    return Edl.model_validate(
        {
            "provenance": PROV,
            "project": "demo",
            "fps": 30,
            "applied": [],
            "duration_frames": 600,
            "segments": [
                {"take": "t", "src_in": 0, "src_out": 300, "rec_in": 0},
                {"take": "t", "src_in": 300, "src_out": 600, "rec_in": 300},
            ],
        }
    )


def _framing(second: dict[str, int] | None = None) -> Framing:
    seg = {"take": "t", "face": [880, 900, 400, 500], "zoom": 1.0, "pip": {"x": 0, "y": 0, "w": 9, "h": 9}}
    full = {"x": 0, "y": 0, "w": 2160, "h": 3840}
    return Framing.model_validate(
        {
            "provenance": PROV | {"stage": "f5_reframe"},
            "project": "demo",
            "frame": "vertical",
            "width": 1080,
            "height": 1920,
            "segments": [seg | {"segment": 0, "full": full}, seg | {"segment": 1, "full": second or full}],
        }
    )


def _timeline(n: int = 60) -> Timeline:
    words = [
        {
            "i": i,
            "text": f"w{i}",
            "start_s": round(0.2 + i * 0.3, 3),
            "end_s": round(0.4 + i * 0.3, 3),
            "scene": "s01",
        }
        for i in range(n)
    ]
    return Timeline.model_validate(
        {
            "provenance": PROV | {"stage": "c5_timing"},
            "project": "demo",
            "fps": 30,
            "total_s": 20.0,
            "words": words,
            "scenes": [
                {"scene": "s01", "start_s": 0, "end_s": 20.0, "voice_start_s": 0.2, "voice_end_s": 19}
            ],
        }
    )


ART = Art(aspect=0.6, styles={"photo": "f-photo.png", "pixel": "f-pixel.png"}, points={"mouth": (0.9, 0.5)})
CAT = Art(
    0.7,
    {"stand": "c.png", "grab": "g.png"},
    {"mouth": (0.95, 0.5)},
    True,
    {"walk": ["c.png"], "run": ["c.png"]},
)


def test_rooms_map_the_master_to_the_frame_per_shot():
    rs = pr.rooms(_edl(), _framing({"x": 270, "y": 480, "w": 1620, "h": 2880}), {"t": (2160, 3840)}, FRAME)
    assert rs[0].k == pytest.approx(0.5) and rs[0].tx == 0
    assert rs[1].k == pytest.approx(1080 / 1620) and rs[1].crop == (270, 480, 1890, 3360)
    assert rs[1].tx == pytest.approx(-270 * 1080 / 1620)
    cover = pr.rooms(_edl(), None, {"t": (1920, 1080)}, FRAME)  # landscape master, no framing: centred cover
    assert cover[0].k == pytest.approx(1920 / 1080) and cover[0].crop[0] == pytest.approx(
        960 - 1080 * 1080 / 3840
    )


def test_named_spots_sit_by_the_face_and_stay_on_screen():
    face = pr.take_face(_framing(), "t", 2160, 3840)
    assert face == (1080, 1150, 400, 500)
    x, y = pr.place("lap", face, 2160, 3840, PC.anchors)
    ax, ay = PC.anchors["lap"]
    assert x == pytest.approx(1080 + ax * 400) and y == pytest.approx(1150 + ay * 500)
    assert pr.place((0.25, 0.5), face, 2160, 3840, PC.anchors) == (540, 1920)
    rs = pr.rooms(_edl(), _framing(), {"t": (2160, 3840)}, FRAME)
    _, cy = pr.clamp((1080, 9999), rs, 400, 300)  # a floor below the frame comes up into it
    assert cy < 3840
    with pytest.raises(ValueError, match="unknown spot"):
        pr.place("ceiling", face, 2160, 3840, PC.anchors)


def test_a_prop_walks_in_acts_and_runs_off_screen():
    edl, fr, tl = _edl(), _framing(), _timeline()
    rs = pr.rooms(edl, fr, {"t": (2160, 3840)}, FRAME)
    p = ReelProp.model_validate(
        {
            "id": "pixie",
            "art": "cat",
            "word": 5,
            "until": 30,
            "at": "lap",
            "enter": "walk_left",
            "exit": "run_right",
            "beats": [{"word": 10, "move": [0.3, 0.8]}, {"word": 12, "do": "jump", "tag": "Pixie"}],
        }
    )
    t = pr.prop_track(p, tl, edl, fr, rs, CAT, PC, 20.0)
    first, arrive = t["moves"][0], t["moves"][1]
    assert first["x"] < 0 and arrive["gait"] == "walk"  # starts past the left edge, walks in
    assert t["moves"][2]["x"] == pytest.approx(648) and t["moves"][2]["dir"] == -1
    run = t["moves"][-1]
    assert run["x"] > 2160 and run["gait"] == "run" and run["t"] + run["d"] == pytest.approx(t["t1"])
    assert t["acts"][0]["do"] == "jump" and t["tags"][0]["text"] == "Pixie"


def test_a_carried_prop_leaves_as_it_is_picked_up():
    edl, fr, tl = _edl(), _framing(), _timeline()
    rs = pr.rooms(edl, fr, {"t": (2160, 3840)}, FRAME)
    fred = ReelProp.model_validate(
        {
            "id": "fred",
            "art": "fish",
            "word": 2,
            "until": 40,
            "beats": [{"word": 6, "style": "pixel"}, {"word": 8, "add": ["top_hat"]}],
        }
    )
    cat = ReelProp.model_validate(
        {"id": "pixie", "art": "cat", "word": 20, "until": 40, "beats": [{"word": 25, "carry": "fred"}]}
    )
    tracks = [pr.prop_track(x, tl, edl, fr, rs, a, PC, 20.0) for x, a in ((fred, ART), (cat, CAT))]
    pr.link_carries(tracks, PC)
    t25 = tl.words[25].start_s
    # visuals lead the voice a little (lead_s): the grab lands just before the word
    assert tracks[0]["t1"] == pytest.approx(t25 - PC.lead_s) and tracks[0]["exit"]["kind"] == "snatched"
    c = tracks[1]["carry"]
    assert c["file"] == "f-pixel.png" and c["acc"] == ["top_hat"] and c["pixel"] is True


def test_visible_share_flags_a_prop_a_punch_in_crops_away():
    edl, tl = _edl(), _timeline()
    fr = _framing({"x": 540, "y": 0, "w": 1080, "h": 1920})  # the second shot: a tight crop, top middle
    rs = pr.rooms(edl, fr, {"t": (2160, 3840)}, FRAME)
    p = ReelProp.model_validate({"id": "f", "art": "fish", "word": 1, "until": 55, "at": [0.5, 0.9]})
    t = pr.prop_track(p, tl, edl, fr, rs, ART, PC, 20.0)
    shares = dict(pr.visible_share(t, rs))
    assert max(shares.values()) == 1.0 and min(shares.values()) == 0.0


def test_plans_reject_bad_props_and_effects():
    with pytest.raises(ValidationError, match="needs `image`"):
        ReelProp.model_validate({"id": "f", "word": 1, "until": 3})
    with pytest.raises(ValidationError, match="beats must go forward"):
        ReelProp.model_validate({"id": "f", "art": "fish", "word": 5, "until": 9, "beats": [{"word": 2}]})
    with pytest.raises(ValidationError, match="needs until"):
        ReelFx.model_validate({"word": 1, "kind": "anime"})
    base = {"layout": [{"word": 0, "layout": "full"}]}
    with pytest.raises(ValidationError, match="not another prop"):
        ReelPlan.model_validate(
            base
            | {
                "props": [
                    {"id": "c", "art": "cat", "word": 1, "until": 5, "beats": [{"word": 2, "carry": "x"}]}
                ]
            }
        )


def test_matte_spans_pad_merge_and_cover():
    tl = _timeline()
    plan = ReelPlan.model_validate(
        {
            "layout": [{"word": 0, "layout": "full"}],
            "props": [
                {"id": "a", "art": "fish", "word": 2, "until": 4, "behind": True},
                {"id": "b", "art": "fish", "word": 5, "until": 6, "behind": True},
                {"id": "c", "art": "fish", "word": 30, "until": 40},  # in front: no matte
            ],
            "fx": [{"word": 20, "until": 22, "kind": "anime"}],
        }
    )
    spans = matte_spans(plan, tl, 30, 600, 0.3)
    assert spans == [(15, 75), (177, 219)]  # a and b merge (padding overlaps); c is not there
    assert covering(
        {"clips": [{"start": 0, "end": 80, "file": "a"}, {"start": 160, "end": 220, "file": "b"}]}, spans
    )
    with pytest.raises(FileNotFoundError):
        covering({"clips": [{"start": 0, "end": 70, "file": "a"}]}, spans)


def test_art_styles_from_a_picture(tmp_path: Path):
    img = Image.new("RGB", (200, 120), (255, 255, 255))
    img.paste((240, 120, 30), (40, 30, 160, 90))  # an orange block on white
    cut = trim(cut_out(img))
    a = np.asarray(cut.getchannel("A"))
    assert cut.size[0] < 130 and a[a.shape[0] // 2, a.shape[1] // 2] == 255 and a[0, 0] == 0
    px = pixelate(cut, 20, scale=4)
    assert px.size[0] == (20 + 2) * 4  # cells plus the outline, scaled crisp
    src = tmp_path / "fish.png"
    img.save(src)
    art = make_art("fred", "image", src, {"pixel", "illustrated", "toon3d"}, tmp_path / "out", 24)
    assert set(art.styles) == {"photo", "pixel", "illustrated", "toon3d"}
    assert all((tmp_path / "out" / f).exists() for f in art.styles.values())


def test_sprite_schedule_walks_while_moving_and_idles_at_rest(tmp_path: Path):
    edl, fr, tl = _edl(), _framing(), _timeline()
    rs = pr.rooms(edl, fr, {"t": (2160, 3840)}, FRAME)
    art = make_art("pixie", "cat", None, set(), tmp_path, 24)
    p = ReelProp.model_validate(
        {
            "id": "pixie",
            "art": "cat",
            "word": 2,
            "until": 30,
            "enter": "walk_left",
            "beats": [{"word": 20, "move": "lap"}],
        }
    )
    t = pr.prop_track(p, tl, edl, fr, rs, art, PC, 20.0) | {"fps": art.fps}
    sched = pr.sprite_schedule(t)
    walk = t["moves"][1]
    during = {k for at, k in sched if walk["t"] <= at < walk["t"] + walk["d"]}
    assert during <= set(art.frames["walk"]) and len(during) > 2  # the walk cycle plays while she walks in
    after = [k for at, k in sched if walk["t"] + walk["d"] + 0.1 < at < t["moves"][2]["t"]]
    assert after and set(after) <= set(art.frames["idle"])
    assert all(b[0] > a[0] for a, b in itertools.pairwise(sched))


def test_props_get_their_sounds():
    from create.footage.reel import prop_sounds
    from create.footage.sfx import events

    data = {
        "props": [
            {
                "t0": 1.0,
                "enter": {"kind": "pop"},
                "styles": [{"t": 1.0}, {"t": 2.0}],
                "acc": [{"t": 1.0, "add": ["moustache"]}, {"t": 3.0, "add": ["top_hat"]}],
                "tags": [],
                "exit": {"kind": "run_left", "t": 5.0},
                "carry": None,
            },
        ],
        "fx": [{"kind": "anime", "t0": 6.0}],
    }
    evs = prop_sounds(data)
    assert [(e["t"], e["sound"]) for e in evs] == [
        (1.0, "pop"),
        (2.0, "sparkle"),
        (3.45, "boing"),
        (5.0, "whoosh"),
        (6.0, "sparkle"),
    ]
    assert (3.45, "boing") in events({"props": {"events": evs}}, CFG.create.footage.sfx)


def test_fred_hops_rows_a_boat_along_a_path_and_holds_things(tmp_path: Path):
    edl, fr, tl = _edl(), _framing(), _timeline()
    rs = pr.rooms(edl, fr, {"t": (2160, 3840)}, FRAME)
    art = make_art("fred", "fred", None, {"pixel"}, tmp_path, 24)
    assert art.rig and set(art.styles) == {"photo"}  # the rig is drawn in the page; only his photo is a file
    p = ReelProp.model_validate(
        {
            "id": "fred",
            "art": "fred",
            "word": 2,
            "until": 50,
            "beats": [
                {"word": 5, "hold": "book"},
                {"word": 8, "hold": "none", "move": "left"},
                {"word": 12, "ride": "boat", "path": ["above", "shoulder_left", [0.7, 0.6]]},
                {"word": 30, "ride": "none", "move": "lap"},
            ],
        }
    )
    t = pr.prop_track(p, tl, edl, fr, rs, art, PC, 20.0)
    gaits = [m.get("gait") for m in t["moves"][1:]]
    assert gaits == ["hop", "boat", "boat", "boat", "hop"]
    legs = [m for m in t["moves"] if m.get("gait") == "boat"]
    # legs follow one another, each at least path_leg_s and as long as the boat's speed needs
    for a, b in itertools.pairwise(legs):
        assert b["t"] == pytest.approx(a["t"] + a["d"], abs=0.002) and a["d"] >= PC.path_leg_s
    assert legs[-1]["x"] == pytest.approx(0.7 * 2160)
    assert [h["hold"] for h in t["holds"]] == ["book", "none"] and t["rides"][0]["ride"] == "boat"


def test_alchemy_circle_sits_under_its_prop():
    edl, fr, tl = _edl(), _framing(), _timeline()
    rs = pr.rooms(edl, fr, {"t": (2160, 3840)}, FRAME)
    p = ReelProp.model_validate({"id": "fred", "art": "fish", "word": 1, "until": 40, "at": [0.4, 0.8]})
    track = pr.prop_track(p, tl, edl, fr, rs, ART, PC, 20.0)
    fx = [ReelFx.model_validate({"word": 10, "kind": "alchemy", "spec": {"at": "fred"}})]
    (a,) = pr.fx_track(fx, tl, 20.0, edl, fr, rs, [track], PC.anchors)
    assert (a["x"], a["y"]) == (track["moves"][0]["x"], track["moves"][0]["y"])
    assert a["t1"] - a["t0"] == pytest.approx(2.4) and a["r"] == pytest.approx(track["w"] * 0.9, abs=0.1)


def test_cat_colors_are_validated():
    with pytest.raises(ValidationError, match="colors"):
        ReelProp.model_validate({"id": "c", "art": "cat", "word": 1, "until": 3, "colors": {"fur": "grey"}})
    ok = ReelProp.model_validate(
        {"id": "c", "art": "cat", "word": 1, "until": 3, "colors": {"fur": "#aabbcc"}}
    )
    assert ok.colors["fur"] == "#aabbcc"


def test_kits_never_show_an_element_only_in_fromto_start_values():
    """HyperFrames renders dropped Fred's hat and moustache: `fromTo(el, {autoAlpha: 1, ...}, {...})` with the
    visibility only in the start values never showed them in a render (the preview did). Put it in both."""
    import re

    for kit in ("fred.js", "props.js", "motion.js"):
        src = (REPO_ROOT / "create" / "kit" / kit).read_text()
        for m in re.finditer(r"fromTo\([^,]*, \{ autoAlpha: 1,[^}]*\}, \{([^}]*)\}", src):
            assert "autoAlpha" in m.group(1), f"{kit}: {m.group(0)[:80]}"


def test_travel_time_follows_gait_speed_in_body_widths():
    w = 400.0
    walk = pr.travel_s(w * PC.speeds["walk"], w, "walk", PC)  # one second's walk
    assert walk == pytest.approx(1.0)
    assert pr.travel_s(w * PC.speeds["walk"], w, "run", PC) < walk  # a run covers it faster
    assert pr.travel_s(1.0, w, "walk", PC) == pytest.approx(0.35)  # never a snap
    assert pr.travel_s(1e6, w, "walk", PC) == PC.max_travel_s  # never a crawl


def test_a_walker_jumps_between_heights():
    edl, fr, tl = _edl(), _framing(), _timeline()
    rs = pr.rooms(edl, fr, {"t": (2160, 3840)}, FRAME)
    cat = ReelProp.model_validate(
        {
            "id": "pixie",
            "art": "cat",
            "word": 2,
            "until": 30,
            "at": "shoulder_right",
            "beats": [{"word": 6, "move": "floor_right"}],
        }
    )
    t = pr.prop_track(cat, tl, edl, fr, rs, CAT, PC, 20.0)
    assert t["moves"][-1]["gait"] == "jump"


def test_3d_fred_turns_once_as_he_becomes_3d_then_idles():
    track = {
        "t0": 0.0,
        "t1": 4.0,
        "rig": True,
        "styles": [
            {"t": 0.0, "style": "illustrated"},
            {"t": 1.0, "style": "toon3d"},
            {"t": 3.0, "style": "pixel"},
        ],
        "acc": [],
        "moves": [],
        "acts": [],
        "carry": None,
        "set_fps": {"3d-": {"turn": 18, "idle": 8}},
    }
    assert pr.style_combos(track, "toon3d") == [()]
    sets = {"3d-plain": {"turn": [f"t{k}" for k in range(16)], "idle": ["i0", "i1"]}}
    sched = pr.sprite_schedule(track, sets)
    keys = dict((round(t, 2), k) for t, k in sched)
    assert keys[0.0] == "rig" and sched[1][1] == "t0"  # the rig, then the turntable on the style change
    turn = [k for t, k in sched if 1.0 <= t < 1.0 + 16 / 18]
    assert turn[:3] == ["t0", "t1", "t2"]
    assert {k for t, k in sched if 2.0 < t < 3.0} <= {"i0", "i1"}  # then the 3D idle
    assert sched[-1][1] == "rig"  # pixel without pixel sets falls back to the rig


def test_a_carrier_stops_beside_its_prey_not_on_it():
    cat = {
        "w": 100.0,
        "moves": [
            {"t": 0, "d": 0, "x": 1000.0, "y": 900.0},
            {"t": 1, "d": 1, "x": 500.0, "y": 900.0, "dir": -1},
        ],
    }
    fish = {"w": 200.0, "moves": [{"t": 0, "d": 0, "x": 500.0, "y": 600.0}]}
    pr.stop_short(cat, fish, 2.5, PC)
    assert cat["moves"][1]["x"] == pytest.approx(
        500 + 100 * PC.approach[0] + 200 * PC.approach[1]
    )  # coming from the right
    assert cat["moves"][1]["y"] == 600.0  # on the fish's surface, not the floor below it
    assert cat["moves"][1]["dir"] == -1


def test_frame_styles_give_way_to_the_rig_in_the_boat():
    track = {
        "t0": 0.0,
        "t1": 3.0,
        "rig": True,
        "styles": [{"t": 0.0, "style": "toon3d"}],
        "acc": [],
        "moves": [],
        "acts": [],
        "carry": None,
        "rides": [{"t": 1.0, "ride": "boat"}, {"t": 2.0, "ride": "none"}],
        "set_fps": {"3d-": {"turn": 18, "idle": 8}},
    }
    sched = pr.sprite_schedule(track, {"3d-plain": {"turn": ["t0"], "idle": ["i0"]}})
    assert [k for t, k in sched if 1.0 <= t < 2.0] == ["rig"]
    assert sched[-1][1] == "i0"


def test_a_move_waits_for_the_one_before_and_hits_land_on_the_grab():
    edl, fr, tl = _edl(), _framing(), _timeline()
    rs = pr.rooms(edl, fr, {"t": (2160, 3840)}, FRAME)
    fred = ReelProp.model_validate({"id": "fred", "art": "fish", "word": 1, "until": 5})
    cat = ReelProp.model_validate(
        {
            "id": "pixie",
            "art": "cat",
            "word": 2,
            "until": 6,
            "enter": "walk_left",
            "beats": [{"word": 3, "move": "lap"}, {"word": 5, "carry": "fred"}],
        }
    )
    tracks = [pr.prop_track(x, tl, edl, fr, rs, a, PC, 20.0) for x, a in ((fred, ART), (cat, CAT))]
    walk_in, to_lap = tracks[1]["moves"][1:3]
    assert to_lap["t"] >= walk_in["t"] + walk_in["d"] - 1e-6  # never two tweens on one position
    pr.link_carries(tracks, PC)
    grab = tracks[1]["carry"]["t"]
    assert tracks[0]["t1"] == grab  # the fish waits to be snatched, past its own `until`
    fx = [ReelFx.model_validate({"word": 5, "kind": "shake"})]
    assert pr.fx_track(fx, tl, 20.0, edl, fr, rs, tracks)[0]["t0"] == grab


def test_an_exit_with_no_time_left_stays_instead_of_flashing_off():
    edl, fr, tl = _edl(), _framing(), _timeline()
    rs = pr.rooms(edl, fr, {"t": (2160, 3840)}, FRAME)
    cat = ReelProp.model_validate(
        {
            "id": "pixie",
            "art": "cat",
            "word": 2,
            "until": 6,
            "exit": "run_left",
            "beats": [{"word": 6, "do": "jump"}],
        }
    )
    end = tl.words[6].end_s + 0.2
    t = pr.prop_track(cat, tl, edl, fr, rs, CAT, PC, end)
    assert t["exit"]["kind"] == "none" and t["exit"]["cut"] and t["t1"] == pytest.approx(end, abs=1e-3)


def test_a_prop_behind_the_presenter_rises_until_it_shows():
    alpha = np.zeros((1000, 800), np.uint8)
    alpha[500:, 200:600] = 255  # the presenter's shoulders and body from y 500 down
    y = pr.peek_y(alpha, 400, 800, 200, 200, 0.5)
    assert y == pytest.approx(600)  # half of its 200 px box above the shoulder line
    assert pr.peek_y(alpha, 100, 800, 100, 100, 0.5) == 800  # beside the body: already visible


KITTEN = Art(  # a cat with every cycle the kitten has, frame names distinct
    0.7,
    {"stand": "i0"},
    {"mouth": (0.95, 0.5)},
    True,
    {a: [f"{a}{k}" for k in range(6)] for a in ("idle", "walk", "run", "grab", "pounce", "jump")},
    fps={"idle": 8, "walk": 12, "run": 14, "grab": 10, "pounce": 10, "jump": 10},
)


def _cat_track(**extra: Any) -> dict[str, Any]:
    base = {
        "t0": 0.0,
        "t1": 4.0,
        "styles": [{"t": 0.0, "style": "photo"}],
        "acc": [],
        "moves": [],
        "acts": [],
    }
    return base | {"carry": None, "frames": KITTEN.frames, "fps": KITTEN.fps} | extra


def test_a_jump_lands_on_its_landing_frame_whatever_its_length():
    for d in (0.4, 0.9):
        t = _cat_track(moves=[{"t": 0.5, "d": d, "x": 0, "y": 0, "gait": "jump"}])
        sched = pr.sprite_schedule(t)
        during = [k for at, k in sched if 0.5 <= at < 0.5 + d]
        assert during[0] == KITTEN.frames["jump"][0] and during[-1] == KITTEN.frames["jump"][-1]
        assert len(during) == len(dict.fromkeys(during))  # never back to the crouch mid-air


def test_the_pounce_starts_after_the_walk_and_the_grab_ignores_later_beats():
    edl, fr, tl = _edl(), _framing(), _timeline()
    rs = pr.rooms(edl, fr, {"t": (2160, 3840)}, FRAME)
    cat = ReelProp.model_validate(
        {
            "id": "pixie",
            "art": "cat",
            "word": 2,
            "until": 30,
            "beats": [{"word": 4, "move": "lap"}, {"word": 5, "carry": "fred"}, {"word": 20, "move": "left"}],
        }
    )
    t = pr.prop_track(cat, tl, edl, fr, rs, KITTEN, PC, 20.0)
    walk = t["moves"][1]
    pounce = pr.once_s(KITTEN.frames, KITTEN.fps, "pounce")
    assert t["carry"]["t"] == pytest.approx(
        max(tl.words[5].start_s - PC.lead_s, walk["t"] + walk["d"] + pounce), abs=2e-3
    )
    assert t["carry"]["t"] < t["moves"][2]["t"]  # not delayed to the move after it


def test_a_fade_with_an_early_until_still_runs_forward():
    edl, fr, tl = _edl(), _framing(), _timeline()
    rs = pr.rooms(edl, fr, {"t": (2160, 3840)}, FRAME)
    fx = [ReelFx.model_validate({"word": 2, "until": 3, "kind": "fade_black"})]
    out = pr.fx_track(fx, tl, 20.0, edl, fr, rs, [{"t1": 15.0}])[0]
    assert out["t1"] > out["t0"]


def test_a_prop_follows_the_hand_down_and_stays_where_it_is_put():
    """follow: hand: keyed moves carry the prop from where it was into the palm and down to the hand's lowest
    point (the put-down), where it stays."""
    track = {
        "moves": [{"t": 0.0, "d": 0.0, "x": 500.0, "y": 900.0, "ease": "none"}],
        "follows": [],
    }
    f = {"t": 1.0, "end": 3.0, "by": "hand"}
    # the hand starts 100 px up and left of the prop, goes down to y 1400 at t=2.2, then lifts again
    path = [(1.0 + k * 0.2, 400.0 + k * 50, 800.0 + min(k, 6) * 100 - max(0, k - 6) * 120) for k in range(11)]
    pr.apply_follow(track, f, path)
    keyed = [m for m in track["moves"] if m.get("follow")]
    assert keyed and keyed[0]["t"] == 1.0
    # it starts where it was (no jump) and settles into the palm: put down on the hand's lowest point
    assert (keyed[0]["x"], keyed[0]["y"]) != (500.0, 900.0) and abs(keyed[0]["x"] - 500) < 60
    assert (keyed[-1]["x"], keyed[-1]["y"]) == (400.0 + 6 * 50, 800.0 + 600)
    assert f["release"] == 2.2  # it is let go at the lowest point, not dragged back up
    assert pr.position_at(track, 2.9) == (keyed[-1]["x"], keyed[-1]["y"])


def test_hand_path_picks_the_nearest_hand_and_holds_through_gaps():
    from create.footage import pose as ps

    def pts(rx: float, lx: float) -> list[list[float]]:
        p = [[0.0, 0.0, 1.0] for _ in range(33)]
        for i in ps.HAND["right"]:
            p[i] = [rx, 500.0, 0.9]
        for i in ps.HAND["left"]:
            p[i] = [lx, 500.0, 0.9]
        return p

    samples = [(0.0, pts(100, 900)), (0.1, None), (0.2, pts(120, 900))]
    side, path = ps.hand_path(samples, (880.0, 520.0), 1)
    assert side == "left"  # the person's left hand is the one at x 900, nearest the prop
    assert [p[0] for p in path] == [0.0, 0.1, 0.2] and path[1][1] == 900.0  # a lost frame holds


def test_planned_sound_cues_always_play_with_their_own_gain():
    """The plan's audio cues (gag effects, narration) are never thinned by min_gap_s like UI pops, and keep
    the gain the plan gave them (ADR 0030)."""
    from create.footage.sfx import events

    meta = {
        "props": {"events": [{"t": 1.0, "sound": "pop"}]},
        "audio": [{"t": 1.01, "file": "/x/camera.mp3", "gain_db": -12.0}, {"t": 1.02, "file": "/x/v.mp3",
                  "gain_db": 0.0}],
    }  # fmt: skip
    got = events(meta, CFG.create.footage.sfx)
    files = [n for _, n in got if n.startswith("file:")]
    assert len(files) == 2 and '"/x/camera.mp3", -12.0' in files[0]


def test_tags_end_at_the_next_cut_once_up_long_enough() -> None:
    edl = _edl()  # a cut at 10 s
    rs = pr.rooms(edl, _framing(), {"t": (2160, 3840)}, FRAME)
    least = PC.tag_cut_least_s
    assert pr._to_cut(9.0, 1.5, rs, edl, least) == 1.0  # up 1.0 s by the cut: it ends there
    assert pr._to_cut(9.6, 1.5, rs, edl, least) == 1.5  # only 0.4 s by the cut: it stays its full time
    assert pr._to_cut(5.0, 1.5, rs, edl, least) == 1.5  # no cut in its way


def test_a_fleeing_prop_keeps_ahead_of_the_hand_and_only_runs_away() -> None:
    track = {
        "w": 100.0,
        "t1": 3.0,
        "moves": [{"t": 0.0, "d": 0.0, "x": 500.0, "y": 900.0, "ease": "none"},
                  {"t": 1.2, "d": 0.3, "x": -300.0, "y": 900.0, "ease": "power1.in", "dir": -1}],
        "exit": {"t": 1.2, "kind": "run_left", "d": 0.3},
    }  # fmt: skip
    f = {"t": 0.2, "end": 3.0, "by": "flee"}
    hand = [(0.2 + k * 0.1, 900.0 - k * 60) for k in range(12)]  # the hand sweeps left past it
    pr.apply_flee(track, f, hand, gap=0.3, chase_s=1.0, duration=10.0)
    xs = [m["x"] for m in track["moves"] if m.get("gait") == "run"]
    assert xs == sorted(xs, reverse=True)  # only ever toward its exit
    for m in track["moves"]:
        if m.get("gait") == "run":
            hx = next(x for t, x in hand if abs(t - (m["t"] + m["d"])) < 1e-6)
            assert m["x"] <= hx - 80 + 1e-6  # half its width plus the gap ahead of the hand
    assert track["exit"]["t"] >= 1.2 and track["moves"][-1]["x"] == -300.0  # then the planned run off


def test_a_bolting_prop_runs_before_the_hand_reaches_it() -> None:
    track = {"w": 100.0, "t1": 3.0, "moves": [{"t": 0.0, "d": 0.0, "x": 500.0, "y": 900.0, "ease": "none"}],
             "exit": {"t": 2.0, "kind": "run_left", "d": 0.3}}  # fmt: skip
    hand = [(k * 0.1, 2000.0) for k in range(10)]  # far away
    pr.apply_flee(track, {"t": 0.0, "end": 3.0, "by": "flee"}, hand, 0.3, 0.9, 10.0, speed=100.0)
    assert pr.position_at(track, 0.85) < (500.0, 900.0)  # it has moved left on its own


def test_lead_path_takes_the_leading_palm_and_drops_one_wild_frame() -> None:
    from create.footage import pose as ps

    def pts(lx: float, rx: float) -> list[tuple[float, float, float]]:
        p = [(0.0, 0.0, 0.0)] * 35
        p[ps.PALM_INDEX["left"]] = (lx, 500.0, 0.9)
        p[ps.PALM_INDEX["right"]] = (rx, 500.0, 0.9)
        return p

    samples = [(k * 0.1, pts(800.0 - k * 10, 900.0)) for k in range(7)]
    samples[3] = (0.3, pts(10.0, 900.0))  # one wrong detection far left
    xs = [x for _, x in ps.lead_path(samples, left=True)]
    assert min(xs) > 600  # the median drops the wild frame
