"""Props and effects for presenter reels (ADR 0027): characters in the room, and effects on the presenter.

A prop lives in room space: positions are pixels on the take's master, so a prop stays on the couch through
the push-in, punch-ins, layout moves and jump cuts (each cut has its own crop, F5 framing). The page gets one
room transform per edit segment (master -> frame) and each prop's moves in master pixels. Named spots
(`lap`, `left`, `shoulder_right`...) are offsets from the take's median face, in face sizes (config
`create.footage.reel.props.anchors`); the prop's bottom centre sits on the spot.

Code times everything from the timeline's words: a prop enters as its first word starts and has left by the
end of its last; a beat happens as its word starts (a move arrives by the end of the word).
"""

from __future__ import annotations

import itertools
import math
import statistics
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from create.footage.framing import segment_index
from create.footage.props_art import Art
from lens.schemas.config import CreateFrame, ReelProps
from lens.schemas.create import Edl, Framing, ReelFx, ReelPlan, ReelProp, Timeline

Face = tuple[float, float, float, float]  # centre x, centre y, width, height on the master


@dataclass(frozen=True)
class Room:
    """One edit segment's map from master pixels to frame pixels: frame = master * k + (tx, ty)."""

    t0: float
    t1: float
    take: str
    k: float
    tx: float
    ty: float
    crop: tuple[float, float, float, float]  # x0, y0, x1, y1: what of the master is on screen
    mw: int
    mh: int


def rooms(
    edl: Edl, framing: Framing | None, masters: dict[str, tuple[int, int]], frame: CreateFrame
) -> list[Room]:
    """Per edit segment: the F5 crop scaled to the frame, or (without framing) the master scaled to cover
    the frame and centred, as `create edit` cuts it."""
    w, h = frame.width, frame.height
    out = []
    for n, s in enumerate(edl.segments):
        mw, mh = masters.get(s.take, (w, h))
        t0, t1 = s.rec_in / edl.fps, (s.rec_in + s.src_out - s.src_in) / edl.fps
        if framing is not None:
            c = framing.segments[n].full
            k = w / c.w
            out.append(
                Room(
                    round(t0, 4),
                    round(t1, 4),
                    s.take,
                    k,
                    -c.x * k,
                    -c.y * k,
                    (c.x, c.y, c.x + c.w, c.y + c.h),
                    mw,
                    mh,
                )
            )
            continue
        k = max(w / mw, h / mh)
        tx, ty = (w - mw * k) / 2, (h - mh * k) / 2
        out.append(
            Room(
                round(t0, 4),
                round(t1, 4),
                s.take,
                k,
                tx,
                ty,
                (-tx / k, -ty / k, (w - tx) / k, (h - ty) / k),
                mw,
                mh,
            )
        )
    return out


def room_at(t: float, rs: list[Room], edl: Edl) -> Room:
    return rs[segment_index(t, edl)]


def take_face(framing: Framing | None, take: str, mw: int, mh: int) -> Face:
    """The presenter's median face on a take's master; without one, a guess at a seated presenter."""
    faces = [s.face for s in (framing.segments if framing else []) if s.take == take and s.face]
    if not faces:
        return (mw / 2, mh * 0.33, mw * 0.24, mw * 0.3)
    x, y, fw, fh = (statistics.median(f[k] for f in faces) for k in range(4))
    return (x + fw / 2, y + fh / 2, fw, fh)


def segment_face(framing: Framing | None, n: int, fallback: Face) -> Face:
    if framing is None or framing.segments[n].face is None:
        return fallback
    x, y, fw, fh = framing.segments[n].face  # type: ignore[misc]
    return (x + fw / 2, y + fh / 2, fw, fh)


def place(
    at: Any,
    face: Face,
    mw: int,
    mh: int,
    anchors: dict[str, tuple[float, float]],
    room: Room | None = None,
) -> tuple[float, float]:
    """A spot on the master in pixels: (x, y) shares of the master, a named spot by the face, or shares of the
    shot on screen (`{frame: [x, y]}`, through `room`'s crop)."""
    frame_at = getattr(at, "frame", None) or (at.get("frame") if isinstance(at, dict) else None)
    if frame_at is not None:
        if room is None:
            raise ValueError("a {frame: [x, y]} spot needs the shot it is in")
        x0, y0, x1, y1 = room.crop
        return (round(x0 + frame_at[0] * (x1 - x0), 1), round(y0 + frame_at[1] * (y1 - y0), 1))
    if isinstance(at, str):
        if at not in anchors:
            raise ValueError(f"unknown spot {at!r} (config create.footage.reel.props.anchors)")
        dx, dy = anchors[at]
        cx, cy, fw, fh = face
        return (round(cx + dx * fw, 1), round(cy + dy * fh, 1))
    x, y = at
    return (round(x * mw, 1), round(y * mh, 1))


