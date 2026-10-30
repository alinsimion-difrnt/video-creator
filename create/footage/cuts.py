"""F3 cut proposals and F4 edit from a verbatim transcript (pure functions; numbers from config).

Words are removed when they are a count-in, fillers, an abandoned first attempt of a line (a false
start, repeated within `retake_window_words`), or a line Robert cancelled with a cue word ("again").
Every gap between two kept words becomes at most one cut: the removed words' kind if any lie in it,
else `silence` when the pause is longer than `silence_max_s`. A cut keeps `keep_after_s` after the last
kept word and `keep_before_s` before the next.
"""

from __future__ import annotations

import itertools
import re
from collections.abc import Iterable
from itertools import pairwise
from typing import Any

from lens.schemas.config import CreateFootage
from lens.schemas.create import CutNotes, CutProposal, EdlSegment, TranscriptWord

_PUNCT = re.compile(r"[^\w']+", re.UNICODE)
_SENTENCE_END = (".", "?", "!", "…")


def norm(text: str) -> str:
    return _PUNCT.sub("", text.lower())


def _lists(table: dict[str, list[str]], language: str) -> list[str]:
    return table.get(language) or [x for v in table.values() for x in v]


def _fillers(words: list[TranscriptWord], cfg: CreateFootage, language: str) -> set[int]:
    tokens = {norm(f) for f in _lists(cfg.fillers, language)}
    return {w.i for w in words if w.kind == "filler" or norm(w.text) in tokens}


def _cues(words: list[TranscriptWord], cfg: CreateFootage, language: str, skip: set[int]) -> set[int]:
    """A cue phrase cancels the line it ends: from the previous sentence end up to the cue."""
    out: set[int] = set()
    seq = [w for w in words if w.i not in skip]
    texts = [norm(w.text) for w in seq]
    for cue in _lists(cfg.retake_cues, language):
        parts = [norm(p) for p in cue.split()]
        n = len(parts)
        for k in range(len(seq) - n + 1):
            if texts[k : k + n] != parts:
                continue
            start = k
            while (
                start > 0 and not seq[start - 1].text.endswith(_SENTENCE_END) and seq[start - 1].i not in out
            ):
                start -= 1
            out |= {w.i for w in seq[start : k + n]}
    return out


_CUT_OFF = ("-", "\u2014", "\u2013", "\u2026")  # hyphen, em dash, en dash, ellipsis


def _retakes(words: list[TranscriptWord], cfg: CreateFootage, language: str, skip: set[int]) -> set[int]:
    """False starts: words[i:j] is dropped when words[j:j+k] repeats words[i:i+k] (k >= retake_min_words),
    the attempt was abandoned within `retake_max_tail_words` words after the repeated part, never finished a
    sentence, and was visibly abandoned: its last word is cut off ("to--"), the repeat is immediate (stutter),
    or a pause of `retake_pause_s` comes first that is not a list ("the X or the Y", "X, Y")."""
    c = cfg.cuts
    joins = {norm(x) for x in _lists(cfg.conjunctions, language)}
    seq = [w for w in words if w.i not in skip]
    texts = [norm(w.text) for w in seq]
    out: set[int] = set()
    j = 1
    while j < len(seq):
        best: tuple[int, int] | None = None  # (k, i)
        for i in range(max(0, j - c.retake_window_words), j):
            k = 0
            while j + k < len(seq) and i + k < j and texts[i + k] == texts[j + k] and texts[j + k]:
                k += 1
            tail = j - i - k
            finished = any(
                w.text.endswith(_SENTENCE_END) for w in seq[i:j]
            )  # a whole sentence is not a false start
            last = seq[j - 1]
            cut_off = last.text.rstrip().endswith(_CUT_OFF)
            pause = seq[j].start_s - last.end_s >= c.retake_pause_s
            listed = texts[j - 1] in joins or last.text.endswith((",", ";"))
            abandoned = cut_off or tail == 0 or (pause and not listed)
            if (
                k >= c.retake_min_words
                and tail <= c.retake_max_tail_words
                and not finished
                and abandoned
                and (best is None or k > best[0])
            ):
                best = (k, i)
        if best is not None:
            out |= {w.i for w in seq[best[1] : j]}
            j += best[0]
        else:
            j += 1
    return out


