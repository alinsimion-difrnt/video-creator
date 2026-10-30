"""C8 grade (ADR 0032): the checks code makes on a motion build.

`create grade <project>` bundles projects/<p>/motion/ into data/create/<p>/motion/render/ (GSAP, the brand's
fonts and logos, the SFX library), then:
- HyperFrames check: lint, runtime, layout and WCAG contrast;
- brand: colours outside the tokens (tints of a token over white or the canvas are fine), banned decoration;
- motion: every timeline move against the measured range; the ease mix against the corpus (families,
  overshoot share, overshoot only on small elements); the frame at rest inside a handover window;
- DOM samples on the timeline: text under the frame's minimum size, accent moments per frame, text running
  into text or the logo (each counted only when it lasts `persist_s`);
- render, then lens signals: hard cuts, dead holds, idle stretches past the corpus shot high;
- SFX: names, times and count against the corpus range;
and writes projects/<p>/motion/grade.json plus two review sheets (overview, handovers) next to the render.
`--lint-only` stops after the check (no render); `--snapshot t1,t2` writes frames for the builder's own look.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import tarfile
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

import yaml

from create.bundle import _get, fonts, gsap
from create.direction import film_s
from create.sketches import hyperframes
from lens import __version__
from lens.hashing import cache_key
from lens.schemas.common import Annotator, Provenance
from lens.schemas.config import CreateRender, LensConfig, MotionGradeConfig
from lens.schemas.create import (
    Brief,
    GradeFinding,
    GradeMeasures,
    MotionGrade,
    Timeline,
    TimelineScene,
    Tokens,
)

STAGE = "c8_grade"
NPM = "https://registry.npmjs.org/hyperframes/-/hyperframes-{v}.tgz"
SFX_IN_TARBALL = "package/dist/skills/media-use/audio/assets/sfx/"
HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


def _f(level: str, area: str, msg: str, t: float | None = None) -> GradeFinding:
    return GradeFinding(level=level, area=area, msg=msg, t=None if t is None else round(t, 2))


# --- pure checks -----------------------------------------------------------------------------------------


def _rgb(h: str) -> tuple[int, int, int]:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def is_tint(colour: str, colors: dict[str, str], g: MotionGradeConfig) -> bool:
    """`colour` is a tintable token laid lightly over white or the canvas (DESIGN.md tints)."""
    x = _rgb(colour)
    bases = {"#FFFFFF", colors.get("canvas", "#FFFFFF")}
    for token in (colors[k] for k in g.tint_tokens if k in colors):
        for base in bases:
            t, b = _rgb(token), _rgb(base)
            alphas = [(xi - bi) / (ti - bi) for xi, ti, bi in zip(x, t, b, strict=True) if abs(ti - bi) > 20]
            if (
                not alphas
                or min(alphas) < 0
                or max(alphas) > g.tint_max_alpha
                or max(alphas) - min(alphas) > g.tint_alpha_spread
            ):
                continue
            a = sum(alphas) / len(alphas)
            if all(
                abs(round(bi + (ti - bi) * a) - xi) <= g.tint_tolerance
                for xi, ti, bi in zip(x, t, b, strict=True)
            ):
                return True
    return False


def colour_findings(html: str, colors: dict[str, str], g: MotionGradeConfig) -> list[GradeFinding]:
    allowed = {c.upper() for c in colors.values()} | {"#FFFFFF", "#000000"}
    off = sorted({c.upper() for c in HEX.findall(html)} - allowed)
    off = [c for c in off if not is_tint(c, colors, g)]
    return [_f("fail", "brand", f"colours outside the brand tokens: {', '.join(off)}")] if off else []


def decoration_findings(html: str, g: MotionGradeConfig) -> list[GradeFinding]:
    out = []
    banned = [
        (r"(linear|radial|conic)-gradient\(", "gradient"),
        (r"text-decoration(-line)?\s*:\s*[^;\"']*underline", "underline"),
        (r"backdrop-filter\s*:", "glass (backdrop-filter)"),
    ]
    for pat, name in banned:
        if re.search(pat, html, re.IGNORECASE):
            out.append(
                _f("fail", "brand", f"banned decoration: {name} (DESIGN.md: no gradients, glows, glass)")
            )
    blurs = [float(b) for b in re.findall(r"blur\(\s*([\d.]+)px", html)]
    if any(b >= g.min_blur_px for b in blurs):
        out.append(_f("fail", "brand", f"banned decoration: blur up to {max(blurs):g}px reads as a glow"))
    copy = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", html)
    if "—" in copy:
        out.append(_f("warn", "brand", "em dash in on-screen copy (DESIGN.md)"))
    return out


def duration_findings(html: str, dur: float) -> list[GradeFinding]:
    m = re.search(r'id=["\']main["\'][^>]*data-duration=["\']([\d.]+)["\']', html) or re.search(
        r'data-duration=["\']([\d.]+)["\'][^>]*id=["\']main["\']', html
    )
    if not m:
        return [_f("fail", "timing", "the root #main has no data-duration")]
    if abs(float(m.group(1)) - dur) > 1e-3:
        return [_f("fail", "timing", f"data-duration {m.group(1)} s, but the film is {dur:g} s")]
    return []


def move_findings(tweens: Iterable[dict[str, float]], g: MotionGradeConfig) -> tuple[list[GradeFinding], int]:
    moves = [t for t in tweens if 0 < t["d"] < g.ambient_min_s]
    long = [t for t in moves if t["d"] > g.max_move_s]
    out = []
    if long:
        out.append(
            _f(
                "warn",
                "motion",
                f"{len(long)} of {len(moves)} moves run past {g.max_move_s:g} s: "
                + ", ".join(f"{t['d']:.2f} s at {t['s']:.1f}" for t in long[:8]),
                long[0]["s"],
            )
        )
    return out, len(moves)


def ease_family(ease: str) -> str | None:
    """A GSAP ease name as a corpus easing class (motion-tokens.json `easing`); None when unknown."""
    name = ease.strip().split("(")[0]
    if name in ("none", "linear") or name.startswith("steps"):
        return "linear"
    if name == "custom" or not name:
        return None
    if name.split(".")[0] in ("back", "elastic", "bounce"):
        return "spring_overshoot"
    if name.endswith(".inOut"):
        return "ease_in_out"
    if name.endswith(".in"):
        return "ease_in"
    return "ease_out"  # ".out", and a bare family ("power2") is GSAP's .out


def ease_findings(
    tweens: Iterable[dict[str, Any]], overshoot_share: float, g: MotionGradeConfig
) -> list[GradeFinding]:
    """Ease mix against the corpus: enough families, overshoot within its share and only on small elements."""
    moves = [t for t in tweens if 0 < t["d"] < g.ambient_min_s and ease_family(t.get("e", "")) is not None]
    fams = [ease_family(t["e"]) for t in moves]
    out = []
    used = sorted(set(f for f in fams if f))
    if len(moves) >= g.ease_min_moves and len(used) < g.min_ease_families:
        out.append(
            _f(
                "warn",
                "motion",
                f"{len(moves)} moves use only {len(used)} ease families ({', '.join(used)}); one ease "
                f"everywhere reads flat (at least {g.min_ease_families})",
            )
        )
    over = [t for t, f in zip(moves, fams, strict=True) if f == "spring_overshoot"]
    if moves and len(over) / len(moves) > overshoot_share * g.overshoot_factor:
        out.append(
            _f(
                "warn",
                "motion",
                f"overshoot on {len(over)} of {len(moves)} moves; the corpus overshoots on "
                f"{overshoot_share:.0%}",
                over[0]["s"],
            )
        )
    big = [t for t in over if t.get("a", 0.0) > g.overshoot_max_area]
    if big:
        out.append(
            _f(
                "warn",
                "motion",
                f"overshoot on {len(big)} large elements (up to {max(t['a'] for t in big):.0%} of the frame) "
                "at " + ", ".join(f"{t['s']:.1f}" for t in big[:6]) + " s: overshoot is for small pops "
                "(chips, icons, avatars), never a card, a text block, data or the camera",
                big[0]["s"],
            )
        )
    return out


def seam_findings(
    tweens: Iterable[dict[str, Any]], scenes: Sequence[TimelineScene], dur: float, g: MotionGradeConfig
) -> list[GradeFinding]:
    """The frame at rest inside a handover window: from one scene's last word to `seam_s` after the next
    scene's first word, something must be moving (the outgoing element leaves in motion, the incoming one
    arrives in motion)."""
    moves = [(t["s"], t["s"] + t["d"]) for t in tweens if 0 < t["d"] < g.ambient_min_s]
    out = []
    for prev, sc in pairwise(scenes):
        a, z = prev.voice_end_s, min(dur, sc.voice_start_s + g.seam_s)
        if z <= a:
            continue
        t, rest, at = a, 0.0, a
        for s, e in sorted((s, e) for s, e in moves if e > a and s < z):
            if s - t > rest:
                rest, at = s - t, t
            t = max(t, e)
        if z - t > rest:
            rest, at = z - t, t
        if rest >= g.seam_rest_s - 1e-9:
            out.append(
                _f(
                    "warn",
                    "motion",
                    f"nothing moves for {rest:.2f} s at {at:.2f} s in the handover into {sc.scene}: the "
                    "outgoing element should still be moving and the incoming one arrive in motion",
                    at,
                )
            )
    return out


def hold_findings(
    holds: Sequence[tuple[int, int, bool]],
    transitions: Sequence[tuple[str, int]],
    fps: float,
    dur: float,
    shot_high_s: float,
) -> list[GradeFinding]:
    out = [
        _f("fail", "pacing", f"hard cut at {f / fps:.2f} s", f / fps)
        for kind, f in transitions
        if kind == "hard_cut"
    ]
    out += [
        _f(
            "warn",
            "pacing",
            f"the frame crossfades at {f / fps:.2f} s: a handover should carry one element that changes "
            "shape, not ghost one layout over the next",
            f / fps,
        )
        for kind, f in transitions
        if kind == "crossfade"
    ]
    for a_f, z_f, dead in holds:
        a, z = a_f / fps, z_f / fps
        if dead:
            out.append(
                _f("fail", "pacing", f"dead hold {a:.2f}-{z:.2f} s (an empty region waits for content)", a)
            )
        elif z - a > shot_high_s and z < dur - 0.05:  # the final hold is meant to be still
            out.append(
                _f(
                    "warn",
                    "pacing",
                    f"idle {a:.2f}-{z:.2f} s ({z - a:.1f} s, past the {shot_high_s:.1f} s shot high)",
                    a,
                )
            )
    return out


def sfx_findings(
    cues: Sequence[dict[str, Any]], dur: float, per_min: dict[str, float], library: Path
) -> list[GradeFinding]:
    out = []
    for c in cues:
        if not (library / f"{c['sfx']}.mp3").exists():
            out.append(_f("fail", "sound", f"no SFX file {c['sfx']!r} in the library", c["t"]))
        elif not 0 <= c["t"] < dur:
            out.append(_f("fail", "sound", f"{c['sfx']} at {c['t']:g} s is outside the film", None))
    lo, hi = round(per_min["low"] * dur / 60), round(per_min["high"] * dur / 60)
    if not lo <= len(cues) <= hi:
        out.append(_f("warn", "sound", f"{len(cues)} SFX; the corpus range for {dur:g} s is {lo}-{hi}"))
    return out


def _overlap(a: Sequence[float], b: Sequence[float], px: float) -> bool:
    return min(a[2], b[2]) - max(a[0], b[0]) > px and min(a[3], b[3]) - max(a[1], b[1]) > px


def _runs(times: list[float], step: float) -> list[tuple[float, float]]:
    """Consecutive sample times grouped into (start, length) runs."""
    runs: list[tuple[float, float]] = []
    for t in sorted(times):
        if runs and t - (runs[-1][0] + runs[-1][1]) <= step * 1.01:
            runs[-1] = (runs[-1][0], t - runs[-1][0] + step)
        else:
            runs.append((t, step))
    return runs


def dom_findings(
    samples: Sequence[dict[str, Any]], min_text_px: float, g: MotionGradeConfig
) -> tuple[list[GradeFinding], dict[str, float | None]]:
    """Text size, accent moments and overlaps from timeline samples; each must last `persist_s`."""
    step = g.sample_step_s
    small: dict[str, list[float]] = {}
    small_px: dict[str, float] = {}
    hits: dict[tuple[str, str], list[float]] = {}
    accent_times: list[float] = []
    sizes: dict[str, list[float]] = {}
    for s in samples:
        texts = s["texts"]
        for x in texts:
            sizes.setdefault(x["text"], []).append(x["px"])
            if x["px"] < min_text_px:
                small.setdefault(x["text"], []).append(s["t"])
                small_px[x["text"]] = min(small_px.get(x["text"], 1e9), x["px"])
        for i, a in enumerate(texts):
            for b in texts[i + 1 :]:
                if a.get("group") is not None and a.get("group") == b.get("group"):
                    continue  # pieces of one line of text (a number and its unit, split words)
                if _overlap(a["box"], b["box"], g.overlap_min_px):
                    hits.setdefault((min(a["text"], b["text"]), max(a["text"], b["text"])), []).append(s["t"])
            for logo in s["logos"]:
                if not logo["covered"] and _overlap(a["box"], logo["box"], g.overlap_min_px):
                    hits.setdefault((a["text"], "the logo"), []).append(s["t"])
        if s["accent"] > g.max_accent_moments:
            accent_times.append(s["t"])
    out: list[GradeFinding] = []

    def persisted(ts: list[float]) -> list[tuple[float, float]]:
        return [r for r in _runs(ts, step) if r[1] >= g.persist_s - 1e-9]

    for text, ts in small.items():
        for start, length in persisted(ts)[:1]:
            out.append(
                _f(
                    "fail",
                    "text",
                    f"{text!r} at {small_px[text]:.0f}px for {length:.1f} s (minimum {min_text_px:g}px)",
                    start,
                )
            )
    for (a, b), ts in hits.items():
        for start, length in persisted(ts)[:1]:
            out.append(_f("fail", "overlap", f"{a!r} runs into {b!r} for {length:.1f} s", start))
    if g.logo_at_close and samples:
        close = [s for s in samples if s["t"] >= samples[-1]["t"] - g.persist_s + 1e-9]
        if not all(any(not lg["covered"] for lg in s["logos"]) for s in close):
            out.append(
                _f("fail", "brand", "no visible logo at the close (missing, faded or covered)", close[0]["t"])
            )
    peak = max((s["accent"] for s in samples), default=0.0)
    for start, length in persisted(accent_times)[:3]:
        out.append(
            _f(
                "warn",
                "accent",
                f"{peak:g} accent moments for {length:.1f} s "
                f"(max {g.max_accent_moments:g}; the logo counts 0.5)",
                start,
            )
        )
    # settled size per text: its largest size, for texts on screen at least persist_s (entrances scale up)
    settled = [max(v) for k, v in sizes.items() if len(v) * step >= g.persist_s - 1e-9]
    return out, {"min_text_px": min(settled) if settled else None, "max_accent_moments": peak}


# --- browser, render, signals ---------------------------------------------------------------------------

COLLECT = """([accent]) => {
  const W = 1920, H = 1080;
  const parse = (c) => { const m = c && c.match(/rgba?\\(([^)]+)\\)/); if (!m) return null;
    const p = m[1].split(',').map(Number); return (p.length > 3 && p[3] < 0.5) ? null : p.slice(0, 3); };
  const isAccent = (c) => { const p = parse(c);
    return !!p && p.every((v, i) => Math.abs(v - accent[i]) <= 6); };
  const vis = (el) => { let o = 1; for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
      const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') return 0;
      o *= parseFloat(cs.opacity); } return o; };
  const onScreen = (r) => r.width > 1 && r.height > 1 && r.right > 0 && r.bottom > 0 &&
    r.left < W && r.top < H;
  const isLogo = (el) => /logo/i.test((el.id || '') + ' ' + (el.getAttribute('class') || '') + ' ' +
      (el.getAttribute('src') || ''));
  const root = document.getElementById('main') || document.body;
  const texts = [], logos = []; let accent_n = 0; const counted = new Set(); const groups = new Map();
  for (const el of root.querySelectorAll('*')) {
    if (el.closest('script,style')) continue;
    const r = el.getBoundingClientRect(); if (!onScreen(r)) continue;
    const o = vis(el); if (o < MINVIS) continue;
    const cs = getComputedStyle(el);
    if (isLogo(el) && !el.parentElement.closest('[data-logo-counted]')) {
      el.setAttribute('data-logo-counted', '');
      const top = document.elementFromPoint((r.left + r.right) / 2, (r.top + r.bottom) / 2);
      const mine = !!top && (el === top || el.contains(top));
      logos.push({box: [r.left, r.top, r.right, r.bottom], covered: !mine});
      if (!counted.has(el)) { accent_n += 0.5; counted.add(el); } continue; }
    const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
    if (own) { const scale = el.offsetHeight ? r.height / el.offsetHeight : 1;
      let blk = el;
      while (blk.parentElement && getComputedStyle(blk).display.startsWith('inline')) blk = blk.parentElement;
      if (!groups.has(blk)) groups.set(blk, groups.size);
      texts.push({text: own.slice(0, 40), px: parseFloat(cs.fontSize) * scale,
                  box: [r.left, r.top, r.right, r.bottom],
                  group: groups.get(blk)}); }
    let a = cs.backgroundColor !== cs.color && isAccent(cs.backgroundColor) && r.width * r.height >= 400;
    if (own && isAccent(cs.color)) a = true;
    if (el instanceof SVGElement && (isAccent(cs.fill) || isAccent(cs.stroke))) a = true;
    if (a) { let p = el.parentElement, inside = false;
      while (p) { if (counted.has(p)) { inside = true; break; } p = p.parentElement; }
      if (!inside) { accent_n += 1; } counted.add(el); }
  }
  document.querySelectorAll('[data-logo-counted]').forEach(e => e.removeAttribute('data-logo-counted'));
  return {texts, logos, accent: accent_n};
}"""


# every tween: duration, start on the film clock, ease name and the largest target's layout area as a share
# of the frame (transforms excluded)
TWEENS = """() => { const main = window.__timelines.main;
  return main.getChildren(true, true, false).map(t => {
  let s = t.startTime();
  for (let p = t.parent; p && p !== main; p = p.parent) s = p.startTime() + s / p.timeScale();
  const e = t.vars.ease; const r = document.getElementById('main') || document.body;
  const full = r.offsetWidth * r.offsetHeight || 1920 * 1080;
  const area = Math.max(0, ...t.targets().map(el => {
    if (!(el instanceof Element)) return 0;
    if (el.offsetWidth !== undefined) return el.offsetWidth * el.offsetHeight;
    const b = el.getBoundingClientRect(); return b.width * b.height; }));
  return {d: t.duration(), s: s,
          e: typeof e === 'string' ? e : (e ? 'custom' : 'power1.out'), a: area / full}; }); }"""


def browse(
    index: Path, dur: float, accent: str, g: MotionGradeConfig
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Seek the paused timeline every `sample_step_s` and collect the DOM samples, plus every tween."""
    from playwright.sync_api import sync_playwright

    from create.browser import launch

    js = COLLECT.replace("MINVIS", str(g.min_visible_opacity))
    with sync_playwright() as pw:
        b = launch(pw)
        page = b.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(index.as_uri())
        page.wait_for_function(
            "() => !!(window.__timelines && window.__timelines.main)", timeout=15000, polling=100
        )
        page.evaluate("() => document.fonts.ready.then(() => true)")
        tweens = page.evaluate(TWEENS)
        samples = []
        n = int(dur / g.sample_step_s + 1e-9)
        for i in range(n + 1):
            t = min(i * g.sample_step_s, dur - 1e-3)
            page.evaluate(f"() => {{ window.__timelines.main.seek({t}, false); return true; }}")
            samples.append({"t": round(t, 3), **page.evaluate(js, [list(_rgb(accent))])})
        b.close()
    return samples, tweens


