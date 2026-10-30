"""The G2 review page: every gold item with the frames the annotator saw and its answers, editable.

The page is one self-contained HTML fragment (images inlined, downscaled) for an Artifact with the
`db` capability: each saved review is a document `reviews/<video>~<item>` holding the item's
corrected fields and `status`. `lens gold import` merges an export of that collection into
gold/<id>/gold.yaml. The page holds third-party frames, so it is never committed.
"""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageDraw

from lens.measure.run import element_ids, manual_box_px
from lens.schemas.annotation import A1File, A2File
from lens.schemas.gold import GoldFile
from lens.schemas.taxonomy import Taxonomy

LONG_EDGE = {"keyframe": 640, "filmstrip": 1100, "end": 900}


def _jpeg(img: Image.Image, long_edge: int) -> str:
    img = img.convert("RGB")
    img.thumbnail((long_edge, long_edge), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=68, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _end_frame(path: Path, a2: A2File) -> str:
    """The marked end frame with the annotator's manual boxes drawn on as m<NN>."""
    img = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(img)
    for el, eid in zip(a2.elements, element_ids(a2), strict=True):
        if el.manual_box is not None:
            x0, y0, x1, y1 = manual_box_px(el.manual_box, img.width, img.height)
            draw.rectangle((x0, y0, x1, y1), outline=(255, 214, 0), width=3)
            draw.rectangle((x0, max(0, y0 - 20), x0 + 34, max(20, y0)), fill=(255, 214, 0))
            draw.text((x0 + 4, max(0, y0 - 18)), eid, fill=(0, 0, 0))
    return _jpeg(img, LONG_EDGE["end"])


def _a1(vdir: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for p in sorted([*vdir.glob("a1.json"), *vdir.glob("a1.p*.json")]):
        for s in A1File.model_validate_json(p.read_text("utf-8")).shots:
            out[s.shot] = s
    return out


def page_data(root: Path, golds: list[GoldFile]) -> dict[str, Any]:
    tax = Taxonomy.model_validate(yaml.safe_load((root / "taxonomy" / "v1.yaml").read_text("utf-8")))
    videos = []
    for g in golds:
        vdir = root / "videos" / g.video
        pk = root / "data" / "packets" / g.video
        a1 = _a1(vdir)
        record = json.loads((vdir / "record.json").read_text("utf-8"))
        shots = []
        for s in g.shots:
            ann = a1[s.shot]
            key = pk / "pass1" / "keyframes" / f"shot_{s.shot}.jpg"
            shots.append(
                {
                    **s.model_dump(mode="json"),
                    "key": f"{g.video}~{s.shot}",
                    "image": _jpeg(Image.open(key), LONG_EDGE["keyframe"]) if key.exists() else None,
                    "what": ann.what_happens,
                    "focal": ann.focal_element,
                    "other": {
                        "shot_type": ann.shot_type_other,
                        "composition": ann.composition_other,
                        "transition_in": ann.transition_other,
                    },
                }
            )
        events = []
        for e in g.events:
            a2 = A2File.model_validate_json((vdir / "events" / f"{e.event}.a2.json").read_text("utf-8"))
            cands = json.loads((pk / "events" / e.event / "candidates.json").read_text("utf-8"))
            facts = json.loads((pk / "events" / e.event / "facts.json").read_text("utf-8"))
            notes = {r.id: r.note for r in a2.sfx_review}
            events.append(
                {
                    **e.model_dump(mode="json"),
                    "key": f"{g.video}~{e.event}",
                    "end": _end_frame(pk / "events" / e.event / "end_marked.jpg", a2),
                    "filmstrip": _jpeg(
                        Image.open(pk / "events" / e.event / "filmstrip.jpg"), LONG_EDGE["filmstrip"]
                    ),
                    "candidates": [{"id": b["id"], "text": b.get("text")} for b in cands["boxes"]],
                    "camera": facts["camera"]["move"],
                    "pattern_note": a2.pattern.description,
                    "sfx_notes": notes,
                    "classifier": {x["id"]: x.get("clap_label") or x["label"] for x in facts["sfx"]},
                }
            )
        videos.append(
            {
                "id": g.video,
                "title": f"{record['brand']}: {record['title']}",
                "watch": g.watch_url,
                "shots": shots,
                "events": events,
            }
        )
    return {
        "options": {
            "shot_type": tax.shot_type,
            "composition": tax.composition,
            "transition_in": tax.transition,
            "depth_cues": tax.depth_cue,
            "role": tax.element_role,
            "change_types": tax.change_type,
            "sfx": tax.sfx,
            "pattern": [*tax.patterns, "other"],
        },
        "videos": videos,
    }


def render_page(root: Path, golds: list[GoldFile]) -> str:
    data = json.dumps(page_data(root, golds), separators=(",", ":")).replace("</", "<\\/")
    return TEMPLATE.replace("/*DATA*/null", data)


TEMPLATE = (Path(__file__).with_name("page.html")).read_text("utf-8")