def clamp(
    pt: tuple[float, float],
    rs: list[Room],
    w: float,
    h: float,
    bottom: float | None = None,
    right: float | None = None,
) -> tuple[float, float]:
    """A named spot kept on screen in every shot `rs` (the tightest crop): a lap or floor below the frame
    edge comes up to it, a spot past a side comes in."""
    x0 = max(r.crop[0] for r in rs) + w * 0.55
    x1 = min(r.crop[2] for r in rs) - w * 0.55
    y0 = max(r.crop[1] for r in rs) + h * 1.05
    y1 = min(r.crop[3] for r in rs) - 0.03 * (rs[0].crop[3] - rs[0].crop[1])
    if bottom is not None:  # above the platform's bottom UI (frame pixels -> master pixels per shot)
        y1 = min(y1, min((bottom - r.ty) / r.k for r in rs))
    if right is not None:  # left of the platform's action rail
        x1 = min(x1, min((right - r.tx) / r.k for r in rs) - w * 0.55)
    x = min(max(pt[0], x0), x1) if x0 <= x1 else (x0 + x1) / 2
    y = min(max(pt[1], y0), y1) if y0 <= y1 else y1
    return (round(x, 1), round(y, 1))


def spans(rs: list[Room], a: float, b: float) -> list[Room]:
    """The shots between `a` and `b` (at least the one at `a`)."""
    out = [r for r in rs if r.t1 > a and r.t0 < b]
    return out or [min(rs, key=lambda r: abs(r.t0 - a))]


def _words(timeline: Timeline) -> dict[int, tuple[float, float]]:
    return {w.i: (w.start_s, w.end_s) for w in timeline.words}


def _need(words: dict[int, tuple[float, float]], i: int, what: str) -> tuple[float, float]:
    if i not in words:
        raise ValueError(f"reel.yaml {what}: word {i} is not in the timeline")
    return words[i]


def offscreen(side: str, room: Room, width: float, y: float) -> tuple[float, float]:
    """Just past the visible crop's left or right edge, in master pixels."""
    x0, _, x1, _ = room.crop
    return (x0 - width * 0.7, y) if side == "left" else (x1 + width * 0.7, y)


def _to_cut(t: float, d: float, rs: list[Room], edl: Edl, least: float) -> float:
    """A tag's or bubble's stay, ended at the next cut when it has shown `least` s by then: across a reframe
    it was stranded at the frame edge (r09, the Pixie tag on the lunge)."""
    end = room_at(t, rs, edl).t1
    return round(d if end - t < least or end >= t + d else end - t, 3)


