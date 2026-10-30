"""S1 ingest: fetch each ready source into data/media/<id>/original.<ext>.

Cloud fetchers: https, r2://inbox/, file://. YouTube/X/LinkedIn are fetched locally with
scripts/local_fetch.sh, which uploads to r2://inbox/ (BUILD_PLAN 6.2).
"""

from __future__ import annotations

import json
import shutil
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

from lens import __version__
from lens.hashing import cache_key, sha256_file
from lens.schemas import SourceEntry
from lens.schemas.sources import Status
from lens.storage import Storage, get_storage, inbox_key

STAGE = "s1_ingest"
VIDEO_EXTS = {"mp4", "mov", "m4v", "webm", "mkv"}


class IngestError(RuntimeError):
    pass


@dataclass(frozen=True)
class IngestResult:
    video: str
    status: str  # "fetched" | "cached" | "skipped" | "waiting"
    path: Path | None = None
    detail: str = ""


def marker_path(root: Path, video: str, stage: str = STAGE) -> Path:
    return root / "data" / "state" / video / f"{stage}.json"


def read_marker(root: Path, video: str, stage: str = STAGE) -> dict[str, object] | None:
    path = marker_path(root, video, stage)
    if not path.exists():
        return None
    data: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return data


def write_marker(root: Path, video: str, stage: str, data: dict[str, object]) -> None:
    path = marker_path(root, video, stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def extension_for(url: str) -> str:
    suffix = PurePosixPath(unquote(urlparse(url).path)).suffix.lower().lstrip(".")
    return suffix if suffix in VIDEO_EXTS else "mp4"


def _file_path(url: str, root: Path) -> Path:
    # file:///abs/path or file://relative/to/repo
    rest = url.removeprefix("file://")
    path = Path(unquote(rest))
    return path if path.is_absolute() else root / path


def _download_https(url: str, dest: Path, timeout: float = 60.0) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": f"explainer-lens/{__version__}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp, dest.open("wb") as fh:
        shutil.copyfileobj(resp, fh, length=1 << 20)


def fetch_to(entry: SourceEntry, dest: Path, root: Path, storage: Storage | None) -> None:
    url = entry.url or ""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    try:
        if url.startswith("file://"):
            src = _file_path(url, root)
            if not src.exists():
                raise IngestError(f"{entry.id}: file not found: {src}")
            shutil.copyfile(src, tmp)
        elif url.startswith("https://"):
            _download_https(url, tmp)
        elif url.startswith("r2://"):
            (storage or get_storage()).download(inbox_key(url), tmp)
        else:
            raise IngestError(f"{entry.id}: unsupported url {url!r}")
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)


def ingest_one(
    entry: SourceEntry, root: Path, storage: Storage | None = None, force: bool = False
) -> IngestResult:
    if entry.status is not Status.READY or not entry.url:
        return IngestResult(entry.id, "skipped", detail="status is draft")
    ext = extension_for(entry.url)
    dest = root / "data" / "media" / entry.id / f"original.{ext}"
    key = cache_key({"stage": STAGE, "url": entry.url, "segment": entry.segment})
    marker = read_marker(root, entry.id)
    if not force and marker and marker.get("cache_key") == key:
        if dest.exists() and sha256_file(dest) == marker.get("sha256"):
            return IngestResult(entry.id, "cached", dest)
        if read_marker(root, entry.id, "s2_normalize"):
            # The original may be gone (lifecycle); normalize already consumed it.
            return IngestResult(entry.id, "cached", None, "original not local; already normalized")
    if entry.url.startswith("r2://"):
        storage = storage or get_storage()
        if storage.size(inbox_key(entry.url)) is None:
            # Not uploaded yet (scripts/fetch_batch.py runs on a local machine): not an error.
            return IngestResult(entry.id, "waiting", detail=f"not in {entry.url} yet")
    fetch_to(entry, dest, root, storage)
    write_marker(
        root,
        entry.id,
        STAGE,
        {
            "cache_key": key,
            "url": entry.url,
            "path": dest.relative_to(root).as_posix(),
            "sha256": sha256_file(dest),
            "bytes": dest.stat().st_size,
            "tool_version": __version__,
            "fetched_at": datetime.now(UTC).isoformat(),
        },
    )
    return IngestResult(entry.id, "fetched", dest)
