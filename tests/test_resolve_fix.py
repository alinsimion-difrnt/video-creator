import numpy as np
import pytest

from create.footage.resolve_fix import (
    apply_cdl,
    colour_mode,
    from_oklab,
    hue_chroma,
    oklab,
    skin_lut,
    skin_stats,
    skin_transform,
    suggest_cdl,
)
from lens.config import load_config

CFG = load_config().create.footage.resolve


def lab_colour(L: float, hue: float, chroma: float) -> np.ndarray:
    lab = np.array([L, chroma * np.cos(np.radians(hue)), chroma * np.sin(np.radians(hue))])
    return from_oklab(lab[None, :])[0]


def test_colour_mode_reads_dji_baked_tag() -> None:
    dji = {"com.apple.quicktime.filterBaked": "1", "com.apple.quicktime.filterID": "AppleLog-Rec709"}
    assert colour_mode(dji) == "baked_rec709"
    assert colour_mode({"com.apple.quicktime.filterID": "AppleLog"}) == "apple_log"
    assert colour_mode({}) == "unknown"


def test_oklab_round_trip() -> None:
    rgb = np.array([[0.2, 0.5, 0.8], [0.7, 0.45, 0.4], [0.5, 0.5, 0.5]])
    assert np.allclose(from_oklab(oklab(rgb)), rgb, atol=1e-6)


def test_skin_transform_leaves_neutrals_alone() -> None:
    greys = np.linspace(0.02, 0.98, 12)[:, None].repeat(3, axis=1)
    assert np.allclose(skin_transform(greys, CFG), greys, atol=1e-6)


def test_skin_transform_moves_camera_skin_to_target() -> None:
    camera_skin = lab_colour(0.61, 36.0, 0.070)  # what the DJI takes measure
    h0, _ = hue_chroma(oklab(camera_skin[None, :]))
    h1, c1 = hue_chroma(oklab(skin_transform(camera_skin[None, :], CFG)))
    assert abs(h1[0] - CFG.skin_hue) < abs(h0[0] - CFG.skin_hue)
    assert abs(h1[0] - CFG.skin_hue) <= CFG.skin_hue_tol
    assert abs(c1[0] - CFG.skin_chroma) <= CFG.skin_chroma_tol


def test_skin_transform_protects_saturated_logo_red_and_greens() -> None:
    logo = lab_colour(0.6, 29.0, 0.22)
    plant = lab_colour(0.5, 135.0, 0.10)
    both = np.stack([logo, plant])
    assert np.allclose(skin_transform(both, CFG), both, atol=1e-6)


def test_skin_lut_is_identity_on_the_grey_axis() -> None:
    lut = skin_lut(CFG)
    n = CFG.lut_size
    assert lut.shape == (n**3, 3)
    # .cube order: red varies fastest; the grey axis is index i * (1 + n + n^2)
    grey = lut[[i * (1 + n + n * n) for i in range(n)]]
    assert np.allclose(grey, np.linspace(0, 1, n)[:, None].repeat(3, axis=1), atol=1e-6)


def test_skin_stats_reads_a_skin_patch() -> None:
    frame = np.full((40, 40, 3), 0.77)
    frame[10:30, 10:30] = lab_colour(0.62, 40.0, 0.06)
    stats = skin_stats(frame, (0.25, 0.75, 0.25, 0.75))
    assert stats["hue"] == pytest.approx(40.0, abs=0.5)
    assert stats["chroma"] == pytest.approx(0.06, abs=0.002)


def test_suggest_cdl_hits_black_white_and_balance_targets() -> None:
    rng = np.random.default_rng(0)
    h, w = 200, 100
    luma = rng.uniform(0.13, 0.815, size=(h, w))
    frame = np.stack([luma, luma, luma], axis=-1)
    wall = (0.05, 0.20, 0.05, 0.20)
    frame[: int(0.2 * h), : int(0.2 * w)] = [0.737, 0.713, 0.679]  # the DJI take's warm wall
    regions = {"wall": wall, "shirt": wall, "face": (0.4, 0.6, 0.4, 0.6)}
    cdl = suggest_cdl(frame, CFG.model_copy(update={"regions": regions}))
    out = apply_cdl(frame, cdl)
    y = out @ np.array([0.2126, 0.7152, 0.0722])
    assert np.percentile(y, 1) == pytest.approx(CFG.black, abs=0.02)
    assert np.percentile(y, 99) == pytest.approx(CFG.white, abs=0.03)
    wall_rgb = out[: int(0.2 * h), : int(0.2 * w)].reshape(-1, 3).mean(0)
    assert wall_rgb[0] / wall_rgb[1] == pytest.approx(CFG.white_rg, abs=0.01)
    assert wall_rgb[2] / wall_rgb[1] == pytest.approx(CFG.white_bg, abs=0.01)
