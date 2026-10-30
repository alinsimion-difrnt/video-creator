"""create cuts --page: the take as text with each proposed cut where it sits, for deciding on a phone."""

import json

from create.footage.cutpage import page, segments
from lens.config import REPO_ROOT
from lens.schemas.create import Cuts, Transcript

PROV = json.loads((REPO_ROOT / "projects/acme-v2/tokens.json").read_text())["provenance"]


def _take() -> tuple[Transcript, Cuts]:
    words = [("Three,", 0.0), ("um", 1.0), ("Hello", 1.5), ("world.", 3.0)]
    tr = Transcript.model_validate({
        "provenance": PROV, "project": "demo", "engine": "elevenlabs", "model": "scribe_v2", "language": "en",
        "words": [{"i": i, "take": "t", "text": w, "kind": "filler" if w == "um" else "word",
                   "start_s": s, "end_s": s + 0.3} for i, (w, s) in enumerate(words)],
    })  # fmt: skip
    cuts = Cuts.model_validate({"provenance": PROV, "project": "demo", "proposals": [
        {"id": "c001", "kind": "count_in", "take": "t", "start_s": 0.0, "end_s": 1.4, "words": [0, 1],
         "reason": "count-in"},
        {"id": "c002", "kind": "silence", "take": "t", "start_s": 1.9, "end_s": 2.9, "reason": "pause"},
    ]})  # fmt: skip
    return tr, cuts


def test_words_and_pauses_in_time_order_name_their_cut():
    items = segments(*_take())
    assert [i["text"] for i in items] == ["Three,", "um", "Hello", "pause 1.0 s", "world."]
    assert [i["cut"] for i in items] == ["c001", "c001", None, "c002", None]


def test_the_page_is_self_contained():
    html = page("demo", *_take())
    assert "{{" not in html and "http" not in html.replace("viewport", "") and "c002" in html
