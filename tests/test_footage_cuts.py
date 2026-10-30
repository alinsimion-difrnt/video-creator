"""F3/F4/C5 presenter mode: cut proposals from a verbatim transcript, the edit, words on the edited clock."""

import itertools

import pytest

from create.footage.cuts import apply_cuts, propose_cuts, remap_words, split_long
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import EdlSegment, TranscriptWord

CFG = load_config(REPO_ROOT / "config" / "lens.yaml").create.footage


def _say(
    spec: list[tuple[str, float, float]], take: str = "t1", kind: dict | None = None
) -> list[TranscriptWord]:
    kind = kind or {}
    return [
        TranscriptWord(i=i, take=take, text=w, kind=kind.get(w, "word"), start_s=a, end_s=b)
        for i, (w, a, b) in enumerate(spec)
    ]


def _even(
    text: str, t0: float = 1.0, step: float = 0.35, dur: float = 0.28, **kw
) -> list[tuple[str, float, float]]:
    return [(w, round(t0 + i * step, 3), round(t0 + i * step + dur, 3)) for i, w in enumerate(text.split())]


def test_long_pause_is_shortened_to_the_padding():
    words = _say([("Hello", 1.0, 1.4), ("there.", 3.0, 3.4)])
    (c,) = propose_cuts(words, CFG, "en")
    assert c.kind == "silence"
    assert c.start_s == pytest.approx(1.4 + CFG.cuts.keep_after_s)
    assert c.end_s == pytest.approx(3.0 - CFG.cuts.keep_before_s)


def test_short_pauses_stay():
    assert propose_cuts(_say(_even("this is a normal pace")), CFG, "en") == []


def test_a_filler_and_its_pause_go_together():
    words = _say([("So", 1.0, 1.2), ("um", 1.6, 1.9), ("today", 2.3, 2.6)], kind={"um": "filler"})
    (c,) = propose_cuts(words, CFG, "en")
    assert c.kind == "filler" and c.words == [1]
    assert c.start_s == pytest.approx(1.2 + CFG.cuts.keep_after_s)
    assert c.end_s == pytest.approx(2.3 - CFG.cuts.keep_before_s)


def test_romanian_fillers_from_config():
    words = _say([("Deci", 1.0, 1.3), ("ăă", 1.35, 1.7), ("azi", 1.75, 2.0)])
    (c,) = propose_cuts(words, CFG, "ro")
    assert c.kind == "filler" and c.words == [1]


def test_false_start_keeps_the_last_complete_take():
    spec = _even("So today I want to so today I want to show you Acme.")
    words = _say(spec)
    cuts = [c for c in propose_cuts(words, CFG, "en") if c.kind == "retake"]
    (c,) = cuts
    assert c.words == [0, 1, 2, 3, 4]  # the abandoned "So today I want to"
    assert words[4].end_s <= c.end_s <= words[5].start_s  # all of the attempt goes, none of the kept line


def test_cue_word_removes_the_line_it_cancels():
    spec = _even(
        "Our tool tracks brands. Our tool tracks the brands again. Our tool tracks the brands AI recommends."
    )
    words = _say(spec)
    (c,) = propose_cuts(words, CFG, "en")  # the first sentence is complete: kept; the cued one goes
    assert [words[i].text for i in c.words] == ["Our", "tool", "tracks", "the", "brands", "again."]
    assert "cue" in c.reason


def test_complete_sentences_that_start_alike_are_not_retakes():
    words = _say(_even("It tracks which brands AI recommends. It tracks which brands ChatGPT names."))
    assert propose_cuts(words, CFG, "en") == []


def test_a_false_start_at_the_head_takes_the_leading_silence_with_it():
    words = _say(_even("So today I want-- so today I want to show you.", t0=1.6))
    head, tail = propose_cuts(words, CFG, "en", {"t1": 8.0})
    assert head.start_s == 0.0 and head.kind == "retake"
    assert tail.kind == "silence" and tail.end_s == 8.0  # the silence after the last word, to the take's end


def test_a_cue_alone_cancels_its_own_line():
    words = _say(_even("Hello everyone. This is wrong again. This is right."))
    cues = [c for c in propose_cuts(words, CFG, "en") if "cue" in c.reason]
    (c,) = cues
    assert [words[i].text for i in c.words] == ["This", "is", "wrong", "again."]


def test_apply_cuts_builds_frame_exact_segments():
    words = _say([("Hello", 1.0, 1.4), ("there.", 3.0, 3.4)])
    cuts = propose_cuts(words, CFG, "en")
    segs = apply_cuts(cuts, {"t1": 150}, fps=30)
    assert [(s.take, s.src_in, s.src_out, s.rec_in) for s in segs] == [
        ("t1", 0, round((1.4 + CFG.cuts.keep_after_s) * 30), 0),
        ("t1", round((3.0 - CFG.cuts.keep_before_s) * 30), 150, segs[0].src_out),
    ]


