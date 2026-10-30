"""Object storage for media: Cloudflare R2 (S3 API) in the cloud, a local directory for tests/offline.

Key layout (BUILD_PLAN 6.3, ADR 0003):
    inbox/<file>                              uploads waiting for ingest (r2://inbox/<file>)
    originals/keep/<video>/original.<ext>     own tier or refetchable: false; never expires
    originals/expiring/<video>/original.<ext> deleted by the lifecycle rule after N days
    media/<video>/proxy.mp4 | audio.wav
    frames/<video>/base/<name>.jpg
    signals/<video>/...                       S3 detail: curves, signals.json, stems
    evidence/<video>/... packets/<video>/...  S4 images and S5 packets

Select the backend with LENS_STORAGE=local:<dir>, or set the R2_* variables.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from lens.schemas import LensConfig, SourceEntry
from lens.schemas.sources import Status


class StorageError(RuntimeError):
    pass


class Storage(Protocol):
    def upload(self, local: Path, key: str) -> None: ...
    def download(self, key: str, local: Path) -> None: ...
    def size(self, key: str) -> int | None: ...
    def list(self, prefix: str) -> list[str]: ...


@dataclass
class LocalStorage:
    root: Path

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root.resolve()):
            raise StorageError(f"key escapes storage root: {key}")
        return path

    def upload(self, local: Path, key: str) -> None:
        dest = self._path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local, dest)

    def download(self, key: str, local: Path) -> None:
        src = self._path(key)
        if not src.exists():
            raise StorageError(f"not found: {key}")
        local.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, local)

    def size(self, key: str) -> int | None:
        path = self._path(key)
        return path.stat().st_size if path.exists() else None

    def list(self, prefix: str) -> list[str]:
        base = self.root.resolve()
        return sorted(
            p.relative_to(base).as_posix()
            for p in base.rglob("*")
            if p.is_file() and p.relative_to(base).as_posix().startswith(prefix)
        )


@dataclass
class R2Storage:
    client: Any
    bucket: str

    @classmethod
    def from_env(cls) -> R2Storage:
        import boto3

        names = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET")
        missing = [n for n in names if not os.environ.get(n)]
        if missing:
            raise StorageError(f"R2 is not configured; missing {', '.join(missing)}")
        client = boto3.client(
            "s3",
            endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            region_name="auto",
        )
        return cls(client, os.environ["R2_BUCKET"])

    def upload(self, local: Path, key: str) -> None:
        self.client.upload_file(str(local), self.bucket, key)

    def download(self, key: str, local: Path) -> None:
        local.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.client.download_file(self.bucket, key, str(local))
        except Exception as exc:  # botocore raises ClientError subclasses
            raise StorageError(f"download failed for {key}: {exc}") from exc

    def size(self, key: str) -> int | None:
        try:
            head = self.client.head_object(Bucket=self.bucket, Key=key)
        except Exception:
            return None
        return int(head["ContentLength"])

    def list(self, prefix: str) -> list[str]:
        keys: list[str] = []
        for page in self.client.get_paginator("list_objects_v2").paginate(Bucket=self.bucket, Prefix=prefix):
            keys.extend(str(o["Key"]) for o in page.get("Contents", []))
        return sorted(keys)


def get_storage() -> Storage:
    spec = os.environ.get("LENS_STORAGE", "")
    if spec.startswith("local:"):
        return LocalStorage(Path(spec.removeprefix("local:")))
    return R2Storage.from_env()


def inbox_key(url: str) -> str:
    """`r2://inbox/<file>` → `inbox/<file>`."""
    prefix = "r2://"
    if not url.startswith(prefix + "inbox/"):
        raise StorageError(f"not an r2 inbox url: {url}")
    return url.removeprefix(prefix)


def keeps_original(entry: SourceEntry, cfg: LensConfig) -> bool:
    return entry.tier.value in cfg.originals.keep_tiers or not entry.refetchable


def original_key(entry: SourceEntry, cfg: LensConfig, ext: str) -> str:
    bucket = "keep" if keeps_original(entry, cfg) else "expiring"
    return f"originals/{bucket}/{entry.id}/original.{ext}"


def lifecycle_configuration(cfg: LensConfig) -> dict[str, Any]:
    """R2/S3 lifecycle rules: expire non-kept originals after `originals.lifecycle_days`."""
    return {
        "Rules": [
            {
                "ID": "expire-originals",
                "Status": "Enabled",
                "Filter": {"Prefix": "originals/expiring/"},
                "Expiration": {"Days": cfg.originals.lifecycle_days},
            },
            {
                "ID": "abort-incomplete-uploads",
                "Status": "Enabled",
                "Filter": {"Prefix": ""},
                "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7},
            },
        ]
    }


def apply_lifecycle(storage: R2Storage, cfg: LensConfig) -> None:
    storage.client.put_bucket_lifecycle_configuration(
        Bucket=storage.bucket, LifecycleConfiguration=lifecycle_configuration(cfg)
    )


# Committed per-video outputs, also kept in R2 (outputs/<video>/<repo path>) so the data PR can be built
# from storage instead of from CI artifacts.
OUTPUT_FILES = (
    "videos/{video}/meta.json",
    "videos/{video}/palette.json",
    "videos/{video}/signals.summary.json",
    "packets/{video}/manifest.json",
)


def output_key(video: str, rel: str) -> str:
    return f"outputs/{video}/{rel}"


def pull_outputs(video: str, root: Path, storage: Storage) -> int:
    """Download a video's committed outputs from R2 into the repo layout (missing ones are skipped)."""
    n = 0
    for tpl in OUTPUT_FILES:
        rel = tpl.format(video=video)
        key = output_key(video, rel)
        if storage.size(key) is None:
            continue
        storage.download(key, root / rel)
        n += 1
    return n


