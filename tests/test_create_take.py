"""create take (ADR 0035): one call from the take Robert sent to the cut page, with a provisional brief whose
language comes from the take, and his words as plain text (no second transcription)."""

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from create.footage.take import kept_ids, place_take, provisional_brief, run_take, said, seconds, set_language
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import Brief, CutProposal, TranscriptWord

CFG = load_config(REPO_ROOT / "config" / "lens.yaml")


def _word(i: int, text: str, kind: str = "word") -> TranscriptWord:
    return TranscriptWord(i=i, take="t01", text=text, kind=kind, start_s=i * 0.4, end_s=i * 0.4 + 0.3)


def test_the_provisional_brief_is_valid_and_takes_the_detected_language():
    text = provisional_brief("x-ads", "en", datetime(2026, 10, 23, tzinfo=UTC))
    brief = Brief.model_validate(yaml.safe_load(text))
    assert brief.project == "x-ads" and brief.brand == "acme" and brief.voice == "presenter"
    assert "TODO" in brief.message and "TODO" in brief.facts[0].claim  # nothing passes for finished
    assert Brief.model_validate(yaml.safe_load(set_language(text, "ro"))).language == "ro"
    other = Brief.model_validate(yaml.safe_load(provisional_brief("p", "en", datetime.now(UTC), "other")))
    assert other.brand == "other" and other.product.spoken == "other" and "TODO" in other.product.one_liner


def test_the_take_is_linked_not_copied_and_never_replaces_another(tmp_path: Path):
    video = tmp_path / "IMG_0042.MOV"
    video.write_bytes(b"take one")
    raw = tmp_path / "raw"
    target = place_take(video, raw)
    assert target.name == "01-take.mov" and target.read_bytes() == b"take one"
    assert place_take(video, raw) == target  # a rerun is fine
    other = tmp_path / "other.mov"
    other.write_bytes(b"another take entirely")
    with pytest.raises(FileExistsError):
        place_take(other, raw)


def test_detected_languages_become_two_letter_codes():
    from create.footage.transcribe import iso1

    codes = ("ron", "eng", "spa", "en-US", "RO", "hun")
    assert [iso1(c) for c in codes] == ["ro", "en", "es", "en", "ro", "hu"]  # fmt: skip
    assert iso1("est") == "" and iso1("") == ""  # unknown: the caller keeps the language it asked for


def test_what_he_says_reads_as_text_without_sound_events():
    words = [_word(0, "So,", "filler"), _word(1, "X"), _word(2, "(laughs)", "event"), _word(3, "writes")]
    assert said(words) == "So, X writes"


def test_take_runs_the_start_in_order_and_lets_the_engine_find_his_language(tmp_path, monkeypatch):
    import create.footage.cutpage as cutpage
    import create.footage.run as run

    calls: list[str] = []
    take = SimpleNamespace(id="t01", width=1080, height=1920, duration_s=40.0, hdr=False)
    monkeypatch.setattr(
        run, "run_ingest", lambda r, p, c: (calls.append("ingest"), SimpleNamespace(takes=[take]))
    )

    def transcript(r, p, c, terms, language=None):
        calls.append(f"transcribe:{language!r}")
        words = [_word(0, "Salut,"), _word(1, "sunt"), _word(2, "Robert.")]
        return None, SimpleNamespace(words=words, engine="elevenlabs", language="ro")

    monkeypatch.setattr(run, "run_transcript", transcript)
    cut = SimpleNamespace(id="c001", start_s=0.0, end_s=1.5, kind="count_in", reason="before the first word")
    monkeypatch.setattr(
        run, "run_cuts", lambda r, p, c: (calls.append("cuts"), SimpleNamespace(proposals=[cut]))
    )
    monkeypatch.setattr(cutpage, "run_cut_page", lambda r, p: calls.append("page") or r / "cuts.html")
    import create.tokens as tokens

    monkeypatch.setattr(
        tokens, "run_tokens", lambda r, p, c: (calls.append("tokens"), SimpleNamespace(frame="vertical"))
    )
    monkeypatch.setattr(tokens, "token_errors", lambda t, d, b: [])
    monkeypatch.setattr("create.project.brand_dir", lambda r, p: r)
    video = tmp_path / "upload.mp4"
    video.write_bytes(b"x")
    lines = run_take(tmp_path, "demo", video, CFG, [])
    assert calls == ["ingest", "transcribe:''", "tokens", "cuts", "page"]  # '' = detect
    brief = Brief.model_validate(yaml.safe_load((tmp_path / "projects/demo/brief.yaml").read_text()))
    assert brief.language == "ro"
    assert lines[-1] == "said: Salut, sunt Robert." and any("provisional" in x for x in lines)
    assert any("~38 s if all are approved" in x for x in lines)
    calls.clear()
    (tmp_path / "projects/demo/tokens.json").write_text("{}")
    run_take(tmp_path, "demo", video, CFG, [])  # a brief and tokens exist now: kept as they are
    assert calls[1] == "transcribe:None" and "tokens" not in calls


