import numpy as np
import pytest

from lens.frames.palette import palette
from lens.frames.phash import hamming, sequence_distance
from lens.media import native_frame_rate, scaled_size, snap_fps


def test_cfr_rate():
    r = native_frame_rate([i / 30 for i in range(120)])
    assert r.native_fps == 30.0 and not r.vfr


def test_ntsc_snaps():
    assert snap_fps(30000 / 1001) == 29.97
    assert snap_fps(24000 / 1001) == 23.976
    assert snap_fps(12.5) == 12.5


def test_vfr_detected_but_native_rate_kept():
    # every 5th frame dropped: durations 1/30 mostly, 2/30 sometimes
    times = [n / 30 for n in range(150) if n % 5 != 4]
    r = native_frame_rate(times)
    assert r.native_fps == 30.0 and r.vfr


def test_rate_fallback():
    assert native_frame_rate([], fallback=25.0).native_fps == 25.0


@pytest.mark.parametrize(
    "src, max_w, out",
    [
        ((1920, 1080), 1280, (1280, 720)),
        ((640, 360), 1280, (640, 360)),
        ((1080, 1920), 1280, (1080, 1920)),
        ((1921, 1081), 960, (960, 540)),
    ],
)
def test_scaled_size(src, max_w, out):
    assert scaled_size(*src, max_w) == out


def test_palette_recovers_two_colours():
    rng = np.random.default_rng(1)
    a = np.tile([228, 87, 46], (3000, 1)) + rng.normal(0, 2, (3000, 3))
    b = np.tile([30, 42, 59], (1000, 1)) + rng.normal(0, 2, (1000, 3))
    result = palette(np.vstack([a, b]), k=6)
    assert len(result) == 2
    (hex1, share1), (hex2, _share2) = result
    assert hex1 == "#e4572e" and abs(share1 - 0.75) < 0.01
    assert hex2 == "#1e2a3b"


def test_phash_distance():
    assert hamming("ffffffffffffffff", "0000000000000000") == 64
    assert sequence_distance(["00ff00ff00ff00ff"], ["00ff00ff00ff00fe"]) == 1.0
