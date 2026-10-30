"""P1: C4 voice (alignment -> words, take choice, caching) and C5 timing, without the network."""

import base64
import json
import shutil
from pathlib import Path

import pytest
import yaml

from create.timing import build_timeline, run_timing
from create.voice import SPEC_KEYS, band_distance, brand_heard, in_range, run_voice, words_from_alignment
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import Script, Voice
from lens.validate import validate_file

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "create" / "demo"


def _alignment(text: str, step: float = 0.06) -> dict:
    chars = list(text)
    return {
        "characters": chars,
        "character_start_times_seconds": [round(i * step, 3) for i in range(len(chars))],
        "character_end_times_seconds": [round((i + 1) * step, 3) for i in range(len(chars))],
    }


def test_words_skip_tags_and_trailing_punctuation():
    words = words_from_alignment(_alignment("[curious] Is yours... one of them?", step=0.1))
    assert [w.text for w in words] == ["Is", "yours...", "one", "of", "them?"]
    yours = words[1]
    assert yours.start_s == pytest.approx(1.3)  # after "[curious] I" (10 characters + "s")
    assert yours.end_s == pytest.approx(1.8)  # ends at the "s", not at the ellipsis
    assert [w.i for w in words] == [0, 1, 2, 3, 4]


def test_words_ignore_multiword_tags():
    words = words_from_alignment(_alignment("Here. [short pause] Then this."))
    assert [w.text for w in words] == ["Here.", "Then", "this."]


SPEC = {
    "wpm": {"low": 118, "high": 172, "median": 151},
    "articulation_wpm": {"low": 180, "high": 216, "median": 199},
    "pause_mean_ms": {"low": 574, "high": 1064, "median": 699},
    "pitch_std_semitones": {"low": 3.2, "high": 4.7, "median": 3.9},
    "energy_std_db": {"low": 6.7, "high": 7.5, "median": 7.4},
}


def test_in_range_and_band_distance():
    good = {"wpm": 150, "articulation_wpm": 200, "pause_mean_ms": 700, "pitch_std_semitones": 3.6}
    good["energy_std_db"] = 7.0
    assert in_range(good, SPEC) == 5
    assert band_distance(good, SPEC, ["wpm", "pitch_std_semitones"]) == 0
    # just outside beats far outside: the old in-band count could not tell these apart
    near = band_distance({**good, "pitch_std_semitones": 4.75}, SPEC, ["pitch_std_semitones"])
    far = band_distance({**good, "pitch_std_semitones": 2.8}, SPEC, ["pitch_std_semitones"])
    assert 0 < near < far
    assert band_distance({**good, "wpm": None}, SPEC, ["wpm"]) == 1.0


def test_brand_heard():
    assert brand_heard("That's what Ack-me is for.", "That's what Acme is for.", "Acme", "Ack-me")
    assert brand_heard("Ack-me. Free plan.", "Ackma. Free plan.", "Acme", "Ack-me") is False
    assert brand_heard("No brand here.", "No brand here.", "Acme", "Ack-me") is None


@pytest.fixture
def root(tmp_path: Path) -> Path:
    for rel in ("config/lens.yaml", "taxonomy/v1.yaml", "exports/voice-spec.json"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, tmp_path / rel)
    (tmp_path / "projects" / "demo").mkdir(parents=True)
    for name in ("brief.yaml", "script.yaml"):
        shutil.copy(FIXTURE / name, tmp_path / "projects" / "demo" / name)
    return tmp_path


class FakeApi:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, text, voice):
        self.calls += 1
        return {"audio_base64": base64.b64encode(b"mp3").decode(), "alignment": _alignment(text)}, len(text)


def _measure_by_take(path: Path, cfg) -> dict:
    """Take 2 is the better read in this fake: everything in band; take 1 is fast and flat."""
    return {**_prosody_by_take(path), "heard": "Demoflow checks three assistants"}


def _prosody_by_take(path: Path) -> dict:
    if path.name.endswith("-t2.mp3"):
        return {
            "wpm": 152,
            "articulation_wpm": 200,
            "pause_mean_ms": 650,
            "pitch_std_semitones": 3.7,
            "energy_std_db": 7.1,
        }
    return {
        "wpm": 185,
        "articulation_wpm": 230,
        "pause_mean_ms": 400,
        "pitch_std_semitones": 2.6,
        "energy_std_db": 7.1,
    }


