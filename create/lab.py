"""Reel lab (ADR 0029): a test presenter video from a photo, a script and a plan, to practise props, effects
and motion without filming.

A lab spec (docs/lab/<name>.yaml) names a script, an ElevenLabs voice and a reel plan whose word fields may be
written as words instead of indexes ("fish", or "fish#2" for the second "fish"). `create lab` then builds a
self-contained project under data/lab/<name>/ (never committed):
- the voice from ElevenLabs with-timestamps (cached by text + voice), so captions and every beat sit on real
  word times; a little room before the first word and after the last;
- the presenter plate from the photo (cover-cropped to the frame) with a slow breathing scale, so a still
  does not read as a freeze frame;
- the face from YuNet on the photo (F5 framing), and optionally a jump cut at a word with a punch-in, so props
  are tested across a cut as in real footage;
- timeline, captions, edit and tokens as the presenter pipeline writes them; then `create reel` renders it.
The photo is passed on the command line (stock photos are media: data/ only, credited in the lab log).
"""

from __future__ import annotations

import base64
import itertools
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from create.captions import group_words
from create.voice import elevenlabs, text_hash, words_from_alignment
from lens.config import REPO_ROOT
from lens.schemas.config import LensConfig
from lens.schemas.create import TimedWord, TimelineWord

WORD_KEYS = {"word", "until"}
LIST_KEYS = {"marks", "punches"}


def resolve_words(node: Any, words: list[str]) -> Any:
    """Word fields written as words become indexes: "fish" is its first occurrence, "fish#2" the second.
    Matching ignores case and punctuation. Unknown words raise with the list of what was said."""

    def index(token: Any) -> Any:
        if not isinstance(token, str):
            return token
        name, _, nth = token.partition("#")
        want = _bare(name)
        hits = [i for i, w in enumerate(words) if _bare(w) == want]
        k = int(nth or 1) - 1
        if k >= len(hits):
            raise ValueError(f"lab plan: {token!r} is not in the script ({' '.join(words)})")
        return hits[k]

    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k in WORD_KEYS:
                out[k] = index(v)
            elif k in LIST_KEYS and isinstance(v, list):
                out[k] = [index(x) for x in v]
            else:
                out[k] = resolve_words(v, words)
        return out
    if isinstance(node, list):
        return [resolve_words(x, words) for x in node]
    return node


def _bare(w: str) -> str:
    return re.sub(r"[^\w']", "", w.lower())


def voice(text: str, voice_id: str, cfg: LensConfig, cache: Path) -> tuple[Path, list[TimedWord]]:
    """The script read by ElevenLabs (cached): an mp3 and its words with times."""
    vc = cfg.create.voice.model_copy(update={"voice_id": voice_id})
    key = text_hash(text, vc)
    mp3, js = cache / f"{key}.mp3", cache / f"{key}.json"
    if not js.exists():
        cache.mkdir(parents=True, exist_ok=True)
        body, _ = elevenlabs(text, vc)
        mp3.write_bytes(base64.b64decode(body["audio_base64"]))
        js.write_text(json.dumps(body.get("normalized_alignment") or body["alignment"]))
    return mp3, words_from_alignment(json.loads(js.read_text()))


def face_box(photo: Path, root: Path, cfg: LensConfig) -> list[float] | None:
    """The largest face on the (already cropped) plate image, [x, y, w, h], from YuNet."""
    import cv2

    from create.footage.reframe import ensure_model, primary_face

    rc = cfg.create.footage.reframe
    model = ensure_model(REPO_ROOT, rc)
    img = cv2.imread(str(photo))
    if img is None:
        return None
    h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create(str(model), "", (w, h), rc.min_score, 0.3, 5000)
    _, faces = det.detect(img)
    if faces is None:
        return None
    return primary_face([list(map(float, f)) for f in faces], rc.min_score)


