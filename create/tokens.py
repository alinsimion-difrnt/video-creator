"""C3 tokens: the brand hand-off made ready for the video frame (handoff 7.4, ADR 0022).

Inputs (both in brands/<brand>/, the brand the brief names): the hand-off's tokens.json and the hand-written
video.yaml that maps it to video roles. Output: projects/<project>/tokens.json with
- colours by role, and a WCAG 2.1 contrast table computed here (a failing pair needs a written exception);
- font families by role, and type styles from the size set video.yaml names, with the overrides applied
  (nothing under the frame's `min_text_px`; other frames than landscape come from video.yaml `frames`);
- glyph coverage measured on the Google Fonts files themselves, with fallbacks for missing glyphs;
- layout in pixels for the brief's destination frame, with its safe area and caption band (config).
"""

from __future__ import annotations

import io
import json
import re
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from lens import __version__
from lens.hashing import cache_key
from lens.schemas.common import Annotator, Provenance
from lens.schemas.config import CreateDesign, LensConfig
from lens.schemas.create import (
    BrandType,
    BrandVideo,
    ContrastPair,
    FontFamily,
    GlyphCoverage,
    Layout,
    Tokens,
    TypeStyle,
)

STAGE = "c3_tokens"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

FetchFont = Callable[[FontFamily, str, str], tuple[bytes, str]]  # (family, text, css base) -> (woff2, url)

# What the templates and the build read (create/templates, create/build.py): every brand must map these.
REQUIRED_ROLES = (
    "canvas",
    "canvas_product",
    "surface",
    "fill_subtle",
    "chip",
    "ink",
    "ink_muted",
    "hairline",
    "accent",
    "accent_text",
    "accent_text_large",
    "success",
)
REQUIRED_STYLES = ("display", "headline", "stat-number", "body", "caption", "uppercase-label")
# Template UI copy each brand writes in its own language (video.yaml `strings`); templates hold none.
REQUIRED_STRINGS = ("example_data", "own_prompt", "suggested_prompt", "asked_as", "own_brand")


def luminance(hex_color: str) -> float:
    rgb = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    """Exact WCAG ratio; compare this unrounded (4.497 must not pass as 4.5)."""
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def required_ratio(size: str, design: CreateDesign) -> float:
    return design.contrast_normal if size == "normal" else design.contrast_large


def resolve(tokens: dict[str, Any], path: str) -> Any:
    node: Any = tokens
    for key in path.split("."):
        node = node[key]
    return node


def px(value: Any) -> int:
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)", str(value))
    if not m:
        raise ValueError(f"no pixel value in {value!r}")
    return round(float(m.group(1)))


def em(value: Any) -> float:
    return float(str(value).replace("em", "").strip() or 0)


def family_query(f: FontFamily) -> str:
    """The Google Fonts css2 `family` value, e.g. `Inter:wght@400..700`."""
    return f"{f.family}:wght@{f.weights}"


