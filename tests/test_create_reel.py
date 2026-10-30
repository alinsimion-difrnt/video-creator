"""create reel: layout blocks from words, caption heights clear of the presenter, widget zones, QA checks."""

import json
from itertools import pairwise

import pytest
from pydantic import ValidationError

from create.footage.reel import OVERSHOOT, Block, blocks, caption_heights, layout_at, overlay_box, product_box
from create.qa import caption_placed, on_body
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import Captions, Edl, Framing, ReelItem, ReelPlan, Timeline

CFG = load_config(REPO_ROOT / "config" / "lens.yaml")
V = CFG.create.design.frames["vertical"]
PROV = json.loads((REPO_ROOT / "projects/acme-v2/tokens.json").read_text())["provenance"]
HAIR = CFG.create.footage.reframe.hair_above_face
FACE = [400.0, 650.0, 280.0, 300.0]  # x, y, w, h in the 1080x1920 master


def _timeline(n: int = 20, step: float = 0.5) -> Timeline:
    words = [
        {"i": i, "text": f"w{i}", "start_s": i * step, "end_s": i * step + 0.4, "scene": "s01"}
        for i in range(n)
    ]
    return Timeline.model_validate(
        {
            "provenance": PROV,
            "project": "demo",
            "fps": 30,
            "total_s": n * step,
            "scenes": [
                {"scene": "s01", "start_s": 0, "end_s": n * step, "voice_start_s": 0, "voice_end_s": n * step}
            ],
            "words": words,
        }
    )


def _edl_framing(frames: int = 300) -> tuple[Edl, Framing]:
    edl = Edl.model_validate(
        {
            "provenance": PROV,
            "project": "demo",
            "fps": 30,
            "applied": [],
            "duration_frames": frames,
            "segments": [{"take": "t", "src_in": 0, "src_out": frames, "rec_in": 0}],
        }
    )
    framing = Framing.model_validate(
        {
            "provenance": PROV,
            "project": "demo",
            "frame": "vertical",
            "width": 1080,
            "height": 1920,
            "segments": [
                {
                    "segment": 0,
                    "take": "t",
                    "face": FACE,
                    "zoom": 1.0,
                    "full": {"x": 0, "y": 0, "w": 1080, "h": 1920},
                    "pip": {"x": 0, "y": 0, "w": 9, "h": 9},
                }
            ],
        }
    )
    return edl, framing


def _captions(times: list[float]) -> Captions:
    groups = [
        {"start": t, "end": t + 0.4, "words": [{"i": k, "w": "WORD", "t": t, "end": t + 0.4}]}
        for k, t in enumerate(times)
    ]
    return Captions.model_validate(
        {"provenance": PROV, "project": "demo", "frame": "vertical", "groups": groups}
    )


def _plan(**kw: object) -> ReelPlan:
    return ReelPlan.model_validate({"layout": [{"word": 0, "layout": "full"}], **kw})


def test_layout_blocks_start_on_words_and_cover_the_video():
    plan = _plan(
        layout=[{"word": 0, "layout": "full"}, {"word": 4, "layout": "split"}, {"word": 10, "layout": "full"}]
    )
    bl = blocks(plan, _timeline(), 10.0)
    assert [(b.start_s, b.layout) for b in bl] == [(0.0, "full"), (2.0, "split"), (5.0, "full")]
    assert bl[-1].end_s == 10.0 and all(a.end_s == b.start_s for a, b in pairwise(bl))
    assert layout_at(3.0, bl) == "split" and layout_at(9.99, bl) == "full"


def test_plans_start_at_word_zero_and_marks_stay_inside_the_item():
    with pytest.raises(ValidationError):
        ReelPlan.model_validate({"layout": [{"word": 3, "layout": "full"}]})
    with pytest.raises(ValidationError):
        ReelItem.model_validate({"word": 5, "until": 8, "kind": "chat", "marks": [9]})


def test_captions_sit_above_the_head_in_full_shots_and_above_the_seam_in_split():
    edl, framing = _edl_framing()
    plan = _plan(layout=[{"word": 0, "layout": "full"}, {"word": 10, "layout": "split"}], split_seam=1080)
    bl = blocks(plan, _timeline(), 10.0)
    half, gap = 70.0, 16.0
    hs = caption_heights(_captions([1.0, 6.0]), V, bl, edl, framing, plan, half, gap, HAIR)
    full, split = hs
    head_top = FACE[1] - HAIR * FACE[3]
    assert full["zone"] == "top" and full["cy"] + half <= head_top - gap + 0.1
    assert caption_placed(full["cy"], half, V, None, "top")
    assert not on_body(full["cy"], half, (FACE[0], FACE[1], FACE[0] + FACE[2], FACE[1] + FACE[3]), HAIR)
    assert split["zone"] == "seam" and split["cy"] + half == pytest.approx(1080 - gap)
    assert split["light"] is True  # ink captions on the light product canvas


