"""Score lens against a HyperFrames answer key (scripts/hyperframes_answer_key.py) for one of our renders.

    uv run python scripts/eval_answer_key.py --video acme-explainer-v1 \
        --key tests/fixtures/acme-v1/answer-key.json [--root DIR] [--tweens 40] [--out report.md]

Needs the video's S2/S3 outputs under the root (proxy, signals). Reports:
- transitions: each true scene boundary matched to a detected transition (start error, kind);
- SFX: recall/precision of detected candidates against the true SFX clips (onset within a window);
- tweens: S7 measurement of a sample of real GSAP tweens on their true end boxes: start error,
  duration error and whether the nearest GSAP ease is the true one (or the same family/direction).
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import deque
from pathlib import Path

import numpy as np

from lens.config import load_config
from lens.measure import measure_element
from lens.measure.curves import gsap_ease
from lens.measure.fit import EaseFit
from lens.media import iter_frames_rgb
from lens.schemas.video import VideoMeta

SFX_WINDOW = (-0.1, 0.8)  # a detected onset this close after a clip's start is that clip (mp3 lead-in)
TRANSITION_TOL_S = 0.2


def family(ease: str) -> str:
    """power2.out -> power2.out family 'power.out'; back.out(1.4) -> 'back.out'."""
    m = re.match(r"([a-z]+)\d?(?:\.(in|out|inOut))?", ease)
    if not m:
        return ease
    return f"{m.group(1)}.{m.group(2) or 'out'}"


def direction(ease: str) -> str:
    if ease in ("none", "linear"):
        return "linear"
    return "inOut" if ".inOut" in ease else ".in" if ".in" in ease else "out"


def eval_transitions(key: dict, detail: dict, fps: float) -> list[str]:
    found = [(t["start_f"] / fps, t["kind"]) for t in detail["transitions"]]
    lines = [
        "## Transitions",
        "",
        "| into | true start | detected | error ms | kind |",
        "|---|---|---|---|---|",
    ]
    hits = 0
    for tr in key["transitions"]:
        best = min(found, key=lambda f: abs(f[0] - tr["start_s"]), default=None)
        if best and abs(best[0] - tr["start_s"]) <= TRANSITION_TOL_S:
            hits += 1
            err = (best[0] - tr["start_s"]) * 1000
            lines.append(f"| {tr['into']} | {tr['start_s']:.2f} | {best[0]:.2f} | {err:+.0f} | {best[1]} |")
        else:
            lines.append(f"| {tr['into']} | {tr['start_s']:.2f} | missed | | |")
    lines.insert(2, f"{hits}/{len(key['transitions'])} found within {TRANSITION_TOL_S * 1000:.0f} ms.\n")
    return [*lines, ""]


def eval_sfx(key: dict, summary: dict) -> list[str]:
    det = [(s["sync_s"], s["id"], s["label"]) for s in (summary.get("audio") or {}).get("sfx", [])]
    lines = ["## SFX", "", "| true clip | start | detected | onset - start ms |", "|---|---|---|---|"]
    used: set[str] = set()
    for s in key["sfx"]:
        lo, hi = s["start_s"] + SFX_WINDOW[0], s["start_s"] + SFX_WINDOW[1]
        m = next((d for d in det if lo <= d[0] <= hi and d[1] not in used), None)
        if m:
            used.add(m[1])
            lines.append(
                f"| {s['file']} | {s['start_s']:.2f} | {m[1]} {m[2]} | {(m[0] - s['start_s']) * 1000:+.0f} |"
            )
        else:
            lines.append(f"| {s['file']} | {s['start_s']:.2f} | missed | |")
    extra = [d for d in det if d[1] not in used]
    lines.insert(2, f"Recall {len(used)}/{len(key['sfx'])}; {len(extra)} detected candidate(s) match no clip"
                 + (f" ({', '.join(f'{d[1]} {d[2]} @ {d[0]:.2f}' for d in extra)})" if extra else "") + ".\n")  # fmt: skip
    return [*lines, ""]


def pick_tweens(key: dict, n: int, scale: float, frame_h: int, band: float) -> list[dict]:
    """Single-target tweens that move, scale or fade a visible box, at least 0.2 s long."""
    out = []
    for t in key["tweens"]:
        if t["n_targets"] != 1 or t["duration_s"] < 0.2 or t["ease"] in ("set", "custom"):
            continue
        props = set(t["to"]) & {"x", "y", "scale", "opacity", "autoAlpha"}
        if not props or not t["boxes"]:
            continue
        x0, y0, x1, y1 = (v * scale for v in t["boxes"][0])
        if x1 - x0 < 16 or y1 - y0 < 12 or y0 >= frame_h * (1 - band):
            continue
        out.append(t)
    step = max(1, len(out) // n)
    return out[::step][:n]


def isolated(t: dict, key: dict) -> bool:
    """No other moving tween overlaps this one in time (with margins) and on screen."""
    a0, a1 = t["start_s"] - 0.2, t["start_s"] + t["duration_s"] + 0.3
    bx = t["boxes"][0]
    for o in key["tweens"]:
        if o is t or o["duration_s"] <= 0 or not o["boxes"] or o["ease"] in ("set", "custom"):
            continue
        if o["start_s"] > a1 or o["start_s"] + o["duration_s"] < a0:
            continue
        for ob in o["boxes"]:
            if ob[0] < bx[2] and bx[0] < ob[2] and ob[1] < bx[3] and bx[1] < ob[3]:
                return False
    return True


def eval_tweens(key: dict, root: Path, video: str, n: int) -> list[str]:
    cfg = load_config(root / "config" / "lens.yaml")
    meta = VideoMeta.model_validate_json((root / "videos" / video / "meta.json").read_text())
    fps, w, h = meta.proxy.fps, meta.proxy.width, meta.proxy.height
    scale = w / key["frame_size"][0]
    tweens = pick_tweens(key, n, scale, h, cfg.signals.captions.band_fraction)
    pre, post = round(0.2 * fps), round(0.3 * fps)
    jobs = sorted(
        (
            max(0, round(t["start_s"] * fps) - pre),
            min(meta.proxy.frames - 1, round((t["start_s"] + t["duration_s"]) * fps) + post),
            t,
        )
        for t in tweens
    )
    window: deque[tuple[int, np.ndarray]] = deque(maxlen=max(b - a for a, b, _ in jobs) + 2)
    rows: list = []
    k = 0
    res_by: dict = {}
    proxy = root / "data" / "media" / video / "proxy.mp4"
    for f, frame in iter_frames_rgb(proxy, fps, w, h):
        window.append((f, frame.copy()))
        while k < len(jobs) and jobs[k][1] <= f:
            a, b, t = jobs[k]
            k += 1
            frames = [fr for i, fr in window if a <= i <= b]
            box = tuple(round(v * scale) for v in t["boxes"][0])
            box = (max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3]))
            m = cfg.measure.track_margin_px
            search = (
                max(0, box[0] - 3 * m),
                max(0, box[1] - 3 * m),
                min(w, box[2] + 3 * m),
                min(h, box[3] + 3 * m),
            )
            res = measure_element(frames, a, fps, box, search, cfg.measure)  # type: ignore[arg-type]
            p = res.primary
            res_by[id(t)] = res
            rows.append((t, p))
        if k >= len(jobs):
            break
    lines = [
        "## Tweens (S7 on true end boxes)",
        "",
        "| tween | true ease / ms | measured channel | nearest GSAP / ms | start err ms | dur err ms | class |"
        " max curve gap |",
        "|---|---|---|---|---|---|---|---|",
    ]
    exact = fam = dirn = measured = alike = 0
    iso_n = iso_alike = 0
    gaps: list[str] = []
    starts, durs = [], []
    for t, p in rows:
        true = f"{t['ease']} / {t['duration_s'] * 1000:.0f}"
        if p is None:
            lines.append(f"| {t['id']} | {true} | none | | | | |")
            continue
        measured += 1
        jt = res_by[id(t)].timing
        assert jt is not None
        ci = res_by[id(t)].channels.index(p)
        # The shared (joint) timing, seen through the primary channel's time axis.
        g = EaseFit(jt.name, jt.t0 - p.channel.frames_start / fps, jt.duration_s, jt.rmse, jt.amplitudes[ci])
        # The channel's time axis starts at its first frame; the fit's t0 is on that axis.
        start_err = (p.channel.frames_start / fps + g.t0 - t["start_s"]) * 1000
        dur_err = (g.duration_s - t["duration_s"]) * 1000
        starts.append(abs(start_err))
        durs.append(abs(dur_err))
        # Do the true and fitted curves draw the same motion? Max difference over the channel's frames,
        # in pixels of travel for x/y/scale, in percentage points for opacity.
        ch = p.channel
        tt = ch.frames_start / fps + ch.t
        true_p = gsap_ease(t["ease"])(np.clip((tt - t["start_s"]) / t["duration_s"], 0, 1))
        # Compare remaining travel: true (from the key) vs fitted (observed travel x fitted amplitude).
        fit_left = g.amplitude * (
            1 - gsap_ease(g.name)(np.clip((ch.t - g.t0) / max(g.duration_s, 1e-6), 0, 1))
        )
        observed = abs(ch.end_value - ch.start_value)
        prop = {"x": "x", "y": "y", "scale": "scale", "opacity": "opacity"}[ch.name]
        true_travel = abs(float(t["from"].get(prop, t["to"].get(prop, 0))) - float(t["to"].get(prop, 0)))
        if ch.name in ("x", "y"):
            true_travel *= scale
        if ch.name == "scale":
            half = max(box[2] - box[0], box[3] - box[1]) / 2
            observed, true_travel = observed * half, true_travel * half
        unit = "pp" if ch.name == "opacity" else "px"
        k = 100 if unit == "pp" else 1
        gap = float(np.max(np.abs(true_travel * (1 - true_p) - observed * fit_left))) * k
        same = gap <= (5.0 if unit == "pp" else 1.0)
        alike += same
        if isolated(t, key):
            iso_n += 1
            iso_alike += same
        gaps.append(f"{gap:.1f} {unit}")
        exact += g.name == t["ease"]
        fam += family(g.name) == family(t["ease"])
        dirn += direction(g.name) == direction(t["ease"])
        lines.append(
            f"| {t['id']} | {true} | {p.channel.name} | {g.name} / {g.duration_s * 1000:.0f} | {start_err:+.0f} |"
            f" {dur_err:+.0f} | {p.fit.cls} | {gaps[-1]}{'' if isolated(t, key) else ' (overlapped)'} |"
        )
    summary = (
        f"{measured}/{len(rows)} measured; {alike} draw the same motion as the truth (within 1 px of travel or "
        f"5 pp of opacity). Nearest GSAP ease exact {exact}, same family {fam}, same direction "
        f"{dirn}. Median |start error| {np.median(starts) if starts else float('nan'):.0f} ms, median |duration "
        f"error| {np.median(durs) if durs else float('nan'):.0f} ms (1 frame = {1000 / fps:.0f} ms). "
        f"Isolated tweens (no other animation overlapping in time and on screen): {iso_alike}/{iso_n} draw "
        f"the same motion.\n"
    )
    lines.insert(2, summary)
    return [*lines, ""]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--key", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=Path(os.environ.get("LENS_ROOT", ".")))
    ap.add_argument("--tweens", type=int, default=40)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    key = json.loads(args.key.read_text())
    meta = VideoMeta.model_validate_json((args.root / "videos" / args.video / "meta.json").read_text())
    detail = json.loads((args.root / "data" / "signals" / args.video / "signals.json").read_text())
    summary = json.loads((args.root / "videos" / args.video / "signals.summary.json").read_text())
    lines = [f"# {args.video} against its answer key", ""]
    lines += eval_transitions(key, detail, meta.proxy.fps)
    lines += eval_sfx(key, summary)
    lines += eval_tweens(key, args.root, args.video, args.tweens)
    text = "\n".join(lines)
    if args.out:
        args.out.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