def check_findings(out: str, returncode: int) -> list[GradeFinding]:
    """`hyperframes check` output: contrast failures fail, layout notes warn, lint/runtime errors fail."""
    found: list[GradeFinding] = []
    section = ""
    for raw in out.splitlines():
        line = raw.strip()
        head = re.match(r"^(Lint|Runtime|Layout|Motion|Contrast|Snapshots)$", line)
        if head:
            section = head.group(1)
            continue
        t = re.search(r"t=([\d.]+)s", line)
        when = float(t.group(1)) if t else None
        if line.startswith("✗"):
            area = "contrast" if section == "Contrast" else "layout"
            found.append(_f("fail", area, line[1:].strip()[:220], when))
        elif line.startswith("\u2139") and section == "Layout":  # the information sign
            found.append(_f("warn", "layout", line[1:].strip()[:220], when))
    if returncode != 0 and not any(f.level == "fail" for f in found):
        found.append(_f("fail", "layout", "hyperframes check failed: " + out.strip()[-200:]))
    return found


def sfx_library(cache: Path, render: CreateRender) -> Path:
    """HyperFrames' bundled SFX (Pixabay Content License) from the pinned npm package, cached."""
    out = cache / f"hyperframes-{render.hyperframes_version}-sfx"
    if not any(out.glob("*.mp3")):
        out.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(_get(NPM.format(v=render.hyperframes_version)))) as tar:
            for m in tar.getmembers():
                if m.name.startswith(SFX_IN_TARBALL) and m.isfile():
                    f = tar.extractfile(m)
                    if f is not None:
                        (out / Path(m.name).name).write_bytes(f.read())
    return out