def build(spec_path: Path, photo: Path, cfg: LensConfig, out_root: Path | None = None) -> Path:
    """Write the lab project (data/lab/<name>/) and return its root (a LENS_ROOT-style folder)."""
    lab = cfg.create.lab
    PRE_S, TAIL_S, FPS = lab.pre_s, lab.tail_s, lab.fps
    spec = yaml.safe_load(spec_path.read_text())
    name = spec["name"]
    root = out_root or REPO_ROOT / "data" / "lab" / name
    base = root / "projects" / name
    base.mkdir(parents=True, exist_ok=True)
    data = root / "data" / "create" / name
    frame = cfg.create.design.frames["vertical"]
    w, h = frame.width, frame.height
    if "take" in spec:  # a span of Robert's own take: his video, his voice, Scribe's word times
        return _build_take(spec, cfg, root, base, data, w, h)
    mp3, said = voice(spec["script"], spec["voice"], cfg, REPO_ROOT / "data" / "lab" / "_voice")
    words = [
        TimelineWord(
            i=w.i,
            text=w.text,
            start_s=round(w.start_s + PRE_S, 3),
            end_s=round(w.end_s + PRE_S, 3),
            scene="s01",
        )
        for w in said
    ]
    total = round(words[-1].end_s + TAIL_S, 3)
    n = round(total * FPS)
    # plate: the photo covering the frame, breathing (a 0.6 % scale swell every ~3.7 s), the voice under it
    still = data / "still.png"
    still.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(photo),
            "-vf",
            f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h}",
            str(still),
        ],
        check=True,
    )
    plate = data / "footage" / "edited" / f"{name}-edited.mp4"
    plate.parent.mkdir(parents=True, exist_ok=True)
    # a slow "breathing" zoom so the still plate is not frozen. It must never drop below 1: a smaller frame
    # than the crop left uninitialised (green) rows on the edges for half of every cycle (lab v06)
    zoom = f"({lab.breathe[0]}+{lab.breathe[1]}*sin(2*PI*t/{lab.breathe[2]}))"
    breathe = f"scale=w='2*trunc({w}*{zoom}/2)':h=-2:eval=frame:flags=bicubic,crop={w}:{h}"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-i",
            str(still),
            "-i",
            str(mp3),
            "-filter_complex",
            f"[0:v]{breathe},format=yuv420p[v];[1:a]adelay={int(PRE_S * 1000)}|{int(PRE_S * 1000)},apad[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-frames:v",
            str(n),
            "-t",
            f"{n / FPS:.3f}",
            "-c:v",
            "libx264",
            "-crf",
            "16",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(plate),
        ],
        check=True,
    )
    return _write_project(spec, cfg, root, base, name, words, total, n, still, plate)


def _build_take(
    spec: dict[str, Any], cfg: LensConfig, root: Path, base: Path, data: Path, w: int, h: int
) -> Path:
    """The plate is a span of a project's take (`take: {project, from, to, x}`): the master cut and cropped to
    the vertical frame around `x` (a share of the master's width), with its own sound; the words are the
    take's transcript in that span. No voice is generated (Robert: tests on his footage use his voice)."""
    from lens.schemas.create import Footage, Transcript

    name, tk = spec["name"], spec["take"]
    proj = REPO_ROOT / "projects" / tk["project"]
    footage = Footage.model_validate(json.loads((proj / "footage.json").read_text()))
    take = next(t for t in footage.takes if t.id == tk.get("id", footage.takes[0].id))
    t0, t1 = float(tk["from"]), float(tk["to"])
    said = Transcript.model_validate(json.loads((proj / "transcript.json").read_text())).words
    span = [x for x in said if x.take == take.id and t0 <= x.start_s and x.end_s <= t1]
    words = [
        TimelineWord(
            i=k, text=x.text, start_s=round(x.start_s - t0, 3), end_s=round(x.end_s - t0, 3), scene="s01"
        )
        for k, x in enumerate(span)
    ]
    fps = cfg.create.lab.fps
    n = round((t1 - t0) * fps)
    cw = round(take.height * w / h / 2) * 2  # the vertical crop of the master, at full height
    cx = min(max(float(tk.get("x", 0.5)) * take.width - cw / 2, 0), take.width - cw)
    plate = data / "footage" / "edited" / f"{name}-edited.mp4"
    plate.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-i", str(REPO_ROOT / take.master),
         "-frames:v", str(n), "-t", f"{n / fps:.3f}",
         "-vf", f"crop={cw}:{take.height}:{cx:.0f}:0,scale={w}:{h}:flags=lanczos,format=yuv420p",
         "-c:v", "libx264", "-crf", "16", "-c:a", "aac", "-b:a", "192k", str(plate)],
        check=True,
    )  # fmt: skip
    still = data / "still.png"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(plate), "-frames:v", "1", str(still)], check=True
    )  # fmt: skip
    return _write_project(spec, cfg, root, base, name, words, round(n / fps, 3), n, still, plate)


