"""study/tiktok/metrics.py on synthetic inputs (the TikTok study, studies/README.md)."""

from __future__ import annotations

import numpy as np
import pytest

from study.tiktok import metrics as m
from study.tiktok.config import load

CFG = load().measure


def test_text_layout_counts_frames_bands_and_safe_area() -> None:
    samples = [0.0, 0.5, 1.0, 1.5]
    boxes = [
        m.Box(0.0, 0.2, 0.2, 0.7, 0.25, "BIG HOOK"),  # top band, inside the core
        m.Box(0.5, 0.2, 0.2, 0.7, 0.25, "BIG HOOK"),
        m.Box(0.5, 0.2, 0.85, 0.7, 0.9, "follow me"),  # bottom band, under the description
        m.Box(1.0, 0.4, 0.5, 0.6, 0.52, "x"),  # one char: ignored
    ]
    out = m.text_layout(boxes, samples, CFG)
    assert out["text_share"] == 0.5
    assert out["first_text_s"] == 0.0
    bands = out["band_share"]
    assert isinstance(bands, dict)
    assert bands["top"] == pytest.approx(2 / 3, abs=1e-3)
    assert bands["bottom"] == pytest.approx(1 / 3, abs=1e-3)
    assert out["outside_safe_share"] == pytest.approx(1 / 3, abs=1e-3)
    assert out["words_on_screen_median"] == 3.0  # 2 words, then 2 + 2
    # all three boxes are 5% tall: caption-sized; tiny code text would not count
    assert out["caption_share"] == 0.5
    cb = out["caption_band_share"]
    assert isinstance(cb, dict) and cb["top"] == pytest.approx(2 / 3, abs=1e-3)
    small = m.text_layout([m.Box(0.0, 0.1, 0.5, 0.9, 0.51, "const x = 1")], [0.0], CFG)
    assert small["text_share"] == 1.0 and small["caption_share"] == 0.0


def test_text_layout_without_text() -> None:
    out = m.text_layout([], [0.0, 1.0], CFG)
    assert out["text_share"] == 0.0
    assert out["first_text_s"] is None


def test_face_summary_keeps_the_largest_face_and_drops_tiny_ones() -> None:
    faces = [
        m.Box(0.0, 0.3, 0.2, 0.7, 0.4),  # h 0.2
        m.Box(0.0, 0.8, 0.8, 0.82, 0.82),  # tiny: ignored
        m.Box(1.0, 0.35, 0.25, 0.65, 0.35),  # h 0.1
    ]
    out = m.face_summary(faces, [0.0, 1.0, 2.0, 3.0], CFG)
    assert out["face_share"] == 0.5
    assert out["face_height_median"] == pytest.approx(0.15)
    assert out["face_cx_median"] == pytest.approx(0.5)


def test_shot_stats() -> None:
    out = m.shot_stats([2.0, 5.0, 6.0], 10.0)
    assert out["cuts"] == 3
    assert out["cuts_per_min"] == 18.0
    assert out["shot_longest_s"] == 4.0
    assert out["first_cut_s"] == 2.0
    none = m.shot_stats([], 10.0)
    assert none["cuts"] == 0 and none["first_cut_s"] is None and none["shot_longest_s"] == 10.0


def test_speech_stats() -> None:
    words = [(0.5, 0.8), (0.9, 1.2), (1.3, 1.5)]
    out = m.speech_stats(words, 4.0)
    assert out["words"] == 3
    assert out["first_word_s"] == 0.5
    assert out["words_per_s_talking"] == pytest.approx(3 / 1.0)
    assert out["silence_share"] == pytest.approx(1 - 0.8 / 4, abs=1e-3)
    assert m.speech_stats([], 4.0)["silence_share"] == 1.0


def test_punch_ins_finds_a_zoom_run_but_not_a_cut_or_jitter() -> None:
    fps = 15.0
    scale = np.ones(60)
    scale[10:16] = 1.02  # 6 frames x 2%: a ~12% push-in
    scale[30] = 1.3  # a cut frame: ignored
    scale[45] = 1.005  # jitter below the step
    out = m.punch_ins(scale, fps, [30], CFG)
    assert out == [round(10 / fps, 2)]


def test_music_bed_db_is_loud_with_a_bed_and_quiet_without() -> None:
    sr = 16000
    t = np.arange(sr * 4) / sr
    words = [(0.5, 1.0), (2.0, 2.5)]
    silent = np.zeros_like(t)
    bed = 0.1 * np.sin(2 * np.pi * 220 * t)
    quiet = m.music_bed_db(silent, sr, words, CFG)
    loud = m.music_bed_db(bed, sr, words, CFG)
    assert quiet is not None and loud is not None
    assert quiet < CFG.music_bed_floor_db < loud


def test_loop_score_and_hook_and_density() -> None:
    a = np.zeros((4, 4))
    assert m.loop_score(a, a) == 1.0
    assert m.loop_score(a, np.ones((4, 4))) == 0.0
    h = m.hook([(0.2, 0.5), (3.5, 3.8)], [0.0, 4.0], [1.0, 5.0], [0.1, 2.9, 3.1], 3.0)
    assert h["first_word_s"] == 0.2 and h["words_in_window"] == 1
    assert h["cuts_in_window"] == 1 and h["events_in_window"] == 2 and h["text_in_window"] is True
    d = m.density([1.0, 2.0, 3.0], [1.5], 30.0)
    assert d["events_per_min"] == 6.0 and d["punches_per_min"] == 2.0


def test_watermark_is_not_text() -> None:
    assert m.is_watermark("TikTok") and m.is_watermark("TikTok Lite") and m.is_watermark("@wesbos")
    assert all(m.is_watermark(x) for x in ("kok", "tikok", "ikok", "ok", "TiOK"))
    assert not m.is_watermark("3 SEO tips") and not m.is_watermark("follow @me for more")
    boxes = [m.Box(0.0, 0.05, 0.05, 0.3, 0.09, "TikTok"), m.Box(0.0, 0.05, 0.1, 0.3, 0.13, "@wesbos")]
    assert m.text_layout(boxes, [0.0], CFG)["caption_share"] == 0.0