def test_words_move_onto_the_edited_clock_and_removed_words_drop():
    words = _say([("So", 1.0, 1.2), ("um", 1.6, 1.9), ("today", 2.3, 2.6)], kind={"um": "filler"})
    cuts = propose_cuts(words, CFG, "en")
    segs = apply_cuts(cuts, {"t1": 120}, fps=30)
    moved = remap_words(words, segs, fps=30, removed={i for c in cuts for i in c.words})
    assert [w.text for w in moved] == ["So", "today"]
    gap = (segs[1].src_in - segs[0].src_out) / 30
    assert moved[1].start_s == pytest.approx(2.3 - gap, abs=1 / 30)


def test_multiple_takes_play_in_order():
    a = _say([("One.", 0.5, 0.9)], take="t1")
    b = [w.model_copy(update={"i": 1}) for w in _say([("Two.", 0.4, 0.8)], take="t2")]
    segs = apply_cuts([], {"t1": 60, "t2": 45}, fps=30)
    assert [(s.take, s.rec_in) for s in segs] == [("t1", 0), ("t2", 60)]
    moved = remap_words(a + b, segs, fps=30, removed=set())
    assert moved[1].start_s == pytest.approx(2.0 + 0.4)


def test_presenter_timeline_scenes_follow_sentences_and_fix_case():
    from create.footage.timeline import build_presenter_timeline

    words = _say(_even("Hello there. it works now. And this is the end of it.", t0=0.2, step=0.9))
    tl = build_presenter_timeline("demo", words, 12.0, 30, scene_target_s=2.0)
    assert [w.text for w in tl.words][2] == "It"  # a sentence start whose filler was cut
    assert [s.scene for s in tl.scenes] == ["s01", "s02"]  # "Hello there." is under the 2 s target: it joins
    assert tl.scenes[0].start_s == 0 and tl.scenes[-1].end_s == 12.0
    for a, b in zip(tl.scenes, tl.scenes[1:], strict=False):
        assert a.end_s == b.start_s and a.voice_end_s <= a.end_s <= b.voice_start_s


def _timed(spec: list[tuple[str, float, float]]) -> list[TranscriptWord]:
    return _say(spec)


def test_parallel_phrases_are_not_retakes():
    # Robert's first take: "the type of restaurant that you have or the type of hotel" (no pause after "or")
    words = _timed([("search", 31.0, 31.3), ("for", 31.35, 31.5), ("the", 31.6, 31.7), ("type", 31.74, 31.9),
                    ("of", 31.94, 32.0), ("restaurant", 32.54, 32.94), ("that", 32.98, 33.12),
                    ("you", 33.16, 33.22), ("have", 33.26, 33.44), ("or", 33.48, 33.56), ("the", 33.6, 33.68),
                    ("type", 33.72, 33.86), ("of", 33.92, 34.0), ("hotel,", 34.04, 34.38)])  # fmt: skip
    assert [c for c in propose_cuts(words, CFG, "en") if c.kind == "retake"] == []


def test_a_restart_after_a_pause_is_a_retake():
    words = _timed([("Find", 1.0, 1.2), ("out", 1.25, 1.4), ("what", 1.45, 1.6), ("it", 1.65, 1.7),
                    ("Find", 2.6, 2.8), ("out", 2.85, 3.0), ("what", 3.05, 3.2), ("it", 3.25, 3.3),
                    ("recommends.", 3.35, 3.9)])  # fmt: skip
    (c,) = [c for c in propose_cuts(words, CFG, "en") if c.kind == "retake"]
    assert c.words == [0, 1, 2, 3]


def test_a_count_in_at_the_start_is_cut():
    words = _timed([("Three,", 2.74, 2.96), ("doi,", 3.36, 3.58), ("unu,", 3.98, 4.18), ("si.", 4.48, 4.6),
                    ("If", 5.14, 5.22), ("you", 5.26, 5.3), ("want", 5.34, 5.5)])  # fmt: skip
    (c,) = [c for c in propose_cuts(words, CFG, "en", {"t1": 6.0}) if c.kind == "count_in"]
    assert c.words == [0, 1, 2, 3] and c.start_s == 0.0  # mixed languages, as Robert counts
    assert c.end_s <= 5.14


def test_numbers_inside_a_sentence_stay():
    words = _timed(_even("I have three tips and two of them are free."))
    assert propose_cuts(words, CFG, "en") == []


def test_stuttered_words_read_clean_in_the_timeline():
    from create.footage.timeline import build_presenter_timeline

    words = _timed([("just", 0.2, 0.4), ("try", 0.45, 0.6), ("t-tracking", 0.65, 1.2), ("now.", 1.25, 1.5)])
    tl = build_presenter_timeline("demo", words, 2.0, 30, scene_target_s=8.0)
    assert [w.text for w in tl.words] == ["Just", "try", "tracking", "now."]


def _long_take() -> list[TranscriptWord]:
    text = (
        "We track your brand in every answer. Then we show the gaps, the wins and the losses. "
        "Every week you get a short report with what to fix first."
    )
    return _say(_even(text, t0=0.5))


