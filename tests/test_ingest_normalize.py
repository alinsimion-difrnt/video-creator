"""M1 acceptance on synthetic fixtures: ingest + normalize, idempotent reruns, storage policy."""

import json
import shutil
from pathlib import Path

import boto3
import pytest
import yaml
from moto import mock_aws

from lens.config import REPO_ROOT, load_config
from lens.frames import NormalizeError, frame_name, normalize_one
from lens.ingest import ingest_one, read_marker
from lens.schemas import SourcesFile
from lens.storage import LocalStorage, R2Storage, apply_lifecycle, original_key, push_video
from lens.validate import validate_all, validate_file
from tests.fixtures import synth

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


@pytest.fixture(scope="module")
def media(tmp_path_factory) -> dict[str, Path]:
    out = tmp_path_factory.mktemp("synth")
    return {name: make(out / f"{name}.mp4") for name, make in synth.ALL.items()}


def _repo(tmp_path: Path, media: dict[str, Path], entries: list[dict]) -> Path:
    for d in ("config", "taxonomy", "sources"):
        (tmp_path / d).mkdir(parents=True)
    shutil.copy(REPO_ROOT / "config" / "lens.yaml", tmp_path / "config" / "lens.yaml")
    shutil.copy(REPO_ROOT / "taxonomy" / "v1.yaml", tmp_path / "taxonomy" / "v1.yaml")
    (tmp_path / "sources" / "sources.yaml").write_text(yaml.safe_dump(entries))
    return tmp_path


def _entry(vid: str, path: Path, **kw) -> dict:
    return {
        "id": vid,
        "url": f"file://{path}",
        "brand": "Synth",
        "title": vid,
        "format": "feature_reel",
        "tier": "reference",
        "why": "fixture",
        **kw,
    }


def _sources(root: Path):
    return SourcesFile.model_validate(yaml.safe_load((root / "sources" / "sources.yaml").read_text())).root


def test_normalize_cfr_1080p(tmp_path, media):
    root = _repo(tmp_path, media, [_entry("cfr", media["cfr30-1080p"])])
    cfg = load_config(root / "config" / "lens.yaml")
    (entry,) = _sources(root)

    assert ingest_one(entry, root).status == "fetched"
    assert normalize_one(entry, root, cfg).status == "normalized"

    meta = json.loads((root / "videos" / "cfr" / "meta.json").read_text())
    assert meta["original"]["native_fps"] == 30.0 and not meta["original"]["vfr"]
    assert (meta["proxy"]["width"], meta["proxy"]["height"]) == (1280, 720)
    assert meta["proxy"]["frames"] == 120
    assert abs(meta["proxy"]["duration_s"] - 4.0) <= 0.1
    assert meta["audio"] == {"sample_rate": 48000, "channels": 2, "duration_s": pytest.approx(4.0, abs=0.05)}
    base = meta["base_frames"]
    assert (base["fps"], base["width"], base["height"], base["count"]) == (2, 960, 540, 8)
    frames = sorted(p.name for p in (root / "data" / "frames" / "cfr" / "base").iterdir())
    assert frames[0] == "t00000000.jpg" and frames[1] == "t00000500.jpg" and len(frames) == 8
    assert meta["provenance"]["stage"] == "s2_normalize"

    # Validates against the committed schemas.
    assert all(r.ok for r in validate_all(root)), [r for r in validate_all(root) if not r.ok]


def test_window_ends_with_the_picture_when_audio_runs_longer(tmp_path, media):
    root = _repo(tmp_path, media, [_entry("tail", media["audio-outlasts-video"])])
    cfg = load_config(root / "config" / "lens.yaml")
    (entry,) = _sources(root)
    ingest_one(entry, root)
    assert normalize_one(entry, root, cfg).status == "normalized"
    meta = json.loads((root / "videos" / "tail" / "meta.json").read_text())
    assert meta["window"]["end_s"] == pytest.approx(3.0, abs=1 / 30)
    assert meta["proxy"]["frames"] == 90