def _count_in(words: list[TranscriptWord], cfg: CreateFootage, language: str) -> set[int]:
    """A count before speaking: a run of count words at a take's start, or set off by pauses on both sides."""
    tokens = {
        norm(x) for v in cfg.count_in.values() for x in v
    }  # every language: counts mix ("Three, doi, unu")
    gap = cfg.cuts.count_in_pause_s
    out: set[int] = set()
    k = 0
    while k < len(words):
        if norm(words[k].text) not in tokens:
            k += 1
            continue
        e = k
        while e + 1 < len(words) and norm(words[e + 1].text) in tokens and words[e + 1].take == words[k].take:
            e += 1
        first = k == 0 or words[k - 1].take != words[k].take
        before = first or words[k].start_s - words[k - 1].end_s >= gap
        after = e + 1 >= len(words) or words[e + 1].start_s - words[e].end_s >= gap
        if (e > k or first) and before and after:
            out |= {w.i for w in words[k : e + 1]}
        k = e + 1
    return out


def _cut(
    n: int, kind: Any, take: str, start: float, stop: float, removed: list[int], reason: str
) -> CutProposal:
    return CutProposal(
        id=f"c{n:03d}",
        kind=kind,
        take=take,
        start_s=round(max(0.0, start), 3),
        end_s=round(stop, 3),
        words=removed,
        reason=reason,
    )


def propose_cuts(
    words: list[TranscriptWord],
    cfg: CreateFootage,
    language: str,
    take_durations: dict[str, float] | None = None,
) -> list[CutProposal]:
    """One proposal per gap between kept words; with `take_durations`, also the silence at a take's ends."""
    c = cfg.cuts
    kinds: dict[int, str] = dict.fromkeys(_count_in(words, cfg, language), "count_in")
    for i in _fillers(words, cfg, language):
        kinds.setdefault(i, "filler")
    for i in _cues(words, cfg, language, set(kinds)):
        kinds.setdefault(i, "cue")
    for i in _retakes(words, cfg, language, set(kinds)):
        kinds.setdefault(i, "retake")
    takes: dict[str, list[TranscriptWord]] = {}
    for w in words:
        takes.setdefault(w.take, []).append(w)
    out: list[CutProposal] = []
    for take, ws in takes.items():
        kept = [w for w in ws if w.i not in kinds]
        end = (take_durations or {}).get(take)
        # (start of the region, end of the region, removed words, keep padding at start / at end)
        regions: list[tuple[float, float, list[int], bool, bool]] = []
        for a, b in zip([None, *kept], [*kept, None], strict=True):
            first_i = a.i if a else -1
            last_i = b.i if b else len(words) + 1
            removed = [w.i for w in ws if first_i < w.i < last_i]
            if a is None and b is None:
                continue
            if a is None:  # before the first kept word
                if removed:  # from the take's start when it is known (the silence before goes too)
                    head = 0.0 if end is not None else ws[0].start_s
                    regions.append((head, b.start_s, removed, False, True))  # type: ignore[union-attr]
                elif end is not None and b is not None and b.start_s > c.silence_max_s:
                    regions.append((0.0, b.start_s, [], False, True))
            elif b is None:  # after the last kept word
                if removed:
                    regions.append((a.end_s, end if end is not None else ws[-1].end_s, removed, True, False))
                elif end is not None and end - a.end_s > c.silence_max_s:
                    regions.append((a.end_s, end, [], True, False))
            elif removed or b.start_s - a.end_s > c.silence_max_s:
                regions.append((a.end_s, b.start_s, removed, True, True))
        for start, stop, removed, pad_a, pad_b in regions:
            lo = start + c.keep_after_s if pad_a else start
            hi = stop - c.keep_before_s if pad_b else stop
            if removed:
                spans = [w for w in ws if w.i in set(removed)]
                lo, hi = min(lo, spans[0].start_s), max(hi, spans[-1].end_s)
                kind = kinds[removed[0]]
                named = "+".join(dict.fromkeys(kinds[i] for i in removed))
                reason = f"{named}: " + " ".join(w.text for w in spans)
            else:
                kind, reason = "silence", f"pause of {stop - start:.2f} s"
                if hi - lo < c.min_cut_s:
                    continue
            out.append(_cut(len(out) + 1, kind, take, lo, hi, removed, reason))
    return out


