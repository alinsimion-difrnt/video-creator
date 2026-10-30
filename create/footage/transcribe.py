"""F2 transcript: every word of every take, verbatim, on the masters' clocks.

ElevenLabs Scribe (`POST /v1/speech-to-text`, model scribe_v2, word timestamps; verbatim by default, so
fillers and false starts are kept: external-facts §21) is the default (ADR 0022). Brand names go in as
`keyterms`.
Local faster-whisper is the fallback (`create.footage.stt_engine: whisper`); it drops most fillers, so the cut
finder then sees fewer of them. Raw responses are cached in data/create/<p>/footage/stt/ by audio hash.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from create.footage.cuts import norm
from lens.schemas.config import CreateFootage
from lens.schemas.create import TranscriptWord

SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"


def _multipart(fields: list[tuple[str, str]], file_field: str, file: Path) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in fields:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{file.name}"\r\n'
        "Content-Type: audio/wav\r\n\r\n".encode()
    )
    body = b"".join(parts) + file.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def scribe(audio: Path, cfg: CreateFootage, language: str, keyterms: list[str]) -> dict[str, Any]:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set (or set create.footage.stt_engine: whisper)")
    fields = [("model_id", cfg.stt_model), ("timestamps_granularity", "word"), ("tag_audio_events", "true")]
    if language:
        fields.append(("language_code", language))
    fields += [("keyterms", k) for k in keyterms]
    body, ctype = _multipart(fields, "file", audio)
    req = urllib.request.Request(SCRIBE_URL, data=body, headers={"xi-api-key": key, "Content-Type": ctype})
    with urllib.request.urlopen(req, timeout=900) as resp:
        data: dict[str, Any] = json.loads(resp.read())
    return data


def words_from_scribe(data: dict[str, Any], take: str, start_index: int) -> list[TranscriptWord]:
    out: list[TranscriptWord] = []
    for w in data.get("words", []):
        kind = {"word": "word", "audio_event": "event"}.get(w.get("type", ""))
        if kind is None or w.get("start") is None or not str(w.get("text", "")).strip():
            continue  # spacing tokens and untimed entries
        out.append(
            TranscriptWord(
                i=start_index + len(out),
                take=take,
                text=str(w["text"]).strip(),
                kind=kind,
                start_s=round(float(w["start"]), 3),
                end_s=round(max(float(w["end"]), float(w["start"])), 3),
                logprob=w.get("logprob"),
            )
        )
    return out


def whisper(audio: Path, cfg: CreateFootage, language: str) -> dict[str, Any]:
    """The local fallback, in Scribe's response shape."""
    import numpy as np

    from lens.signals.speech import _model, load_mono

    model = _model(cfg.whisper_model, "int8")
    segments, info = model.transcribe(
        load_mono(audio).astype(np.float32), language=language or None, word_timestamps=True,
        vad_filter=False, condition_on_previous_text=False, beam_size=5,
    )  # fmt: skip
    words = [
        {"text": w.word.strip(), "type": "word", "start": float(w.start), "end": float(w.end)}
        for seg in segments for w in (seg.words or []) if w.word.strip()
    ]  # fmt: skip
    return {"language_code": info.language, "words": words}


# ISO 639-3 -> 639-1 for the languages a take is likely in (Scribe may detect either form); others: unknown
ISO3_TO_1 = {"eng": "en", "ron": "ro", "hun": "hu", "ita": "it", "nld": "nl", "fin": "fi", "rus": "ru",
             "spa": "es", "ger": "de", "deu": "de", "fre": "fr", "fra": "fr", "por": "pt", "dut": "nl",
             "pol": "pl", "cze": "cs", "ces": "cs", "swe": "sv", "jpn": "ja", "chi": "zh", "zho": "zh",
             "ukr": "uk", "bul": "bg", "gre": "el", "ell": "el", "rum": "ro", "slk": "sk", "slo": "sk",
             "dan": "da"}  # fmt: skip


def iso1(code: str) -> str:
    """The brief's two-letter code: 'ron' -> 'ro', 'spa' -> 'es', 'en-US' -> 'en'; "" if unknown."""
    c = code.strip().lower().split("-")[0]
    return c if len(c) == 2 else ISO3_TO_1.get(c, "")


def transcribe_take(
    audio: Path,
    take: str,
    cache: Path,
    cfg: CreateFootage,
    language: str,
    keyterms: list[str],
    start_index: int,
) -> tuple[list[TranscriptWord], str]:
    """Words of one take (cached by audio, engine, model, language and keyterms) and the detected language."""
    h = hashlib.sha256(audio.read_bytes()).hexdigest()[:16]
    model = cfg.stt_model if cfg.stt_engine == "elevenlabs" else cfg.whisper_model
    params = hashlib.sha256(json.dumps([cfg.stt_engine, model, language, keyterms]).encode()).hexdigest()[:8]
    path = cache / f"{take}-{h}-{params}.json"
    if path.exists():
        data = json.loads(path.read_text())
    else:
        data = (
            scribe(audio, cfg, language, keyterms)
            if cfg.stt_engine == "elevenlabs"
            else whisper(audio, cfg, language)
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False))
    return words_from_scribe(data, take, start_index), iso1(
        str(data.get("language_code") or "")
    ) or language or "en"


def keyterms_for(brand_name: str, spoken: str, extra: list[str]) -> list[str]:
    """Names to bias recognition with: the brand as written and as said, plus the brief's own list."""
    terms = [t for t in dict.fromkeys([brand_name, *extra]) if t and norm(t)]
    return [t for t in terms if len(t) < 50 and len(t.split()) <= 5 and not set(t) & set("<>{}[]\\")][
        :100
    ] or [spoken]