def bundle(root: Path, project: str, tokens: Tokens, brand: str, render: CreateRender) -> Path:
    """data/create/<p>/motion/render/: the build plus assets/ (GSAP, fonts, logos, SFX)."""
    base = root / "projects" / project / "motion"
    out = root / "data" / "create" / project / "motion" / "render"
    assets = out / "assets"
    (assets / "fonts").mkdir(parents=True, exist_ok=True)
    cache = root / "data" / "create" / "_cache"
    shutil.copy(gsap(cache), assets / "gsap.min.js")
    css, files = fonts(cache, tokens.fonts_css)
    for f in files:
        shutil.copy(f, assets / "fonts" / f.name)
    (assets / "fonts.css").write_text(css)
    names = {"primary": "logo.svg", "on_dark": "logo-on-dark.svg", "mono": "logo-mono.svg"}
    for variant, rel in tokens.logo.files().items():
        shutil.copy(root / "brands" / brand / rel, assets / names[variant])
    sfx = assets / "sfx"
    if sfx.exists():
        shutil.rmtree(sfx)
    shutil.copytree(sfx_library(cache, render), sfx)
    shutil.copy(base / "index.html", out / "index.html")
    return out


def lens_signals(video: Path, fps: float, cfg: LensConfig) -> dict[str, Any]:
    from lens.signals import video as V

    v = cfg.signals.video
    fs = V.scan(video, fps, 1920, 1080, v)
    trans = V.detect_transitions(fs, V.detect_cuts(fs, v), v)
    shots = V.build_shots(fs.n, trans)
    events = V.detect_events(fs, shots, v)
    holds = V.detect_holds(fs, shots, events, v, cfg.signals.dead_hold_min_s)
    return {
        "frames": fs.n,
        "transitions": [(t.kind, t.start_f) for t in trans],
        "events": len(events),
        "busy": sum(e.end_f - e.start_f + 1 for e in events),
        "holds": [(h.start_f, h.end_f, h.dead) for h in holds],
    }