def prop_track(
    p: ReelProp,
    timeline: Timeline,
    edl: Edl,
    framing: Framing | None,
    rs: list[Room],
    art: Art,
    cfg: ReelProps,
    duration: float,
) -> dict[str, Any]:
    """Everything the page needs to play one prop: when it is shown, where it goes, what it does."""
    words = _words(timeline)
    # visuals lead the word a touch; never at 0 itself (r06: the cold open began without its cat)
    t0 = max(1 / 30, _need(words, p.word, f"prop {p.id}")[0] - cfg.lead_s)
    if p.from_start:  # a loop's start shows what its end did (n09); at 0 itself the page never shows it
        t0 = 1 / 30
    t1 = min(_need(words, p.until, f"prop {p.id}")[1], duration - 0.04)
    if p.to_end:
        t1 = duration
    r0 = room_at(t0, rs, edl)
    face = take_face(framing, r0.take, r0.mw, r0.mh)
    w = p.size * r0.mw
    h = w * art.aspect
    x, y = place(p.at, face, r0.mw, r0.mh, cfg.anchors, r0)
    rest_end = _need(words, p.beats[0].word, "")[0] if p.beats else t1
    if isinstance(p.at, str):
        x, y = clamp((x, y), spans(rs, t0, rest_end), w, h, cfg.safe_bottom, cfg.safe_right)
    moves: list[dict[str, Any]] = []  # {t, d, x, y, ease, gait}
    gait = "walk" if art.frames else None
    # entrance
    enter: dict[str, Any] = {"t": round(t0, 3), "kind": p.enter, "d": 0.4}
    if p.enter in ("walk_left", "walk_right", "slide_left", "slide_right"):
        side = "left" if p.enter.endswith("left") else "right"
        sx, _ = offscreen(side, r0, w, y)
        g = "walk" if art.frames else ("hop" if art.rig else "slide")
        d = travel_s(abs(x - sx), w, g, cfg)  # from the distance and the gait's speed: feet do not slide
        moves.append({"t": round(t0, 3), "d": 0.0, "x": round(sx, 1), "y": y, "ease": "none"})
        moves.append(
            {
                "t": round(t0, 3),
                "d": round(d, 3),
                "x": x,
                "y": y,
                "ease": "none" if p.enter.startswith("walk") else "power2.out",
                "gait": ("hop" if art.rig else gait) if p.enter.startswith("walk") else None,
            }
        )
        enter["d"] = round(d, 3)
    else:
        moves.append({"t": round(t0, 3), "d": 0.0, "x": x, "y": y, "ease": "none"})
    if p.enter == "drop":
        enter["d"] = 0.6
    styles: list[dict[str, Any]] = [{"t": round(t0, 3), "style": p.style}]
    acc: list[dict[str, Any]] = [{"t": round(t0, 3), "add": list(p.accessories), "remove": []}]
    acts: list[dict[str, Any]] = []
    tags: list[dict[str, Any]] = []
    carry: dict[str, Any] | None = None
    holds: list[dict[str, Any]] = []
    rides: list[dict[str, Any]] = []
    follows: list[dict[str, Any]] = []
    gags: list[dict[str, Any]] = []
    riding = False

    def gait_now() -> str | None:
        if art.rig:
            return "boat" if riding else "hop"
        return gait

    cur = (x, y)
    for b in p.beats:
        bs, be = _need(words, b.word, f"prop {p.id} beat")
        bs = max(t0, bs - cfg.lead_s)
        if b.style:
            styles.append({"t": round(bs, 3), "style": b.style})
        if b.add or b.remove:
            acc.append({"t": round(bs, 3), "add": list(b.add), "remove": list(b.remove)})
        if b.ride is not None:
            riding = b.ride == "boat"
            rides.append({"t": round(bs, 3), "ride": b.ride})
        if b.hold is not None:
            holds.append({"t": round(bs, 3), "hold": b.hold})
        targets = ([b.move] if b.move is not None else []) + list(b.path)
        leg = max(cfg.move_s, be - bs) if len(targets) == 1 else cfg.path_leg_s
        g_now = gait_now()
        nxt = next((x for x in p.beats if x.word > b.word and x.carry), None)
        if nxt is not None and g_now == "walk" and targets:  # a walk that cannot arrive in time becomes a run
            avail = max(0.3, _need(words, nxt.word, "")[0] - cfg.lead_s - bs)
            rb0 = room_at(bs, rs, edl)
            tx_, ty_ = place(
                targets[0], take_face(framing, rb0.take, rb0.mw, rb0.mh), rb0.mw, rb0.mh, cfg.anchors, rb0
            )
            if travel_s(math.hypot(tx_ - cur[0], ty_ - cur[1]), w, "walk", cfg) > avail:
                g_now = "run"
        # each leg starts where the previous one ended (legs differ in length); the first waits for any move
        # still running (v04: the run to Fred started mid walk-in, and two tweens fought over her position)
        tk = max([bs] + [m["t"] + m["d"] for m in moves])
        base_leg = leg
        for target in targets:
            rb = room_at(bs, rs, edl)
            nx, ny = place(target, take_face(framing, rb.take, rb.mw, rb.mh), rb.mw, rb.mh, cfg.anchors, rb)
            if isinstance(target, str):
                nx, ny = clamp((nx, ny), spans(rs, bs, t1), w, h, cfg.safe_bottom, cfg.safe_right)
            leg = base_leg
            g_leg = g_now
            if g_now in ("walk", "run") and abs(ny - cur[1]) > h * cfg.jump_rise:
                g_leg = "jump"  # a walker does not walk up or down through the air: it jumps (lab v08)
            if g_leg:  # a gaited move takes as long as its legs need at that gait's speed
                leg = max(
                    base_leg if len(targets) > 1 else 0.0,
                    travel_s(math.hypot(nx - cur[0], ny - cur[1]), w, g_leg, cfg),
                )
            moves.append(
                {
                    "t": round(tk, 3),
                    "d": round(leg, 3),
                    "x": nx,
                    "y": ny,
                    "ease": ("none" if g_leg in ("walk", "run", "jump") else "power1.inOut")
                    if g_leg
                    else ("power2.inOut" if len(targets) == 1 else "sine.inOut"),
                    "gait": g_leg,
                    "dir": 1 if nx >= cur[0] else -1,
                }
            )
            cur = (nx, ny)
            tk += leg
        if b.gag:  # a pixel item beside it (or instead of it) until its next gag, at most 3 s
            gnext = [x for x in p.beats if x.word > b.word and x.gag]
            end = _need(words, gnext[0].word, "")[0] - cfg.lead_s if gnext else t1
            gags.append(
                {"t": round(bs, 3), "d": round(b.gag_s or min(3.0, max(0.6, end - bs)), 3), "name": b.gag}
            )
        if b.follow:  # carried by a hand until the next beat (keyed from the pose later: apply_follow)
            later = [x for x in p.beats if x.word > b.word]
            if b.follow == "flee":  # ahead of the hands until its exit (keyed in reel.py from the pose)
                later = []
            if b.follow == "palm":  # held on the palm through style and accessory beats
                later = [x for x in later if x.move is not None or x.path or x.follow]
            end = _need(words, later[0].word, "")[0] - cfg.lead_s if later else t1
            follows.append({"t": round(bs, 3), "end": round(max(bs + 0.2, end), 3), "by": b.follow})
        if b.do:
            acts.append({"t": round(bs, 3), "do": b.do})
        if b.tag:  # after the entrance: a tag on a prop still walking in was cut by the frame edge (v09)
            ts = max(bs, t0 + enter["d"])
            tags.append(
                {
                    "t": round(ts, 3),
                    "kind": "tag",
                    "text": b.tag,
                    "d": _to_cut(ts, cfg.tag_s, rs, edl, cfg.tag_cut_least_s),
                }
            )
        if b.say:
            tags.append(
                {
                    "t": round(bs, 3),
                    "kind": "say",
                    "text": b.say,
                    "d": _to_cut(bs, 1.6, rs, edl, cfg.tag_cut_least_s),
                }
            )
        if b.emote:  # a big symbol over its head (tournament n10: expressions read as specks at his size)
            tags.append({"t": round(bs, 3), "kind": "emote", "text": b.emote, "d": 0.9})
        if b.carry:
            carry = {"t": round(bs, 3), "id": b.carry, "word": b.word, "n_moves": len(moves)}
    from create.pixel.items import PLACE

    swaps = [g for g in gags if PLACE.get(g["name"]) == "swap"]
    # a swap ends where the next swap begins (r04: the dog's "back to Fred" fired during the bird, so both
    # showed); items beside him may overlap
    for sw, nsw in zip(swaps, [*swaps[1:], None], strict=False):  # empty swaps: nothing
        if nsw is not None and sw["t"] + sw["d"] > nsw["t"]:
            sw["d"] = round(max(0.3, nsw["t"] - sw["t"]), 3)
    if carry is not None:
        # the grab happens when the carrier is there, never from across the room (v02), and after its pounce
        # (a pounce over the end of a walk skated: audit). Only moves up to the carry's beat count (audit).
        arrive = max(m["t"] + m["d"] for m in moves[: carry.pop("n_moves")])
        if p.enter == "none" and carry["word"] == p.word:  # it is there with the prey already (a cold open:
            # r05's pounce delay showed an empty frame first)
            carry["t"] = round(t0, 3)
        else:
            carry["t"] = round(max(carry["t"], arrive + once_s(art.frames, art.fps, "pounce")), 3)
    # exit: ends as the last word ends
    exit_d = cfg.exit_s if p.exit in ("run_left", "run_right", "swim_left", "swim_right", "fall") else 0.35
    if p.exit in ("run_left", "run_right", "swim_left", "swim_right"):  # the run's length from its distance
        re0 = room_at(t1 - exit_d, rs, edl)
        ex0, _ = offscreen("left" if p.exit.endswith("left") else "right", re0, w, cur[1])
        g = "run" if art.frames else (gait_now() or "swim")
        # a short dash is stretched to the shortest readable exit, not cancelled (r11: a 0.2 s bolt off the
        # frame was dropped and Pixie sat still while Robert lunged)
        exit_d = max(cfg.min_exit_s, travel_s(abs(ex0 - cur[0]), w, g, cfg))
    te = max(t0 + float(enter["d"]) + 0.1, t1 - exit_d)
    # the exit waits for the last beat to finish (a move, a carry): two motions must never fight over the
    # prop (v01: the run-off began before the walk to Fred ended). It may run a little past its last word.
    last = max(
        [m["t"] + m["d"] for m in moves] + [c["t"] + 0.3 for c in [carry] if c] + [a["t"] + 0.4 for a in acts]
    )
    if last > te:
        te = last
    if te + exit_d > t1:  # it runs a little past its last word rather than lose its exit (r11: a cold open)
        t1 = min(duration - 0.04, te + exit_d)
    exit_: dict[str, Any] = {"t": round(te, 3), "kind": p.exit, "d": round(t1 - te, 3)}
    if (
        p.exit != "none" and exit_["d"] < cfg.min_exit_s - 1e-3
    ):  # no room left: stay to the end (v04: a 2-frame run)
        exit_ = {"t": round(te, 3), "kind": "none", "d": 0.0, "cut": True}
        t1 = duration
    if exit_["kind"] in ("run_left", "run_right", "swim_left", "swim_right"):
        re = room_at(te, rs, edl)
        side = "left" if p.exit.endswith("left") else "right"
        ex, _ = offscreen(side, re, w, cur[1])
        moves.append(
            {
                "t": round(te, 3),
                "d": round(t1 - te, 3),
                "x": round(ex, 1),
                "y": cur[1],
                "ease": "power1.in",
                "gait": "run" if art.frames else gait_now(),
                "dir": 1 if side == "right" else -1,
            }
        )
    return {
        "id": p.id,
        "t0": round(t0, 3),
        "t1": round(t1, 3),
        "w": round(w, 1),
        "h": round(h, 1),
        "aspect": art.aspect,
        "files": art.styles,
        "frames": art.frames,
        "pixel": art.pixel,
        "points": art.points | {k: tuple(v) for k, v in p.points.items()},
        "flip": p.flip,
        "idle": p.idle,
        "behind": p.behind,
        "enter": enter,
        "exit": exit_,
        "moves": moves,
        "styles": styles,
        "acc": acc,
        "acts": acts,
        "tags": tags,
        "carry": carry,
        "rig": art.rig,
        "holds": holds,
        "rides": rides,
        "follows": follows,
        "gags": gags,
        "colors": dict(p.colors),
    }


