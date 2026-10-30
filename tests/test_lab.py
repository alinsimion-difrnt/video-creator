"""The animation lab (create/lab.py, ADR 0029): plans written in words, and the green-edge scan."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from create.lab import green_edges, resolve_words

WORDS = ["Even", "this", "fish?", "AI.", "This", "fish", "too."]


def test_plan_words_become_indexes_with_occurrences():
    plan = {"props": [{"word": "fish", "until": "fish#2", "beats": [{"word": "AI"}]}], "punches": ["this#2"]}
    out = resolve_words(plan, WORDS)
    assert out["props"][0]["word"] == 2 and out["props"][0]["until"] == 5
    assert out["props"][0]["beats"][0]["word"] == 3 and out["punches"] == [4]
    with pytest.raises(ValueError, match="not in the script"):
        resolve_words({"word": "cat"}, WORDS)


def test_green_edges_finds_uninitialised_rows(tmp_path: Path):
    clean, bad = tmp_path / "clean.mp4", tmp_path / "bad.mp4"
    base = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x806050:s=270x480:d=0.4:r=30"]
    subprocess.run([*base, "-pix_fmt", "yuv420p", str(clean)], check=True)
    box = "drawbox=x=0:y=0:w=iw:h=6:color=0x00ff00:t=fill"
    subprocess.run([*base, "-vf", box, "-pix_fmt", "yuv420p", str(bad)], check=True)
    assert green_edges(clean) == []
    assert len(green_edges(bad)) >= 10