def test_chest_captions_count_as_on_the_body():
    face = (FACE[0], FACE[1], FACE[0] + FACE[2], FACE[1] + FACE[3])
    band = V.caption_band
    assert on_body((band.y0 + band.y1) / 2, 70, face, HAIR)  # the old band: on the chest


def test_overlays_go_on_the_chest_when_the_captions_are_on_top():
    face = (FACE[0], FACE[1], FACE[0] + FACE[2], FACE[1] + FACE[3])
    item = ReelItem.model_validate({"word": 0, "until": 2, "kind": "sticker"})
    margin = CFG.create.footage.overlays.margin
    r = overlay_box(item, face, V, True, margin, HAIR)
    assert r.y0 == int(face[3] + margin) and r.y1 == V.safe[0].y1 - OVERSHOOT  # room for a spring
    top = ReelItem.model_validate({"word": 0, "until": 2, "kind": "sticker", "position": "top"})
    with pytest.raises(ValueError):
        overlay_box(top, face, V, True, margin, HAIR)


def test_chest_starts_below_the_beard_and_a_shot_with_no_room_says_so():
    face = (FACE[0], FACE[1], FACE[0] + FACE[2], FACE[1] + FACE[3])
    item = ReelItem.model_validate({"word": 0, "until": 2, "kind": "sticker"})
    margin = CFG.create.footage.overlays.margin
    r = overlay_box(item, face, V, True, margin, HAIR, chin_k=0.15)
    assert r.y0 == int(face[3] + margin + 0.15 * (face[3] - face[1]))
    low = (150.0, 900.0, 900.0, 1150.0)  # a close-up: chin low, no room beside
    with pytest.raises(ValueError, match="no room"):
        overlay_box(item, low, V, True, margin, HAIR, chin_k=0.15)


def test_shirt_captions_pass_qa_only_below_the_chin():
    face = (FACE[0], FACE[1], FACE[0] + FACE[2], FACE[1] + FACE[3])
    chin = CFG.create.design.caption_face_gap
    below = face[3] + chin * (face[3] - face[1]) + 1
    assert not on_body(below + 30, 30, face, HAIR, chin)  # on the shirt: allowed with caption_shirt
    assert on_body(face[3] + 30, 30, face, HAIR, chin)  # on the beard


def test_product_widgets_stay_above_the_caption_strip_in_split():
    r = product_box("split", V, 1080, (0, 0, 0), 172)
    assert r.y0 >= V.safe[0].y0 and r.y1 == 1080 - 172 - 40  # clear of the entrance overshoot
    off = product_box("off", V, 1080, (0, 0, 0), 172)
    assert off.y1 < V.caption_band.y0


def test_block_is_a_scene_for_poses():
    b = Block("b00", 0.0, 1.0, "full")
    assert (b.scene, b.start_s, b.end_s) == ("b00", 0.0, 1.0)


def test_sound_events_follow_widgets_and_layout_moves_and_keep_apart():
    from create.footage.sfx import events

    sfx = CFG.create.footage.sfx
    meta = {
        "overlays": {"items": [{"t0": 1.0, "kind": "sticker"}, {"t0": 1.1, "kind": "chat"}]},
        "product": {"items": [{"t0": 5.0, "kind": "cta", "click": 6.0}]},
        "layout": {"scenes": [{"start_s": 0, "layout": "full"}, {"start_s": 4.0, "layout": "split"}]},
    }
    ev = events(meta, sfx)
    names = [n for _, n in ev]
    assert names == ["pop", "whoosh", "pop", "click"]
    assert all(b[0] - a[0] >= sfx.min_gap_s for a, b in pairwise(ev))


def test_overlays_take_the_roomier_zone_for_tall_widgets():
    wide = (560.0, 760.0, 760.0, 1000.0)  # a wide shot: the chin is low, the chest zone is short
    item = ReelItem.model_validate({"word": 0, "until": 2, "kind": "sources"})
    margin = CFG.create.footage.overlays.margin
    r = overlay_box(item, wide, V, True, margin, HAIR, CFG.create.footage.reel.overlay_aspect["sources"])
    assert r.x1 <= wide[0] - margin and r.y0 > V.caption_top.y1  # left of the face, under the captions