def google_font(family: FontFamily, text: str, css_base: str) -> tuple[bytes, str]:
    """The Google Fonts file for `family`, subset to `text` (glyphs the font lacks are simply absent)."""
    query = urllib.parse.urlencode({"family": family_query(family), "text": text})
    req = urllib.request.Request(f"{css_base}?{query}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        css = resp.read().decode()
    m = re.search(r"url\((https://[^)]+)\)", css)
    if not m:
        raise RuntimeError(f"no font file for {family.family!r} in the Google Fonts response")
    with urllib.request.urlopen(m.group(1), timeout=60) as resp:
        return resp.read(), m.group(1).split("?")[0]


def coverage(family: FontFamily, glyphs: str, design: CreateDesign, fetch: FetchFont) -> GlyphCoverage:
    from fontTools.ttLib import TTFont

    data, url = fetch(family, glyphs, design.google_fonts_css)
    cmap = TTFont(io.BytesIO(data)).getBestCmap()
    return GlyphCoverage(family=family.family, source=url, has={g: ord(g) in cmap for g in glyphs})


def _type_styles(brand: dict[str, Any], spec: BrandType) -> dict[str, TypeStyle]:
    families = {f.family for f in spec.families.values()}
    out: dict[str, TypeStyle] = {}
    for name, style in brand["type"]["styles"].items():
        if spec.sizes not in style:
            raise ValueError(f"type style {name!r} has no {spec.sizes!r} sizes")
        v = style[spec.sizes]
        family = style["family"]
        if family not in families:
            raise ValueError(f"type style {name!r} uses {family!r}, not a brand family")
        size = px(v["size"])
        note = None
        if name in spec.overrides:
            size = round(spec.overrides[name].get("size", size))
            note = f"size {px(v['size'])}px -> {size}px (video.yaml)"
        out[name] = TypeStyle(
            family=family,
            weight=int(style["weight"]),
            size_px=size,
            line_height=float(v["lineHeight"]),
            tracking_em=em(v.get("tracking", 0)),
            uppercase=v.get("transform") == "uppercase",
            override=note,
        )
    return out


def _value(brand: dict[str, Any], ref: str | int) -> Any:
    """A layout value: a token path into the hand-off ("group.name"), or a literal."""
    if isinstance(ref, int):
        return ref
    try:
        return resolve(brand, ref)
    except (KeyError, TypeError):
        return ref


def _for_frame(spec: BrandVideo, frame: str) -> BrandVideo:
    """The brand spec with that frame's type sizes and layout applied (landscape is the base)."""
    if frame == "landscape":
        return spec
    if frame not in spec.frames:
        raise ValueError(f"the brand has no {frame!r} sizes (video.yaml frames.{frame}: sizes, layout)")
    f = spec.frames[frame]
    t = spec.type.model_copy(update={"sizes": f.sizes, "overrides": f.overrides})
    layout = spec.layout.model_copy(update=f.layout)
    return spec.model_copy(update={"type": t, "layout": layout})


def build_tokens(
    project: str,
    brand: dict[str, Any],
    video: dict[str, Any],
    cfg: LensConfig,
    fetch: FetchFont = google_font,
    frame: str = "landscape",
) -> Tokens:
    design = cfg.create.design
    if frame not in design.frames:
        raise ValueError(f"frame {frame!r} is not in config create.design.frames")
    geo = design.frames[frame]
    spec = _for_frame(BrandVideo.model_validate(video), frame)
    colors = {role: str(resolve(brand["color"], path)).upper() for role, path in spec.colors.items()}
    pairs = []
    for p in spec.pairs:
        if p.text not in colors or p.bg not in colors:
            raise ValueError(f"pair {p.text} on {p.bg}: unknown colour role")
        ratio = contrast(colors[p.text], colors[p.bg])
        need = required_ratio(p.size, design)
        pairs.append(
            ContrastPair(
                text=p.text,
                bg=p.bg,
                size=p.size,
                use=p.use,
                ratio=round(ratio, 2),
                required=need,
                passes=ratio >= need,
                exception=p.exception,
            )
        )
    styles = _type_styles(brand, spec.type)
    # families the styles use, plus fallback families that only set a missing glyph (checked and loaded too)
    used = {s.family for s in styles.values()} | set(spec.type.glyph_fallback.values())
    families = [f for f in spec.type.families.values() if f.family in used]
    families = list({f.family: f for f in families}.values())  # one check per family
    glyph_set = "".join(dict.fromkeys(design.required_glyphs + spec.type.extra_glyphs))
    glyphs = [coverage(f, glyph_set, design, fetch) for f in sorted(families, key=lambda f: f.family)]
    lay = spec.layout
    layout = Layout(
        width=geo.width,
        height=geo.height,
        safe_margin=px(_value(brand, lay.safe_margin)),
        section_gap=px(_value(brand, lay.section_gap)),
        stack_gap=px(_value(brand, lay.stack_gap)),
        card_padding=px(_value(brand, lay.card_padding)),
        card_radius=px(_value(brand, lay.card_radius)),
        chip_radius=px(_value(brand, lay.chip_radius)),
        hairline_width=lay.hairline_width,
        card_shadow=str(_value(brand, lay.card_shadow)),
        caption_keepout_px=geo.height - geo.caption_band.y0,
        safe=geo.safe,
        caption_band=geo.caption_band,
    )
    query = urllib.parse.urlencode(
        [("family", family_query(f)) for f in sorted(families, key=lambda f: f.family)]
        + [("display", "swap")]
    )
    return Tokens(
        provenance=Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CODE,
            input_hash=cache_key(
                {"brand": brand, "video": video, "design": design.model_dump(), "frame": frame}
            ),
            created_at=datetime.now(UTC),
        ),
        project=project,
        frame=frame,
        colors=colors,
        contrast=pairs,
        type=styles,
        families=dict(spec.type.families),
        fonts_css=f"{design.google_fonts_css}?{query}",
        glyphs=glyphs,
        glyph_fallback=dict(spec.type.glyph_fallback),
        layout=layout,
        logo=spec.logo,
        accent_tint_alpha=spec.accent_tint_alpha or design.accent_tint_alpha,
        strings=dict(spec.strings),
        captions=spec.captions.get(frame),
    )


