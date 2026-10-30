"""P2: C3 tokens (contrast computed and enforced, video type sizes, glyph coverage), without the network."""

import io
import json
import shutil
from pathlib import Path

import pytest
import yaml
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from create.tokens import build_tokens, contrast, run_tokens, token_errors
from lens.config import REPO_ROOT, load_config
from lens.schemas.create import FontFamily
from lens.validate import validate_file

BRAND = REPO_ROOT / "brands" / "acme"


def _font(chars: str) -> bytes:
    """A tiny TrueType font whose cmap holds exactly `chars`."""
    names = [".notdef"] + [f"g{ord(c)}" for c in chars]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(names)
    fb.setupCharacterMap({ord(c): f"g{ord(c)}" for c in chars})
    pen = TTGlyphPen(None)
    pen.moveTo((0, 0)), pen.lineTo((0, 100)), pen.lineTo((100, 0)), pen.closePath()
    glyph = pen.glyph()
    fb.setupGlyf({n: glyph for n in names})
    fb.setupHorizontalMetrics({n: (500, 0) for n in names})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "T", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    buf = io.BytesIO()
    fb.save(buf)
    return buf.getvalue()


def fake_fetch(missing: dict[str, str]):
    def fetch(family: FontFamily, text: str, css_base: str) -> tuple[bytes, str]:
        name = family.family
        return _font("".join(c for c in text if c not in missing.get(name, ""))), f"test://{name}"

    return fetch


@pytest.fixture
def root(tmp_path: Path) -> Path:
    for rel in ("config/lens.yaml", "taxonomy/v1.yaml"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, tmp_path / rel)
    shutil.copytree(BRAND, tmp_path / "brands" / "demo")
    (tmp_path / "projects" / "demo").mkdir(parents=True)
    (tmp_path / "projects" / "demo" / "brief.yaml").write_text("project: demo\nbrand: demo\n")  # brand only
    return tmp_path


