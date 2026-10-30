"""F5 framing: where to crop each edited segment, for the full frame and for the corner bubble.

Faces come from OpenCV YuNet (MIT; config `create.footage.reframe`) on the masters at `sample_fps`. Each
segment gets one steady crop at its median face, eyes on `eye_line` (no in-shot camera motion, so nothing
jitters), and consecutive jump cuts within a take alternate a `punch_in` zoom to hide the jump. Without a
face the crop is centred. The bubble crop is a square `pip_face_scale` face-widths across. A shot Robert set
on the edit page (projects/<p>/edits.yaml) takes his zoom and shift exactly instead.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from create.footage.edits import load_edits
from lens import __version__
from lens.hashing import cache_key
from lens.schemas.common import Annotator, Provenance
from lens.schemas.config import FootagePose, FootageReframe, LensConfig
from lens.schemas.create import Crop, Edl, Footage, Framing, SegmentFraming, ShotEdit

STAGE = "f5_reframe"
EYES_IN_FACE = 0.4  # eyes sit about 40% down a face box


def primary_face(faces: list[list[float]], min_score: float) -> list[float] | None:
    """The largest face above the score (a presenter, not a face on a screen behind them)."""
    good = [f for f in faces if f[-1] >= min_score]
    if not good:
        return None
    best = max(good, key=lambda f: f[2] * f[3])
    return [float(v) for v in best[:4]]


def median_face(track: list[list[float] | None]) -> list[float] | None:
    seen = [f for f in track if f is not None]
    if not seen:
        return None
    return [float(statistics.median(f[k] for f in seen)) for k in range(4)]


def nearest_face(track: Track, t: float, n: int = 5) -> list[float] | None:
    """The median of the `n` detections nearest `t`: for a segment with none of its own (shorter than the
    sampling step, or a missed detection), so its crop stays on the face instead of jumping to the centre."""
    seen = sorted(((abs(ts - t), f) for ts, f in track if f is not None), key=lambda x: x[0])
    return median_face([f for _, f in seen[:n]])


def _clamp(v: float, lo: float, hi: float) -> int:
    return round(min(max(v, lo), hi))


def fill_crop(
    src_w: int,
    src_h: int,
    out_w: int,
    out_h: int,
    face: list[float] | None,
    zoom: float,
    eye_line: float,
    shift: tuple[float, float] = (0.0, 0.0),
) -> Crop:
    """The largest crop of the output's aspect (divided by `zoom`), placed on the face, then moved by `shift`
    (shares of the crop's width and height) and kept inside the master."""
    aspect = out_w / out_h
    w, h = (src_h * aspect, float(src_h)) if src_w / src_h > aspect else (float(src_w), src_w / aspect)
    w, h = w / zoom, h / zoom
    if face is None:
        cx, top = src_w / 2, (src_h - h) / 2
    else:
        cx = face[0] + face[2] / 2
        top = face[1] + EYES_IN_FACE * face[3] - eye_line * h
    cx, top = cx + shift[0] * w, top + shift[1] * h
    cw, ch = round(w), round(h)  # round the size first, so x + w never passes the source edge
    x = _clamp(cx - cw / 2, 0, src_w - cw)
    y = _clamp(top, 0, src_h - ch)
    return Crop(x=x, y=y, w=cw, h=ch)


def pip_crop(src_w: int, src_h: int, face: list[float] | None, face_scale: float) -> Crop:
    """A square around the face (or the centre), never larger than the master."""
    side = min(src_w, src_h, (face[2] * face_scale) if face else min(src_w, src_h) * 0.6)
    if face is None:
        cx, cy = src_w / 2, src_h / 2
    else:
        cx, cy = face[0] + face[2] / 2, face[1] + face[3] / 2
    x = _clamp(cx - side / 2, 0, src_w - side)
    y = _clamp(cy - side / 2, 0, src_h - side)
    s = round(side)
    return Crop(x=x, y=y, w=s, h=s)


def ensure_model(root: Path, cfg: FootageReframe | FootagePose) -> Path:
    """A pinned model file (YuNet, BlazePose): downloaded once, checked against its sha256."""
    path = root / cfg.model
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(cfg.model_url, timeout=120) as resp:
            path.write_bytes(resp.read())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != cfg.model_sha256:
        raise RuntimeError(f"{cfg.model}: sha256 {digest} is not the pinned {cfg.model_sha256}")
    return path


def face_track(master: Path, model: Path, cfg: FootageReframe) -> list[tuple[float, list[float] | None]]:
    """(time, primary face) every 1/sample_fps seconds of a master."""
    import cv2

    cap = cv2.VideoCapture(str(master))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, round(fps / cfg.sample_fps))
    det = cv2.FaceDetectorYN.create(str(model), "", (320, 320), cfg.min_score, 0.3, 5000)
    out: list[tuple[float, list[float] | None]] = []
    i = 0
    while True:
        ok = cap.grab()
        if not ok:
            break
        if i % step == 0:
            _, frame = cap.retrieve()
            h, w = frame.shape[:2]
            det.setInputSize((w, h))
            _, faces = det.detect(frame)
            found = [] if faces is None else [[float(v) for v in f[:4]] + [float(f[-1])] for f in faces]
            out.append((round(i / fps, 3), primary_face(found, cfg.min_score)))
        i += 1
    cap.release()
    return out