def apply_follow(
    track: dict[str, Any], f: dict[str, Any], path: list[tuple[float, float, float]], settle: float = 0.3
) -> None:
    """A prop carried by a hand (`follow: hand`): from `f["t"]` its bottom centre keeps its offset from the
    hand's palm (`path`: record time, master x, y), keyed every sample, until the hand's lowest point before
    `f["end"]`, where it is put down and stays. Moves that start before the release are replaced (a hand
    carry wins over a planned move); the prop's later moves start from where it was put down."""
    seg = [q for q in path if f["t"] <= q[0] <= f["end"]]
    if len(seg) < 2:
        return
    x0, y0 = position_at(track, f["t"])
    ox, oy = x0 - seg[0][1], y0 - seg[0][2]
    if f["by"] == "palm":  # standing on the palm from the start: no offset to settle
        ox = oy = 0.0
    else:
        release = max(range(len(seg)), key=lambda k: seg[k][2])  # lowest on screen: the put-down
        seg = seg[: release + 1]
    keep = [m for m in track["moves"] if m["d"] == 0 or m["t"] + m["d"] <= f["t"]]
    after = [m for m in track["moves"] if m["d"] > 0 and m["t"] >= seg[-1][0]]
    # he settles into the palm (his bottom on it) over the first part of the carry, then rides it
    span = max(1e-3, (seg[-1][0] - seg[0][0]) * settle)

    def at(q: tuple[float, float, float]) -> tuple[float, float]:
        k = max(0.0, 1 - (q[0] - seg[0][0]) / span)
        k = k * k * (3 - 2 * k)  # smoothstep: no snap at either end
        return (round(q[1] + ox * k, 1), round(q[2] + oy * k, 1))

    keyed = [
        {"t": round(a[0], 3), "d": round(b[0] - a[0], 3), "x": at(b)[0], "y": at(b)[1],
         "ease": "none", "gait": None, "follow": True}
        for a, b in itertools.pairwise(seg)
    ]  # fmt: skip
    track["moves"] = keep + keyed + after
    f["release"] = round(seg[-1][0], 3)


