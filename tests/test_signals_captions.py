"""Caption chunking from burned-in captions (handoff 5.10/6: choppy 2-3 word groups)."""

import shutil

import pytest

from lens.config import load_config
from lens.signals.captions import detect, stats
from tests.fixtures.scenes import captioned_clip, encode

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
CFG = load_config().signals.captions


@pytest.fixture(scope="module", params=[30.0, 60.0], ids=["30fps", "60fps"])
def clip(request, tmp_path_factory):
    fps = request.param
    frames, truth = captioned_clip(fps)
    path = encode(frames, fps, tmp_path_factory.mktemp("c") / "captions.mp4")
    return fps, truth, detect(path, fps, 640, 360, CFG)


def test_groups_and_switch_frames(clip):
    _, truth, groups = clip
    assert [g.words for g in groups] == truth["words"]
    assert [g.start_f for g in groups[1:]] == pytest.approx(truth["switch_frames"], abs=1)
    assert groups[0].text.lower() == truth["texts"][0].lower()


def test_stats_and_word_sync(clip):
    fps, truth, groups = clip
    synced_words = [f / fps for f in truth["switch_frames"]]
    s = stats(groups, fps, truth["frames"], synced_words, CFG)
    assert s is not None
    assert s.words_per_group_mean == pytest.approx(sum(truth["words"]) / len(truth["words"]))
    assert s.word_synced_share == 1.0
    off = stats(groups, fps, truth["frames"], [f / fps + 0.3 for f in truth["switch_frames"]], CFG)
    assert off is not None and off.word_synced_share == 0.0


def test_no_captions_returns_none(clip):
    fps, truth, groups = clip
    assert stats(groups[:2], fps, truth["frames"], [], CFG) is None
