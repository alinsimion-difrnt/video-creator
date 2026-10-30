"""scripts/study_youtube_fetch.py: reading yt-dlp results (no network)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("syf", ROOT / "scripts" / "study_youtube_fetch.py")
assert _spec and _spec.loader
syf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(syf)


def test_entries_of_video_playlist_and_nested_channel() -> None:
    assert [e["id"] for e in syf.entries_of({"id": "abc", "title": "v"})] == ["abc"]
    pl = {"_type": "playlist", "entries": [{"id": "a"}, None, {"id": "b"}]}
    assert [e["id"] for e in syf.entries_of(pl)] == ["a", "b"]
    ch = {"_type": "playlist", "entries": [{"_type": "playlist", "entries": [{"id": "s1"}, {"id": "s2"}]}]}
    assert [e["id"] for e in syf.entries_of(ch)] == ["s1", "s2"]
    assert syf.entries_of({}) == []


def test_plan_is_valid_and_tracks_are_known() -> None:
    import yaml

    plan = yaml.safe_load((ROOT / "studies" / "youtube-fetch.yaml").read_text())
    for s in plan["sources"]:
        assert s["track"] in syf.TRACK_DIR
        assert s.get("url") or s.get("search")
        assert s["subject"] == s["subject"].lower()