def review_sheets(video: Path, timeline: Timeline, dur: float, out: Path) -> list[Path]:
    """Two contact sheets for a fresh-eyes reviewer: the whole film, and around each handover."""
    from create.sketches import sheet_png

    out.mkdir(parents=True, exist_ok=True)
    n = 12
    overview = [round(dur * (i + 0.5) / n, 2) for i in range(n)]
    handovers = [
        round(sc.start_s + d, 2)
        for sc in timeline.scenes[1:]
        if sc.start_s < dur
        for d in (-0.6, -0.3, 0.0, 0.3, 0.6, 0.9)
    ]
    sheets = []
    for name, times in (("overview", overview), ("handovers", handovers)):
        if not times:
            continue
        frames = []
        for i, t in enumerate(times):
            f = out / f".{name}-{i:02d}.png"
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-ss",
                    f"{t}",
                    "-i",
                    str(video),
                    "-frames:v",
                    "1",
                    "-vf",
                    f"scale=640:-1,drawtext=text='{t:.2f} s':x=12:y=12:fontsize=26:fontcolor=white:"
                    "box=1:boxcolor=black@0.6",
                    str(f),
                ],
                check=True,
            )
            frames.append(f)
        sheets.append(sheet_png(frames, 6 if name == "handovers" else 4, out / f"{name}.png"))
        for f in frames:
            f.unlink()
    return sheets