def test_long_stretches_are_split_at_sentence_ends():
    words = _long_take()
    fps = 30
    end = round((words[-1].end_s + 0.3) * fps)
    seg = EdlSegment(take="t1", src_in=0, src_out=end, rec_in=0)
    out = split_long([seg], words, fps, CFG.cuts.punch_max_s, CFG.cuts.punch_min_s)
    assert len(out) > 1
    assert out[0].src_in == 0 and out[-1].src_out == end
    for a, b in itertools.pairwise(out):
        assert a.src_out == b.src_in  # contiguous: nothing is removed
        assert b.rec_in == a.rec_in + (a.src_out - a.src_in)
    for s in out:
        assert CFG.cuts.punch_min_s <= (s.src_out - s.src_in) / fps <= CFG.cuts.punch_max_s
    ends = {
        round((w.end_s + n.start_s) / 2 * fps) for w, n in itertools.pairwise(words) if w.text.endswith(".")
    }
    assert out[0].src_out in ends


def test_short_segments_stay_whole():
    words = _say(_even("Short and sweet."))
    seg = EdlSegment(take="t1", src_in=0, src_out=60, rec_in=0)
    assert split_long([seg], words, 30, CFG.cuts.punch_max_s, CFG.cuts.punch_min_s) == [seg]


def test_the_first_shot_ends_inside_the_hook():
    words = _long_take()
    fps = 30
    seg = EdlSegment(take="t1", src_in=0, src_out=round((words[-1].end_s + 0.3) * fps), rec_in=0)
    out = split_long([seg], words, fps, CFG.cuts.punch_max_s, CFG.cuts.punch_min_s, CFG.cuts.punch_hook_s)
    assert out[0].src_out / fps <= CFG.cuts.punch_hook_s
    later = split_long([seg.model_copy(update={"rec_in": 0})], words, fps, 5.0, 1.8, None)
    assert later[0].src_out / fps > CFG.cuts.punch_hook_s  # no hook: the sentence end


def test_cut_notes_set_the_start_and_end_keep_a_span_and_add_cuts():
    """Robert's notes (cut-notes.yaml): everything before the start and after the end goes, proposals inside
    them go, a kept span loses its cuts (the black-hole silence), and an extra cut is added."""
    from create.footage.cuts import apply_notes
    from lens.schemas.create import CutNotes

    words = _say(
        [
            ("notes", 0.5, 0.9),
            ("go.", 1.2, 1.5),
            ("Hello", 3.0, 3.3),
            ("brand", 4.0, 4.3),
            ("there.", 5.0, 5.3),
            ("wait.", 9.0, 9.3),
            ("end.", 12.0, 12.3),
        ]
    )
    props = propose_cuts(words, CFG, "en", {"t1": 15.0})
    notes = CutNotes(
        take="t1",
        start_s=2.8,
        end_s=13.0,
        keep=[{"start_s": 5.4, "end_s": 9.0}],
        cut=[{"start_s": 3.9, "end_s": 4.4, "reason": "false start"}],
    )
    out = apply_notes(props, notes, words, 15.0)
    assert [c.id for c in out] == [f"c{k:03d}" for k in range(1, len(out) + 1)]
    head = out[0]
    assert (head.start_s, head.end_s, head.kind) == (0.0, 2.8, "cue") and head.words == [0, 1]
    assert out[-1].start_s == 13.0 and out[-1].end_s == 15.0
    assert not any(c.start_s < 9.0 and c.end_s > 5.4 for c in out)  # nothing cut inside the kept span
    assert any(c.reason.endswith("false start") and c.words == [3] for c in out)
    assert all(c.start_s >= 2.8 for c in out[1:])


def test_a_cold_open_plays_first_and_its_words_come_twice():
    """open_with: a flash-forward segment first (its words said there and again in place), the rest after."""
    from create.footage.cuts import cold_open
    from lens.schemas.create import EdlSegment

    segs = [
        EdlSegment(take="t1", src_in=0, src_out=90, rec_in=0),
        EdlSegment(take="t1", src_in=120, src_out=300, rec_in=90),
    ]
    out = cold_open(segs, "t1", 8.0, 9.0, 30)
    assert out[0].cold_open and (out[0].src_in, out[0].src_out, out[0].rec_in) == (240, 270, 0)
    assert [s.rec_in for s in out[1:]] == [30, 120]
    words = _say([("hello", 0.5, 0.9), ("Pixie,", 8.1, 8.5), ("no!", 8.6, 8.9)])
    got = remap_words(words, out, 30, set())
    assert [w.text for w in got] == ["Pixie,", "no!", "hello", "Pixie,", "no!"]
    assert got[0].start_s == 0.1 and got[2].start_s == 1.5 and got[3].start_s == 8.1


def test_a_cold_open_keeps_its_words_when_their_place_is_cut():
    """A loop's spans stop before the flash-forward (n09): the cold open still says its words."""
    from create.footage.cuts import cold_open
    from lens.schemas.create import EdlSegment

    out = cold_open([EdlSegment(take="t1", src_in=0, src_out=90, rec_in=0)], "t1", 8.0, 9.0, 30)
    words = _say([("hello", 0.5, 0.9), ("Pixie,", 8.1, 8.5), ("no!", 8.6, 8.9)])
    got = remap_words(words, out, 30, {1, 2})  # both cut from their own place
    assert [w.text for w in got] == ["Pixie,", "no!", "hello"]
