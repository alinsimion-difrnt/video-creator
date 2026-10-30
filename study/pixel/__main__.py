"""The pixel-art study's commands (studies/README.md, track 2):

uv run python -m study.pixel clips      # measure the pixel-art TikTok clips (studies/pixel-art/tiktok.yaml)
uv run python -m study.pixel pick       # re-pick the clips from the tag candidates
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from study.pixel.config import MEDIA, STUDY, load


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    cfg = load()
    if cmd == "clips":
        from study.pixel.video import measure

        for row in yaml.safe_load((STUDY / "tiktok.yaml").read_text()):
            src = MEDIA / "tiktok" / "clips" / f"{row['id']}.mp4"
            if not src.exists():
                continue
            try:
                measure(src, row["id"], cfg, force="--force" in argv)
                print(row["id"], "ok", flush=True)
            except Exception as e:  # one broken clip must not stop the batch
                print(row["id"], "error:", e, flush=True)
    elif cmd == "gifs":
        from study.pixel.gifs import measure_all

        print(" ".join(measure_all(cfg)))
    elif cmd == "validate":
        from pydantic import ValidationError

        from study.pixel.schemas import PixelNote

        files = [Path(a) for a in argv[1:]] or sorted((STUDY / "notes").glob("*.json"))
        errs = []
        for f in files:
            try:
                note = PixelNote.model_validate_json(f.read_text())
                if note.id != f.stem:
                    errs.append(f"{f.name}: id {note.id} does not match the file name")
            except ValidationError as e:
                errs += [f"{f.name}: {err['loc']}: {err['msg']}" for err in e.errors()]
        print("\n".join(errs) if errs else f"{len(files)} notes valid")
        return 1 if errs else 0
    elif cmd == "pick":
        from study.pixel.clips import build

        print(build(), "clips")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
