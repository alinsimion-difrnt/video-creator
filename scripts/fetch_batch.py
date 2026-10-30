"""Fetch a batch of corpus videos on your own machine and upload them to r2://inbox/.

Cloud runners are bot-blocked by YouTube/X/LinkedIn, so fetching happens locally (ADR 0006); the cloud
analyses whatever has arrived. Run from the repo root:

    uv run python scripts/fetch_batch.py              # next 10 videos not yet in the inbox
    uv run python scripts/fetch_batch.py --limit 30
    uv run python scripts/fetch_batch.py --no-upload  # only download to ~/lens-inbox (drag into R2 by hand)

Picks ready sources that have a `page_url` and an `r2://inbox/` url. yt-dlp reads each video's length
before downloading and skips anything over `batch.fetch_max_seconds` (config/lens.yaml). Re-running is
safe: videos already in the inbox (or in ~/lens-inbox with --no-upload) are skipped.
Needs yt-dlp (`brew install yt-dlp` or `pipx install yt-dlp`) and ffmpeg; uploading needs the R2_*
variables in your shell (docs/operating-guide.md).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lens.config import load_config  # noqa: E402
from lens.storage import Storage, get_storage, inbox_key  # noqa: E402
from lens.validate import load_sources  # noqa: E402


def probe_seconds(page_url: str) -> float | None:
    out = subprocess.run(
        ["yt-dlp", "--skip-download", "--no-warnings", "-J", page_url], capture_output=True, text=True
    )
    if out.returncode != 0:
        return None
    duration = json.loads(out.stdout).get("duration")
    return float(duration) if duration else None


def download(page_url: str, dest: Path) -> None:
    subprocess.run(
        [
            "yt-dlp",
            "--no-warnings",
            "-f",
            "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
            "--merge-output-format",
            "mp4",
            "-o",
            str(dest),
            page_url,
        ],
        check=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--out", type=Path, default=Path.home() / "lens-inbox")
    ap.add_argument("--no-upload", action="store_true")
    args = ap.parse_args()

    if shutil.which("yt-dlp") is None:
        sys.exit("install yt-dlp first: brew install yt-dlp (or pipx install yt-dlp)")
    upload = not args.no_upload
    if upload and not (os.environ.get("LENS_STORAGE") or os.environ.get("R2_ACCOUNT_ID")):
        sys.exit("R2_* variables not set: export them, or use --no-upload and drag ~/lens-inbox into R2")
    storage: Storage | None = get_storage() if upload else None
    max_s = load_config().batch.fetch_max_seconds
    args.out.mkdir(parents=True, exist_ok=True)

    done: list[str] = []
    too_long: list[str] = []
    failed: list[str] = []
    for e in load_sources(ROOT):
        if len(done) >= args.limit:
            break
        if e.status.value != "ready" or not e.page_url or not (e.url or "").startswith("r2://inbox/"):
            continue
        key = inbox_key(e.url or "")
        local = args.out / Path(key).name
        if (storage and storage.size(key) is not None) or (not storage and local.exists()):
            continue
        seconds = probe_seconds(e.page_url)
        if seconds is None:
            failed.append(f"{e.id}: yt-dlp could not read {e.page_url}")
            continue
        if seconds > max_s:
            too_long.append(f"{e.id}: {seconds:.0f} s")
            continue
        print(f"-> {e.id} ({seconds:.0f} s)", flush=True)
        try:
            download(e.page_url, local)
            if storage:
                storage.upload(local, key)
                local.unlink()
            done.append(e.id)
        except (subprocess.CalledProcessError, OSError) as exc:
            failed.append(f"{e.id}: {exc}")

    print(f"\n{len(done)} fetched" + ("" if storage else f" into {args.out} (drag them into R2 inbox/)"))
    if too_long:
        print(f"{len(too_long)} over {max_s} s (skipped; tell Claude to set them to draft):")
        print("\n".join(f"  {x}" for x in too_long))
    if failed:
        print(f"{len(failed)} failed:")
        print("\n".join(f"  {x}" for x in failed))


if __name__ == "__main__":
    main()