def _write_project(
    spec: dict[str, Any],
    cfg: LensConfig,
    root: Path,
    base: Path,
    name: str,
    words: list[TimelineWord],
    total: float,
    n: int,
    still: Path,
    plate: Path,
) -> Path:
    """Timeline, captions, edit, framing, footage, tokens and plan of a lab project around its plate."""
    lab = cfg.create.lab
    FPS = lab.fps
    frame = cfg.create.design.frames["vertical"]
    w, h = frame.width, frame.height
    prov = json.loads((REPO_ROOT / "projects" / lab.brand_project / "tokens.json").read_text())["provenance"]
    tl = {
        "provenance": prov,
        "project": name,
        "fps": FPS,
        "total_s": total,
        "words": [x.model_dump() for x in words],
        "scenes": [
            {
                "scene": "s01",
                "start_s": 0,
                "end_s": total,
                "voice_start_s": words[0].start_s,
                "voice_end_s": words[-1].end_s,
            }
        ],
    }
    (base / "timeline.json").write_text(json.dumps(tl))
    groups = group_words(
        [TimedWord(i=x.i, text=x.text, start_s=x.start_s, end_s=x.end_s) for x in words],
        cfg.create.design.captions["vertical"],
        cfg.create.design.caption_function_words.get("en", []),
    )
    (base / "captions.json").write_text(
        json.dumps(
            {
                "provenance": prov,
                "project": name,
                "frame": "vertical",
                "groups": [g.model_dump() for g in groups],
            }
        )
    )
    # the edit: one shot, or a jump cut at `cut_at` with a punch-in on the second shot (as F5 alternates)
    face = face_box(still, REPO_ROOT, cfg)
    cut = None
    if spec.get("cut_at") is not None:
        cut_word = resolve_words({"word": spec["cut_at"]}, [x.text for x in words])["word"]
        cut = round(words[cut_word].start_s * FPS)
    bounds = [0, cut, n] if cut else [0, n]
    segs = [{"take": "lab", "src_in": a, "src_out": b, "rec_in": a} for a, b in itertools.pairwise(bounds)]
    (base / "edl.json").write_text(
        json.dumps(
            {
                "provenance": prov,
                "project": name,
                "fps": FPS,
                "applied": [],
                "duration_frames": n,
                "segments": segs,
            }
        )
    )
    full = {"x": 0, "y": 0, "w": w, "h": h}
    framings = []
    for k in range(len(segs)):
        crop = full
        if k % 2 == 1 and face is not None:  # punch-in: 1/punch of the frame, centred on the face
            cw, ch = round(w / lab.punch), round(h / lab.punch)
            cx, cy = face[0] + face[2] / 2, face[1] + face[3] / 2
            crop = {
                "x": int(min(max(cx - cw / 2, 0), w - cw)),
                "y": int(min(max(cy - ch * 0.4, 0), h - ch)),
                "w": cw,
                "h": ch,
            }
        framings.append(
            {
                "segment": k,
                "take": "lab",
                "face": face,
                "zoom": 1.0 if crop is full else lab.punch,
                "full": crop,
                "pip": {"x": 0, "y": 0, "w": 9, "h": 9},
            }
        )
    (base / "framing.json").write_text(
        json.dumps(
            {
                "provenance": prov,
                "project": name,
                "frame": "vertical",
                "width": w,
                "height": h,
                "segments": framings,
            }
        )
    )
    (base / "footage.json").write_text(
        json.dumps(
            {
                "provenance": prov,
                "project": name,
                "fps": FPS,
                "takes": [
                    {
                        "id": "lab",
                        "raw": "-",
                        "master": str(plate.relative_to(root)),  # the pose reads it (follow, automail)
                        "audio": "-",
                        "width": w,
                        "height": h,
                        "frames": n,
                        "duration_s": n / FPS,
                        "source_fps": "30",
                        "hdr": False,
                    }
                ],
            }
        )
    )
    tokens = json.loads((REPO_ROOT / "projects" / lab.brand_project / "tokens.json").read_text())
    tokens["frame"] = "vertical"
    tokens["captions"] = {
        **tokens["captions"],
        "kind": "karaoke",
        "size_px": 64,
        "max_width_px": 560,
        "background": None,
        "stroke": "ink",
        "stroke_px": 7,
        "uppercase": True,
        "padding_px": [0, 0],
        "text": "surface",
        "active": "accent",
    }
    (base / "tokens.json").write_text(json.dumps(tokens))
    brief = yaml.safe_load((REPO_ROOT / "projects" / lab.brand_project / "brief.yaml").read_text())
    (base / "brief.yaml").write_text(f"brand: {brief['brand']}\nlanguage: en\n")
    plan = resolve_words(spec["plan"], [x.text for x in words])
    (base / "reel.yaml").write_text(yaml.safe_dump(plan, sort_keys=False))
    for asset in spec.get("assets", []):  # e.g. a fish PNG for `art: image`
        (base / "assets").mkdir(exist_ok=True)
        shutil.copy(REPO_ROOT / asset, base / "assets" / Path(asset).name)
    cache = root / "data" / "create" / "_cache"
    cache.mkdir(parents=True, exist_ok=True)
    for f in (REPO_ROOT / "data" / "create" / "_cache").glob("*"):
        if f.is_file() and not (cache / f.name).exists():
            shutil.copy(f, cache / f.name)
    shared = REPO_ROOT / "data" / "create" / "_cache" / "fred3d"  # slow 3D renders: one cache for all runs
    shared.mkdir(parents=True, exist_ok=True)
    if not (cache / "fred3d").exists():
        (cache / "fred3d").symlink_to(shared, target_is_directory=True)
    return root