def test_product_widgets_hold_until_the_next_one_or_the_layout_moves():
    from create.footage.reel import hold_product

    bl = [Block("b00", 0.0, 4.0, "split"), Block("b01", 4.0, 10.0, "full")]
    items = [{"where": "product", "t0": 0.5, "t1": 1.5}, {"where": "product", "t0": 2.0, "t1": 3.0}]
    a, b = hold_product(items, bl, 10.0)
    assert a["t1"] == pytest.approx(2.0) and b["t0"] == pytest.approx(2.12)  # a clean hand-over
    assert b["t1"] == pytest.approx(4.0)


def test_overlays_in_the_same_place_never_crossfade():
    from create.footage.reel import no_overlap

    a = {"t0": 1.0, "t1": 4.0, "box": [120, 900, 780, 1248]}
    b = {"t0": 3.0, "t1": 5.0, "box": [120, 900, 780, 1248]}
    no_overlap([a, b])
    assert a["t1"] <= b["t0"]


def test_widgets_wait_for_a_layout_move_to_finish():
    from create.footage.reel import settle

    bl = [Block("b00", 0.0, 4.0, "full"), Block("b01", 4.0, 10.0, "split")]
    assert settle(3.9, bl, 0.6) == pytest.approx(4.3)
    assert settle(2.0, bl, 0.6) == 2.0


def test_every_sound_recipe_renders(tmp_path):
    import subprocess

    from create.footage.sfx import RECIPES, sound

    for name, (_, dur) in RECIPES.items():
        wav = sound(tmp_path, name)
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              str(wav)], capture_output=True, text=True, check=True).stdout  # fmt: skip
        assert float(out) == pytest.approx(dur, abs=0.01)


def test_layout_kits_never_tween_clip_path_strings():
    # GSAP mangled clip-path strings between poses (the presenter vanished mid-move); clips come from
    # numeric custom properties instead
    for kit in ("reel.html", "layout.html"):
        js = (REPO_ROOT / "create" / "kit" / kit).read_text()
        assert "clipPath:" not in js and '"--cy"' in js and "var(--cy" in js


def test_the_face_lookup_uses_the_nearest_segment_outside_the_edit():
    from create.footage.framing import face_box, segment_index

    edl, framing = _edl_framing(300)
    assert segment_index(-1.0, edl) == 0 and segment_index(99.0, edl) == 0  # one segment: always it
    box = face_box(99.0, edl, framing, 1080)
    assert box == (FACE[0], FACE[1], FACE[0] + FACE[2], FACE[1] + FACE[3])  # past the end: still the face


# Reel flow (ADR 0033): a motion style per video, carried hand-overs, shared step labels, cuts in step.


def _plan(**extra) -> ReelPlan:
    return ReelPlan.model_validate({"layout": [{"word": 0, "layout": "split"}], **extra})


def test_motion_style_is_the_preset_with_the_plans_overrides():
    from create.footage.reel import motion_style

    rc = CFG.create.footage.reel
    classic = motion_style(_plan(), rc)  # no motion: the first take's look
    assert classic["style"] == "classic" and classic["handover"] == "cut" and classic["kicker"] == "each"
    paper = motion_style(_plan(motion={"style": "paper"}), rc)
    assert paper["handover"] == "morph" and paper["bg"] == "drift" and paper["push_alternate"] is True
    assert paper["handover_s"] == rc.handover_s and paper["kicker_h"] == rc.kicker_h
    mixed = motion_style(_plan(motion={"style": "paper", "handover": "stack", "bg": "none"}), rc)
    assert mixed["handover"] == "stack" and mixed["bg"] == "none" and mixed["cards"] == "rise"
    with pytest.raises(ValueError, match="motion style 'noir'"):
        motion_style(_plan(motion={"style": "noir"}), rc)
    with pytest.raises(ValidationError):
        _plan(motion={"style": "paper", "handover": "crossfade"})


def test_the_style_sets_an_entrance_per_kind_of_widget_unless_the_plan_chose_one():
    from create.footage.reel import styled_spec

    editorial = {"cards": "wipe", "stickers": "slide", "numbers": "unfold"}
    assert styled_spec({"title": "Sources"}, "sources", editorial)["motion"] == "wipe"
    assert styled_spec({"text": "Hi"}, "sticker", editorial)["motion"] == "slide"
    assert styled_spec({"value": 3}, "counter", editorial)["motion"] == "unfold"
    assert styled_spec({"sprite": "robot"}, "pixel", editorial).get("motion") is None  # keeps its own
    assert styled_spec({"title": "S", "motion": "pop"}, "sources", editorial)["motion"] == "pop"
    spec = {"title": "S"}
    styled_spec(spec, "sources", editorial)
    assert "motion" not in spec  # the plan's spec is not written to