def test_voice_chooses_best_take_and_validates(root: Path):
    api = FakeApi()
    path = run_voice(
        root,
        "demo",
        load_config(root / "config/lens.yaml"),
        synth=api,
        measure=_measure_by_take,
        log=lambda _: None,
    )
    takes = load_config(root / "config/lens.yaml").create.voice.takes
    assert api.calls == 2 * takes
    voice = Voice.model_validate(json.loads(path.read_text()))
    assert [s.take for s in voice.scenes] == [2, 2]
    assert voice.scenes[0].prosody.in_range == 5
    assert voice.scenes[1].words[0].text == "Demo-flow"  # the [curious] tag is not a word
    assert (
        voice.credits_used
        == sum(
            len(s["spoken"])
            for s in yaml.safe_load((root / "projects/demo/script.yaml").read_text())["scenes"]
        )
        * takes
    )
    assert (root / "data/create/demo/voice/s01-t1.mp3").exists()
    result = validate_file(path, root)
    assert result.ok, result.errors


def test_voice_rerun_is_free_and_script_change_regenerates_one_scene(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    run_voice(root, "demo", cfg, synth=FakeApi(), measure=_measure_by_take, log=lambda _: None)
    again = FakeApi()
    run_voice(root, "demo", cfg, synth=again, measure=_measure_by_take, log=lambda _: None)
    assert again.calls == 0

    script = yaml.safe_load((root / "projects/demo/script.yaml").read_text())
    script["scenes"][0]["spoken"] = "People ask AI about almost everything now."
    (root / "projects/demo/script.yaml").write_text(yaml.safe_dump(script))
    changed = FakeApi()
    run_voice(root, "demo", cfg, synth=changed, measure=_measure_by_take, log=lambda _: None)
    assert changed.calls == cfg.create.voice.takes  # only s01's takes


def test_timeline_from_voice(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    run_voice(root, "demo", cfg, synth=FakeApi(), measure=_measure_by_take, log=lambda _: None)
    path, timeline, _, preview = run_timing(root, "demo", cfg.create.timing)
    assert preview is None  # the fake takes are not decodable audio
    t = cfg.create.timing
    voice = Voice.model_validate(json.loads((root / "projects/demo/voice.json").read_text()))
    s1, s2 = timeline.scenes
    assert s1.start_s == 0 and s1.voice_start_s == t.pre_roll_s
    assert s1.end_s == pytest.approx(t.pre_roll_s + voice.scenes[0].duration_s + t.scene_tail_s)
    assert s2.start_s == s1.end_s and s2.voice_start_s == s2.start_s
    assert timeline.total_s == pytest.approx(s2.voice_end_s + t.close_tail_s)
    assert timeline.words[0].start_s == pytest.approx(t.pre_roll_s + voice.scenes[0].words[0].start_s)
    assert [w.i for w in timeline.words] == list(range(len(timeline.words)))
    result = validate_file(path, root)
    assert result.ok, result.errors


def test_build_timeline_matches_fixture_rules():
    script = Script.model_validate(yaml.safe_load((FIXTURE / "script.yaml").read_text()))
    voice = Voice.model_validate(json.loads((FIXTURE / "voice.json").read_text()))
    timing = load_config().create.timing
    timeline = build_timeline("demo", script, voice, timing)
    assert [s.scene for s in timeline.scenes] == ["s01", "s02"]
    assert set(SPEC_KEYS) <= set(SPEC)


def test_misheard_brand_ranks_last(root: Path):
    def measure(path: Path, cfg) -> dict:
        heard = "Demo flaw checks" if path.name == "s02-t2.mp3" else "Demoflow checks"
        return {**_prosody_by_take(path), "heard": heard}

    cfg = load_config(root / "config/lens.yaml")
    path = run_voice(root, "demo", cfg, synth=FakeApi(), measure=measure, log=lambda _: None)
    voice = Voice.model_validate(json.loads(path.read_text()))
    s02 = voice.scenes[1]
    assert s02.take == 1  # take 2 reads better but says "Demo flaw"
    assert s02.prosody.brand_heard is True
    assert voice.scenes[0].prosody.brand_heard is None  # s01 does not say the brand


def test_cached_takes_are_remeasured_without_credits(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    run_voice(root, "demo", cfg, synth=FakeApi(), measure=_measure_by_take, log=lambda _: None)
    side = root / "data/create/demo/voice/s01-t1.json"
    take = json.loads(side.read_text())
    del take["prosody"]["heard"]  # as written before the brand check existed
    side.write_text(json.dumps(take))
    api = FakeApi()
    run_voice(root, "demo", cfg, synth=api, measure=_measure_by_take, log=lambda _: None)
    assert api.calls == 0
    assert "heard" in json.loads(side.read_text())["prosody"]