def apply_notes(
    proposals: list[CutProposal], notes: CutNotes, words: list[TranscriptWord], duration: float
) -> list[CutProposal]:
    """Robert's cut notes over the proposals: a cut before `start_s` and after `end_s` (proposals inside them
    go), proposals clipped out of the `keep` spans, and the extra cuts; ids renumbered in time order."""
    take = notes.take
    rows: list[tuple[str, float, float, list[int], str]] = []
    head, tail = notes.start_s, notes.end_s
    for c in proposals:
        a, b = c.start_s, c.end_s
        if c.take == take:
            if head is not None:
                a = max(a, head)
            if tail is not None:
                b = min(b, tail)
            for k in notes.keep:  # clip out of a kept span; a cut inside one goes
                if a < k.end_s and b > k.start_s:
                    a, b = (a, k.start_s) if a < k.start_s else (max(a, k.end_s), b)
        if b - a > 1e-3:
            ws = [i for i in c.words if any(w.i == i and a <= w.start_s < b for w in words)]
            rows.append((c.kind, a, b, ws, c.reason))
    ends: list[tuple[float | None, float | None, str]] = [
        (0.0, head, "before the start"),
        (tail, duration, "after the end"),
    ]
    extra = [(a, b, why, True) for a, b, why in ends if a is not None and b is not None and b > a]
    extra += [(r.start_s, r.end_s, r.reason, False) for r in notes.cut]
    if notes.keep_only:  # a short version: the gaps between the kept spans go (inside the start and end)
        spans = sorted((r.start_s, r.end_s) for r in notes.keep_only)
        lo, hi = head or 0.0, tail if tail is not None else duration
        gaps = (
            [(lo, spans[0][0])] + [(a[1], b[0]) for a, b in itertools.pairwise(spans)] + [(spans[-1][1], hi)]
        )
        extra += [
            (max(a, lo), min(b, hi), "not in the short version", False)
            for a, b in gaps
            if min(b, hi) > max(a, lo)
        ]
        inside = [r for r in rows if any(a <= r[1] and r[2] <= b for a, b in spans)]
        rows[:] = inside
    for a, b, why, quote in extra:
        ws = [w.i for w in words if w.take == take and a <= w.start_s < b]
        said = " ".join(w.text for w in words if w.i in set(ws)) if quote else ""
        rows.append(("cue", a, b, ws, f"Robert's note, {why}" + (f": {said}" if said else "")))
    rows.sort(key=lambda r: r[1])
    return [_cut(n + 1, k, take, a, b, ws, why) for n, (k, a, b, ws, why) in enumerate(rows)]


def apply_cuts(cuts: Iterable[CutProposal], take_frames: dict[str, int], fps: int) -> list[EdlSegment]:
    """Kept ranges of every take, in take order, as frame-exact segments on one edited clock."""
    by_take: dict[str, list[tuple[int, int]]] = {}
    for cut in cuts:
        by_take.setdefault(cut.take, []).append((round(cut.start_s * fps), round(cut.end_s * fps)))
    segments: list[EdlSegment] = []
    rec = 0
    for take, frames in take_frames.items():
        pos = 0
        for a, b in sorted(by_take.get(take, [])):
            a, b = max(a, pos), min(b, frames)
            if a > pos:
                segments.append(EdlSegment(take=take, src_in=pos, src_out=a, rec_in=rec))
                rec += a - pos
            pos = max(pos, b)
        if pos < frames:
            segments.append(EdlSegment(take=take, src_in=pos, src_out=frames, rec_in=rec))
            rec += frames - pos
    return segments