def words_of(root: Path, name: str) -> list[str]:
    tl = json.loads((root / "projects" / name / "timeline.json").read_text())
    return [w["text"] for w in tl["words"]]


def beats(data: dict[str, Any]) -> list[tuple[str, float, tuple[float, float, float]]]:
    """Every moment worth studying: (label, time, (x, y, size) on the frame) for each prop's entrance, style
    changes, accessories, acts, tags, moves, carry and exit."""
    rooms = data.get("rooms") or []

    def to_frame(t: float, x: float, y: float) -> tuple[float, float, float]:
        r = rooms[0]
        for rr in rooms:
            if rr["t0"] <= t:
                r = rr
        return x * r["k"] + r["tx"], y * r["k"] + r["ty"], r["k"]

    out = []
    for p in data.get("props", []):

        def at(t: float, p: dict[str, Any] = p) -> tuple[float, float]:
            x, y = p["moves"][0]["x"], p["moves"][0]["y"]
            for m in p["moves"]:
                if m["t"] <= t:
                    x, y = m["x"], m["y"]
            return x, y

        items = [("enter", p["t0"])] + [(f"style {s['style']}", s["t"]) for s in p["styles"][1:]]
        items += [(f"add {'+'.join(a['add'])}", a["t"]) for a in p["acc"][1:] if a["add"]]
        items += [(f"do {a['do']}", a["t"]) for a in p["acts"]] + [
            (f"move {m.get('gait') or ''}", m["t"])
            for m in p["moves"][1:]
            if m["d"] > 0 and not m.get("follow")
        ]
        items += [(f"follow {f['by']}", f["t"]) for f in p.get("follows", [])]
        items += [("put down", f["release"]) for f in p.get("follows", []) if "release" in f]
        items += [(f"hold {h['hold']}", h["t"]) for h in p.get("holds", [])]
        items += [("carry", p["carry"]["t"])] if p.get("carry") else []
        items += [(f"exit {p['exit']['kind']}", p["exit"]["t"])]
        for label, t in items:
            x, y = at(t)
            fx, fy, k = to_frame(t, x, y - p["h"] / 2)
            out.append((f"{p['id']}: {label}", t, (fx, fy, max(p["w"], p["h"]) * k * 2.2)))
    return sorted(out, key=lambda b: b[1])


