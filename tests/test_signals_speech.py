"""S3 speech: local whisper words + prosody on espeak-ng narrations with known answers."""

from pathlib import Path

import pytest

from lens.config import load_config
from lens.signals.speech import SR, load_mono, pauses, prosody, tighten, transcribe, wpm_in
from tests.fixtures import voice

pytestmark = [
    pytest.mark.skipif(not voice.available(), reason="needs espeak-ng"),
    pytest.mark.slow,
]
CFG = load_config().signals.speech


def _run(tmp: Path, pitches: list[int]):
    path = tmp / "voice.wav"
    truth = voice.narration(path, pitches=pitches)
    mono = load_mono(path)
    words = tighten(transcribe(path, CFG), mono, SR, CFG)
    return truth, words, prosody(words, mono, SR, CFG)


@pytest.fixture(scope="module")
def flat(tmp_path_factory):
    return _run(tmp_path_factory.mktemp("flat"), [50, 50, 50, 50])


@pytest.fixture(scope="module")
def varied(tmp_path_factory):
    return _run(tmp_path_factory.mktemp("varied"), [20, 80, 30, 90])


def _norm(w: str) -> str:
    return w.strip(".,!?").lower()


def test_words_recovered(flat):
    truth, words, _ = flat
    got = [_norm(w.text) for w in words]
    want = [_norm(w) for w in truth["words"]]
    hits = sum(1 for w in want if w in got)
    assert hits / len(want) >= 0.9


def test_wpm_and_speech_span(flat):
    truth, words, p = flat
    true_wpm = len(truth["words"]) / (truth["speech_end_s"] - truth["speech_start_s"]) * 60
    assert p.wpm == pytest.approx(true_wpm, rel=0.05)
    assert words[0].start_s == pytest.approx(truth["speech_start_s"], abs=0.1)


def test_pauses_found_where_inserted(flat):
    truth, words, p = flat
    found = pauses(words, CFG.pause_min_ms)
    assert p.pause_count == len(truth["pauses"]) == len(found)
    for got, (_, want) in zip(found, truth["pauses"], strict=True):
        assert got / 1000 == pytest.approx(want, abs=0.15)


def test_pitch_variability_separates_flat_from_expressive(flat, varied):
    assert varied[2].pitch_std_semitones > flat[2].pitch_std_semitones + 2.0


def test_no_emotion_claimed(flat):
    assert flat[2].perceived_emotion is None


def test_wpm_in_window(flat):
    _, words, _ = flat
    assert wpm_in(words, 0.0, 3.0) is not None
    assert wpm_in(words, 30.0, 40.0) is None
