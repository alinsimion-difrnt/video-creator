"""A3 pattern cards: numbers must be the S9 stats verbatim; the Markdown carries them."""

from __future__ import annotations

import json

from lens.schemas.cards import PatternCard
from lens.synth.cards import card_numbers_errors, render_md

STAT = {
    "n": 12,
    "videos": 4,
    "weight": 9.0,
    "median": 480.0,
    "p25": 400.0,
    "p75": 560.0,
    "ci": [430.0, 530.0],
}
EMPTY = {"n": 0, "videos": 0, "weight": 0.0, "median": None, "p25": None, "p75": None, "ci": None}
NUMBERS = {
    "id": "kinetic_word_reveal",
    "events": 9,
    "videos": 4,
    "weight": 6.5,
    "duration_ms": STAT,
    "easing_mix": {"ease_out": 0.7, "ease_in_out": 0.3},
    "change_mix": {"fade": 0.6, "slide_up": 0.4},
    "role_mix": {"headline": 1.0},
    "sfx_label_mix": {},
    "sfx_offset_ms": EMPTY,
    "examples": [{"video": "v1", "event": "e001", "score": 4}],
}
PROV = {
    "tool_version": "t",
    "stage": "a3_pattern_cards",
    "annotator": "claude-code",
    "input_hash": "0" * 64,
    "created_at": "2026-01-01T00:00:00Z",
}


def _card(**over):
    base = {
        "provenance": PROV,
        "id": "kinetic_word_reveal",
        "name": "Words Rise In",
        "summary": "A headline arrives word by word and settles.",
        "when_to_use": ["Title cards"],
        "steps": ["Split the words.", "Bring them in one after another."],
        "build": {"gsap": "from autoAlpha and y with a stagger", "remotion": "a spring per word"},
        "sound": "no typical sound",
        "why_premium": "It reads like speech, not like pasted text.",
        "numbers": NUMBERS,
        "examples": NUMBERS["examples"],
    }
    return PatternCard.model_validate({**base, **over})


def _root(tmp_path):
    stats = tmp_path / "corpus" / "stats"
    stats.mkdir(parents=True)
    w = {"tier": {"reference": 1.0}, "score_from": "overall", "score_missing": 0.6, "quality": True}
    patterns = {"provenance": PROV | {"stage": "s9_synth", "annotator": "code"}, "weighting": w}
    (stats / "patterns.json").write_text(json.dumps(patterns | {"patterns": [NUMBERS], "other_events": 0}))
    return tmp_path


def test_numbers_must_be_verbatim(tmp_path):
    root = _root(tmp_path)
    assert card_numbers_errors(root, _card()) == []
    changed = {**NUMBERS, "duration_ms": {**STAT, "median": 300.0}}
    assert "numbers differ" in card_numbers_errors(root, _card(numbers=changed))[0]
    stranger = [{"video": "v9", "event": "e002", "score": 3}]
    assert "not one of" in card_numbers_errors(root, _card(examples=stranger))[0]
    unknown = {**NUMBERS, "id": "nope"}
    assert card_numbers_errors(root, _card(id="nope", numbers=unknown))


def test_markdown_shows_the_measured_numbers():
    md = render_md(_card())
    assert md.startswith("# Words Rise In")
    assert "median 480 ms, 90% interval 430 to 530 (n=12, 4 videos)" in md
    assert "ease out 70%" in md and "not measured" in md
    assert "`v1` e001 (video score 4/5)" in md
