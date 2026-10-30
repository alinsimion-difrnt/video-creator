"""M4.5 compare --targets-only on hand-built summaries (fast, no media)."""

from datetime import UTC, datetime

import pytest

from lens.compare import compare_targets
from lens.config import load_config
from lens.report import html_page, markdown
from lens.schemas.common import Annotator, Provenance
from lens.schemas.signals import SignalsSummary
from lens.schemas.video import VideoMeta

CFG = load_config()
PROV = Provenance(
    tool_version="0",
    stage="s3_signals",
    annotator=Annotator.CODE,
    input_hash="a" * 64,
    created_at=datetime(2026, 10, 3, tzinfo=UTC),
)


def _summary(video_id: str = "demo", voice: bool = True, **audio_over) -> SignalsSummary:
    audio = {
        "stems": True,
        "ducking_db": 1.0,
        "loudness": {
            "integrated_lufs": -20.9,
            "short_term_max_lufs": -18.0,
            "lra_lu": 4.0,
            "sample_peak_dbfs": -3.2,
            "true_peak_dbtp": -3.0,
        },
        "bpm": 120.0,
        "beat_confidence": 0.6,
        "sfx": [
            {
                "id": "x001",
                "sync_s": 10.0,
                "label": "whoosh",
                "rules_label": "whoosh",
                "clap_label": "whoosh",
                "clap_score": 0.6,
                "agreement": True,
                "label_source": "rules",
                "on_beat": False,
                "reveal_offset_ms": None,
                "scene_start_offset_ms": 0.0,
                "at_scene_start": True,
            },
            {
                "id": "x002",
                "sync_s": 20.0,
                "label": "click",
                "rules_label": "click",
                "clap_label": None,
                "clap_score": None,
                "agreement": None,
                "label_source": "rules",
                "on_beat": False,
                "reveal_offset_ms": None,
                "scene_start_offset_ms": 33.0,
                "at_scene_start": True,
            },
        ],
        "sfx_per_min": 2.0,
        "label_agreement_share": 1.0,
        "sfx_at_scene_start_share": 1.0,
        "sfx_near_reveal_share": 0.0,
        "cuts_on_beat_share": 0.1,
    } | audio_over
    speech = {
        "words": 419,
        "speech_span_s": 140.0,
        "wpm": 180.0,
        "articulation_wpm": 190.0,
        "pause_count": 30,
        "pause_mean_ms": 300.0,
        "pause_p90_ms": 400.0,
        "pause_cv": 0.2,
        "pauses_by_length": {"short": 25, "medium": 5, "long": 0},
        "phrase_rate_cv": 0.05,
        "pitch_median_hz": 210.0,
        "pitch_std_semitones": 1.5,
        "energy_std_db": 4.0,
        "wpm_cv_across_shots": 0.05,
    }
    return SignalsSummary.model_validate(
        {
            "provenance": PROV.model_dump(),
            "video_id": video_id,
            "video": {
                "fps": 30.0,
                "duration_s": 144.6,
                "shots": [
                    {
                        "id": "s001",
                        "start_s": 0,
                        "end_s": 70,
                        "transition_in": None,
                        "motion_energy": 0.01,
                        "events_per_s": 0.2,
                        "wpm": 180,
                    }
                ],
                "transitions_by_kind": {"crossfade": 10, "push": 3, "zoom_through": 1},
                "mean_shot_s": 9.6,
                "events": [],
                "camera_moves": {},
                "holds": [{"shot": "s007", "start_s": 61.0, "end_s": 62.6, "dead": True}],
                "dead_hold_count": 1,
                "dead_hold_s": 1.6,
                "pace_cv": 0.1,
            },
            "audio": audio,
            "speech": speech if voice else None,
            "captions": None,
        }
    )


def _meta(video_id: str, duration: float, fps: float, frames: int) -> VideoMeta:
    h = "b" * 64
    return VideoMeta.model_validate(
        {
            "provenance": PROV.model_dump() | {"stage": "s2_normalize"},
            "video": video_id,
            "original": {
                "sha256": h,
                "bytes": 1,
                "container": "mp4",
                "video_codec": "h264",
                "duration_s": duration,
                "width": 1920,
                "height": 1080,
                "native_fps": fps,
                "vfr": False,
                "irregular_frame_share": 0,
                "has_audio": True,
                "audio_codec": "aac",
                "audio_sample_rate": 48000,
                "audio_channels": 2,
            },
            "window": {"start_s": 0, "end_s": duration, "capped": False},
            "proxy": {
                "sha256": h,
                "width": 1280,
                "height": 720,
                "fps": fps,
                "duration_s": duration,
                "frames": frames,
                "has_audio": True,
            },
            "audio": {"sample_rate": 48000, "channels": 2, "duration_s": duration},
            "base_frames": {"fps": 2, "width": 960, "height": 540, "count": 289},
            "phash": ["0" * 16],
        }
    )