def cold_open(
    segments: list[EdlSegment], take: str, start_s: float, end_s: float, fps: int
) -> list[EdlSegment]:
    """A flash-forward (CutNotes.open_with): that span of `take` first, every other segment after it."""
    a, b = round(start_s * fps), round(end_s * fps)
    first = EdlSegment(take=take, src_in=a, src_out=b, rec_in=0, cold_open=True)
    return [first] + [s.model_copy(update={"rec_in": s.rec_in + (b - a)}) for s in segments]


def remap_words(
    words: list[TranscriptWord], segments: list[EdlSegment], fps: int, removed: set[int]
) -> list[TranscriptWord]:
    """Kept words with their times on the edited clock (a word whose start was cut away is dropped). A
    flash-forward (a `cold_open` segment) says its words twice: first in the cold open, then in place; the
    timeline renumbers them in time order."""
    out = []
    for w in words:
        for s in sorted(segments, key=lambda s: not s.cold_open):  # the cold open copy, then the word's place
            if w.i in removed and not s.cold_open:  # cut from its place; a cold open still says it (n09: a
                continue  # loop whose spans stop before the flash-forward lost "Pixie, no!" altogether)
            a, b = s.src_in / fps, s.src_out / fps
            if s.take == w.take and a - 1e-6 <= w.start_s < b:
                shift = s.rec_in / fps - a
                out.append(
                    w.model_copy(
                        update={
                            "start_s": round(w.start_s + shift, 3),
                            "end_s": round(min(w.end_s, b) + shift, 3),
                        }
                    )
                )
                if not s.cold_open:
                    break
    return sorted(out, key=lambda w: w.start_s)


def split_long(
    segments: list[EdlSegment],
    words: list[TranscriptWord],
    fps: int,
    max_s: float,
    min_s: float,
    hook_s: float | None = None,
) -> list[EdlSegment]:
    """Split segments longer than `max_s` at word boundaries (sentence ends first, then commas, then any
    pause) so each piece is `min_s`..`max_s`. Pieces are contiguous on the source: nothing is removed; F5
    framing alternates the punch-in on them, which keeps something changing on screen. With `hook_s`, the
    first shot of the edit ends by then (a visual change inside the hook)."""
    out: list[EdlSegment] = []
    rec = 0
    for s in segments:
        first = hook_s if rec == 0 and hook_s is not None else max_s
        cuts = _split_points(s, [w for w in words if w.take == s.take], fps, max_s, min_s, first)
        edges = [s.src_in, *cuts, s.src_out]
        for a, b in pairwise(edges):
            out.append(EdlSegment(take=s.take, src_in=a, src_out=b, rec_in=rec))
            rec += b - a
    return out


def _split_points(
    s: EdlSegment, words: list[TranscriptWord], fps: int, max_s: float, min_s: float, first_s: float
) -> list[int]:
    a, b = s.src_in / fps, s.src_out / fps
    inside = [w for w in words if a <= w.start_s and w.end_s <= b]
    # candidate boundaries: the midpoint of the gap after a word, ranked by how strong a break it is
    cands: list[tuple[float, int]] = []
    for w, nxt in pairwise(inside):
        rank = 0 if w.text.endswith(_SENTENCE_END) else 1 if w.text.endswith((",", ";", ":")) else 2
        cands.append(((w.end_s + nxt.start_s) / 2, rank))
    points: list[int] = []
    start = a
    limit = min(first_s, max_s)
    while b - start > limit:
        ok = [(t, r) for t, r in cands if start + min(min_s, limit) <= t <= start + limit and b - t >= min_s]
        if not ok:
            if limit < max_s:  # no break inside the hook: fall back to the normal window
                limit = max_s
                continue
            break
        best = min(r for _, r in ok)
        t = max(t for t, r in ok if r == best)  # the latest strong break inside the window
        points.append(round(t * fps))
        start, limit = t, max_s
    return points
