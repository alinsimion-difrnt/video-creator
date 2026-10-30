"""Seed the variants tournament (Robert, 2026-10-12: "try 10 completely random ideas and variations for this
build, improve each 3 times, then a leaderboard; improve the winner 5 times").

    uv run python scripts/tour_variants.py   # writes projects/fred-and-pixie-tiktok/plans/tour/vNN-*/i0.yaml

Each variant is the r11 base plan with one idea applied. Later rounds (i1..) are edited by hand from what the
preview sheets show; this only writes the starting points. Word indexes are the TikTok timeline's.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

BASE = Path("projects/fred-and-pixie-tiktok/plans/r11.yaml")
OUT = Path("projects/fred-and-pixie-tiktok/plans/tour")
Plan = dict[str, Any]


def _sticker(word: int, until: int, text: str, **kw: Any) -> dict[str, Any]:
    return {
        "word": word,
        "until": until,
        "kind": "sticker",
        "position": "chest",
        "spec": {"text": text, **kw},
    }


def _drop_items(p: Plan, keep: Callable[[dict[str, Any]], bool]) -> None:
    p["items"] = [i for i in p["items"] if keep(i)]


def _prop(p: Plan, pid: str) -> dict[str, Any]:
    return next(x for x in p["props"] if x["id"] == pid)


def _retune_audio(p: Plan, table: dict[int, str]) -> None:
    """Replace the gag sounds on these words with new prompts (the narration and the rest stay)."""
    for a in p["audio"]:
        if a["word"] in table and "prompt" in a:
            a["prompt"] = table[a["word"]]


def doc(p: Plan) -> str:
    p["fx"].insert(0, {"word": 2, "kind": "look", "spec": {"letterbox": 150, "vignette": 0.35, "grain": 0.3}})
    p["grade"] = {"contrast": 1.08, "saturate": 0.95, "brightness": 1.0, "warmth": 0.08}
    p["items"] = [i for i in p["items"] if i["kind"] != "sticker" or "edited" in i["spec"]["text"]]
    p["items"] += [
        _sticker(22, 27, "Homo marketus · the presenter", icon="person"),
        _sticker(76, 80, "Cyprinus fredericus · common carp", icon="eye", tilt=0),
        _sticker(196, 199, "Felis pixius · apex predator", icon="eye", tilt=0, accent=True),
    ]
    p["audio"] += [
        {
            "word": 2,
            "prompt": "soft orchestral nature documentary music, gentle strings and harp, wonder, "
            "instrumental, no drums",
            "duration_s": 30,
            "gain_db": -6,
        },
        {
            "word": 94,
            "prompt": "light curious nature documentary music, pizzicato strings and woodwinds, instrumental",
            "duration_s": 30,
            "gain_db": -6,
        },
        {
            "word": 192,
            "prompt": "tense nature documentary predator music, low strings building",
            "duration_s": 6,
            "gain_db": -2,
        },
    ]
    return "A nature documentary: letterbox, grain, Latin species lower-thirds, an orchestral bed"


def arcade(p: Plan) -> str:
    steps = [
        [101, "100"],
        [105, "250"],
        [115, "500"],
        [126, "750"],
        [133, "FREE!"],
        [139, "1000"],
        [164, "1500"],
        [167, "2000"],
        [182, "???"],
        [196, "BOSS"],
    ]
    p["fx"].append(
        {"word": 49, "until": 204, "kind": "hud", "spec": {"label": "SCORE", "start": "0", "steps": steps}}
    )
    p["items"] = [i for i in p["items"] if i["kind"] != "sticker" or "edited" in i["spec"]["text"]]
    p["items"] += [
        _sticker(49, 52, "LEVEL 1 · THE FISH", icon="play", accent=True),
        _sticker(99, 101, "LEVEL 2 · THE MACHINE", icon="play", accent=True),
    ]
    _retune_audio(
        p,
        {
            101: "8-bit retro game power-up sound",
            105: "8-bit coin pickup sound",
            115: "8-bit retro camera shutter blip",
            133: "8-bit coin pickup jingle",
            139: "8-bit error buzz",
            164: "8-bit retro bark blip",
            167: "8-bit bird chirp blip",
            192: "8-bit boss warning alarm",
            205: "8-bit game over jingle",
        },
    )
    for e in p["fx"]:
        if e["kind"] == "endcard":
            e["spec"]["title"] = "GAME OVER"
            e["spec"]["sub"] = "Pixie wins · insert coin"
    p["audio"].append({"word": 49, "prompt": "8-bit level start jingle", "duration_s": 1.5, "gain_db": 4})
    return "An 8-bit game: a SCORE HUD that counts the gags, level cards, chiptune sounds, GAME OVER"


def noir(p: Plan) -> str:
    p["fx"].insert(0, {"word": 2, "until": 182, "kind": "grade", "spec": {"saturate": 0.0, "contrast": 1.25}})
    p["fx"].insert(
        1, {"word": 2, "until": 205, "kind": "look", "spec": {"grain": 0.7, "flicker": 0.6, "vignette": 0.55}}
    )
    p["items"] = [i for i in p["items"] if i["kind"] != "sticker"]
    p["items"] += [
        _sticker(49, 52, "Chapter I · The Fish", tilt=0),
        _sticker(99, 102, "Chapter II · The Machine", tilt=0),
        _sticker(192, 196, "Chapter III · The Cat", tilt=0, accent=True),
    ]
    p["audio"] += [
        {"word": w, "prompt": "short silent film ragtime piano sting", "duration_s": 1.5, "gain_db": 2}
        for w in (49, 99)
    ]
    p["audio"].append(
        {"word": 192, "prompt": "film noir muted trumpet sting, suspense", "duration_s": 2, "gain_db": 2}
    )
    return "Noir: Robert in black and white, Fred and Pixie in colour, grain and flicker, chapter cards"


def thriller(p: Plan) -> str:
    peeks = [
        (67, 70, [0.04, 0.9], "slide_left"),
        (127, 131, [0.97, 0.62], "slide_right"),
        (166, 169, [0.05, 0.9], "slide_left"),
    ]
    for k, (w, u, at, enter) in enumerate(peeks):
        p["props"].append(
            {
                "id": f"peek{k}",
                "art": "cat",
                "word": w,
                "until": u,
                "at": {"frame": at},
                "size": 0.1,
                "enter": enter,
                "exit": "fade",
                "beats": [{"word": w + 1, "do": "look"}],
            }
        )
        p["audio"].append(
            {
                "word": w,
                "prompt": "low ominous horror sting, a single deep hit",
                "duration_s": 1.5,
                "gain_db": 4,
            }
        )
    p["zooms"].append({"word": 192, "until": 194, "scale": 1.35})
    p["fx"].insert(0, {"word": 183, "until": 205, "kind": "look", "spec": {"vignette": 0.6}})
    p["audio"].append({"word": 188, "prompt": "slow suspense heartbeat, low", "duration_s": 4, "gain_db": 2})
    p["grade"] = {"contrast": 1.1, "saturate": 1.0, "brightness": 0.98, "warmth": 0.0}
    return "A thriller: Pixie is foreshadowed (she peeks in three times, watching), stings, a heartbeat"


def minimal(p: Plan) -> str:
    p["props"] = [x for x in p["props"] if x["id"] not in ("peek", "hop")]
    fred = _prop(p, "fred")
    fred["beats"] = [b for b in fred["beats"] if "gag" not in b or b["gag"] in ("censor", "dog", "bird")]
    _drop_items(p, lambda i: i["kind"] in ("counter", "code") or "edited" in i["spec"].get("text", ""))
    p["audio"] = [a for a in p["audio"] if a["word"] not in (4, 101, 105, 115, 133)]
    p["punches"] = [5, 205]
    p["push"] = 1.02
    p["fx"] = [e for e in p["fx"] if e["kind"] != "flash"]
    return "Minimal: Fred's story, three widgets, few sounds; does less read as premium?"


def meme(p: Plan) -> str:
    booms = [8, 56, 66, 76, 140, 182]
    for w in booms:
        p["audio"].append(
            {"word": w, "prompt": "vine boom bass hit meme sound", "duration_s": 1, "gain_db": 6}
        )
    p["punches"] = sorted(set(p["punches"] + booms))
    p["fx"] += [{"word": 56, "kind": "glitch"}, {"word": 66, "kind": "glitch"}]
    p["items"] += [
        _sticker(41, 43, "💀", tilt=-8),
        _sticker(56, 57, "🤯", tilt=6),
        _sticker(87, 88, "😎", tilt=-4),
        _sticker(196, 198, "🥺", tilt=4),
    ]
    p["zooms"].append({"word": 192, "until": 194, "scale": 1.5})
    p["audio"].append({"word": 192, "prompt": "dramatic dun dun dun sting", "duration_s": 2, "gain_db": 6})
    return "Meme edition: vine booms with punch-ins, glitch hits, emoji reactions, a dramatic zoom"


def anime(p: Plan) -> str:
    p["fx"] += [
        {"word": 67, "until": 69, "kind": "anime", "spec": {"eyes": True, "hair": False}},
        {"word": 194, "until": 197, "kind": "anime", "spec": {"eyes": True, "hair": False}},
    ]
    p["audio"] += [
        {"word": 67, "prompt": "anime sparkle chime, magical", "duration_s": 1.2, "gain_db": 6},
        {"word": 194, "prompt": "kawaii anime sparkle chime", "duration_s": 1.2, "gain_db": 6},
        {"word": 204, "prompt": "anime dramatic impact whoosh", "duration_s": 1.2, "gain_db": 8},
    ]
    p["zooms"].append({"word": 192, "until": 194, "scale": 1.4})
    p["grade"] = {"contrast": 1.08, "saturate": 1.2, "brightness": 1.02, "warmth": 0.02}
    return "Anime: sparkly eyes on 'I like this' and 'cute cat', chimes, a dramatic zoom"


def studio(p: Plan) -> str:
    p["layout"] = [
        {"word": 0, "layout": "full"},
        {"word": 100, "layout": "split"},
        {"word": 158, "layout": "full"},
    ]
    p["product_bg"] = "ink"
    for i in p["items"]:
        if i["kind"] in ("counter", "bucket", "code"):
            i["where"] = "product"
            i.pop("position", None)
    return "Studio: a split screen with big product cards through the tech part"


def sound(p: Plan) -> str:
    p["audio"] += [
        {
            "word": 2,
            "prompt": "upbeat quirky background music, ukulele, glockenspiel and claps, light, instrumental",
            "duration_s": 30,
            "gain_db": -8,
        },
        {
            "word": 85,
            "prompt": "upbeat quirky background music, ukulele, glockenspiel and claps, light, instrumental",
            "duration_s": 30,
            "gain_db": -8,
        },
        {
            "word": 183,
            "prompt": "playful mischievous pizzicato music, instrumental",
            "duration_s": 9,
            "gain_db": -8,
        },
        {"word": 50, "prompt": "a wet fish flopping in a hand", "duration_s": 0.8, "gain_db": 6},
        {"word": 56, "prompt": "a magical sparkle whoosh", "duration_s": 0.8, "gain_db": 6},
        {"word": 65, "prompt": "an 8-bit sparkle transform sound", "duration_s": 0.8, "gain_db": 6},
        {"word": 93, "prompt": "a squelchy fish plop on a carpet", "duration_s": 0.7, "gain_db": 6},
        {"word": 178, "prompt": "a rising whoosh riser", "duration_s": 1.8, "gain_db": 6},
    ]
    return "Sound first: the r11 picture with a music bed, foley for Fred and a riser into space"


VARIANTS: dict[str, Callable[[Plan], str]] = {
    "v01-doc": doc,
    "v02-arcade": arcade,
    "v04-noir": noir,
    "v05-thriller": thriller,
    "v06-minimal": minimal,
    "v07-meme": meme,
    "v08-anime": anime,
    "v09-studio": studio,
    "v10-sound": sound,
}


def main() -> None:
    base = yaml.safe_load(BASE.read_text())
    base.setdefault("zooms", [])
    for name, make in VARIANTS.items():
        p = copy.deepcopy(base)
        idea = make(p)
        d = OUT / name
        d.mkdir(parents=True, exist_ok=True)
        head = f"# {name} i0: {idea}.\n# Seeded by scripts/tour_variants.py from plans/r11.yaml.\n"
        (d / "i0.yaml").write_text(head + yaml.safe_dump(p, sort_keys=False, allow_unicode=True, width=110))
        print(d / "i0.yaml")


if __name__ == "__main__":
    main()
