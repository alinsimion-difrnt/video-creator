"""Where the presenter's face is at a moment of the edit, in output pixels (from F5 framing).

One lookup for every consumer (captions in burn, overlays, layout poses, reels, QA). A time before the first
or past the last segment uses the nearest segment, so all of them agree at the clip's ends.
"""

from __future__ import annotations

from lens.schemas.create import Edl, Framing

Box = tuple[float, float, float, float]  # x0, y0, x1, y1


def segment_index(t: float, edl: Edl) -> int:
    """The edit segment playing at `t` seconds (the nearest one outside the edit)."""
    frame_t = round(t * edl.fps)
    for k, s in enumerate(edl.segments):
        if s.rec_in <= frame_t < s.rec_in + s.src_out - s.src_in:
            return k
    return 0 if frame_t < edl.segments[0].rec_in else len(edl.segments) - 1


def face_box(t: float, edl: Edl, framing: Framing, width: int) -> Box | None:
    """The face at `t` in output pixels (the segment's full-frame crop scaled to `width`), or None."""
    seg = framing.segments[segment_index(t, edl)]
    if seg.face is None:
        return None
    fx, fy, fw, fh = seg.face
    k = width / seg.full.w
    return (
        (fx - seg.full.x) * k,
        (fy - seg.full.y) * k,
        (fx + fw - seg.full.x) * k,
        (fy + fh - seg.full.y) * k,
    )
