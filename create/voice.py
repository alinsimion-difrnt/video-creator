"""C4 voice: ElevenLabs REST with-timestamps per scene, N takes, keep the take closest to the voice spec.

- Word timings come from the character alignment (audio tags such as `[chuckles]` are skipped), so no
  whisper pass decides caption timing (BUILD_PLAN 12b).
- Prosody is measured the way the corpus was (lens speech: local whisper words, tightened), so takes are
  compared with `exports/voice-spec.json` on equal terms.
- Each take is cached under data/create/<project>/voice/ by a hash of text + voice + model + format: a rerun
  with an unchanged script costs no credits. Only the API call needs the network and the key.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from lens import __version__
from lens.hashing import cache_key
from lens.schemas.common import Annotator, Provenance
from lens.schemas.config import CreateVoice, LensConfig
from lens.schemas.create import Brief, Script, TakeProsody, TimedWord, Voice, VoiceScene

STAGE = "c4_voice"
API = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps?output_format={fmt}"
# voice-spec measures that a single scene can show (pause p90 and phrase variation need a whole read).
SPEC_KEYS = ("wpm", "articulation_wpm", "pause_mean_ms", "pitch_std_semitones", "energy_std_db")
CREDIT_HEADERS = ("character-cost", "x-character-count")

Synth = Callable[[str, CreateVoice], tuple[dict[str, Any], int | None]]
Measure = Callable[[Path, LensConfig], dict[str, Any]]  # SPEC_KEYS values plus "heard" (the transcript)


def text_hash(text: str, voice: CreateVoice) -> str:
    return cache_key(
        {"text": text, "voice": voice.voice_id, "model": voice.model_id, "fmt": voice.output_format}
    )


def words_from_alignment(alignment: dict[str, Any]) -> list[TimedWord]:
    """Characters -> words. Tags in brackets are not words; a word ends at its last letter or digit,
    so trailing punctuation such as an ellipsis does not stretch it into the pause."""
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]
    words: list[TimedWord] = []
    text, start, end, in_tag = "", 0.0, 0.0, False

    def flush() -> None:
        if any(c.isalnum() for c in text):
            words.append(TimedWord(i=len(words), text=text, start_s=round(start, 3), end_s=round(end, 3)))

    for ch, a, b in zip(chars, starts, ends, strict=True):
        if ch == "[":
            flush()
            text, in_tag = "", True
        elif in_tag:
            in_tag = ch != "]"
        elif ch.isspace():
            flush()
            text = ""
        else:
            if not text:
                start = a
            text += ch
            if ch.isalnum():
                end = b
    flush()
    return words


def elevenlabs(text: str, voice: CreateVoice) -> tuple[dict[str, Any], int | None]:
    """One with-timestamps call. Returns the JSON body and the credit cost when the response states it."""
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set")
    req = urllib.request.Request(
        API.format(voice_id=voice.voice_id, fmt=voice.output_format),
        data=json.dumps({"text": text, "model_id": voice.model_id}).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = json.load(resp)
        cost = next((resp.headers.get(h) for h in CREDIT_HEADERS if resp.headers.get(h)), None)
    return body, int(float(cost)) if cost else None


def lens_prosody(path: Path, cfg: LensConfig) -> dict[str, Any]:
    """Measure one take as the corpus was measured (lens speech), and keep what whisper heard."""
    from lens.signals.speech import SR, load_mono, prosody, tighten, transcribe

    speech = cfg.signals.speech
    mono = load_mono(path)
    raw = transcribe(path, speech)
    p = prosody(tighten(raw, mono, SR, speech), mono, SR, speech)
    measured: dict[str, Any] = (
        dict.fromkeys(SPEC_KEYS) if p is None else {k: getattr(p, k) for k in SPEC_KEYS}
    )
    measured["heard"] = " ".join(w.text for w in raw)
    return measured


def in_range(measured: dict[str, Any], spec: dict[str, Any]) -> int:
    """How many voice-spec measures fall inside the premium band."""
    return sum(
        1
        for k in SPEC_KEYS
        if measured.get(k) is not None and spec[k]["low"] <= measured[k] <= spec[k]["high"]
    )


def band_distance(measured: dict[str, Any], spec: dict[str, Any], keys: list[str]) -> float:
    """Summed distance outside each band, in band widths (0 inside; a missing measure counts as 1)."""
    total = 0.0
    for k in keys:
        v, lo, hi = measured.get(k), spec[k]["low"], spec[k]["high"]
        if v is None:
            total += 1.0
        elif v < lo or v > hi:
            total += (lo - v if v < lo else v - hi) / (hi - lo)
    return round(total, 4)


def _letters(text: str) -> str:
    return "".join(c for c in text.lower() if c.isalnum())


def brand_heard(spoken: str, heard: str | None, name: str, spoken_name: str) -> bool | None:
    """Did the transcript bring the brand back? None when the line does not say it."""
    if _letters(spoken_name) not in _letters(spoken) or heard is None:
        return None
    return _letters(name) in _letters(heard)


def rank_key(
    take: dict[str, Any], spec: dict[str, Any], keys: list[str], brand: bool | None
) -> tuple[int, float, float]:
    """Lower is better: a misheard brand last, then distance from the bands, then wpm from the median."""
    wpm = take["prosody"].get("wpm") or 0.0
    return (
        1 if brand is False else 0,
        band_distance(take["prosody"], spec, keys),
        abs(wpm - spec["wpm"]["median"]),
    )


def _take(
    root: Path,
    project: str,
    scene: str,
    n: int,
    text: str,
    cfg: LensConfig,
    synth: Synth,
    measure: Measure,
    force: bool,
) -> tuple[dict[str, Any], bool]:
    """A cached take (sidecar JSON next to the mp3). Returns it and whether credits were spent."""
    out = root / "data" / "create" / project / "voice"
    mp3, side = out / f"{scene}-t{n}.mp3", out / f"{scene}-t{n}.json"
    h = text_hash(text, cfg.create.voice)
    if not force and mp3.exists() and side.exists():
        cached = json.loads(side.read_text())
        if cached.get("text_hash") == h:
            if "heard" not in cached["prosody"]:  # measured before the brand check: re-measure, no credits
                cached["prosody"] = measure(mp3, cfg)
                side.write_text(json.dumps(cached))
            return cached, False
    out.mkdir(parents=True, exist_ok=True)
    body, credits = synth(text, cfg.create.voice)
    mp3.write_bytes(base64.b64decode(body["audio_base64"]))
    alignment = body.get("alignment") or body["normalized_alignment"]
    take = {
        "text_hash": h,
        "credits": credits,
        "alignment": alignment,
        "duration_s": round(max(alignment["character_end_times_seconds"]), 3),
        "prosody": measure(mp3, cfg),
    }
    side.write_text(json.dumps(take))
    return take, True


def run_voice(
    root: Path,
    project: str,
    cfg: LensConfig,
    *,
    force: bool = False,
    synth: Synth = elevenlabs,
    measure: Measure = lens_prosody,
    log: Callable[[str], None] = print,
) -> Path:
    """Generate (or reuse) every take, choose one per scene and write projects/<project>/voice.json."""
    script_path = root / "projects" / project / "script.yaml"
    script = Script.model_validate(yaml.safe_load(script_path.read_text()))
    brief = Brief.model_validate(yaml.safe_load((root / "projects" / project / "brief.yaml").read_text()))
    spec = json.loads((root / "exports" / "voice-spec.json").read_text())
    voice_cfg = cfg.create.voice
    keys: list[str] = list(voice_cfg.select_on)
    scenes: list[VoiceScene] = []
    spent: list[int] = []
    for sc in script.scenes:
        takes = []
        for n in range(1, voice_cfg.takes + 1):
            take, new = _take(root, project, sc.id, n, sc.spoken, cfg, synth, measure, force)
            takes.append((n, take))
            if new and take["credits"] is not None:
                spent.append(take["credits"])
            log(f"{sc.id} take {n}: {'generated' if new else 'cached'}")
        name, spoken_name = brief.product.name, brief.product.spoken
        brands = {n: brand_heard(sc.spoken, t["prosody"].get("heard"), name, spoken_name) for n, t in takes}
        best_n, best = min(takes, key=lambda t: rank_key(t[1], spec, keys, brands[t[0]]))
        if brands[best_n] is False:
            log(f"{sc.id}: no take says {name!r} clearly; listen, or respell {spoken_name!r} in the script")
        scenes.append(
            VoiceScene(
                scene=sc.id,
                text_hash=best["text_hash"],
                take=best_n,
                takes=voice_cfg.takes,
                audio=f"data/create/{project}/voice/{sc.id}-t{best_n}.mp3",
                duration_s=best["duration_s"],
                words=words_from_alignment(best["alignment"]),
                prosody=TakeProsody(
                    **{k: best["prosody"].get(k) or 0.0 for k in SPEC_KEYS[:3]},
                    pitch_std_semitones=best["prosody"].get("pitch_std_semitones"),
                    energy_std_db=best["prosody"].get("energy_std_db"),
                    in_range=in_range(best["prosody"], spec),
                    band_distance=band_distance(best["prosody"], spec, keys),
                    brand_heard=brands[best_n],
                ),
                credits=sum(t["credits"] for _, t in takes if t["credits"] is not None) or None,
            )
        )
    voice = Voice(
        provenance=Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CODE,
            input_hash=cache_key(
                {"script": script.model_dump(mode="json")["scenes"], "voice": voice_cfg.model_dump()}
            ),
            created_at=datetime.now(UTC),
        ),
        project=project,
        voice_id=voice_cfg.voice_id,
        model_id=voice_cfg.model_id,
        scenes=scenes,
        credits_used=sum(spent) if spent else None,
    )
    path = root / "projects" / project / "voice.json"
    path.write_text(voice.model_dump_json(indent=1) + "\n")
    return path