def apply_flee(
    track: dict[str, Any],
    f: dict[str, Any],
    lead: list[tuple[float, float]],
    gap: float,
    chase_s: float,
    duration: float,
    speed: float = 0.0,
) -> None:
    """A prop running from the presenter's hands (`follow: flee`): for `chase_s` from `f["t"]` (or to its
    planned exit, if later) it keeps `gap` of its widths ahead of the leading hand (`lead`: record time,
    master x of the hand nearest the exit side), only ever moving toward its exit. Then the exit runs it off
    from wherever the chase left it (r11: Pixie sat facing Robert while his hands passed her). `speed`: its
    own pace without a hand behind it, master px a second."""
    ex = track["exit"]
    if ex["kind"] not in ("run_left", "run_right"):
        return
    sign = -1 if ex["kind"] == "run_left" else 1
    end = min(max(ex["t"], f["t"] + chase_s), duration - 0.04 - ex["d"])
    seg = [q for q in lead if f["t"] <= q[0] <= end]
    if len(seg) < 2:
        return
    x0, y0 = position_at(track, f["t"])
    off = track["w"] * (0.5 + gap)
    keyed: list[dict[str, Any]] = []
    x, prev = x0, seg[0][0]
    for t, hx in seg[1:]:
        # it bolts at `speed` on its own and the hand pushes it faster (r11: waiting for the hand, Pixie
        # crossed Robert's whole body in two frames)
        want = (
            min(hx + sign * off, x + sign * speed * (t - prev))
            if sign < 0
            else max(hx + sign * off, x + sign * speed * (t - prev))
        )
        nx = min(x, want) if sign < 0 else max(x, want)
        if abs(nx - x) > 0.5:  # a step: it runs; otherwise it waits, watching the hand come
            keyed.append({"t": round(prev, 3), "d": round(t - prev, 3), "x": round(nx, 1), "y": y0,
                          "ease": "none", "gait": "run", "dir": sign})  # fmt: skip
            x = nx
        prev = t
    run = [m for m in track["moves"] if m["d"] > 0 and abs(m["t"] - ex["t"]) < 1e-3]  # the planned exit run
    keep = [m for m in track["moves"] if m not in run and (m["d"] == 0 or m["t"] + m["d"] <= f["t"])]
    exit_at = max(end, keyed[-1]["t"] + keyed[-1]["d"]) if keyed else end
    for m in run:
        m["t"] = round(exit_at, 3)
    track["moves"] = sorted(keep + keyed + run, key=lambda m: m["t"])
    ex["t"] = round(exit_at, 3)
    track["t1"] = round(min(duration - 0.04, exit_at + ex["d"]), 3)
    f["release"] = round(exit_at, 3)


def travel_s(dist: float, w: float, gait: str, cfg: ReelProps) -> float:
    """How long a move of `dist` master pixels takes at a gait's speed (body widths a second, config
    `speeds`): a walk cycle whose body travels faster than its feet step reads as skating."""
    speed = cfg.speeds.get(gait, cfg.speeds.get("slide", 2.0)) * max(w, 1.0)
    return round(min(cfg.max_travel_s, max(cfg.min_travel_s, dist / speed)), 3)


def state_at(track: dict[str, Any], t: float) -> tuple[str, list[str]]:
    """A prop's style and accessories at `t` (what a carrier shows in its mouth)."""
    style = track["styles"][0]["style"]
    for s in track["styles"]:
        if s["t"] <= t:
            style = s["style"]
    on: list[str] = []
    for a in track["acc"]:
        if a["t"] <= t:
            on = [x for x in on if x not in a["remove"]] + [x for x in a["add"] if x not in on]
    return style, on


