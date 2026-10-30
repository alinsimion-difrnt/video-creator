"""Local CLAP zero-shot labels for SFX candidates (BUILD_PLAN 7.1; ADR 0008).

Policy: measured rule labels stand when the rules decide; CLAP fills in where the rules say
"unsure" and is recorded alongside, with agreement, for the gold-set evaluation at G2.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import librosa
import numpy as np

from lens.schemas.config import ClapConfig

SR = 48_000

# Taxonomy sfx value -> text prompt.
PROMPTS: dict[str, str] = {
    "whoosh": "a whoosh sound effect",
    "swoosh_reverse": "a reverse swoosh sound effect",
    "click": "a mouse click",
    "tick": "a clock tick",
    "pop": "a pop sound",
    "riser": "a rising riser sound effect",
    "impact": "a deep impact hit",
    "chime": "a chime",
    "glitch": "a glitch sound",
    "typing": "keyboard typing",
    "music": "music",
    "speech": "speech",
}
# Labels that count as agreeing with each other (rules cannot tell these apart).
FAMILIES = [{"whoosh", "swoosh_reverse", "riser"}, {"click", "tick", "pop"}]


@dataclass(frozen=True)
class ClapLabel:
    label: str
    score: float


@cache
def _model(name: str) -> tuple[Any, Any]:
    from transformers import ClapModel, ClapProcessor

    model = ClapModel.from_pretrained(name)
    model.eval()  # type: ignore[no-untyped-call]
    return model, ClapProcessor.from_pretrained(name)


def agree(a: str, b: str) -> bool:
    return a == b or any(a in f and b in f for f in FAMILIES)


def _clip(audio: np.ndarray, onset_s: float, sync_s: float, cfg: ClapConfig) -> np.ndarray:
    start = max(0.0, min(onset_s, sync_s) - cfg.pre_s)
    end = max(sync_s, onset_s) + cfg.post_s
    end = max(end, start + cfg.min_clip_s)
    return audio[int(start * SR) : int(end * SR)].astype(np.float32)


def label(audio_path: Path, events: list[tuple[float, float]], cfg: ClapConfig) -> list[ClapLabel]:
    """CLAP label + probability for each (onset_s, sync_s) on the given audio (accompaniment stem)."""
    if not events:
        return []
    import torch

    model, processor = _model(cfg.model)
    y, _ = librosa.load(str(audio_path), sr=SR, mono=True)
    names = list(PROMPTS)
    out: list[ClapLabel] = []
    for i in range(0, len(events), cfg.batch_size):
        clips = [_clip(y, o, s, cfg) for o, s in events[i : i + cfg.batch_size]]
        inputs = processor(
            text=[PROMPTS[n] for n in names], audio=clips, sampling_rate=SR, return_tensors="pt", padding=True
        )
        with torch.no_grad():
            probs = model(**inputs).logits_per_audio.softmax(-1).numpy()
        for row in probs:
            k = int(np.argmax(row))
            out.append(ClapLabel(names[k], round(float(row[k]), 3)))
    return out
