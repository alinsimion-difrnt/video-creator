"""Two-stem separation (vocals / accompaniment) with demucs, locally on CPU (BUILD_PLAN 7.1).

Vocals feed word timing and prosody; the accompaniment feeds beats, SFX candidates and ducking.
Without stems those metrics are computed on the full mix and marked low-confidence.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf


@cache
def _model(name: str) -> Any:
    from demucs.pretrained import get_model

    model = get_model(name)
    model.eval()
    return model


def separate(wav: Path, out_dir: Path, model_name: str) -> tuple[Path, Path]:
    """Write vocals.wav and accompaniment.wav (model sample rate, stereo); return their paths."""
    import librosa
    import torch
    from demucs.apply import apply_model

    model = _model(model_name)
    data, sr = sf.read(str(wav), always_2d=True, dtype="float32")
    mix = data.T
    if mix.shape[0] == 1:
        mix = np.repeat(mix, 2, axis=0)
    if sr != model.samplerate:
        mix = librosa.resample(mix, orig_sr=sr, target_sr=model.samplerate)
    tensor = torch.from_numpy(np.ascontiguousarray(mix[:2]))
    ref = tensor.mean(0)
    scale = ref.std() + 1e-8
    # shifts=0: demucs' default (1) applies a random time shift per run, which makes stems (and
    # every metric downstream) non-deterministic. Reproducibility is a plan principle (2.7).
    torch.manual_seed(0)
    with torch.no_grad():
        sources = apply_model(
            model,
            ((tensor - ref.mean()) / scale)[None],
            shifts=0,
            device="cpu",
            split=True,
            overlap=0.25,
            progress=False,
        )[0]
    sources = sources * scale + ref.mean()
    names = list(model.sources)
    vocals = sources[names.index("vocals")].numpy()
    accompaniment = torch.stack([sources[i] for i, n in enumerate(names) if n != "vocals"]).sum(0).numpy()
    out_dir.mkdir(parents=True, exist_ok=True)
    vpath, apath = out_dir / "vocals.wav", out_dir / "accompaniment.wav"
    sf.write(vpath, vocals.T, model.samplerate, subtype="PCM_16")
    sf.write(apath, accompaniment.T, model.samplerate, subtype="PCM_16")
    return vpath, apath


def ducking_db(accompaniment: Path, word_spans: list[tuple[float, float]], guard_s: float) -> float | None:
    """How far the bed drops under the voice: median bed level away from speech minus during speech."""
    import librosa

    y, sr = librosa.load(str(accompaniment), sr=16_000, mono=True)
    if not word_spans or y.size == 0:
        return None
    hop = 160
    rms = librosa.feature.rms(y=y, frame_length=640, hop_length=hop)[0]
    db = 20 * np.log10(np.maximum(rms, 1e-9))
    t = np.arange(len(db)) * hop / sr
    speaking = np.zeros(len(db), dtype=bool)
    near = np.zeros(len(db), dtype=bool)
    for a, b in word_spans:
        speaking |= (t >= a) & (t < b)
        near |= (t >= a - guard_s) & (t < b + guard_s)
    away = ~near
    if speaking.sum() < 10 or away.sum() < 10:
        return None
    return round(float(np.median(db[away]) - np.median(db[speaking])), 2)
