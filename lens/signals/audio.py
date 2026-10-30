"""S3 audio signals (local only): loudness, peaks, beats, SFX candidates with features and rule labels.

Speech (word timings, prosody) lives in `lens.signals.speech`. Stems (demucs) and CLAP labels are
optional layers on top; without them, SFX candidates come from the full mix and repeating musical
onsets are filtered out as music.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfiltfilt

from lens.schemas.config import AudioSignalsConfig

ANALYSIS_SR = 22_050
HOP = 256  # ~11.6 ms at 22.05 kHz


def load(path: Path) -> tuple[np.ndarray, int]:
    """(samples x channels float64, sample rate)."""
    data, sr = sf.read(str(path), always_2d=True, dtype="float64")
    return data, int(sr)


# ---------------------------------------------------------------------------------------------
# Loudness (ITU-R BS.1770 / EBU R128)


@dataclass(frozen=True)
class Loudness:
    integrated_lufs: float
    short_term_max_lufs: float
    lra_lu: float
    sample_peak_dbfs: float
    true_peak_dbtp: float


def _k_weighted(data: np.ndarray, sr: int) -> np.ndarray:
    meter = pyln.Meter(sr)
    out = data.copy()
    for _, filt in meter._filters.items():
        for ch in range(out.shape[1]):
            out[:, ch] = filt.apply_filter(out[:, ch])
    return out


def _window_loudness(kw: np.ndarray, sr: int, win_s: float, hop_s: float) -> np.ndarray:
    win, hop = int(win_s * sr), int(hop_s * sr)
    if kw.shape[0] < win:
        win = kw.shape[0]
    sq = kw**2
    csum = np.vstack([np.zeros((1, sq.shape[1])), np.cumsum(sq, axis=0)])
    starts = np.arange(0, kw.shape[0] - win + 1, hop)
    ms = (csum[starts + win] - csum[starts]) / win  # per channel mean square
    power = ms.sum(axis=1)  # channel weights are 1.0 for L/R
    with np.errstate(divide="ignore"):
        return np.asarray(-0.691 + 10 * np.log10(np.maximum(power, 1e-12)))


def loudness(data: np.ndarray, sr: int) -> Loudness:
    meter = pyln.Meter(sr)
    integrated = float(meter.integrated_loudness(data))
    kw = _k_weighted(data, sr)
    short = _window_loudness(kw, sr, 3.0, 0.1)
    gated = short[short > -70.0]
    lra = 0.0
    if gated.size:
        mean_power = 10 * np.log10(np.mean(10 ** (gated / 10)))
        rel = gated[gated > mean_power - 20.0]
        if rel.size:
            lra = float(np.percentile(rel, 95) - np.percentile(rel, 10))
    peak = float(np.max(np.abs(data)))
    over = resample_poly(data, 4, 1, axis=0)
    true_peak = float(np.max(np.abs(over)))

    def db(v: float) -> float:
        return float(20 * np.log10(max(v, 1e-12)))

    return Loudness(
        integrated_lufs=round(integrated, 2),
        short_term_max_lufs=round(float(short.max()), 2),
        lra_lu=round(lra, 2),
        sample_peak_dbfs=round(db(peak), 2),
        true_peak_dbtp=round(db(true_peak), 2),
    )


# ---------------------------------------------------------------------------------------------
# Beats


@dataclass(frozen=True)
class Beats:
    bpm: float
    times: list[float]
    confidence: float  # 0..1 pulse clarity; low means no steady beat (VO-only, ambient)


def beats(mono: np.ndarray, sr: int) -> Beats:
    env = librosa.onset.onset_strength(y=mono, sr=sr, hop_length=HOP)
    tempo, frames = librosa.beat.beat_track(onset_envelope=env, sr=sr, hop_length=HOP, units="frames")
    bpm = float(np.atleast_1d(tempo)[0])
    frames = _kick_phase(mono, sr, np.asarray(frames, dtype=int), bpm)
    times = _snap_to_kicks(mono, sr, librosa.frames_to_time(frames, sr=sr, hop_length=HOP))
    # Pulse clarity: autocorrelation of the onset envelope at the beat lag vs at lag 0.
    ac = librosa.autocorrelate(env - env.mean())
    lag = round(60.0 / bpm * sr / HOP) if bpm > 0 else 0
    conf = float(ac[lag] / ac[0]) if 0 < lag < len(ac) and ac[0] > 0 else 0.0
    return Beats(round(bpm, 2), [round(t, 4) for t in times], round(max(0.0, min(1.0, conf)), 3))


def _snap_to_kicks(mono: np.ndarray, sr: int, times: np.ndarray, search_s: float = 0.06) -> list[float]:
    """The onset envelope lags the hit by a few hops. Snap each beat to the sample-accurate start
    of the low-frequency hit within +-search_s (left unchanged where there is no clear hit)."""
    sos = butter(4, 150, btype="low", fs=sr, output="sos")
    low = sosfiltfilt(sos, mono)
    win = max(1, int(0.005 * sr))
    env = np.sqrt(np.convolve(low**2, np.ones(win) / win, mode="same"))
    floor = float(np.median(env))
    out = []
    for t in times:
        a, b = max(0, int((t - search_s) * sr)), min(len(env), int((t + search_s) * sr))
        seg = env[a:b]
        if seg.size == 0 or seg.max() < 4 * floor:
            out.append(float(t))
            continue
        p = int(np.argmax(seg))
        below = np.flatnonzero(seg[:p] < seg[p] * 0.1)
        out.append((a + (int(below[-1]) + 1 if below.size else 0)) / sr)
    return out


def _kick_phase(mono: np.ndarray, sr: int, frames: np.ndarray, bpm: float) -> np.ndarray:
    """The tracker can lock onto off-beats (hats on the 8ths). Of the found phase and the
    half-beat-shifted one, keep the phase with more low-frequency (kick) onset energy."""
    if frames.size < 4 or bpm <= 0:
        return frames
    low = librosa.onset.onset_strength(y=mono, sr=sr, hop_length=HOP, fmax=150, n_mels=32)
    half = round(30.0 / bpm * sr / HOP)

    def energy(fr: np.ndarray) -> float:
        fr = fr[(fr >= 0) & (fr < len(low))]
        # allow +-2 frames of slack around each beat
        return float(sum(low[max(0, f - 2) : f + 3].max() for f in fr)) / max(len(fr), 1)

    shifted = frames + half
    return shifted[shifted < len(low)] if energy(shifted) > 1.5 * energy(frames) else frames


# ---------------------------------------------------------------------------------------------
# SFX candidates


@dataclass(frozen=True)
class SfxCandidate:
    id: str
    onset_s: float
    sync_s: float  # the moment that should line up with the picture (peak for swells, onset for hits)
    attack_ms: float
    duration_ms: float
    flatness: float
    centroid_hz: float
    centroid_slope_hz_s: float
    low_ratio: float
    on_beat: bool
    label: str
    label_source: str  # "rules" (CLAP adds "clap" in a later layer)


def foreground(mono: np.ndarray, sr: int, beat_period_s: float | None, cfg: AudioSignalsConfig) -> np.ndarray:
    """Complex STFT of the non-repeating part of the mix (period-based REPET).

    A music bed repeats every beat (kick, hats) and every bar (chords): the median of the
    spectrogram at +-k beat periods models it, and one-off SFX (and speech) are what is left.
    Without a steady beat the full mix is returned.
    """
    D = librosa.stft(mono, n_fft=2048, hop_length=HOP)
    S = np.abs(D)
    if not beat_period_s:
        return np.asarray(D)
    period = max(1, round(beat_period_s * sr / HOP))
    n = S.shape[1]
    stack = []
    for k in range(-cfg.repet_periods, cfg.repet_periods + 1):
        shift = k * period
        shifted = np.full_like(S, np.nan)
        if shift >= 0:
            shifted[:, : n - shift] = S[:, shift:]
        else:
            shifted[:, -shift:] = S[:, : n + shift]
        stack.append(shifted)
    background = np.nanmedian(np.stack(stack), axis=0)
    background = np.minimum(S, np.nan_to_num(background, nan=0.0))
    mask = librosa.util.softmask(S - background, cfg.repet_margin * background, power=2)
    return np.asarray(mask * D)


def _regions(F: np.ndarray, sr: int, cfg: AudioSignalsConfig) -> list[tuple[int, int]]:
    """Contiguous foreground sounds (start, end exclusive) in frames."""
    rms = np.sqrt(np.mean(F**2, axis=0))
    db = 20 * np.log10(np.maximum(rms, 1e-9))
    smooth = np.convolve(db, np.ones(3) / 3, mode="same")
    threshold = max(float(smooth.max()) - cfg.sfx_max_below_loudest_db, float(np.percentile(smooth, 50)) + 10)
    active = smooth > threshold
    gap = int(cfg.sfx_min_gap_s * sr / HOP)
    regions: list[tuple[int, int]] = []
    idx = np.flatnonzero(active)
    if idx.size == 0:
        return regions
    start = prev = int(idx[0])
    for i in idx[1:]:
        i = int(i)
        if i - prev > gap:
            regions.append((start, prev + 1))
            start = i
        prev = i
    regions.append((start, prev + 1))
    # Backtrack each start down its own slope to the nearest local minimum (where the build began),
    # never past the previous region or sfx_backtrack_s.
    out: list[tuple[int, int]] = []
    limit = int(cfg.sfx_backtrack_s * sr / HOP)
    for a, b in regions:
        floor_i = max(out[-1][1] if out else 0, a - limit)
        i = a
        while i - 1 >= floor_i and smooth[i - 1] < smooth[i]:
            i -= 1
        out.append((i, b))
    return out


def _features(F: np.ndarray, sr: int, start: int, stop: int, cfg: AudioSignalsConfig) -> dict[str, float]:
    """Features of the foreground sound in frames [start, stop)."""
    stop = max(stop, start + 1)
    seg = F[:, start:stop]
    rms = np.sqrt(np.mean(seg**2, axis=0)) if seg.size else np.zeros(1)
    rms_db = 20 * np.log10(np.maximum(rms, 1e-9))
    peak_i = int(np.argmax(rms))
    below = np.flatnonzero(rms_db[peak_i:] < rms_db[peak_i] - cfg.sfx_decay_db)
    end_i = peak_i + (int(below[0]) if below.size else len(rms) - peak_i)
    frames = seg[:, : max(1, end_i)]
    flat = float(np.mean(librosa.feature.spectral_flatness(S=frames)))
    cent = librosa.feature.spectral_centroid(S=frames, sr=sr, n_fft=2048)[0]
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    low = float(frames[freqs < 200].sum() / max(frames.sum(), 1e-9))
    slope = float(np.polyfit(np.arange(len(cent)) * HOP / sr, cent, 1)[0]) if len(cent) >= 3 else 0.0
    t0 = start * HOP / sr
    return {
        "onset_s": t0,
        "peak_s": t0 + peak_i * HOP / sr,
        "attack_ms": peak_i * HOP / sr * 1000,
        "duration_ms": end_i * HOP / sr * 1000,
        "flatness": flat,
        "centroid_hz": float(np.mean(cent)) if len(cent) else 0.0,
        "slope": slope,
        "low_ratio": low,
        "peak_db": float(rms_db[peak_i]),
    }


def _label(f: dict[str, float], cfg: AudioSignalsConfig) -> str:
    if f["duration_ms"] <= cfg.click_max_ms:
        return "click"
    if f["low_ratio"] >= cfg.impact_min_low_ratio and f["attack_ms"] <= cfg.impact_max_attack_ms:
        return "impact"
    if f["attack_ms"] >= cfg.swell_min_attack_ms and f["flatness"] >= cfg.noise_min_flatness:
        return "riser" if f["attack_ms"] >= cfg.riser_min_attack_ms else "whoosh"
    return "unsure"


def _refine(env: np.ndarray, sr: int, a: int, b: int, decay_db: float) -> tuple[float, float, float]:
    """Sample-accurate (onset, peak, end) in seconds for a region given in STFT frames.

    STFT frames smear time by half a window (~46 ms); the foreground waveform's 5 ms envelope
    does not. Onset = last point before the peak below peak - decay_db; end = first after it.
    """
    lo = max(0, (a - 4) * HOP)
    hi = min(len(env), (b + 4) * HOP)
    seg = env[lo:hi]
    if seg.size == 0:
        return a * HOP / sr, a * HOP / sr, b * HOP / sr
    p = int(np.argmax(seg))
    level = seg[p] * 10 ** (-decay_db / 20)
    before = np.flatnonzero(seg[:p] < level)
    after = np.flatnonzero(seg[p:] < level)
    onset = int(before[-1]) + 1 if before.size else 0
    end = p + (int(after[0]) if after.size else len(seg) - p)
    return (lo + onset) / sr, (lo + p) / sr, (lo + end) / sr


def sfx_candidates(
    mono: np.ndarray, sr: int, beat_times: list[float], bpm: float | None, cfg: AudioSignalsConfig
) -> list[SfxCandidate]:
    D = foreground(mono, sr, 60.0 / bpm if bpm else None, cfg)
    F = np.abs(D)
    y_fg = librosa.istft(D, hop_length=HOP, length=len(mono))
    win = max(1, int(0.005 * sr))
    env = np.sqrt(np.convolve(y_fg**2, np.ones(win) / win, mode="same"))
    beat_arr = np.asarray(beat_times)
    out: list[SfxCandidate] = []
    for a, b in _regions(F, sr, cfg):
        f = _features(F, sr, a, b, cfg)
        onset, peak, end = _refine(env, sr, a, b, cfg.sfx_decay_db)
        if onset < cfg.sfx_edge_guard_s or end > len(mono) / sr - cfg.sfx_edge_guard_s:
            continue  # STFT/REPET edge artefacts at the very start or end of the file
        f.update(
            onset_s=onset, peak_s=peak, attack_ms=(peak - onset) * 1000, duration_ms=(end - onset) * 1000
        )
        label = _label(f, cfg)
        sync = f["peak_s"] if label in ("whoosh", "riser") else f["onset_s"]
        nearest = float(np.min(np.abs(beat_arr - sync))) if beat_arr.size else np.inf
        out.append(
            SfxCandidate(
                id=f"x{len(out) + 1:03d}",
                onset_s=round(f["onset_s"], 4),
                sync_s=round(sync, 4),
                attack_ms=round(f["attack_ms"], 1),
                duration_ms=round(f["duration_ms"], 1),
                flatness=round(f["flatness"], 4),
                centroid_hz=round(f["centroid_hz"], 1),
                centroid_slope_hz_s=round(f["slope"], 1),
                low_ratio=round(f["low_ratio"], 3),
                on_beat=bool(nearest * 1000 <= cfg.beat_grid_tolerance_ms),
                label=label,
                label_source="rules",
            )
        )
    return out


def analyse(
    path: Path, cfg: AudioSignalsConfig, bed: Path | None = None
) -> tuple[Loudness, Beats, list[SfxCandidate]]:
    """Loudness on the full mix; beats and SFX on `bed` (the accompaniment stem) when given."""
    data, sr = load(path)
    loud = loudness(data, sr)
    if bed is not None:
        data, sr = load(bed)
    mono = librosa.resample(data.mean(axis=1), orig_sr=sr, target_sr=ANALYSIS_SR)
    bt = beats(mono, ANALYSIS_SR)
    steady = bt.confidence >= cfg.beat_min_confidence
    times = bt.times if steady else []
    return loud, bt, sfx_candidates(mono, ANALYSIS_SR, times, bt.bpm if steady else None, cfg)
