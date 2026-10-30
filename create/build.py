"""C8 build: one standalone HyperFrames composition per scene, from the storyboard and the templates.

Each scene file is self-contained HTML: the brand tokens as CSS variables, the shared base styles and runtime
(create/templates/_base.css, _kit.js), the archetype's template script and the scene's data (slots, cues in
seconds from the scene start, motion values from exports/motion-tokens.json). One paused GSAP timeline is
registered under the scene id, as HyperFrames requires.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

import yaml

from lens.schemas.create import Brief, Storyboard, StoryScene, Timeline, Tokens

TEMPLATES = Path(__file__).parent / "templates"
GSAP_VERSION = "3.14.2"  # the version lens' goldens were sampled from (external-facts §12)
# Scenes load GSAP and fonts from a local assets/ folder (create/bundle.py), never from a CDN at render time.
ASSETS = "assets"


def template_path(archetype: str) -> Path:
    return TEMPLATES / f"{archetype}.js"


_FRAMES = re.compile(r"^//\s*frames:\s*([a-z_, ]+)", re.MULTILINE)


def template_frames(archetype: str) -> set[str]:
    """The frames a template is laid out for (its `// frames: ...` header line)."""
    m = _FRAMES.search(template_path(archetype).read_text())
    return {f.strip() for f in m.group(1).split(",") if f.strip()} if m else set()


def blend(hex_color: str, alpha: float, over: str) -> str:
    """`hex_color` at `alpha` over `over`, flattened (tints are specified as alpha over white)."""
    a = [int(hex_color[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(over[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * alpha + y * (1 - alpha)):02X}" for x, y in zip(a, b, strict=True))


def css_vars(tokens: Tokens) -> str:
    c, t, lay = tokens.colors, tokens.type, tokens.layout
    v: dict[str, str] = {f"--{k.replace('_', '-')}": val for k, val in c.items()}
    v["--accent-tint"] = blend(c["accent"], tokens.accent_tint_alpha, c["surface"])
    v.setdefault("--accent-fill", c["accent"])  # solid accent fills; a brand may map accent_fill elsewhere
    for role, f in tokens.families.items():
        v[f"--font-{role.replace('_', '-')}"] = f'"{f.family}", {f.fallback}'
    for name, key in (
        ("display", "display"),
        ("headline", "headline"),
        ("stat", "stat-number"),
        ("body", "body"),
        ("caption", "caption"),
        ("label", "uppercase-label"),
    ):
        s = t[key]
        fam = next((f for f in tokens.families.values() if f.family == s.family), None)
        v[f"--{name}-font"] = f'"{s.family}", {fam.fallback if fam else "sans-serif"}'
        v[f"--{name}-wt"] = str(s.weight)
        v[f"--{name}-size"] = f"{s.size_px:g}px"
        v[f"--{name}-lh"] = f"{s.line_height:g}"
        v[f"--{name}-tr"] = f"{s.tracking_em:g}em"
    core = lay.safe[0]  # the first safe rect is the core every platform leaves clear
    v.update(
        {
            "--frame-w": f"{lay.width}px",
            "--frame-h": f"{lay.height}px",
            "--safe-x0": f"{core.x0}px",
            "--safe-y0": f"{core.y0}px",
            "--safe-x1": f"{core.x1}px",
            "--safe-y1": f"{core.y1}px",
            "--caption-y0": f"{lay.caption_band.y0}px",
            "--safe": f"{lay.safe_margin}px",
            "--keepout": f"{lay.caption_keepout_px}px",
            "--stack": f"{lay.stack_gap}px",
            "--card-pad": f"{lay.card_padding}px",
            "--card-radius": f"{lay.card_radius}px",
            "--chip-radius": f"{lay.chip_radius}px",
            "--hair": f"{lay.hairline_width}px",
            "--card-shadow": lay.card_shadow,
        }
    )
    return ":root{" + ";".join(f"{k}:{val}" for k, val in v.items()) + "}"


def motion_values(motion: dict[str, Any]) -> dict[str, Any]:
    """Seconds and GSAP eases from the corpus motion tokens (medians)."""
    role, change, ease = motion["duration_ms_by_role"], motion["duration_ms_by_change"], motion["easing"]
    return {
        "text": round(role["body_text"]["median"] / 1000, 3),
        "card": round(role["card"]["median"] / 1000, 3),
        "chip": round(role["button"]["median"] / 1000, 3),
        "draw": round(change["draw_on"]["median"] / 1000, 3),
        "highlight": round(change["highlight"]["median"] / 1000, 3),
        "word_stagger": round(motion["word_stagger_ms"]["median"] / 1000, 3),
        "ease_out": ease["ease_out"]["gsap"],
        "ease_in": ease["ease_in"]["gsap"],
        "ease_overshoot": ease["spring_overshoot"]["gsap"],
    }


def clean_svg(svg: str) -> str:
    """Inline-safe logo: no metadata blocks (the hand-off SVGs carry a large C2PA manifest)."""
    svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.DOTALL)
    return re.sub(r"<\?xml[^>]*>", "", svg).strip()


def scene_data(
    sc: StoryScene,
    timeline: Timeline,
    motion: dict[str, Any],
    logos: dict[str, str],
    brand: dict[str, str],
    strings: dict[str, str],
) -> dict[str, Any]:
    bounds = {s.scene: s for s in timeline.scenes}[sc.scene]
    words = {w.i: w for w in timeline.words}
    return {
        "scene": sc.scene,
        "duration": round(bounds.end_s - bounds.start_s, 3),
        "title": sc.title,
        "slots": sc.slots,
        "cues": [
            {"t": round(words[c.word].start_s - bounds.start_s, 3), "target": c.target, "do": c.do}
            for c in sc.cues
        ],
        "example_data": sc.example_data,
        "accent": sc.accent,
        "motion": motion,
        "logo": logos,
        "brand": brand,
        "strings": strings,
    }


def scene_html(
    sc: StoryScene, data: dict[str, Any], tokens: Tokens, css_root: str, language: str = "en"
) -> str:
    base = (TEMPLATES / "_base.css").read_text()
    kit = (TEMPLATES / "_kit.js").read_text()
    tpl = template_path(sc.archetype).read_text()
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="{language}">
<head>
<meta charset="utf-8">
<title>{html.escape(sc.scene)} {html.escape(sc.archetype)}</title>
<link rel="stylesheet" href="{ASSETS}/fonts.css">
<script src="{ASSETS}/gsap.min.js"></script>
<style>{css_root}
{base}</style>
</head>
<body>
<div id="{sc.scene}" class="scene {sc.canvas}" data-composition-id="{sc.scene}"
 data-width="{tokens.layout.width}" data-height="{tokens.layout.height}" data-start="0"
 data-duration="{data["duration"]}">
<script type="application/json" id="scene-data">{blob}</script>
<script>
{kit}
{tpl}
runScene(render);
</script>
</div>
</body>
</html>
"""