def test_v1_like_video_gets_the_handoff_problems():
    r = compare_targets(_meta("demo", 144.6, 30, 4338), _summary(), CFG)
    failing = {m.id for m in r.metrics if m.status == "fail"}
    assert {
        "loudness",
        "sfx_at_scene_start",
        "sfx_on_reveals",
        "dead_holds",
        "pace_variation",
        "intonation",
    } <= failing
    assert 1 <= len(r.fixes) <= 10
    assert [f.severity for f in r.fixes] == sorted((f.severity for f in r.fixes), reverse=True)
    holds = next(f for f in r.fixes if f.metric == "dead_holds")
    assert holds.evidence == ["1:01.00-1:02.60 (1.6s, shot s007)"]
    at_start = next(f for f in r.fixes if f.metric == "sfx_at_scene_start")
    assert len(at_start.evidence) == 2


def test_voice_metrics_are_na_without_voice():
    r = compare_targets(_meta("demo", 144.6, 30, 4338), _summary(voice=False), CFG)
    by_id = {m.id: m for m in r.metrics}
    assert by_id["intonation"].status == "n/a" and "voice" in (by_id["intonation"].note or "")
    assert by_id["ducking"].status == "n/a"


def test_destination_changes_loudness_target():
    r = compare_targets(_meta("demo", 144.6, 30, 4338), _summary(), CFG, destination="youtube")
    loud = next(m for m in r.metrics if m.id == "loudness")
    assert (loud.min, loud.max) == (-15, -13)
    with pytest.raises(ValueError):
        compare_targets(_meta("demo", 144.6, 30, 4338), _summary(), CFG, destination="myspace")


def test_baseline_check_reproduces_acme_known_values():
    s = _summary("acme-explainer-v1")
    r = compare_targets(_meta("acme-explainer-v1", 144.6, 30, 4338), s, CFG)
    assert r.baseline is not None
    checks = {c.name: c for c in r.baseline}
    assert checks["integrated_lufs"].ok and checks["duration_s"].ok and checks["frames"].ok
    assert checks["transitions"].ok  # 14 detected
    assert checks["sfx_at_scene_start_share"].ok
    assert checks["wpm"].ok


def test_baseline_check_flags_a_wrong_tool():
    s = _summary(
        "acme-explainer-v1",
        loudness={
            "integrated_lufs": -14.0,
            "short_term_max_lufs": -12.0,
            "lra_lu": 4.0,
            "sample_peak_dbfs": -1.0,
            "true_peak_dbtp": -0.5,
        },
    )
    r = compare_targets(_meta("acme-explainer-v1", 144.6, 30, 4338), s, CFG)
    assert not {c.name: c for c in r.baseline}["integrated_lufs"].ok


def test_reports_render():
    r = compare_targets(_meta("demo", 144.6, 30, 4338), _summary(), CFG)
    md = markdown(r)
    assert "## Top fixes" in md and "1:01.00-1:02.60" in md and "house placeholders" in md
    page = html_page(r)
    assert page.startswith("<!doctype html>") and "prefers-color-scheme:dark" in page


# --- M9 corpus mode ------------------------------------------------------------------------------------


def test_place_gives_weighted_percentile_and_band():
    from lens.compare.corpus import place

    vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    pct, lo, med, hi = place(3.0, vals, [1.0] * 5)
    assert pct == 50.0 and med == 3.0 and lo < med < hi
    assert place(0.0, vals, [1.0] * 5)[0] == 0.0
    assert place(9.0, vals, [1.0] * 5)[0] == 100.0
    heavy = place(3.0, vals, [10.0, 1.0, 1.0, 1.0, 1.0])
    assert heavy[0] > 50.0  # most of the weight sits below


def test_fix_references_must_exist(tmp_path):
    import json as _json

    from lens.compare.fixes import _token_exists

    ex = tmp_path / "exports"
    ex.mkdir()
    (ex / "motion-tokens.json").write_text(
        _json.dumps({"duration_ms_by_role": {"headline": {"median": 500}}})
    )
    assert _token_exists(tmp_path, "motion-tokens.json#duration_ms_by_role.headline.median")
    assert not _token_exists(tmp_path, "motion-tokens.json#duration_ms_by_role.nope")
    assert not _token_exists(tmp_path, "secrets.json#x")
