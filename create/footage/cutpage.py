"""A phone page for the cut decisions (`create cuts <p> --page`, the human gate between F3 and F4).

The whole take reads as text: every proposed cut is struck through where it sits (a filler, a false start, a
long pause, the count-in) with its reason. Robert taps a cut to keep that part in, and the page shows the
command that records his decisions (`create cuts <p> --approve all --reject ...`), with a copy button, to
send back. It is one self-contained HTML file with no media and no network, so it can be published as an
Artifact.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from lens.schemas.create import Cuts, Transcript

KIT = Path(__file__).resolve().parent.parent / "kit"


def segments(transcript: Transcript, cuts: Cuts) -> list[dict[str, object]]:
    """The take as a list of words and pauses in time order; each removed one names its cut."""
    by_word = {w: c.id for c in cuts.proposals for w in c.words}
    out: list[tuple[float, int, dict[str, object]]] = [
        (w.start_s, 0, {"t": round(w.start_s, 2), "text": w.text, "cut": by_word.get(w.i), "kind": w.kind})
        for w in transcript.words
    ]
    out += [
        (c.start_s, 1, {"t": round(c.start_s, 2), "text": f"pause {c.end_s - c.start_s:.1f} s", "cut": c.id,
                        "kind": "pause"})
        for c in cuts.proposals
        if not c.words  # silences remove no words: shown as a marker where they sit
    ]  # fmt: skip
    return [item for _, _, item in sorted(out, key=lambda e: (e[0], e[1]))]


def page(project: str, transcript: Transcript, cuts: Cuts) -> str:
    takes = sorted({w.take for w in transcript.words})
    dur = sum(max((w.end_s for w in transcript.words if w.take == t), default=0) for t in takes)
    data = {
        "project": project,
        "duration": round(dur, 1),
        "cuts": [{"id": c.id, "kind": c.kind, "s": round(c.end_s - c.start_s, 2), "reason": c.reason}
                 for c in cuts.proposals],
        "items": segments(transcript, cuts),
    }  # fmt: skip
    out = (KIT / "cuts.html").read_text()
    for key, val in {
        "{{PROJECT}}": html.escape(project),
        "{{DATA}}": json.dumps(data, ensure_ascii=False).replace("</", "<\\/"),
    }.items():
        out = out.replace(key, val)
    return out


def run_cut_page(root: Path, project: str, out: Path | None = None) -> Path:
    base = root / "projects" / project
    transcript = Transcript.model_validate(json.loads((base / "transcript.json").read_text()))
    cuts = Cuts.model_validate(json.loads((base / "cuts.json").read_text()))
    target = out or root / "data" / "create" / project / "cuts.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page(project, transcript, cuts))
    return target
