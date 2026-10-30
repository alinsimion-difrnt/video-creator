"""S3 speech: word timestamps (local faster-whisper) and measurable prosody (BUILD_PLAN 7.1).

We report expressiveness that can be measured (pace, pauses, pitch and energy variability) and
never claim perceived vocal emotion (null in v1).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from itertools import pairwise
from pathlib import Path
from typing import Any

import librosa
import numpy as np

from lens.schemas.config import SpeechConfig

SR = 16_000


@dataclass(frozen=True)
class Word:
    i: int
    text: str
    start_s: float
    end_s: float
    prob: float


@cache
def _model(name: str, compute_type: str) -> Any:
    from faster_whisper import WhisperModel

    return WhisperModel(name, device="cpu", compute_type=compute_type)


def transcribe(path: Path, cfg: SpeechConfig) -> list[Word]:
    model = _model(cfg.whisper_model, cfg.whisper_compute_type)
    # Decode ourselves (16 kHz mono): faster-whisper's own PyAV decoding breaks on newer PyAV.
    segments, _ = model.transcribe(
        load_mono(path).astype(np.float32),
        language=cfg.language,
        word_timestamps=True,
        vad_filter=True,
        condition_on_previous_text=False,
        beam_size=5,
    )
    words: list[Word] = []
    for seg in segments:
        for w in seg.words or []:
            text = w.word.strip()
            if text:
                words.append(
                    Word(
                        len(words),
                        text,
                        round(float(w.start), 3),
                        round(float(w.end), 3),
                        round(float(w.probability), 3),
                    )
                )
    return words


def tighten(words: list[Word], mono: np.ndarray, sr: int, cfg: SpeechConfig) -> list[Word]:
    """Whisper's word boundaries drift by 100-400 ms into silence. Trim each word to the span
    where the voice is actually sounding (frame energy above a floor), so pauses measure true.

    Works best on a vocal stem; on a full mix the music keeps the floor high and trimming is mild.
    """
    hop = int(0.01 * sr)
    rms = librosa.feature.rms(y=mono, frame_length=2 * hop, hop_length=hop)[0]
    db = 20 * np.log10(np.maximum(rms, 1e-9))
    floor = max(float(np.percentile(db, 10)) + cfg.voice_floor_db, float(db.max()) - cfg.voice_range_db)
    out = []
    for w in words:
        a, b = int(w.start_s * sr / hop), max(int(w.start_s * sr / hop) + 1, int(w.end_s * sr / hop))
        on = np.flatnonzero(db[a:b] > floor)
        if on.size:
            start, end = (a + on[0]) * hop / sr, (a + on[-1] + 1) * hop / sr
            w = Word(w.i, w.text, round(start, 3), round(max(end, start + 0.03), 3), w.prob)
        out.append(w)
    return out


@dataclass(frozen=True)
class Prosody:
    words: int
    speech_span_s: float
    wpm: float  # words / speech span
    articulation_wpm: float  # words / time actually speaking (pauses removed)
    pause_count: int
    pause_mean_ms: float
    pause_p90_ms: float
    pause_cv: float  # variety of pause lengths
    pauses_by_length: dict[str, int]
    phrase_rate_cv: float  # variation of speaking rate between phrases
    pitch_median_hz: float | None
    pitch_std_semitones: float | None  # expressiveness of intonation
    energy_std_db: float | None
    perceived_emotion: None = None  # deliberately not claimed in v1


def pauses(words: list[Word], min_ms: float) -> list[float]:
    gaps = [(b.start_s - a.end_s) * 1000 for a, b in pairwise(words)]
    return [g for g in gaps if g >= min_ms]


def phrases(words: list[Word], split_ms: float) -> list[list[Word]]:
    out: list[list[Word]] = []
    for w in words:
        if out and (w.start_s - out[-1][-1].end_s) * 1000 < split_ms:
            out[-1].append(w)
        else:
            out.append([w])
    return out


def prosody(words: list[Word], mono: np.ndarray, sr: int, cfg: SpeechConfig) -> Prosody | None:
    if len(words) < 2:
        return None
    span = words[-1].end_s - words[0].start_s
    p = pauses(words, cfg.pause_min_ms)
    speaking = span - sum(p) / 1000
    buckets = {"short": 0, "medium": 0, "long": 0}
    for g in p:
        buckets["short" if g < cfg.pause_medium_ms else "medium" if g < cfg.pause_long_ms else "long"] += 1
    rates = [
        len(ph) / max(ph[-1].end_s - ph[0].start_s, 0.2)
        for ph in phrases(words, cfg.phrase_split_ms)
        if len(ph) >= 3
    ]
    phrase_cv = float(np.std(rates) / np.mean(rates)) if len(rates) >= 2 else 0.0

    # Pitch and energy only inside words (voice), so music and silence don't count.
    mask = np.zeros(len(mono), dtype=bool)
    for w in words:
        mask[int(w.start_s * sr) : int(w.end_s * sr)] = True
    voiced_audio = mono[mask]
    pitch_med = pitch_std = energy_std = None
    if voiced_audio.size > sr // 2:
        f0, voiced, _ = librosa.pyin(
            voiced_audio, fmin=cfg.pitch_fmin_hz, fmax=cfg.pitch_fmax_hz, sr=sr, frame_length=1024
        )
        f0 = f0[voiced & ~np.isnan(f0)]
        if f0.size >= 10:
            med = float(np.median(f0))
            pitch_med = round(med, 1)
            pitch_std = round(float(np.std(12 * np.log2(f0 / med))), 2)
        rms = librosa.feature.rms(y=voiced_audio, frame_length=1024, hop_length=256)[0]
        db = 20 * np.log10(np.maximum(rms, 1e-9))
        db = db[db > db.max() - 40]
        energy_std = round(float(np.std(db)), 2) if db.size else None
    return Prosody(
        words=len(words),
        speech_span_s=round(span, 3),
        wpm=round(len(words) / span * 60, 1) if span > 0 else 0.0,
        articulation_wpm=round(len(words) / speaking * 60, 1) if speaking > 0 else 0.0,
        pause_count=len(p),
        pause_mean_ms=round(float(np.mean(p)), 1) if p else 0.0,
        pause_p90_ms=round(float(np.percentile(p, 90)), 1) if p else 0.0,
        pause_cv=round(float(np.std(p) / np.mean(p)), 3) if len(p) >= 2 else 0.0,
        pauses_by_length=buckets,
        phrase_rate_cv=round(phrase_cv, 3),
        pitch_median_hz=pitch_med,
        pitch_std_semitones=pitch_std,
        energy_std_db=energy_std,
    )


def wpm_in(words: list[Word], start_s: float, end_s: float) -> float | None:
    """Words per minute inside a time window (e.g. a shot); None if nobody speaks there."""
    inside = [w for w in words if start_s <= (w.start_s + w.end_s) / 2 < end_s]
    if not inside or end_s <= start_s:
        return None
    return round(len(inside) / (end_s - start_s) * 60, 1)


def load_mono(path: Path) -> np.ndarray:
    y, _ = librosa.load(str(path), sr=SR, mono=True)
    return np.asarray(y)