def test_carried_handovers_keep_the_last_card_through_the_next():
    from create.footage.reel import hold_product

    bl = [Block("b00", 0.0, 4.0, "split"), Block("b01", 4.0, 10.0, "full")]
    items = [{"where": "product", "t0": 0.5, "t1": 1.5}, {"where": "product", "t0": 2.0, "t1": 3.0}]
    a, b = hold_product(items, bl, 10.0, "morph", 0.55)
    assert a["t1"] == pytest.approx(2.55) and b["t0"] == pytest.approx(2.0)  # a stays while b takes over
    assert a["handover_out"] == "morph" and b["handover"] == "morph" and b["prev"] == 0
    assert b["t1"] == pytest.approx(4.0) and "handover" not in a and "handover_out" not in b
    # an item's own choice wins over the style: a cut keeps the first take's gap
    items = [
        {"where": "product", "t0": 0.5, "t1": 1.5},
        {"where": "product", "t0": 2.0, "t1": 3.0, "handover_pref": "cut"},
    ]
    a, b = hold_product(items, bl, 10.0, "push", 0.55)
    assert a["t1"] == pytest.approx(2.0) and b["t0"] == pytest.approx(2.12) and "handover" not in b
    assert "handover_pref" not in b  # a planning note, not page data


def test_cards_in_a_row_with_one_kicker_share_a_step_label():
    from create.footage.reel import kicker_runs

    bl = [Block("b00", 0.0, 10.0, "split")]
    box = [120, 320, 888, 830]

    def card(t0, t1, kicker, step=None, title="A"):
        spec = {"kicker": kicker, "title": title} | ({"step": step} if step else {})
        return {"where": "product", "t0": t0, "t1": t1, "box": list(box), "spec": spec}

    items = [
        card(0.5, 3.0, "SEO on a budget", "1/4", "A"),
        card(3.0, 5.0, "SEO on a budget", "1/4", "B"),
        card(5.0, 7.0, "SEO on a budget", "2/4", "C"),
        card(7.0, 9.0, "Other", None, "D"),
        {
            "where": "overlay",
            "t0": 1.0,
            "t1": 2.0,
            "box": [120, 900, 780, 1200],
            "spec": {"kicker": "SEO on a budget"},
        },
    ]
    runs = kicker_runs(items, bl, 96)
    assert len(runs) == 1  # D is alone and keeps its own label; the overlay is not a product card
    run = runs[0]
    assert run["text"] == "SEO on a budget" and run["t0"] == 0.5 and run["t1"] == 7.0
    assert run["steps"] == [[0.5, "1/4"], [5.0, "2/4"]]  # the step flips only when it changes
    assert run["box"] == [120, 320, 888, 416]
    for it in items[:3]:
        assert "kicker" not in it["spec"] and "step" not in it["spec"] and it["spec"]["title"]
        assert it["box"] == [120, 416, 888, 830] and it["align"] == "top"
    assert items[3]["spec"]["kicker"] == "Other" and items[3]["box"] == box and "align" not in items[3]


def test_a_card_enters_on_the_cut_when_its_word_starts_just_after_it():
    from create.footage.reel import snap_to_cut

    cuts = [4.0, 9.5]
    assert snap_to_cut(4.2, cuts, 0.3) == 4.0
    assert snap_to_cut(4.4, cuts, 0.3) == 4.4  # too late: the word, not the cut
    assert snap_to_cut(3.9, cuts, 0.3) == 3.9  # never later than the word
    assert snap_to_cut(9.5, cuts, 0.3) == 9.5


def test_a_carried_card_arrives_with_a_whoosh_and_a_cut_one_with_a_pop():
    from create.footage.sfx import events

    cards = [
        {"t0": 1.0, "t1": 3.0, "kind": "chat"},
        {"t0": 3.0, "t1": 5.0, "kind": "sources", "handover": "morph"},
        {"t0": 5.0, "t1": 7.0, "kind": "counter", "handover": "stack"},
    ]
    meta = {"product": {"items": cards}}
    names = [n for _, n in events(meta, CFG.create.footage.sfx)]
    assert names == ["pop", "whoosh", "pop"]
