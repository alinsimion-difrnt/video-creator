"""Move a reel plan's word indexes from one edit of a take to the next (after a re-cut).

    uv run python scripts/plan_remap.py --old-edl old-edl.json --old-timeline old-timeline.json \
        --project <p> --plan plans/r04.yaml --out plans/r05.yaml

Each old index is traced to its word's time on the take (through the old EDL) and found again in the new
timeline (through the new EDL). An index whose word was cut away is reported and mapped to the nearest kept
word after it. The cold open's words (a flash-forward) are matched to the cold open again. Comments and order
are kept: the plan is rewritten textually, only `word:`, `until:`, `marks:` and `punches:` numbers change.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def src_times(timeline: dict[str, Any], edl: dict[str, Any]) -> list[tuple[float, bool]]:
    """(time on the take, in the cold open) for each timeline word."""
    fps = edl["fps"]
    out = []
    for w in timeline["words"]:
        t = w["start_s"]
        for s in edl["segments"]:
            a = s["rec_in"] / fps
            b = a + (s["src_out"] - s["src_in"]) / fps
            if a - 1e-6 <= t < b:
                out.append((round(s["src_in"] / fps + (t - a), 2), bool(s.get("cold_open"))))
                break
        else:
            out.append((-1.0, False))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-edl", required=True)
    ap.add_argument("--old-timeline", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    base = Path("projects") / a.project
    old = src_times(json.loads(Path(a.old_timeline).read_text()), json.loads(Path(a.old_edl).read_text()))
    new_tl = json.loads((base / "timeline.json").read_text())
    new = src_times(new_tl, json.loads((base / "edl.json").read_text()))
    missing: list[int] = []

    def remap(i: int) -> int:
        t, cold = old[i]
        hits = [k for k, (u, c) in enumerate(new) if c == cold and abs(u - t) < 0.02]
        if hits:
            return hits[0]
        missing.append(i)
        later = [k for k, (u, c) in enumerate(new) if c == cold and u > t]
        return later[0] if later else len(new) - 1

    text = Path(a.plan).read_text()
    text = re.sub(r"\b(word|until): (\d+)", lambda m: f"{m.group(1)}: {remap(int(m.group(2)))}", text)
    text = re.sub(
        r"\b(marks|punches): \[([0-9, ]*)\]",
        lambda m: (
            f"{m.group(1)}: ["
            + ", ".join(str(remap(int(x))) for x in m.group(2).split(",") if x.strip())
            + "]"
        ),
        text,
    )
    Path(a.out).write_text(text)
    print(a.out, "cut words:", sorted(set(missing)) or "none")


if __name__ == "__main__":
    main()