def run_tokens(
    root: Path, project: str, cfg: LensConfig, fetch: FetchFont = google_font
) -> tuple[Path, Tokens]:
    from create.project import brand_dir as find_brand

    brand_dir = find_brand(root, project)
    brand = json.loads((brand_dir / "tokens.json").read_text())
    video = yaml.safe_load((brand_dir / "video.yaml").read_text())
    brief = yaml.safe_load((root / "projects" / project / "brief.yaml").read_text())
    frame, _ = cfg.create.design.frame_for(brief.get("destination", "linkedin"))
    tokens = build_tokens(project, brand, video, cfg, fetch, frame)
    path = root / "projects" / project / "tokens.json"
    path.write_text(tokens.model_dump_json(indent=1) + "\n")
    return path, tokens


def token_errors(tokens: Tokens, design: CreateDesign, brand_dir: Path | None = None) -> list[str]:
    """Checks a tokens file must pass (also run by `lens validate`)."""
    errors = [
        f"colour role {r!r} is missing (templates need it)" for r in REQUIRED_ROLES if r not in tokens.colors
    ]
    errors += [
        f"type style {s!r} is missing (templates need it)" for s in REQUIRED_STYLES if s not in tokens.type
    ]
    errors += [
        f"string {s!r} is missing (templates need it)" for s in REQUIRED_STRINGS if s not in tokens.strings
    ]
    for role in ("heading", "body"):
        if role not in tokens.families:
            errors.append(f"font family role {role!r} is missing")
    known = {f.family for f in tokens.families.values()}
    for name, s in tokens.type.items():
        if s.family not in known:
            errors.append(f"type {name}: {s.family!r} is not a brand family")
    for p in tokens.contrast:
        if p.text not in tokens.colors or p.bg not in tokens.colors:
            errors.append(f"contrast {p.text} on {p.bg}: unknown colour role")
            continue
        ratio = contrast(tokens.colors[p.text], tokens.colors[p.bg])
        if abs(ratio - p.ratio) > 0.01:
            errors.append(f"contrast {p.text} on {p.bg}: recorded {p.ratio}, measured {ratio:.2f}")
        if ratio < required_ratio(p.size, design) and not p.exception:
            errors.append(
                f"contrast {p.text} on {p.bg} is {ratio:.2f}:1, under {required_ratio(p.size, design)}:1, "
                "with no exception"
            )
    geo = design.frames.get(tokens.frame)
    if geo is None:
        errors.append(f"frame {tokens.frame!r} is not in config create.design.frames")
    else:
        if (tokens.layout.width, tokens.layout.height) != (geo.width, geo.height):
            errors.append(
                f"layout is {tokens.layout.width}x{tokens.layout.height}, frame is {geo.width}x{geo.height}"
            )
        for name, s in tokens.type.items():
            if s.size_px < geo.min_text_px:
                errors.append(
                    f"type {name}: {s.size_px}px is under the {geo.min_text_px:g}px {tokens.frame} minimum"
                )
    if not tokens.glyphs:
        errors.append("glyph coverage was not checked")
    has = {g.family: g.has for g in tokens.glyphs}
    checked = "".join(g for cov in tokens.glyphs for g in cov.has)  # house set plus the brand's extra glyphs
    for g in dict.fromkeys(design.required_glyphs + checked):
        for family in has:
            target = tokens.glyph_fallback.get(g, family)
            if not has.get(target, {}).get(g, False):
                errors.append(
                    f"glyph {g!r}: missing in {family} and no family that has it is set as fallback"
                )
                break
    errors += caption_errors(tokens, design)
    if brand_dir is not None:
        for name, file in tokens.logo.files().items():
            if not (brand_dir / file).exists():
                errors.append(f"logo.{name}: {file} is not in the brand folder")
    return errors


def caption_errors(tokens: Tokens, design: CreateDesign) -> list[str]:
    """A caption style must use known roles, be large enough for the frame and readable on its surface."""
    c = tokens.captions
    if c is None:
        return []
    errors = []
    roles = [r for r in (c.text, c.active, c.background, c.stroke) if r is not None]
    errors += [f"captions: colour role {r!r} is unknown" for r in roles if r not in tokens.colors]
    if c.family not in tokens.families:
        errors.append(f"captions: font family role {c.family!r} is unknown")
    geo = design.frames.get(tokens.frame)
    if geo is not None:
        if c.size_px < geo.min_text_px:
            errors.append(
                f"captions: {c.size_px:g}px is under the {geo.min_text_px:g}px {tokens.frame} minimum"
            )
        if c.max_width_px > geo.caption_band.x1 - geo.caption_band.x0:
            errors.append(
                f"captions: max_width_px {c.max_width_px} is wider than the {tokens.frame} caption band"
            )
    if errors:
        return errors
    under = c.background or c.stroke
    assert under is not None  # CaptionStyle guarantees one of them
    for role in {c.text, c.active}:
        ratio = contrast(tokens.colors[role], tokens.colors[under])
        if ratio < design.contrast_normal:
            errors.append(f"captions: {role} on {under} is {ratio:.2f}:1, under {design.contrast_normal}:1")
    return errors