def test_his_cut_decision_reads_phone_times_and_keeps_the_cuts_near_them():
    assert [seconds(t) for t in ("41", "41.5", "0:41", "1:05")] == [41.0, 41.5, 41.0, 65.0]
    cuts = [CutProposal(id=f"c00{i}", kind="silence", take="t01", start_s=a, end_s=b, reason="pause")
            for i, (a, b) in enumerate([(0.0, 2.3), (40.2, 40.9), (64.0, 64.5)], 1)]  # fmt: skip
    assert kept_ids(cuts, [41.0], 1.0) == ["c002"]  # 0.1 s after the cut ends: his 0:41
    assert kept_ids(cuts, [30.0], 1.0) == []  # nothing near: nothing kept
    assert kept_ids(cuts, [], 1.0) == []


def test_take_with_his_decision_records_it_and_writes_no_cut_page(tmp_path, monkeypatch):
    import create.footage.cutpage as cutpage
    import create.footage.run as run
    import create.tokens as tokens

    take = SimpleNamespace(id="t01", width=1080, height=1920, duration_s=60.0, hdr=False)
    words = [_word(0, "Hi")]
    cuts = [
        CutProposal(id="c001", kind="count_in", take="t01", start_s=0.0, end_s=1.5, reason="count-in"),
        CutProposal(id="c002", kind="silence", take="t01", start_s=40.2, end_s=40.9, reason="pause"),
    ]
    monkeypatch.setattr(run, "run_ingest", lambda r, p, c: (None, SimpleNamespace(takes=[take])))
    monkeypatch.setattr(run, "run_transcript", lambda r, p, c, t, language=None: (
        None, SimpleNamespace(words=words, engine="elevenlabs", language="en")))  # fmt: skip
    monkeypatch.setattr(run, "run_cuts", lambda r, p, c: (None, SimpleNamespace(proposals=cuts)))
    monkeypatch.setattr(tokens, "run_tokens", lambda r, p, c: (None, SimpleNamespace(frame="vertical")))
    monkeypatch.setattr(tokens, "token_errors", lambda t, d, b: [])
    monkeypatch.setattr("create.project.brand_dir", lambda r, p: r)
    monkeypatch.setattr(cutpage, "run_cut_page", lambda r, p: pytest.fail("he already decided: no page"))
    video = tmp_path / "take.mov"
    video.write_bytes(b"x")
    lines = run_take(tmp_path, "demo", video, CFG, [], approve=True, keep=[41.0, 20.0])
    approvals = yaml.safe_load((tmp_path / "projects/demo/cuts-approved.yaml").read_text())
    assert approvals == {"approve": "all", "reject": ["c002"]}
    assert any("approved: 1 cuts" in x and "kept in: c002" in x and "no proposed cut near 20 s" in x
               for x in lines)  # fmt: skip