def test_wcag_contrast_matches_known_values():
    assert contrast("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert contrast("#00AA90", "#FFFFFF") == pytest.approx(2.94, abs=0.005)  # the hand-off's own figure
    assert contrast("#6B7280", "#F5F7FA") > 4.5  # 4.5046: passes unrounded, only just


def test_acme_tokens_build_and_validate(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    path, tokens = run_tokens(root, "demo", cfg, fetch=fake_fetch({"Space Grotesk": "✓"}))
    assert tokens.colors["ink"] == "#3E0863" and tokens.colors["accent"] == "#00AA90"
    assert tokens.type["uppercase-label"].size_px == 24  # 22 -> 24 override
    assert tokens.type["display"].size_px == 128 and tokens.type["display"].family == "Space Grotesk"
    band = cfg.create.design.frames["landscape"].caption_band
    assert tokens.frame == "landscape" and tokens.layout.caption_keepout_px == 1080 - band.y0 == 184
    failing = [p for p in tokens.contrast if not p.passes]
    assert failing and all(p.exception for p in failing)  # only the orange accent, with its brand rule
    assert {p.text for p in failing} == {"accent"}
    assert token_errors(tokens, cfg.create.design, root / "brands/demo") == []
    result = validate_file(path, root)
    assert result.ok, result.errors


def _video(root: Path) -> dict:
    return yaml.safe_load((root / "brands/demo/video.yaml").read_text())


def _brand(root: Path) -> dict:
    return json.loads((root / "brands/demo/tokens.json").read_text())


def test_failing_pair_without_exception_is_an_error(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    video = _video(root)
    video["pairs"].append({"text": "accent", "bg": "surface", "size": "normal", "use": "small orange text"})
    tokens = build_tokens("demo", _brand(root), video, cfg, fake_fetch({"Space Grotesk": "✓"}))
    errors = token_errors(tokens, cfg.create.design)
    assert any("accent on surface" in e and "no exception" in e for e in errors)


def test_text_under_the_video_minimum_is_an_error(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    video = _video(root)
    del video["type"]["overrides"]["uppercase-label"]  # back to the hand-off's 22px
    tokens = build_tokens("demo", _brand(root), video, cfg, fake_fetch({"Space Grotesk": "✓"}))
    assert any("uppercase-label" in e and "22.0px" in e for e in token_errors(tokens, cfg.create.design))


def test_missing_glyph_needs_a_fallback_that_has_it(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    video = _video(root)
    video["type"]["glyph_fallback"] = {}
    tokens = build_tokens("demo", _brand(root), video, cfg, fake_fetch({"Space Grotesk": "✓"}))
    assert any("'✓'" in e and "Space Grotesk" in e for e in token_errors(tokens, cfg.create.design))
    # a fallback to a family that lacks it too is still an error
    video["type"]["glyph_fallback"] = {"✓": "Inter"}
    tokens = build_tokens("demo", _brand(root), video, cfg, fake_fetch({"Space Grotesk": "✓", "Inter": "✓"}))
    assert any("'✓'" in e for e in token_errors(tokens, cfg.create.design))


def test_fallback_family_no_style_uses_is_checked_and_loaded(root: Path):
    """A brand whose styles all lack ✓ names a fallback family only for it (acme: Geist -> Inter)."""
    cfg = load_config(root / "config/lens.yaml")
    video = _video(root)
    video["type"]["families"]["symbols"] = {"family": "Noto Sans Symbols 2", "weights": "400"}
    video["type"]["glyph_fallback"] = {"✓": "Noto Sans Symbols 2"}
    tokens = build_tokens("demo", _brand(root), video, cfg, fake_fetch({"Space Grotesk": "✓"}))
    assert "Noto Sans Symbols 2" in {g.family for g in tokens.glyphs}
    assert "Noto+Sans+Symbols+2" in tokens.fonts_css
    assert not [e for e in token_errors(tokens, cfg.create.design) if "glyph" in e]


def test_tampered_ratio_is_caught(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    path, _ = run_tokens(root, "demo", cfg, fetch=fake_fetch({"Space Grotesk": "✓"}))
    data = json.loads(path.read_text())
    data["contrast"][0]["ratio"] = 20.0
    path.write_text(json.dumps(data))
    assert any("recorded 20.0" in e for e in validate_file(path, root).errors)


def test_missing_logo_file_is_an_error(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    (root / "brands/demo/logo/acme-mono.svg").unlink()
    _, tokens = run_tokens(root, "demo", cfg, fetch=fake_fetch({"Space Grotesk": "✓"}))
    assert any("logo.mono" in e for e in token_errors(tokens, cfg.create.design, root / "brands/demo"))


def test_brand_glyphs_and_families_are_checked(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    video = _video(root)
    video["type"]["extra_glyphs"] = "ș"
    tokens = build_tokens("demo", _brand(root), video, cfg, fake_fetch({"Space Grotesk": "✓ș", "Inter": "ș"}))
    assert all("ș" in g.has for g in tokens.glyphs)
    assert any("'ș'" in e for e in token_errors(tokens, cfg.create.design))
    video["type"]["families"]["body"]["weights"] = "300..700"
    tokens = build_tokens("demo", _brand(root), video, cfg, fake_fetch({"Space Grotesk": "✓"}))
    assert "Inter%3Awght%40300..700" in tokens.fonts_css


def test_video_yaml_needs_heading_and_body(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    video = _video(root)
    del video["type"]["families"]["heading"]
    with pytest.raises(ValueError, match="heading"):
        build_tokens("demo", _brand(root), video, cfg, fake_fetch({}))


def test_template_roles_and_styles_are_required(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    video = _video(root)
    del video["colors"]["chip"]
    video["pairs"] = [p for p in video["pairs"] if "chip" not in (p["text"], p["bg"])]
    tokens = build_tokens("demo", _brand(root), video, cfg, fake_fetch({"Space Grotesk": "✓"}))
    assert any("colour role 'chip'" in e for e in token_errors(tokens, cfg.create.design))


def test_template_strings_are_required(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    video = _video(root)
    del video["strings"]["asked_as"]
    tokens = build_tokens("demo", _brand(root), video, cfg, fake_fetch({"Space Grotesk": "✓"}))
    assert any("string 'asked_as'" in e for e in token_errors(tokens, cfg.create.design))


def _vertical(video: dict) -> dict:
    """A vertical size set for the demo brand: every style at its landscape size + 50% (test only)."""
    video["frames"] = {"vertical": {"sizes": "vertical", "layout": {"safe_margin": 120}}}
    return video


def _with_vertical_sizes(brand: dict) -> dict:
    for style in brand["type"]["styles"].values():
        v = dict(style["video1920"])
        v["size"] = f"{round(float(str(v['size']).rstrip('px')) * 1.5)}px"
        style["vertical"] = v
    return brand


def test_vertical_tokens_use_the_frame_and_its_minimum(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    brand = _with_vertical_sizes(_brand(root))
    video = _vertical(_video(root))
    tokens = build_tokens("demo", brand, video, cfg, fake_fetch({"Space Grotesk": "✓"}), "vertical")
    geo = cfg.create.design.frames["vertical"]
    assert (tokens.frame, tokens.layout.width, tokens.layout.height) == ("vertical", 1080, 1920)
    assert tokens.layout.safe == geo.safe and tokens.layout.safe_margin == 120
    assert tokens.layout.caption_keepout_px == 1920 - geo.caption_band.y0
    assert tokens.type["headline"].size_px == round(72 * 1.5)
    # 1.5x the 24px label is 36px: under the 44px phone minimum
    assert any(
        "uppercase-label" in e and "vertical minimum" in e for e in token_errors(tokens, cfg.create.design)
    )


def test_a_frame_the_brand_has_no_sizes_for_is_an_error(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    with pytest.raises(ValueError, match="no 'vertical' sizes"):
        build_tokens("demo", _brand(root), _video(root), cfg, fake_fetch({}), "vertical")


def test_run_tokens_takes_the_frame_from_the_destination(root: Path):
    cfg = load_config(root / "config/lens.yaml")
    brand_dir = root / "brands/demo"
    (brand_dir / "tokens.json").write_text(json.dumps(_with_vertical_sizes(_brand(root))))
    (brand_dir / "video.yaml").write_text(yaml.safe_dump(_vertical(_video(root)), allow_unicode=True))
    (root / "projects/demo/brief.yaml").write_text("project: demo\nbrand: demo\ndestination: tiktok\n")
    _, tokens = run_tokens(root, "demo", cfg, fetch=fake_fetch({"Space Grotesk": "✓"}))
    assert tokens.frame == "vertical"