def test_rerun_is_noop(tmp_path, media):
    root = _repo(tmp_path, media, [_entry("cfr", media["cfr30-1080p"])])
    cfg = load_config(root / "config" / "lens.yaml")
    (entry,) = _sources(root)
    ingest_one(entry, root)
    normalize_one(entry, root, cfg)
    meta_before = (root / "videos" / "cfr" / "meta.json").read_text()
    assert ingest_one(entry, root).status == "cached"
    assert normalize_one(entry, root, cfg).status == "cached"
    assert (root / "videos" / "cfr" / "meta.json").read_text() == meta_before


def test_vfr_source_gets_cfr_proxy_at_native_rate(tmp_path, media):
    root = _repo(tmp_path, media, [_entry("vfr", media["vfr-from30"])])
    cfg = load_config(root / "config" / "lens.yaml")
    (entry,) = _sources(root)
    ingest_one(entry, root)
    normalize_one(entry, root, cfg)
    meta = json.loads((root / "videos" / "vfr" / "meta.json").read_text())
    assert meta["original"]["vfr"] is True
    assert meta["original"]["native_fps"] == 30.0
    assert meta["proxy"]["fps"] == 30.0
    assert meta["audio"] is None and meta["proxy"]["has_audio"] is False


def test_palette_and_segment(tmp_path, media):
    root = _repo(tmp_path, media, [_entry("two", media["two-colour-25"], segment={"start": 0.5, "end": 2.5})])
    cfg = load_config(root / "config" / "lens.yaml")
    (entry,) = _sources(root)
    ingest_one(entry, root)
    normalize_one(entry, root, cfg)
    meta = json.loads((root / "videos" / "two" / "meta.json").read_text())
    assert meta["window"] == {"start_s": 0.5, "end_s": 2.5, "capped": False}
    assert meta["proxy"]["frames"] == 50 and meta["proxy"]["fps"] == 25.0
    pal = json.loads((root / "videos" / "two" / "palette.json").read_text())["video_palette"]
    top = [s["hex"] for s in pal[:2]]
    for expected in synth.TWO_COLOURS:
        assert any(_close(expected, got, 12) for got in top), (expected, top)
    assert abs(pal[0]["share"] - 0.5) < 0.1


def _close(a: str, b: str, tol: int) -> bool:
    ca = [int(a[i : i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i : i + 2], 16) for i in (1, 3, 5)]
    return all(abs(x - y) <= tol for x, y in zip(ca, cb, strict=True))


def test_duplicate_detected(tmp_path, media):
    root = _repo(tmp_path, media, [_entry("a", media["cfr30-1080p"]), _entry("b", media["cfr30-1080p"])])
    cfg = load_config(root / "config" / "lens.yaml")
    a, b = _sources(root)
    for e in (a, b):
        ingest_one(e, root)
        normalize_one(e, root, cfg)
    meta_b = json.loads((root / "videos" / "b" / "meta.json").read_text())
    assert meta_b["possible_duplicates"] == ["a"]


def test_original_changed_is_refused(tmp_path, media):
    root = _repo(tmp_path, media, [_entry("cfr", media["cfr30-1080p"])])
    cfg = load_config(root / "config" / "lens.yaml")
    (entry,) = _sources(root)
    ingest_one(entry, root)
    marker = read_marker(root, "cfr")
    (root / str(marker["path"])).write_bytes(b"tampered")
    with pytest.raises(NormalizeError, match="changed since ingest"):
        normalize_one(entry, root, cfg)


def test_draft_is_skipped(tmp_path, media):
    root = _repo(tmp_path, media, [_entry("d", media["cfr30-1080p"], url=None, status="draft")])
    (entry,) = _sources(root)
    assert ingest_one(entry, root).status == "skipped"