MEDIA_KINDS = ("media", "signals", "evidence", "packets")


def pull_media(video: str, kind: str, root: Path, storage: Storage, workers: int = 8) -> int:
    """Download one kind of a video's local data (S2 media, S3 signals, S4 evidence, S5 packets) from
    storage into data/<kind>/<video>/, e.g. to rebuild packets, annotate or measure where the stage did not
    run."""
    if kind not in MEDIA_KINDS:
        raise StorageError(f"unknown kind {kind!r}; one of {', '.join(MEDIA_KINDS)}")
    from concurrent.futures import ThreadPoolExecutor

    prefix = f"{kind}/{video}/"
    keys = storage.list(prefix)
    dest = root / "data" / kind / video
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(lambda k: storage.download(k, dest / k.removeprefix(prefix)), keys))
    return len(keys)


def pull_packets(video: str, root: Path, storage: Storage) -> int:
    """Download a video's S5 packet (images and JSON) into data/packets/<video>/ for annotation."""
    return pull_media(video, "packets", root, storage)


def media_keys(video: str, root: Path) -> list[tuple[Path, str]]:
    """Local derived media of a video and their storage keys."""
    pairs: list[tuple[Path, str]] = []
    media = root / "data" / "media" / video
    for name in ("proxy.mp4", "audio.wav"):
        if (media / name).exists():
            pairs.append((media / name, f"media/{video}/{name}"))
    base = root / "data" / "frames" / video / "base"
    if base.is_dir():
        for frame in sorted(base.glob("*.jpg")):
            pairs.append((frame, f"frames/{video}/base/{frame.name}"))
    for tpl in OUTPUT_FILES:
        rel = tpl.format(video=video)
        if (root / rel).exists():
            pairs.append((root / rel, output_key(video, rel)))
    for kind in ("signals", "evidence", "packets"):
        d = root / "data" / kind / video
        if d.is_dir():
            for f in sorted(p for p in d.rglob("*") if p.is_file()):
                pairs.append((f, f"{kind}/{video}/{f.relative_to(d).as_posix()}"))
    return pairs


def _same_bytes(storage: Storage, key: str, local: Path) -> bool:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        remote = Path(tmp) / "remote"
        storage.download(key, remote)
        return remote.read_bytes() == local.read_bytes()


def push_video(video: str, entry: SourceEntry, cfg: LensConfig, root: Path, storage: Storage) -> int:
    """Upload a normalized video's media. The original is uploaded only once the proxy is verified
    (i.e. the s2 marker exists). Returns the number of objects uploaded (existing same-size ones skipped).
    """
    pairs = media_keys(video, root)
    if (root / "data" / "state" / video / "s2_normalize.json").exists():
        for original in (root / "data" / "media" / video).glob("original.*"):
            pairs.append((original, original_key(entry, cfg, original.suffix.lstrip("."))))
    uploaded = 0
    for local, key in pairs:
        # Media: the same size means the same file. Small outputs can change content without
        # changing size on a rerun, so they are compared byte for byte.
        same_size = storage.size(key) == local.stat().st_size
        if same_size and (not key.startswith("outputs/") or _same_bytes(storage, key, local)):
            continue
        storage.upload(local, key)
        uploaded += 1
    return uploaded


def state_marker_names() -> list[str]:
    """Marker file names declared in the stage registry (data/state/{video}/<name>)."""
    from lens.stages import STAGES

    prefix = "data/state/{video}/"
    return sorted(w.removeprefix(prefix) for s in STAGES for w in s.writes if w.startswith(prefix))


def push_state(video: str, root: Path, storage: Storage) -> int:
    """Upload a video's stage markers so the next CI run knows what is done."""
    n = 0
    for name in state_marker_names():
        local = root / "data" / "state" / video / name
        if local.exists():
            storage.upload(local, f"state/{video}/{name}")
            n += 1
    return n


def pull_state(video: str, root: Path, storage: Storage) -> int:
    """Download a video's stage markers (missing ones are fine: that stage has not run)."""
    n = 0
    for name in state_marker_names():
        key = f"state/{video}/{name}"
        if storage.size(key) is None:
            continue
        storage.download(key, root / "data" / "state" / video / name)
        n += 1
    return n


def failed_key(video: str) -> str:
    """Set when a prepare job fails on a video, so the queue does not retry it every run."""
    return f"failed/{video}.json"


def queue(entries: list[SourceEntry], storage: Storage, limit: int, retry_failed: bool = False) -> list[str]:
    """Ready sources still to analyse whose media is reachable: S3 not done (per the markers in
    storage), and for r2 inbox sources, the upload has arrived (or S1 already consumed it)."""
    out: list[str] = []
    for e in entries:
        if len(out) >= limit:
            break
        if e.status is not Status.READY or not e.url:
            continue
        if storage.size(f"state/{e.id}/s3_signals.json") is not None:
            continue
        if not retry_failed and storage.size(failed_key(e.id)) is not None:
            continue
        if (
            e.url.startswith("r2://")
            and storage.size(inbox_key(e.url)) is None
            and storage.size(f"state/{e.id}/s1_ingest.json") is None
        ):
            continue
        out.append(e.id)
    return out