def link_carries(tracks: list[dict[str, Any]], cfg: ReelProps) -> None:
    """A carried prop leaves where it is as it is picked up; the carrier shows it in its mouth from then on,
    in the look it had at that moment, sized as it was relative to the carrier."""
    by_id = {t["id"]: t for t in tracks}
    for t in tracks:
        c = t["carry"]
        if c is None:
            continue
        other = by_id[c["id"]]
        stop_short(t, other, c["t"], cfg)
        style, on = state_at(other, c["t"])
        photo = other["files"].get("photo") or next(iter(other["files"].values()))
        c.update(
            {
                "file": other["files"].get(style, photo),
                "acc": on,
                "pixel": style == "pixel",
                # at most 0.55 of the carrier: full size it stood in front of her face (lab v07, v08)
                "w_rel": round(min(cfg.carry_max, other["w"] / t["w"]), 3),
                "aspect": other["aspect"],
                "points": other["points"],
                "rig": other.get("rig", False),
                "style": style,
            }
        )
        other["t1"] = c["t"]  # it stays until it is snatched, even past its own `until` (v04: it left first)
        other["exit"] = {"t": c["t"], "kind": "snatched", "d": 0.0}
        # acting: the victim startles just before (anticipation for the viewer); the carrier crouches (a
        # sprite with a pounce plays it instead: sprite_schedule)
        other["acts"].append({"t": round(c["t"] - 0.35, 3), "do": "jump"})
        if "pounce" not in (t.get("frames") or {}):
            t["acts"].append({"t": round(c["t"] - 0.2, 3), "do": "squash"})


def stop_short(t: dict[str, Any], other: dict[str, Any], at: float, cfg: ReelProps) -> None:
    """A carrier's last move before a carry ends beside the prop it grabs, its mouth at the prop's near edge,
    not on top of it (v03: Pixie walked over Fred and stood in front of him before the grab)."""
    before = [m for m in t["moves"] if m["d"] > 0 and m["t"] <= at]
    if not before:
        return
    m = before[-1]
    prev = t["moves"][t["moves"].index(m) - 1]
    vic = [v for v in other["moves"] if v["t"] <= at] or other["moves"][:1]
    vx, vy = vic[-1]["x"], vic[-1]["y"]
    side = 1 if vx >= prev["x"] else -1  # the way it comes from
    m["x"] = round(vx - side * (t["w"] * cfg.approach[0] + other["w"] * cfg.approach[1]), 1)
    old_y = m["y"]
    m["y"] = vy  # on the prey's surface (v08: she grabbed a lap from the floor)
    for later in t["moves"][t["moves"].index(m) + 1 :]:  # the exit run leaves level, not sloping (audit)
        if later["y"] == old_y:
            later["y"] = vy
    if m.get("gait") in ("walk", "run") and abs(vy - prev["y"]) > t["h"] * cfg.jump_rise:  # a climb now: jump
        m["gait"], m["ease"] = "jump", "none"
    m["dir"] = side


def peek_y(alpha: Any, x: float, y: float, w: float, h: float, share: float) -> float:
    """A prop behind the presenter, standing at bottom-centre (x, y): raise it until `share` of its box shows
    outside the presenter's matte (`alpha`). All in the matte's pixels, which are frame pixels. At the
    shoulder spot the matte hid all but a sliver of Pixie (lab v15); raised, she peeks over the shoulder."""
    rows, cols = alpha.shape
    x0, x1 = max(0, int(x - w / 2)), min(cols, int(x + w / 2))
    for k in range(16):
        yy = y - k * 0.1 * h
        y0, y1 = max(0, int(yy - h)), min(rows, int(yy))
        if x1 <= x0 or y1 <= y0:
            break
        if float((alpha[y0:y1, x0:x1] < 128).mean()) >= share:
            return round(yy, 1)
    return y


def visible_share(track: dict[str, Any], rs: list[Room]) -> list[tuple[float, float]]:
    """(time, share of the prop's box on screen) at each resting place, per segment it spans: for
    `create reel --check` (a prop on the couch must not sit outside a punch-in's crop)."""
    out = []
    rests = [m for m in track["moves"] if m.get("gait") != "run"]
    for k, m in enumerate(rests):
        a = m["t"] + m["d"]
        b = rests[k + 1]["t"] if k + 1 < len(rests) else track["exit"]["t"]
        if b - a < 0.3:
            continue
        x0, x1 = m["x"] - track["w"] / 2, m["x"] + track["w"] / 2
        y0, y1 = m["y"] - track["h"], m["y"]
        for r in rs:
            if r.t1 <= a or r.t0 >= b:
                continue
            cx0, cy0, cx1, cy1 = r.crop
            iw = max(0.0, min(x1, cx1) - max(x0, cx0))
            ih = max(0.0, min(y1, cy1) - max(y0, cy0))
            out.append((round(max(a, r.t0), 3), round(iw * ih / ((x1 - x0) * (y1 - y0)), 3)))
    return out


def position_at(track: dict[str, Any], t: float) -> tuple[float, float]:
    """Where a prop stands at `t` (its last move's target)."""
    x, y = track["moves"][0]["x"], track["moves"][0]["y"]
    for m in track["moves"]:
        if m["t"] <= t:
            x, y = m["x"], m["y"]
    return (x, y)