def snapshots(root: Path, project: str, times: list[float], render: CreateRender) -> list[Path]:
    """Frames at `times` (seconds) for the builder's own look, after bundling."""
    out = root / "data" / "create" / project / "motion" / "render"
    snap = out / "snapshots"
    if snap.exists():
        shutil.rmtree(snap)
    res = hyperframes(
        render,
        "snapshot",
        ".",
        "--at",
        ",".join(f"{t:g}" for t in times),
        "--no-end",
        "--describe",
        "false",
        "-o",
        str(snap),
        cwd=out,
    )
    pngs = sorted(snap.glob("*.png"))
    if res.returncode != 0 or not pngs:
        raise RuntimeError(f"snapshot failed\n{res.stdout[-800:]}{res.stderr[-800:]}")
    return pngs


# --- the builder's budget (config create.motion.build) ---------------------------------------------------


class BudgetError(RuntimeError):
    """The build round has spent its full grades or snapshot frames."""


def _budget_path(root: Path, project: str) -> Path:
    return root / "data" / "create" / project / "motion" / "render" / "budget.json"


def spend(root: Path, project: str, kind: str, n: int, limit: int) -> int:
    """Count `n` of `kind` (grades | frames) against this round's `limit`; returns what is left."""
    path = _budget_path(root, project)
    used: dict[str, int] = json.loads(path.read_text()) if path.exists() else {}
    if used.get(kind, 0) + n > limit:
        raise BudgetError(
            f"this round has used {used.get(kind, 0)} of {limit} {kind} (config create.motion.build); "
            "report what is left to fix instead"
        )
    used[kind] = used.get(kind, 0) + n
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(used))
    return limit - used[kind]


