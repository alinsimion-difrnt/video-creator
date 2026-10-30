"""Batch queue: only ready sources whose media has arrived and whose S3 is not done (or failed)."""

import json
from pathlib import Path

import pytest

from lens.ingest import ingest_one
from lens.schemas import SourceEntry
from lens.storage import LocalStorage, failed_key, queue


def _entry(vid: str, **kw) -> SourceEntry:
    base = {
        "id": vid,
        "url": f"r2://inbox/{vid}.mp4",
        "page_url": "https://www.youtube.com/watch?v=abcdefghijk",
        "brand": "B",
        "title": vid,
        "format": "feature_reel",
        "tier": "reference",
        "why": "test",
    }
    return SourceEntry.model_validate(base | kw)


def _put(storage: LocalStorage, key: str, tmp: Path) -> None:
    f = tmp / "obj"
    f.write_text(json.dumps({}))
    storage.upload(f, key)


def test_queue_picks_arrived_and_unfinished(tmp_path: Path) -> None:
    st = LocalStorage(tmp_path / "bucket")
    entries = [
        _entry("waiting"),  # not uploaded yet
        _entry("arrived"),
        _entry("done"),
        _entry("broken"),
        _entry("ingested"),  # inbox expired, but S1 already has it
        _entry("draft", status="draft"),
        _entry("arrived-2"),
    ]
    for v in ("arrived", "done", "broken", "draft", "arrived-2"):
        _put(st, f"inbox/{v}.mp4", tmp_path)
    _put(st, "state/done/s3_signals.json", tmp_path)
    _put(st, "state/ingested/s1_ingest.json", tmp_path)
    _put(st, failed_key("broken"), tmp_path)

    assert queue(entries, st, limit=10) == ["arrived", "ingested", "arrived-2"]
    assert queue(entries, st, limit=1) == ["arrived"]
    assert queue(entries, st, limit=10, retry_failed=True) == ["arrived", "broken", "ingested", "arrived-2"]


def test_ingest_waits_for_an_inbox_upload(tmp_path: Path) -> None:
    st = LocalStorage(tmp_path / "bucket")
    r = ingest_one(_entry("later"), tmp_path, storage=st)
    assert r.status == "waiting"
    assert not (tmp_path / "data" / "state" / "later").exists()


def test_outputs_round_trip_through_storage(tmp_path: Path) -> None:
    """The data PR is rebuilt from R2: a job pushes its committed outputs, collect pulls them back."""
    from lens.storage import pull_outputs, push_video

    st = LocalStorage(tmp_path / "bucket")
    job = tmp_path / "job"
    for rel in ("videos/v1/meta.json", "videos/v1/signals.summary.json", "packets/v1/manifest.json"):
        (job / rel).parent.mkdir(parents=True, exist_ok=True)
        (job / rel).write_text(json.dumps({"rel": rel}))
    push_video("v1", _entry("v1"), _cfg(), job, st)
    collect = tmp_path / "collect"
    assert pull_outputs("v1", collect, st) == 3
    assert json.loads((collect / "packets/v1/manifest.json").read_text()) == {
        "rel": "packets/v1/manifest.json"
    }
    assert not (collect / "videos/v1/palette.json").exists()  # never produced: skipped, not an error
    # a rerun with same-sized but different content still refreshes the copy in storage
    (job / "videos/v1/meta.json").write_text(json.dumps({"rel": "videos/v1/meta.jsoX"}))
    push_video("v1", _entry("v1"), _cfg(), job, st)
    pull_outputs("v1", collect, st)
    assert "jsoX" in (collect / "videos/v1/meta.json").read_text()


def test_packets_pull_for_annotation(tmp_path: Path) -> None:
    """Annotation runs on a machine without the S5 workspace: the packet comes back from storage whole."""
    from lens.storage import pull_packets, push_video

    st = LocalStorage(tmp_path / "bucket")
    job = tmp_path / "job"
    files = ("pass1/anchors.json", "pass1/sheets/shot_s001_1.jpg", "events/e001/filmstrip.jpg")
    for rel in files:
        (job / "data/packets/v1" / rel).parent.mkdir(parents=True, exist_ok=True)
        (job / "data/packets/v1" / rel).write_text(rel)
    (job / "data/packets/v10/pass1").mkdir(parents=True)
    (job / "data/packets/v10/pass1/anchors.json").write_text("other video")
    push_video("v1", _entry("v1"), _cfg(), job, st)
    push_video("v10", _entry("v10"), _cfg(), job, st)
    here = tmp_path / "annotate"
    assert pull_packets("v1", here, st) == 3  # not v10's files, though its id shares the prefix
    for rel in files:
        assert (here / "data/packets/v1" / rel).read_text() == rel


def test_pull_media_restores_stage_data(tmp_path: Path) -> None:
    from lens.storage import StorageError, pull_media, push_video

    st = LocalStorage(tmp_path / "bucket")
    job = tmp_path / "job"
    for rel in (
        "data/signals/v1/curves.npz",
        "data/evidence/v1/evidence.json",
        "data/evidence/v1/events/e1/a.jpg",
        "data/media/v1/proxy.mp4",
    ):
        (job / rel).parent.mkdir(parents=True, exist_ok=True)
        (job / rel).write_text(rel)
    push_video("v1", _entry("v1"), _cfg(), job, st)
    here = tmp_path / "repack"
    assert pull_media("v1", "evidence", here, st) == 2
    assert pull_media("v1", "signals", here, st) == 1
    assert (here / "data/evidence/v1/events/e1/a.jpg").read_text() == "data/evidence/v1/events/e1/a.jpg"
    assert pull_media("v1", "media", here, st) == 1  # the proxy S7 measures on
    assert (here / "data/media/v1/proxy.mp4").exists()
    with pytest.raises(StorageError):
        pull_media("v1", "frames", here, st)


def _cfg():
    from lens.config import load_config

    return load_config()
