"""S3 audio signals against a synthetic soundtrack with known answers (BUILD_PLAN 11.1)."""

import re
import shutil
import subprocess

import pytest

from lens.config import load_config
from lens.signals.audio import analyse
from tests.fixtures.sounds import BPM, explainer_soundtrack

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
CFG = load_config().signals.audio
FPS = 30.0
FRAME_S = 1 / FPS


@pytest.fixture(scope="module")
def track(tmp_path_factory):
    path = tmp_path_factory.mktemp("a") / "track.wav"
    # Aligned to scenes.explainer(30): landing of scene 0's box, a beat, scene 2's reveal, the zoom.
    return explainer_soundtrack(
        path, 9.8, landing_s=36 / FPS, impact_beat_s=4.5, click_s=171 / FPS, riser_end_s=249 / FPS
    )


@pytest.fixture(scope="module")
def result(track):
    return analyse(track.path, CFG)


def _ffmpeg_r128(path):
    out = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            "ebur128=peak=true:framelog=quiet",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stderr
    summary = out[out.rindex("Summary:") :]
    grab = lambda key: float(re.search(rf"{key}:\s+(-?[\d.]+)", summary).group(1))  # noqa: E731
    return grab("I"), grab("LRA"), grab("Peak")


def test_loudness_matches_target_and_ffmpeg(track, result):
    loud, _, _ = result
    assert loud.integrated_lufs == pytest.approx(track.integrated_lufs, abs=0.1)
    i, lra, tp = _ffmpeg_r128(track.path)
    assert loud.integrated_lufs == pytest.approx(i, abs=0.1)
    assert loud.lra_lu == pytest.approx(lra, abs=0.5)
    assert loud.true_peak_dbtp == pytest.approx(tp, abs=0.3)
    assert loud.true_peak_dbtp >= loud.sample_peak_dbfs


def test_bpm_and_beat_phase(result):
    _, beats, _ = result
    assert beats.bpm == pytest.approx(BPM, abs=1.0)
    period = 60.0 / BPM
    phase_err = [min(t % period, period - t % period) for t in beats.times]
    assert max(phase_err) <= CFG.beat_grid_tolerance_ms / 1000


def test_every_sfx_found_labelled_and_timed(track, result):
    _, _, sfx = result
    for want in track.sfx:
        match = min(sfx, key=lambda c: abs(c.sync_s - float(want["sync_s"])))
        assert abs(match.sync_s - float(want["sync_s"])) <= FRAME_S, (want, match)
        assert match.label == want["label"], (want, match)


def test_music_bed_is_not_sfx(track, result):
    _, _, sfx = result
    assert len(sfx) == len(track.sfx)  # no kick, hat or pad onsets leak through


def test_on_beat_is_a_feature_not_a_filter(track, result):
    _, _, sfx = result
    impact = next(c for c in sfx if c.label == "impact")
    assert impact.on_beat is True  # kept although it sits exactly on the beat (plan 7.1)
    whoosh = next(c for c in sfx if c.label == "whoosh")
    assert whoosh.sync_s < 36 / FPS  # the whoosh peaks before the visual landing (sound leads)
