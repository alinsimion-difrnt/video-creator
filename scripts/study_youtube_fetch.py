"""YouTube for the studies, on Robert's laptop (YouTube blocks the cloud; studies/youtube-fetch.md).

    uv run python scripts/study_youtube_fetch.py list    # studies/youtube-fetch.yaml resolved into
                                                          # studies/<track>/youtube.yaml (ids, titles)
    uv run python scripts/study_youtube_fetch.py fetch   # download each listed video, upload it to
                                                          # r2://study/<track>/youtube/<id>.mp4 (skips done)
    uv run python scripts/study_youtube_fetch.py fetch --no-upload   # keep them in ~/study-inbox/<track>/

Needs yt-dlp and ffmpeg; uploading needs the R2_* variables (as for scripts/fetch_batch.py). Re-running is
safe. The lists are committed; the videos never are.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lens.storage import get_storage  # noqa: E402

PLAN = ROOT / "studies" / "youtube-fetch.yaml"
TRACK_DIR = {"pixel-art": ROOT / "studies" / "pixel-art", "tiktok": ROOT / "studies" / "tiktok"}


def ytdlp_json(target: str, flat: bool = True) -> dict[str, Any] | None:
    cmd = ["yt-dlp", "--no-warnings", "-J", *(["--flat-playlist"] if flat else []), target]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if out.returncode != 0 or not out.stdout.strip():
        return None
    data: dict[str, Any] = json.loads(out.stdout)
    return data


def entries_of(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Videos in a yt-dlp result: a playlist/channel/search has `entries`, a single video is itself."""
    if data.get("_type") in ("playlist", "multi_video") or "entries" in data:
        out: list[dict[str, Any]] = []
        for e in data.get("entries") or []:
            if e and e.get("_type") == "playlist":  # a channel page nests its tabs
                out.extend(entries_of(e))
            elif e and e.get("id"):
                out.append(e)
        return out
    return [data] if data.get("id") else []


def resolve(src: dict[str, Any], defaults: dict[str, Any]) -> list[dict[str, Any]]:
    take = int(src.get("take", defaults["take"]))
    max_s = float(src.get("max_seconds", defaults["max_seconds"]))
    targets = []
    if src.get("url"):
        targets.append(src["url"])
    if src.get("search"):
        targets.append(f"ytsearch{take * 3}:{src['search']}")
    picked: list[dict[str, Any]] = []
    for i, target in enumerate(targets):
        data = ytdlp_json(target)
        if data is None and i == 0 and src.get("fallback_search"):
            data = ytdlp_json(f"ytsearch{take * 3}:{src['fallback_search']}")
        for e in entries_of(data or {}):
            dur = e.get("duration")
            if dur is not None and float(dur) > max_s:
                continue
            picked.append(
                {
                    "id": e["id"],
                    "url": f"https://www.youtube.com/watch?v={e['id']}",
                    "title": e.get("title"),
                    "channel": e.get("channel") or e.get("uploader"),
                    "duration_s": dur,
                    "views": e.get("view_count"),
                    "subject": src["subject"],
                    "from": target,
                }
            )
            if len(picked) >= take:
                return picked
    return picked


def cmd_list() -> None:
    plan = yaml.safe_load(PLAN.read_text())
    lists: dict[str, list[dict[str, Any]]] = {t: [] for t in TRACK_DIR}
    seen: set[str] = set()
    for src in plan["sources"]:
        got = resolve(src, plan["defaults"])
        fresh = [g for g in got if g["id"] not in seen]
        seen.update(g["id"] for g in fresh)
        lists[src["track"]].extend(fresh)
        print(f"{src['track']:9} {src['subject']:28} {len(fresh)} videos", flush=True)
    for track, items in lists.items():
        out = TRACK_DIR[track] / "youtube.yaml"
        out.parent.mkdir(parents=True, exist_ok=True)
        head = f"# YouTube videos for the {track} study, resolved by scripts/study_youtube_fetch.py list.\n"
        out.write_text(head + yaml.safe_dump(items, sort_keys=False, allow_unicode=True))
        print(f"wrote {out.relative_to(ROOT)} ({len(items)} videos)")


def cmd_fetch(upload: bool, out_root: Path) -> None:
    storage = get_storage() if upload else None
    done, failed = 0, []
    for track, d in TRACK_DIR.items():
        f = d / "youtube.yaml"
        if not f.exists():
            continue
        for item in yaml.safe_load(f.read_text()) or []:
            key = f"study/{track}/youtube/{item['id']}.mp4"
            local = out_root / track / f"{item['id']}.mp4"
            if (storage and storage.size(key) is not None) or (not storage and local.exists()):
                continue
            local.parent.mkdir(parents=True, exist_ok=True)
            print(f"-> {track} {item['subject']} {item['id']}", flush=True)
            r = subprocess.run(
                [
                    "yt-dlp",
                    "--no-warnings",
                    "-f",
                    "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
                    "--merge-output-format",
                    "mp4",
                    "-o",
                    str(local),
                    item["url"],
                ],
                check=False,
            )
            if r.returncode != 0 or not local.exists():
                failed.append(f"{track} {item['id']}")
                continue
            if storage:
                storage.upload(local, key)
                local.unlink()
            done += 1
    print(f"\n{done} fetched" + ("" if storage else f" into {out_root}"))
    if failed:
        print(f"{len(failed)} failed:\n" + "\n".join(f"  {x}" for x in failed))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["list", "fetch"])
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--out", type=Path, default=Path.home() / "study-inbox")
    args = ap.parse_args()
    if shutil.which("yt-dlp") is None:
        sys.exit("install yt-dlp first: brew install yt-dlp (or pipx install yt-dlp)")
    if args.cmd == "list":
        cmd_list()
        return
    upload = not args.no_upload
    if upload and not (os.environ.get("LENS_STORAGE") or os.environ.get("R2_ACCOUNT_ID")):
        sys.exit("R2_* variables not set: export them, or use --no-upload")
    cmd_fetch(upload, args.out)


if __name__ == "__main__":
    main()
