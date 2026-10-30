"""Colour and level checks for a raw presenter take fixed in DaVinci Resolve (skill resolve-fix-take).

Code measures, Resolve applies: this module reads the take's tags, measures frames (luma points, white
balance on the wall and shirt, skin in Oklab inside the face box), suggests the CDL for node 1 and writes the
skin-only 3D LUT that moves the camera's skin to the target measured from Robert's own photos. All colour
maths assumes display-referred Rec.709 Gamma 2.4, the timeline the skill grades on.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Literal

import numpy as np

from create.footage.media import display_size, probe, video_stream
from lens.schemas.config import FootageResolve

Box = tuple[float, float, float, float]  # x0, x1, y0, y1 as frame fractions
Cdl = dict[str, list[float]]  # slope, offset, power (per channel), saturation ([s])

GAMMA = 2.4
LUMA = np.array([0.2126, 0.7152, 0.0722])
_M709 = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
_M1 = np.array(
    [[0.8189330101, 0.3618667424, -0.1288597137],
     [0.0329845436, 0.9293118715, 0.0361456387],
     [0.0482003018, 0.2643662691, 0.6338517070]]
)  # fmt: skip
_M2 = np.array(
    [[0.2104542553, 0.7936177850, -0.0040720468],
     [1.9779984951, -2.4285922050, 0.4505937099],
     [0.0259040371, 0.7827717662, -0.8086757660]]
)  # fmt: skip
_TO_LMS = _M1 @ _M709
_FROM_LMS = np.linalg.inv(_TO_LMS)
_M2_INV = np.linalg.inv(_M2)


def colour_mode(tags: dict[str, str]) -> Literal["baked_rec709", "apple_log", "unknown"]:
    """DJI Mimo writes Log takes with the Apple Log -> Rec.709 LUT already baked in (filterBaked=1): those
    are Rec.709 and must not get a log transform. Anything else naming Apple Log is real log."""
    if tags.get("com.apple.quicktime.filterBaked") == "1":
        return "baked_rec709"
    if any("applelog" in v.lower().replace(" ", "") for v in tags.values()):
        return "apple_log"
    return "unknown"


def take_tags(path: Path) -> dict[str, str]:
    tags = probe(path).get("format", {}).get("tags", {})
    return {str(k): str(v) for k, v in tags.items()}


def load_frame(path: Path, at_s: float | None = None) -> np.ndarray:
    """One frame as float RGB in [0, 1] (H, W, 3). Video is decoded with the BT.709 matrix: ffmpeg's
    default for an untagged matrix is BT.601, which skews skin hue by several degrees."""
    w, h = display_size(video_stream(probe(path)))
    cmd = ["ffmpeg", "-v", "error"]
    if at_s is not None:
        cmd += ["-ss", f"{at_s:.3f}"]
    cmd += ["-i", str(path), "-frames:v", "1",
            "-vf", "scale=in_color_matrix=bt709:in_range=tv:out_range=pc,format=rgb48le",
            "-f", "rawvideo", "-"]  # fmt: skip
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<u2").reshape(h, w, 3).astype(np.float64) / 65535.0


def oklab(rgb: np.ndarray) -> np.ndarray:
    lin = np.clip(rgb, 0.0, None) ** GAMMA
    return np.asarray(np.cbrt(lin @ _TO_LMS.T) @ _M2.T, dtype=np.float64)


def from_oklab(lab: np.ndarray) -> np.ndarray:
    lin = ((lab @ _M2_INV.T) ** 3) @ _FROM_LMS.T
    return np.asarray(np.clip(lin, 0.0, 1.0) ** (1 / GAMMA), dtype=np.float64)


def hue_chroma(lab: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360, np.hypot(lab[..., 1], lab[..., 2])


def crop(rgb: np.ndarray, box: Box) -> np.ndarray:
    h, w = rgb.shape[:2]
    x0, x1, y0, y1 = box
    return rgb[int(y0 * h) : int(y1 * h), int(x0 * w) : int(x1 * w)].reshape(-1, 3)


def _ramp(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return np.clip((x - lo) / (hi - lo), 0.0, 1.0)


def skin_stats(rgb: np.ndarray, box: Box, cfg: FootageResolve | None = None) -> dict[str, float]:
    """Median Oklab L, hue and chroma of the skin pixels inside `box`."""
    lab = oklab(crop(rgb, box))
    hue, chroma = hue_chroma(lab)
    if cfg is None:
        keep = chroma > 0.0
    else:
        m = cfg.skin_mask
        keep = (lab[:, 0] > m.min_l) & (chroma > m.min_chroma) & (hue > m.hue[0]) & (hue < m.hue[1])
    if not keep.any():
        return {"share": 0.0, "L": float("nan"), "hue": float("nan"), "chroma": float("nan")}
    return {
        "share": float(keep.mean()),
        "L": float(np.median(lab[keep, 0])),
        "hue": float(np.median(hue[keep])),
        "chroma": float(np.median(chroma[keep])),
    }


def balance(rgb: np.ndarray, boxes: list[Box]) -> tuple[float, float]:
    """R/G and B/G of the mean of near-white regions (wall, shirt)."""
    mean = np.concatenate([crop(rgb, b) for b in boxes]).mean(0)
    return float(mean[0] / mean[1]), float(mean[2] / mean[1])


def suggest_cdl(rgb: np.ndarray, cfg: FootageResolve) -> Cdl:
    """CDL for node 1 from an ungraded (pass-through) frame: the 1st/99th luma percentiles go to
    cfg.black/cfg.white and the wall and shirt to cfg.white_rg/white_bg after cfg.saturation."""
    y = rgb @ LUMA
    lo, hi = np.percentile(y, [1, 99])
    gain = (cfg.white - cfg.black) / (hi - lo)
    lift = cfg.black - lo * gain
    graded = rgb * gain + lift
    rg, bg = balance(graded, [cfg.regions["wall"], cfg.regions["shirt"]])
    # saturation scales a near-white's distance from neutral; aim before it so the target holds after it
    want_rg = 1 + (cfg.white_rg - 1) / cfg.saturation
    want_bg = 1 + (cfg.white_bg - 1) / cfg.saturation
    mul = [want_rg / rg, 1.0, want_bg / bg]
    return {
        "slope": [round(gain * m, 4) for m in mul],
        "offset": [round(lift * m, 4) for m in mul],
        "power": [1.0, 1.0, 1.0],
        "saturation": [cfg.saturation],
    }


def apply_cdl(rgb: np.ndarray, cdl: Cdl) -> np.ndarray:
    """ASC CDL as Resolve applies it on node 1 (preview and tests only)."""
    out = np.clip(rgb * np.array(cdl["slope"]) + np.array(cdl["offset"]), 0.0, 1.0) ** np.array(cdl["power"])
    y = (out @ LUMA)[..., None]
    return np.asarray(np.clip(y + cdl["saturation"][0] * (out - y), 0.0, 1.0), dtype=np.float64)


def cdl_strings(cdl: Cdl) -> dict[str, str]:
    """The dict TimelineItem.SetCDL takes (node 1)."""

    def fmt(v: list[float]) -> str:
        return " ".join(f"{x:g}" for x in v)

    return {"NodeIndex": "1", "Slope": fmt(cdl["slope"]), "Offset": fmt(cdl["offset"]),
            "Power": fmt(cdl["power"]), "Saturation": fmt(cdl["saturation"])}  # fmt: skip


def skin_transform(rgb: np.ndarray, cfg: FootageResolve) -> np.ndarray:
    """Skin-only correction in Oklab: inside the hue window, pull hue toward cfg.skin_hue_to, scale chroma by
    cfg.skin_chroma_mul and lift L, with a raised-cosine weight; near-neutrals, saturated reds (logo) and
    deep shadows are left alone."""
    lab = oklab(rgb)
    hue, chroma = hue_chroma(lab)
    centre, half = cfg.skin_window
    dist = np.abs((hue - centre + 180) % 360 - 180)
    w = np.where(dist < half, 0.5 * (1 + np.cos(np.pi * dist / half)), 0.0)
    w = w * _ramp(chroma, *cfg.skin_neutral) * (1 - _ramp(chroma, *cfg.skin_saturated))
    w = w * _ramp(lab[..., 0], *cfg.skin_shadow)
    new_hue = hue + cfg.skin_hue_pull * w * ((cfg.skin_hue_to - hue + 180) % 360 - 180)
    new_chroma = chroma * (1 - (1 - cfg.skin_chroma_mul) * w)
    new = np.stack(
        [lab[..., 0] + cfg.skin_lift * w,
         new_chroma * np.cos(np.radians(new_hue)),
         new_chroma * np.sin(np.radians(new_hue))], axis=-1,
    )  # fmt: skip
    return np.where((w > 0)[..., None], from_oklab(new), rgb)


def skin_lut(cfg: FootageResolve) -> np.ndarray:
    """The skin transform sampled on a cfg.lut_size^3 lattice, in .cube order (red varies fastest)."""
    axis = np.linspace(0.0, 1.0, cfg.lut_size)
    b, g, r = np.meshgrid(axis, axis, axis, indexing="ij")
    grid = np.stack([r, g, b], axis=-1).reshape(-1, 3)
    return skin_transform(grid, cfg)


def write_cube(path: Path, lut: np.ndarray, title: str) -> Path:
    n = round(len(lut) ** (1 / 3))
    lines = [f'TITLE "{title}"', f"LUT_3D_SIZE {n}", "DOMAIN_MIN 0 0 0", "DOMAIN_MAX 1 1 1"]
    lines += [f"{r:.6f} {g:.6f} {b:.6f}" for r, g, b in lut]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def frame_report(rgb: np.ndarray, cfg: FootageResolve) -> dict[str, float | bool]:
    """Everything the skill checks on a graded frame, with pass flags against cfg."""
    y = rgb @ LUMA
    p1, p99 = np.percentile(y, [1, 99])
    rg, bg = balance(rgb, [cfg.regions["wall"], cfg.regions["shirt"]])
    skin = skin_stats(rgb, cfg.regions["face"], cfg)
    return {
        "luma_p1": float(p1),
        "luma_p99": float(p99),
        "clipped_pct": float((rgb.max(-1) >= 0.995).mean() * 100),
        "white_rg": rg,
        "white_bg": bg,
        "skin_share": skin["share"],
        "skin_L": skin["L"],
        "skin_hue": skin["hue"],
        "skin_chroma": skin["chroma"],
        "skin_ok": bool(
            abs(skin["hue"] - cfg.skin_hue) <= cfg.skin_hue_tol
            and abs(skin["chroma"] - cfg.skin_chroma) <= cfg.skin_chroma_tol
        ),
    }
