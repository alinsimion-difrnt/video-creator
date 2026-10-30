"""The TikTok study's commands (studies/README.md):

uv run python -m study.tiktok select            # studies/tiktok/sources.yaml from the candidates
uv run python -m study.tiktok fetch             # download the listed videos (study/web/tiktok.cjs)
uv run python -m study.tiktok measure [ids...]  # measure + annotator packet for each downloaded video
uv run python -m study.tiktok validate [files]  # check notes (all of studies/tiktok/notes by default)
uv run python -m study.tiktok status            # what is listed, fetched, measured, noted
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import yaml
from pydantic import ValidationError

from study.tiktok import packets, sources
from study.tiktok.config import MEDIA, ROOT, STUDY, load
from study.tiktok.schemas import TikTokNote

TOL = 0.05


def listed() -> list[str]:
    return [r["id"] for r in yaml.safe_load((STUDY / "sources.yaml").read_text())]


def validate(path: Path) -> list[str]:
    try:
        note = TikTokNote.model_validate_json(path.read_text())
    except ValidationError as e:
        return [f"{path.name}: {err['loc']}: {err['msg']}" for err in e.errors()]
    errs = []
    if note.id != path.stem:
        errs.append(f"{path.name}: id {note.id} does not match the file name")
    try:
        allowed = packets.allowed_times(note.id)
    except FileNotFoundError:
        return [*errs, f"{path.name}: no packet for {note.id} (run measure first)"]
    times = [b.t for b in note.beats] + ([note.cta.t] if note.cta.t is not None else [])
    for t in times:
        if not any(abs(t - a) <= TOL for a in allowed):
            errs.append(f"{path.name}: time {t} is not one of the packet's times")
    return errs


def main(argv: list[str]) -> int:
    cmd, args = (argv[0], argv[1:]) if argv else ("status", [])
    cfg = load()
    if cmd == "select":
        picked = sources.select(sources.load_candidates(), cfg.select, time.time())
        sources.write_sources(picked)
        print(f"wrote studies/tiktok/sources.yaml: {len(picked)} videos")
    elif cmd == "fetch":
        ids = MEDIA / "ids.txt"
        MEDIA.mkdir(parents=True, exist_ok=True)
        ids.write_text("\n".join(listed()))
        return subprocess.call(["node", str(ROOT / "study/web/tiktok.cjs"), "fetch", str(ids), str(MEDIA)])
    elif cmd == "measure":
        from study.tiktok.measure import measure

        for vid in args or listed():
            if not (MEDIA / f"{vid}.mp4").exists():
                continue
            try:
                measure(vid, cfg)
                packets.build(vid, cfg)
                print(vid, "ok", flush=True)
            except Exception as e:  # one broken video must not stop the batch
                print(vid, "error:", e, flush=True)
    elif cmd == "retext":
        from study.tiktok.measure import retext

        for f in sorted((STUDY / "measure").glob("*.json")):
            if (MEDIA / "work" / f.stem / "ocr.json").exists():
                retext(f.stem, cfg)
        print("text numbers recomputed")
    elif cmd == "validate":
        files = [Path(a) for a in args] or sorted((STUDY / "notes").glob("*.json"))
        errs = [e for f in files for e in validate(f)]
        print("\n".join(errs) if errs else f"{len(files)} notes valid")
        return 1 if errs else 0
    elif cmd == "status":
        listed_ids = listed() if (STUDY / "sources.yaml").exists() else []

        def have(d: Path, ext: str) -> int:
            return sum((d / f"{i}{ext}").exists() for i in listed_ids)

        counts = {
            "listed": len(listed_ids),
            "fetched": have(MEDIA, ".mp4"),
            "measured": have(STUDY / "measure", ".json"),
            "noted": have(STUDY / "notes", ".json"),
        }
        print(json.dumps(counts))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