def run_build(root: Path, project: str) -> list[Path]:
    """Writes projects/<project>/scenes/<scene>.html for every templated scene."""
    base = root / "projects" / project
    board = Storyboard.model_validate(json.loads((base / "storyboard.json").read_text()))
    timeline = Timeline.model_validate(json.loads((base / "timeline.json").read_text()))
    tokens = Tokens.model_validate(json.loads((base / "tokens.json").read_text()))
    brief = Brief.model_validate(yaml.safe_load((base / "brief.yaml").read_text()))
    motion = motion_values(json.loads((root / "exports" / "motion-tokens.json").read_text()))
    logos = {
        k: clean_svg((root / "brands" / brief.brand / f).read_text()) for k, f in tokens.logo.files().items()
    }
    brand = {"name": brief.product.name, "host": re.sub(r"^https?://", "", brief.product.url).rstrip("/")}
    css_root = css_vars(tokens)
    out = base / "scenes"
    out.mkdir(exist_ok=True)
    written = []
    for sc in board.scenes:
        if sc.archetype == "freeform":
            continue  # built by c8_build_freeform
        if not template_path(sc.archetype).exists():
            raise FileNotFoundError(f"{sc.scene}: no template for archetype {sc.archetype!r}")
        if tokens.frame not in template_frames(sc.archetype):
            raise ValueError(
                f"{sc.scene}: template {sc.archetype!r} has no {tokens.frame} layout "
                f"(it supports {', '.join(sorted(template_frames(sc.archetype))) or 'no frame'})"
            )
        path = out / f"{sc.scene}.html"
        path.write_text(
            scene_html(
                sc,
                scene_data(sc, timeline, motion, logos, brand, tokens.strings),
                tokens,
                css_root,
                brief.language,
            )
        )
        written.append(path)
    return written