def study(
    video: Path,
    data: dict[str, Any],
    out: Path,
    frames: int = 8,
    step: float = 0.1,
    tile: int = 240,
    scale: float = 1.0,
    per: int = 6,
) -> Path:
    """Motion strips: per beat, `frames` frames `step` s apart from just before it, cropped around the prop,
    one row per beat with its label, `per` rows a page. `scale` is the video's size over the frame's (drafts
    are 0.5)."""
    from PIL import Image, ImageDraw

    rows = []
    tmp = out.parent / ".study"
    tmp.mkdir(parents=True, exist_ok=True)
    for n, (label, t, (cx, cy, size)) in enumerate(beats(data)):
        tiles = []
        for k in range(frames):
            ts = max(0.0, t - step + k * step)
            png = tmp / f"b{n:03d}_{k}.png"
            s = min(size * scale, 1080 * scale)  # never bigger than the video (a large prop on a draft)
            x0 = min(max(0, cx * scale - s / 2), 1080 * scale - s)
            y0 = min(max(0, cy * scale - s / 2), 1920 * scale - s)
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-ss",
                    f"{ts:.3f}",
                    "-i",
                    str(video),
                    "-frames:v",
                    "1",
                    "-vf",
                    f"crop={int(s)}:{int(s)}:{int(x0)}:{int(y0)},scale={tile}:{tile}",
                    str(png),
                ],
                check=False,
            )
            tiles.append(Image.open(png).convert("RGB") if png.exists() else Image.new("RGB", (tile, tile)))
        row = Image.new("RGB", (tile * frames, tile + 22), (30, 30, 30))
        for k, im in enumerate(tiles):
            row.paste(im, (k * tile, 22))
        ImageDraw.Draw(row).text(
            (6, 4), f"{label}  @ {t:.2f}s  (frames {step:g}s apart)", fill=(255, 255, 255)
        )
        rows.append(row)
    for page in range(0, max(1, len(rows)), per):
        chunk = rows[page : page + per] or [Image.new("RGB", (tile, tile))]
        sheet = Image.new("RGB", (tile * frames, sum(r.height for r in chunk)), (0, 0, 0))
        y = 0
        for r in chunk:
            sheet.paste(r, (0, y))
            y += r.height
        sheet.save(out if page == 0 else out.with_name(f"{out.stem}-{page // per + 1}{out.suffix}"))
    shutil.rmtree(tmp, ignore_errors=True)
    return out


def green_edges(video: Path, w: int = 270, h: int = 480) -> list[float]:
    """Times (s) of frames whose edge rows or columns are green: uninitialised YUV pixels from a crop larger
    than its input (lab v06). Frames are read one at a time at a small size."""
    import numpy as np

    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"scale={w}:{h},fps=30", "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE,
    )  # fmt: skip
    assert proc.stdout is not None
    out: list[float] = []
    k = 0
    while buf := proc.stdout.read(w * h * 3):
        if len(buf) < w * h * 3:
            break
        f = np.frombuffer(buf, np.uint8).reshape(h, w, 3).astype(int)
        for edge in (f[0], f[-1], f[:, 0], f[:, -1]):
            if (edge[:, 1] - (edge[:, 0] + edge[:, 2]) / 2).mean() > 25:
                out.append(round(k / 30, 2))
                break
        k += 1
    proc.wait()
    return out