def new_round(root: Path, project: str) -> None:
    """A fresh budget for the next build round (the main session starts each round)."""
    _budget_path(root, project).unlink(missing_ok=True)


# --- the stage -------------------------------------------------------------------------------------------


def _inputs(root: Path, project: str) -> tuple[Brief, Timeline, Tokens, str, list[dict[str, Any]]]:
    base = root / "projects" / project
    brief = Brief.model_validate(yaml.safe_load((base / "brief.yaml").read_text()))
    timeline = Timeline.model_validate_json((base / "timeline.json").read_text())
    tokens = Tokens.model_validate_json((base / "tokens.json").read_text())
    html = (base / "motion" / "index.html").read_text()
    sfx_path = base / "motion" / "sfx.json"
    cues = json.loads(sfx_path.read_text()) if sfx_path.exists() else []
    return brief, timeline, tokens, html, cues


def prepare(root: Path, project: str, cfg: LensConfig) -> tuple[Path, list[GradeFinding]]:
    """Bundle the build and run `hyperframes check` (the fast part: what `--lint-only` reports)."""
    brief, timeline, tokens, html, _ = _inputs(root, project)
    out = bundle(root, project, tokens, brief.brand, cfg.create.render)
    hyperframes(cfg.create.render, "telemetry", "disable", cwd=out)
    res = hyperframes(cfg.create.render, "check", ".", cwd=out)
    dur = film_s(brief, timeline, cfg.create.motion.final_hold_s)
    found = check_findings(res.stdout + res.stderr, res.returncode) + duration_findings(html, dur)
    return out, found