def test_r2_inbox_ingest_via_storage(tmp_path, media):
    store = LocalStorage(tmp_path / "bucket")
    store.upload(media["two-colour-25"], "inbox/clip.mp4")
    root = _repo(
        tmp_path / "repo", media, [{**_entry("r2", media["two-colour-25"]), "url": "r2://inbox/clip.mp4"}]
    )
    (entry,) = _sources(root)
    result = ingest_one(entry, root, storage=store)
    assert result.status == "fetched" and result.path and result.path.name == "original.mp4"


def test_push_keeps_own_and_expires_reference(tmp_path, media):
    root = _repo(
        tmp_path / "repo",
        media,
        [
            _entry("ref", media["two-colour-25"]),
            _entry("own", media["two-colour-25"], tier="own"),
        ],
    )
    cfg = load_config(root / "config" / "lens.yaml")
    store = LocalStorage(tmp_path / "bucket")
    for e in _sources(root):
        ingest_one(e, root)
        # Before normalize, the original must not be uploaded (proxy not yet verified).
        push_video(e.id, e, cfg, root, store)
        assert not list((tmp_path / "bucket").glob("originals/**/*.mp4"))
    for e in _sources(root):
        normalize_one(e, root, cfg)
        push_video(e.id, e, cfg, root, store)
    assert (tmp_path / "bucket" / "originals" / "expiring" / "ref" / "original.mp4").exists()
    assert (tmp_path / "bucket" / "originals" / "keep" / "own" / "original.mp4").exists()
    assert (tmp_path / "bucket" / "media" / "own" / "proxy.mp4").exists()
    assert (tmp_path / "bucket" / "frames" / "own" / "base" / frame_name(0, 2)).exists()
    # Second push uploads nothing new.
    _ref, own = _sources(root)
    assert push_video("own", own, cfg, root, store) == 0


def test_original_key_respects_refetchable(tmp_path, media):
    cfg = load_config()
    root = _repo(tmp_path, media, [_entry("x", media["two-colour-25"], refetchable=False)])
    (entry,) = _sources(root)
    assert original_key(entry, cfg, "mp4") == "originals/keep/x/original.mp4"


@mock_aws
def test_lifecycle_rule_applies_to_bucket():
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="lens")
    cfg = load_config()
    apply_lifecycle(R2Storage(client, "lens"), cfg)
    rules = client.get_bucket_lifecycle_configuration(Bucket="lens")["Rules"]
    expire = next(r for r in rules if r["ID"] == "expire-originals")
    assert expire["Filter"]["Prefix"] == "originals/expiring/"
    assert expire["Expiration"]["Days"] == cfg.originals.lifecycle_days


def test_meta_schema_rejects_garbage(tmp_path):
    (tmp_path / "videos" / "x").mkdir(parents=True)
    (tmp_path / "videos" / "x" / "meta.json").write_text("{}")
    assert not validate_file(tmp_path / "videos" / "x" / "meta.json", tmp_path).ok


def test_fresh_runner_rerun_is_noop_after_pulling_state(tmp_path, media):
    """CI: a new checkout has meta.json (git) but no data/; pulled markers make the rerun a no-op."""
    from lens.storage import pull_state, push_state, state_marker_names

    assert state_marker_names() == [
        "s1_ingest.json",
        "s2_normalize.json",
        "s3_signals.json",
        "s4_evidence.json",
        "s5_packets.json",
    ]
    first = _repo(tmp_path / "run1", media, [_entry("ref", media["two-colour-25"])])
    cfg = load_config(first / "config" / "lens.yaml")
    store = LocalStorage(tmp_path / "bucket")
    (entry,) = _sources(first)
    ingest_one(entry, first)
    normalize_one(entry, first, cfg)
    push_state("ref", first, store)

    second = _repo(tmp_path / "run2", media, [_entry("ref", media["two-colour-25"])])
    shutil.copytree(first / "videos", second / "videos")  # committed outputs
    assert pull_state("ref", second, store) == 2
    assert ingest_one(entry, second).status == "cached"
    assert normalize_one(entry, second, cfg).status == "cached"
    assert not (second / "data" / "media").exists()  # nothing was downloaded or re-encoded