def fx_track(
    fx: list[ReelFx],
    timeline: Timeline,
    duration: float,
    edl: Edl,
    framing: Framing | None,
    rs: list[Room],
    tracks: list[dict[str, Any]] | None = None,
    anchors: dict[str, tuple[float, float]] | None = None,
) -> list[dict[str, Any]]:
    """Effects with their times; face effects (anime) get the face per segment on the master."""
    words = _words(timeline)
    out = []
    for e in fx:
        t0 = _need(words, e.word, f"fx {e.kind}")[0]
        t1 = _need(words, e.until, f"fx {e.kind}")[1] if e.until is not None else None
        if (
            e.kind == "blackhole"
        ):  # the silence between two words: from the end of one to the start of the next
            if t1 is None:
                raise ValueError("fx blackhole needs until (the word that ends the silence)")
            a, b = words[e.word][1], words[e.until][0] if e.until is not None else duration
            d = {"t0": round(a, 3), "t1": round(b, 3)}
        elif e.kind == "endcard":
            d = {
                "t0": round(min(t0 + float(e.spec.get("delay_s", 0.0)), duration - 0.5), 3),
                "t1": round(duration, 3),
            }
        elif e.kind == "fade_black":
            end = t1 if t1 is not None else duration
            busy = max([tr["t1"] for tr in tracks or []] + [0.0])
            t0 = min(max(t0, busy - 0.25), duration - 0.4)  # the action finishes before the black (v02)
            d = {"t0": round(t0, 3), "t1": round(min(max(end, t0 + 0.4), duration), 3)}  # never ends first
        elif t1 is None:
            if e.kind in ("shake", "flash", "glitch"):  # a hit on a grab's word lands on the grab (v04)
                cs = [tr["carry"] for tr in tracks or [] if tr.get("carry")]
                grabs = [c["t"] for c in cs if c.get("word") == e.word]
                t0 = max([t0, *grabs])
            hold = {
                "alchemy": 2.4,
                "automail": duration,
                "look": duration,
                "hud": duration,
                "panels": duration,
                "wall": duration,
                "burst": 0.9,
                "rewind": float(e.spec.get("d", 0.5)),
            }.get(e.kind, 0.4)
            t0 += float(e.spec.get("offset_s", 0.0)) if e.kind == "rewind" else 0.0
            d = {"t0": round(t0, 3), "t1": round(min(t0 + hold, duration), 3)}
        else:
            d = {"t0": round(t0, 3), "t1": round(min(t1, duration), 3)}
        item: dict[str, Any] = {"kind": e.kind, "spec": e.spec} | d
        if e.kind == "anime":
            faces = []
            for n, r in enumerate(rs):
                if r.t1 <= d["t0"] or r.t0 >= d["t1"]:
                    continue
                fb = take_face(framing, r.take, r.mw, r.mh)
                cx, cy, fw, fh = segment_face(framing, n, fb)
                faces.append(
                    {
                        "t0": max(r.t0, d["t0"]),
                        "cx": round(cx, 1),
                        "cy": round(cy, 1),
                        "fw": round(fw, 1),
                        "fh": round(fh, 1),
                    }
                )
            item["faces"] = faces
        if e.kind == "panels":  # its freeze-frames: the record times of its words (frames cut in reel.py)
            item["t0"] = round(t0 + float(e.spec.get("delay_s", 0.0)), 3)  # shots may come after its word
            item["shots"] = [
                round(_need(words, int(w), "fx panels shot")[0] + float(e.spec.get("offset_s", 0.3)), 3)
                for w in e.spec.get("words", [])
            ]
        if e.kind == "freeze":  # the frozen moment and its length
            a = t0 + float(e.spec.get("offset_s", 0.0))
            item |= {"t0": round(a, 3), "t1": round(min(a + float(e.spec.get("dur", 1.6)), duration), 3)}
        if e.kind == "clone":  # where its footage comes from, on the edited clock
            item["src_t"] = round(
                _need(words, int(e.spec.get("from_word", e.word)), "fx clone")[0]
                + float(e.spec.get("delay_s", 0)),
                3,
            )
        if e.kind == "wall":  # its words on their times (the surface is measured in reel.py)
            item["steps"] = [
                [round(_need(words, int(w), "fx wall step")[0], 3), str(text)]
                for w, text in e.spec.get("steps", [])
            ]
        if e.kind == "hud":  # its steps on their words
            item["steps"] = [
                [round(_need(words, int(w), "fx hud step")[0], 3), str(text)]
                for w, text in e.spec.get("steps", [])
            ]
        if e.kind == "alchemy":
            item |= alchemy_place(e, t0, tracks or [], rs, edl, framing, anchors or {})
        out.append(item)
    return out


def alchemy_place(
    e: ReelFx,
    t: float,
    tracks: list[dict[str, Any]],
    rs: list[Room],
    edl: Edl,
    framing: Framing | None,
    anchors: dict[str, tuple[float, float]],
) -> dict[str, float]:
    """The circle's centre on the floor (master pixels) and radius: under a prop, or at a spot."""
    at = e.spec.get("at", "lap")
    by_id = {tr["id"]: tr for tr in tracks}
    r = room_at(t, rs, edl)
    if isinstance(at, str) and at in by_id:
        x, y = position_at(by_id[at], t)
        rad = by_id[at]["w"] * float(e.spec.get("size", 0.9))
    else:
        x, y = place(at, take_face(framing, r.take, r.mw, r.mh), r.mw, r.mh, anchors, r)
        rad = r.mw * float(e.spec.get("size", 0.2))
    return {"x": round(x, 1), "y": round(y, 1), "r": round(rad, 1)}


def room_data(rs: list[Room]) -> list[dict[str, Any]]:
    return [
        {"t0": r.t0, "k": round(r.k, 6), "tx": round(r.tx, 2), "ty": round(r.ty, 2), "mw": r.mw, "mh": r.mh}
        for r in rs
    ]


