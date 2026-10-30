"""Measure a raw presenter take for the DaVinci Resolve fix (skill resolve-fix-take). Code measures; the
Resolve run-scripts in .claude/skills/resolve-fix-take/resolve/ apply.

    uv run python scripts/resolve_take.py inspect <take.mov>          # mode, loudness, constants for setup.py
    uv run python scripts/resolve_take.py cdl <frame.png|take.mov> [--at 10]  # SetCDL dict (ungraded frame)
    uv run python scripts/resolve_take.py lut <name>               # skin LUT -> Resolve LUT/MCP/<name>.cube
    uv run python scripts/resolve_take.py check <graded.mov|frame.png> [--at 10,40]  # pass/fail vs config

Targets live in config/lens.yaml (create.footage.resolve; loudness: targets.loudness.<destination>).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from create.footage import resolve_fix as rf
from create.footage.media import loudness
from lens.config import load_config

RESOLVE_LUT_DIR = Path("/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/MCP")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def frames(path: Path, at: str | None) -> list[tuple[str, np.ndarray]]:
    if path.suffix.lower() in IMAGE_SUFFIXES:
        return [(path.name, rf.load_frame(path))]
    times = [float(t) for t in (at or "10").split(",")]
    return [(f"{path.name}@{t:g}s", rf.load_frame(path, t)) for t in times]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_inspect = sub.add_parser("inspect")
    p_inspect.add_argument("video", type=Path)
    p_inspect.add_argument("--destination", default="tiktok")  # presenter takes are TikToks
    p_cdl = sub.add_parser("cdl")
    p_cdl.add_argument("source", type=Path)
    p_cdl.add_argument("--at", default=None)
    p_lut = sub.add_parser("lut")
    p_lut.add_argument("name")
    p_check = sub.add_parser("check")
    p_check.add_argument("source", type=Path)
    p_check.add_argument("--at", default=None)
    args = ap.parse_args()

    cfg = load_config()
    res = cfg.create.footage.resolve
    if args.cmd == "inspect":
        dest = args.destination
        target = cfg.targets.loudness[dest]
        tags = rf.take_tags(args.video)
        level = loudness(args.video)
        mode = rf.colour_mode(tags)
        print(json.dumps({"colour_mode": mode, "tags": {k: v for k, v in tags.items() if "apple" in k},
                          "loudness": level}, indent=2))  # fmt: skip
        if mode == "baked_rec709":
            print("\nBaked Rec.709 (DJI Mimo): NO log transform. Grade in DaVinci YRGB, Rec.709 Gamma 2.4.")
        print("\n# constants for resolve/setup.py")
        print(f'SOURCE = "{args.video.resolve()}"')
        print(f'MODE = "{mode}"')
        print(f"TARGET_LUFS = {(target.min_lufs + target.max_lufs) / 2:g}")
        print(f"MAX_TRUE_PEAK = {cfg.create.footage.voice.true_peak_db:g}  # limiter trim aims here")
    elif args.cmd == "cdl":
        name, rgb = frames(args.source, args.at)[0]
        print(f"# from {name} (an UNGRADED pass-through frame)")
        print(json.dumps(rf.cdl_strings(rf.suggest_cdl(rgb, res))))
    elif args.cmd == "lut":
        out = rf.write_cube(RESOLVE_LUT_DIR / f"{args.name}.cube", rf.skin_lut(res), args.name)
        print(out)
    else:
        ok = True
        for name, rgb in frames(args.source, args.at):
            rep = rf.frame_report(rgb, res)
            ok = ok and bool(rep["skin_ok"])
            print(name, json.dumps({k: round(v, 3) if isinstance(v, float) else v for k, v in rep.items()}))
        if args.source.suffix.lower() not in IMAGE_SUFFIXES:
            print("loudness", json.dumps(loudness(args.source)))
        print(
            "skin within target" if ok else f"skin OFF target (hue {res.skin_hue}, chroma {res.skin_chroma})"
        )


if __name__ == "__main__":
    main()
