"""S1-S3 end to end on a synthetic explainer with music, SFX and a narration (stems on)."""

import json
import shutil

import pytest
import yaml

from lens.config import REPO_ROOT, load_config
from lens.frames import normalize_one
from lens.ingest import ingest_one
from lens.schemas import SourcesFile
from lens.signals import run_signals
from lens.validate import validate_all
from tests.fixtures import voice
from tests.fixtures.scenes import explainer_with_sound

pytestmark = [
    pytest.mark.skipif(
        shutil.which("ffmpeg") is None or not voice.available(), reason="needs ffmpeg + espeak-ng"
    ),
    pytest.mark.slow,
]


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    root = tmp_path_factory.mktemp("repo")
    for d in ("config", "taxonomy", "sources", "media"):
        (root / d).mkdir()
    shutil.copy(REPO_ROOT / "config" / "lens.yaml", root / "config" / "lens.yaml")
    shutil.copy(REPO_ROOT / "taxonomy" / "v1.yaml", root / "taxonomy" / "v1.yaml")
    mp4, truth = explainer_with_sound(root / "media")
    entry = {
        "id": "synth",
        "url": f"file://{mp4}",
        "brand": "Synth",
        "title": "synth",
        "format": "narrated_explainer",
        "tier": "own",
        "why": "e2e",
    }
    (root / "sources" / "sources.yaml").write_text(yaml.safe_dump([entry]))
    (src,) = SourcesFile.model_validate([entry]).root
    cfg = load_config(root / "config" / "lens.yaml")
    ingest_one(src, root)
    normalize_one(src, root, cfg)
    status = run_signals(src, root, cfg)
    summary = json.loads((root / "videos" / "synth" / "signals.summary.json").read_text())
    return root, src, cfg, truth, status, summary


def test_outputs_valid_and_rerun_cached(run):
    root, src, cfg, _, status, _ = run
    assert status == "analysed"
    assert all(r.ok for r in validate_all(root))
    assert run_signals(src, root, cfg) == "cached"
    assert (root / "data" / "signals" / "synth" / "stems" / "vocals.wav").exists()


def test_video_side(run):
    *_, truth, _, s = run
    v = s["video"]
    assert v["transitions_by_kind"] == {"hard_cut": 1, "crossfade": 1, "push": 1, "zoom_through": 1}
    assert v["dead_hold_count"] == 1 and v["dead_hold_s"] == pytest.approx(1.2, abs=0.1)
    assert len(v["shots"]) == len(truth["scene_starts"])


def test_sfx_with_voice_and_music(run):
    *_, truth, _, s = run
    a = s["audio"]
    assert a["stems"] is True
    assert len(a["sfx"]) == len(truth["sfx"])  # neither the voice nor the groove leaks in
    for want in truth["sfx"]:
        got = min(a["sfx"], key=lambda x: abs(x["sync_s"] - want["sync_s"]))
        tol = 0.15 if want["label"] == "riser" else 1 / 30
        assert abs(got["sync_s"] - want["sync_s"]) <= tol, (want, got)
        assert got["label"] == want["label"]
    impact = next(x for x in a["sfx"] if x["label"] == "impact")
    assert impact["on_beat"] is True
    click = next(x for x in a["sfx"] if x["label"] == "click")
    assert abs(click["reveal_offset_ms"]) <= 50  # the click sits on the fade-in's start


def test_beat_and_cuts_on_beat(run):
    *_, truth, _, s = run
    a = s["audio"]
    assert a["bpm"] == pytest.approx(truth["bpm"], abs=1)
    assert a["cuts_on_beat_share"] == pytest.approx(0.25)  # only the cut at 2.0 s is on a beat


def test_speech_from_vocal_stem(run):
    *_, s = run
    sp = s["speech"]
    assert sp is not None and sp["words"] >= 18 and 120 <= sp["wpm"] <= 200
    assert sp["perceived_emotion"] is None
    assert abs(s["audio"]["ducking_db"]) < 2  # this mix has no ducking


def test_baseline_audit_on_the_synthetic_explainer(run):
    """M4.5 on real S1-S3 output: the planted problems come back as fixes with timestamps."""
    from lens.compare import compare_targets
    from lens.schemas.signals import SignalsSummary
    from lens.schemas.video import VideoMeta

    root, _, cfg, *_ = run
    meta = VideoMeta.model_validate_json((root / "videos" / "synth" / "meta.json").read_text())
    summary = SignalsSummary.model_validate_json(
        (root / "videos" / "synth" / "signals.summary.json").read_text()
    )
    r = compare_targets(meta, summary, cfg)
    fixes = {f.metric: f for f in r.fixes}
    assert "dead_holds" in fixes and fixes["dead_holds"].evidence  # the empty card in scene 2
    assert "intonation" in fixes  # espeak is flat
    assert "cuts_on_beat" in fixes  # 1 of 4 boundaries on the beat
    assert "ducking" in fixes  # the fixture never ducks
    statuses = {m.id: m.status for m in r.metrics}
    assert statuses["sfx_at_scene_start"] == "pass" and statuses["sfx_on_reveals"] == "pass"


def test_stems_are_deterministic(run, tmp_path):
    """Same input, same stems: demucs must not apply random shifts (regression: flaky SFX count)."""
    import numpy as np
    import soundfile as sf

    from lens.signals.stems import separate

    root, _, cfg, *_ = run
    wav = root / "data" / "media" / "synth" / "audio.wav"
    a, _ = separate(wav, tmp_path / "a", cfg.signals.stems.model)
    b, _ = separate(wav, tmp_path / "b", cfg.signals.stems.model)
    assert np.array_equal(sf.read(a)[0], sf.read(b)[0])
