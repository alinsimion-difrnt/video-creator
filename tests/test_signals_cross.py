from pytest import approx

from lens.signals import _span_offset


def test_sfx_inside_a_transition_is_at_the_scene_change() -> None:
    spans = [(0.0, 0.0), (9.5, 9.9), (20.0, 20.0)]
    assert _span_offset(9.7, spans) == 0.0  # mid-dissolve
    assert _span_offset(9.95, spans) == approx(0.05)  # just after the clean frame
    assert _span_offset(9.4, spans) == approx(-0.1)  # just before the dissolve starts
    assert _span_offset(19.9, spans) == approx(-0.1)  # a hard cut is a point
    assert _span_offset(0.14, spans) == approx(0.14)