def needs_matte(plan: ReelPlan) -> bool:
    """Props behind the presenter and a black hole that pulls him in need the matte (`create matte`);
    background swaps use it when present."""
    return any(p.behind for p in plan.props) or any(
        (e.kind == "blackhole" and e.spec.get("presenter")) or e.kind == "clone" for e in plan.fx
    )


SPRITE_ACTS = {"wave": 1.2, "clap": 1.0}  # pixel Fred's acts with frames, and how long they play


def once_s(cycles: dict[str, list[str]] | None, fps: Mapping[str, float] | None, anim: str) -> float:
    """How long an animation plays once at its frame rate (0 when the art has no such frames)."""
    seq = (cycles or {}).get(anim) or []
    return len(seq) / (fps or {}).get(anim, 10) if seq else 0.0


STEP = 1 / 24  # the schedule's sampling step (finer than any sprite's frame rate)


def style_combos(track: dict[str, Any], style: str) -> list[tuple[str, ...]]:
    """The accessory sets Fred wears while in `style` (pixel or toon3d: one frame set each)."""
    out: list[tuple[str, ...]] = []
    for t in sorted({track["t0"], *(s["t"] for s in track["styles"]), *(a["t"] for a in track["acc"])}):
        now, on = state_at(track, t)
        combo = tuple(sorted(on))
        if now == style and combo not in out:
            out.append(combo)
    return out


def pixel_combos(track: dict[str, Any]) -> list[tuple[str, ...]]:
    return style_combos(track, "pixel")


SET_PREFIX = {"pixel": "px-", "toon3d": "3d-"}  # Fred's styles drawn as frames, and their set keys


def riding_at(track: dict[str, Any], t: float) -> bool:
    on = False
    for r in track.get("rides") or []:
        if r["t"] <= t:
            on = r["ride"] == "boat"
    return on


def sprite_schedule(
    track: dict[str, Any], sets: dict[str, dict[str, list[str]]] | None = None
) -> list[list[Any]]:
    """[time, image key] whenever the shown image changes, for sprite props (the cat; Fred in pixel or 3D).

    A move with a gait plays that cycle, an act with frames plays once, a carry shows the grab, and the
    rest of the time the idle cycle loops. 3D Fred turns once (a turntable: the proof he is 3D) as he
    becomes 3D. Fred shows his photo or his rig outside frame styles. `track["set_fps"]` holds per-prefix
    frame rates when two frame styles (pixel, 3D) share a track."""
    fps = track.get("fps") or {}
    set_fps = track.get("set_fps") or {}
    frames = track.get("frames") or {}
    # start, end, animation, mode: "loop" cycles, "once" plays and holds its last frame, "fit" spreads the
    # frames over the window (a jump of any length lands on its landing frame: audit)
    windows: list[tuple[float, float, str, str]] = []
    for m in track["moves"]:
        if m.get("gait") and m["d"] > 0:
            anim = {"run": "run", "walk": "walk", "hop": "hop", "jump": "jump"}.get(m["gait"], "")
            windows.append((m["t"], m["t"] + m["d"], anim, "fit" if anim == "jump" else "loop"))
    for a in track["acts"]:
        if a["do"] in SPRITE_ACTS:
            windows.append((a["t"], a["t"] + SPRITE_ACTS[a["do"]], a["do"], "once"))
    if track.get("carry"):  # a pounce into the grab (the cat: crouch, wiggle, leap), then the grab
        ct = track["carry"]["t"]
        pounce = once_s(frames, fps, "pounce")
        if pounce:
            windows.append((max(track["t0"], ct - pounce), ct, "pounce", "once"))
        windows.append((ct, ct + max(0.4, once_s(frames, fps, "grab")), "grab", "once"))
    first3d = next((s for s in track["styles"] if s["style"] == "toon3d"), None)
    if first3d and track.get("rig"):  # the proof he is 3D, once: a second spin repeats the joke (v10)
        turn = max((once_s(st, set_fps.get("3d-"), "turn") for st in (sets or {}).values()), default=0.0)
        windows.append((first3d["t"], first3d["t"] + turn, "turn", "once"))
    out: list[list[Any]] = []
    t, last = track["t0"], None
    while t < track["t1"]:
        style, on = state_at(track, t)
        prefix = SET_PREFIX.get(style, "")
        if track.get("rig") and (
            not prefix or riding_at(track, t) or not any(k.startswith(prefix) for k in sets or {})
        ):  # the boat is drawn in the rig only: frames there left him rowing nothing in mid-air (v05)
            key = "photo" if style == "photo" else "rig"
        else:
            cyc = (
                frames
                if not track.get("rig")
                else (sets or {}).get(prefix + ("-".join(sorted(on)) or "plain"), {})
            )
            win = next((w for w in reversed(windows) if w[0] <= t < w[1] and cyc.get(w[2])), None)
            anim, t_start, mode = (win[2], win[0], win[3]) if win else ("idle", track["t0"], "loop")
            seq = cyc.get(anim) or cyc.get("idle") or []
            if not seq:
                break
            rate = set_fps.get(prefix, fps).get(anim, 10)
            if mode == "fit" and win is not None:
                rate = len(seq) / max(win[1] - win[0], 1e-3)
            n = int((t - t_start) * rate + 1e-6)
            key = seq[n % len(seq)] if mode == "loop" else seq[min(n, len(seq) - 1)]
        if key != last:
            out.append([round(t, 3), key])
            last = key
        t += STEP
    return out