def run_grade(root: Path, project: str, cfg: LensConfig) -> MotionGrade:
    brief, timeline, tokens, html, cues = _inputs(root, project)
    mc = cfg.create.motion
    g = mc.grade
    dur = film_s(brief, timeline, mc.final_hold_s)
    out, found = prepare(root, project, cfg)
    pacing = json.loads((root / "exports" / "pacing.json").read_text())
    shot = pacing["shot_s_by_format"].get(brief.format, pacing["shot_s"])
    sound = json.loads((root / "exports" / "sound-spec.json").read_text())
    frame = cfg.create.design.frames[tokens.frame]

    found += colour_findings(html, tokens.colors, g) + decoration_findings(html, g)
    samples, tweens = browse(out / "index.html", dur, tokens.colors["accent"], g)
    moves_found, moves = move_findings(tweens, g)
    dom_found, dom = dom_findings(samples, frame.min_text_px, g)
    motion = json.loads((root / "exports" / "motion-tokens.json").read_text())
    found += moves_found + dom_found
    found += ease_findings(tweens, motion["easing"]["spring_overshoot"]["share"], g)
    found += seam_findings(tweens, timeline.scenes, dur, g)

    res = hyperframes(
        cfg.create.render,
        "render",
        ".",
        "-o",
        "video.mp4",
        "--quiet",
        "--video-frame-format",
        "png",
        "--frames-cache-dir",
        "off",
        cwd=out,
    )
    if res.returncode != 0:
        raise RuntimeError(f"hyperframes render failed\n{res.stdout[-1500:]}{res.stderr[-1500:]}")
    video = out / "video.mp4"
    sig = lens_signals(video, timeline.fps, cfg)
    expected = round(dur * timeline.fps)
    if abs(sig["frames"] - expected) > 1:
        found.append(_f("fail", "timing", f"{sig['frames']} frames rendered, expected {expected}"))
    found += hold_findings(sig["holds"], sig["transitions"], timeline.fps, dur, shot["high"])
    found += sfx_findings(cues, dur, sound["sfx_per_min"], out / "assets" / "sfx")
    review_sheets(video, timeline, dur, out / "review")

    fps = timeline.fps
    fails = sum(f.level == "fail" for f in found)
    grade = MotionGrade(
        provenance=Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CODE,
            input_hash=cache_key({"html": html, "sfx": cues, "grade": g.model_dump(), "dur": dur}),
            created_at=datetime.now(UTC),
        ),
        project=project,
        duration_s=dur,
        measures=GradeMeasures(
            transitions=[f"{k}@{f / fps:.2f}" for k, f in sig["transitions"]],
            events=sig["events"],
            motion_share=round(min(1.0, sig["busy"] / max(1, sig["frames"])), 3),
            moves=moves,
            sfx=len(cues),
            dead_hold_s=round(sum(z - a for a, z, d in sig["holds"] if d) / fps, 2),
            longest_idle_s=round(max((z - a for a, z, _ in sig["holds"]), default=0) / fps, 2),
            min_text_px=None if dom["min_text_px"] is None else round(dom["min_text_px"], 1),
            max_accent_moments=dom["max_accent_moments"] or 0.0,
        ),
        findings=found,
        fails=fails,
        warns=len(found) - fails,
        ok=fails == 0,
    )
    path = root / "projects" / project / "motion" / "grade.json"
    path.write_text(grade.model_dump_json(indent=1) + "\n")
    return grade