Track = list[tuple[float, list[float] | None]]


def plan(
    edl: Edl,
    sizes: dict[str, tuple[int, int]],
    tracks: dict[str, Track],
    out_w: int,
    out_h: int,
    cfg: FootageReframe,
    edits: dict[tuple[str, int], ShotEdit] | None = None,
) -> list[SegmentFraming]:
    segments = []
    auto = 1.0
    for k, s in enumerate(edl.segments):
        a, b = s.src_in / edl.fps, s.src_out / edl.fps
        face = median_face([f for t, f in tracks.get(s.take, []) if a <= t < b]) or nearest_face(
            tracks.get(s.take, []), (a + b) / 2
        )
        jump = k > 0 and edl.segments[k - 1].take == s.take
        auto = (cfg.punch_in if auto == 1.0 else 1.0) if jump else 1.0
        edit = (edits or {}).get((s.take, s.src_in))
        zoom, shift = (edit.zoom, (edit.dx, edit.dy)) if edit else (auto, (0.0, 0.0))
        w, h = sizes[s.take]
        segments.append(
            SegmentFraming(
                segment=k,
                take=s.take,
                face=[round(v, 1) for v in face] if face else None,
                full=fill_crop(w, h, out_w, out_h, face, zoom, cfg.eye_line, shift),
                zoom=zoom,
                pip=pip_crop(w, h, face, cfg.pip_face_scale),
            )
        )
    return segments


def run_reframe(root: Path, project: str, cfg: LensConfig, destination: str) -> tuple[Path, Framing]:
    base = root / "projects" / project
    cache = root / "data" / "create" / project / "footage" / "faces"
    footage = Footage.model_validate(json.loads((base / "footage.json").read_text()))
    edl = Edl.model_validate(json.loads((base / "edl.json").read_text()))
    rc = cfg.create.footage.reframe
    frame_name, frame = cfg.create.design.frame_for(destination)
    model = ensure_model(root, rc)
    tracks = {}
    for t in footage.takes:
        path = cache / f"{t.id}-{rc.sample_fps:g}.json"
        if path.exists():
            tracks[t.id] = [(x, f) for x, f in json.loads(path.read_text())]
        else:
            tracks[t.id] = face_track(root / t.master, model, rc)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(tracks[t.id]))
    sizes = {t.id: (t.width, t.height) for t in footage.takes}
    edits = load_edits(base)
    shot_edits = {(e.take, e.src_in): e for e in edits.shots}
    framing = Framing(
        provenance=Provenance(
            tool_version=__version__, stage=STAGE, annotator=Annotator.CODE,
            input_hash=cache_key({"edl": edl.model_dump(mode="json")["segments"], "tracks": tracks,
                                  "cfg": rc.model_dump(), "frame": frame_name,
                                  "shots": [e.model_dump() for e in edits.shots]}),
            created_at=datetime.now(UTC),
        ),
        project=project, frame=frame_name, width=frame.width, height=frame.height,
        segments=plan(edl, sizes, tracks, frame.width, frame.height, rc, shot_edits),
    )  # fmt: skip
    path = base / "framing.json"
    path.write_text(framing.model_dump_json(indent=1) + "\n")
    return path, framing
