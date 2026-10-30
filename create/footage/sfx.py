"""Sound design for presenter videos: soft UI sounds under the voice, synthesised with ffmpeg (no samples,
no API). A pop when a widget lands, a whoosh when the layout moves, a click on a call to action.

The sounds are generated from formulas into data/create/_cache/sfx/, placed at the times the reel's meta
sidecar records (create reel), mixed `level_db` under the finished voice and limited to the voice's true-peak
ceiling. Levels and the sound recipes live in config (create.footage.sfx).
"""

from __future__ import annotations

import json
import subprocess
from itertools import pairwise
from pathlib import Path
from typing import Any

from lens.schemas.config import FootageSfx

# ffmpeg aevalsrc recipes (t in seconds, 48 kHz mono; quoted, so commas stay inside the expression).
# Kept short and soft: they sit under speech.
RECIPES = {
    # a pitch-dropping sine blip, like a bubble
    "pop": ("0.9*sin(2*PI*(260*t+(620/38)*(1-exp(-38*t))))*exp(-30*t)", 0.16),
    # band-limited noise swell (a sum of detuned sines keeps it deterministic)
    "whoosh": (
        "0.5*sin(PI*t/0.42)^2*(sin(2*PI*410*t+3*sin(2*PI*7*t))+0.7*sin(2*PI*620*t+5*sin(2*PI*11*t))"
        "+0.5*sin(2*PI*930*t+7*sin(2*PI*13*t))+0.35*sin(2*PI*1410*t+9*sin(2*PI*17*t)))/2.5",
        0.42,
    ),
    # a rising shimmer: a quick glissando with a little vibrato (a style change, magic)
    "sparkle": ("0.6*sin(2*PI*(900*t+1800*t*t)+2*sin(2*PI*30*t))*exp(-9*t)", 0.35),
    # a springy boing: a sine whose pitch wobbles and settles (a hat landing)
    "boing": ("0.8*sin(2*PI*(180*t+40*sin(2*PI*9*t)*exp(-6*t)/(2*PI*9)*9))*exp(-7*t)", 0.4),
    # a short mouse click: two quick decaying high blips
    "click": (
        "0.8*(sin(2*PI*2400*t)*exp(-260*t)+0.6*sin(2*PI*1500*(t-0.012))*exp(-260*(t-0.012))*gt(t,0.012))",
        0.06,
    ),
}


def sound(cache: Path, name: str) -> Path:
    out = cache / "sfx" / f"{name}.wav"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    expr, dur = RECIPES[name]
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"aevalsrc=exprs='{expr}':s=48000:d={dur}",
         "-af", "afade=t=out:st=" + f"{dur * 0.7:.3f}:d={dur * 0.3:.3f}", "-c:a", "pcm_s16le", str(out)],
        check=True,
    )  # fmt: skip
    return out


SFX_API = "https://api.elevenlabs.io/v1/sound-generation"  # external-facts §10 (2026-10-12)


def el_sound(cache: Path, prompt: str, duration_s: float | None) -> Path:
    """An ElevenLabs sound effect (subscription, CLAUDE.md), cached by prompt and length: one call ever."""
    import hashlib
    import os
    import urllib.request

    key = hashlib.sha256(json.dumps([prompt, duration_s]).encode()).hexdigest()[:16]
    out = cache / "sfx" / f"el-{key}.mp3"
    if out.exists():
        return out
    body: dict[str, Any] = {"text": prompt, "prompt_influence": 0.6}
    if duration_s:
        body["duration_seconds"] = duration_s
    req = urllib.request.Request(
        SFX_API, data=json.dumps(body).encode(),
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
    )  # fmt: skip
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = resp.read()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(out)
    return out


MUSIC_API = "https://api.elevenlabs.io/v1/music"  # external-facts section 10 (g), 2026-10-06


def el_music(cache: Path, prompt: str, length_s: float, model: str) -> Path:
    """An Eleven Music instrumental bed of `length_s` (subscription; ~12.5 credits a second), cached by
    prompt, length and model: one call ever."""
    import hashlib
    import os
    import urllib.request

    ms = round(length_s * 1000)
    key = hashlib.sha256(json.dumps([prompt, ms, model]).encode()).hexdigest()[:16]
    out = cache / "music" / f"el-{key}.mp3"
    if out.exists():
        return out
    body = {"prompt": prompt, "music_length_ms": ms, "model_id": model, "force_instrumental": True}
    req = urllib.request.Request(
        MUSIC_API, data=json.dumps(body).encode(),
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
    )  # fmt: skip
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = resp.read()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(out)
    return out


def el_voice(cache: Path, text: str, voice: Any) -> tuple[Path, float]:
    """A narrated line (ElevenLabs with-timestamps, cached by text and voice) and its length in seconds."""
    import base64

    from create.voice import elevenlabs, text_hash

    key = text_hash(text, voice)
    out = cache / "voiceover" / f"{key}.mp3"
    meta = out.with_suffix(".json")
    if not meta.exists():
        body, _ = elevenlabs(text, voice)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(body["audio_base64"]))
        al = body.get("normalized_alignment") or body["alignment"]
        meta.write_text(json.dumps({"duration_s": float(al["character_end_times_seconds"][-1])}))
    return out, float(json.loads(meta.read_text())["duration_s"])


def events(meta: dict[str, Any], cfg: FootageSfx) -> list[tuple[float, str]]:
    """(time, sound) from the reel's sidecar: widget entrances, layout moves, call-to-action clicks."""
    out: list[tuple[float, str]] = []
    for group in ("overlays", "product"):
        for it in (meta.get(group) or {}).get("items", []):
            carried = it.get("handover") in ("morph", "push")  # one surface moving on (ADR 0033)
            out.append((float(it["t0"]) + cfg.pop_offset_s, "whoosh" if carried else "pop"))
            if it.get("kind") == "cta" and it.get("click") is not None:
                out.append((float(it["click"]), "click"))
    for ev in (meta.get("props") or {}).get("events", []):  # characters and effects (ADR 0027)
        out.append((float(ev["t"]), str(ev["sound"])))
    for ev in meta.get("audio", []):  # the plan's own cues: files, never thinned (ADR 0030)
        out.append((float(ev["t"]), "file:" + json.dumps([ev["file"], ev["gain_db"]])))
    scenes = (meta.get("layout") or {}).get("scenes", [])
    for a, b in pairwise(scenes):
        if a["layout"] != b["layout"]:
            out.append((max(0.0, float(b["start_s"]) - cfg.whoosh_lead_s), "whoosh"))
    out.sort()
    kept: list[tuple[float, str]] = []
    for t, n in out:  # never two UI sounds closer than min_gap_s: the first wins (planned cues always play)
        if n.startswith("file:") or not kept or t - kept[-1][0] >= cfg.min_gap_s:
            kept.append((t, n))
    return kept


def mix(video: Path, meta_path: Path, out: Path, cache: Path, cfg: FootageSfx, true_peak_db: float) -> Path:
    """`video` with its audio plus the sound design (video stream copied, one AAC encode)."""
    meta = json.loads(meta_path.read_text())
    evs = events(meta, cfg)
    if not evs:
        raise ValueError("no sound events in the sidecar")
    inputs: list[str] = ["-i", str(video)]
    chains = []
    for k, (t, name) in enumerate(evs):
        if name.startswith("file:"):  # a planned cue: its own file and gain (effects: under the voice)
            path, gain = json.loads(name[5:])
            inputs += ["-i", str(path)]
        else:
            inputs += ["-i", str(sound(cache, name))]
            gain = cfg.level_db + cfg.trim_db.get(name, 0.0)
        ms = max(0, round(t * 1000))
        chains.append(f"[{k + 1}:a]volume={gain:g}dB,adelay={ms}|{ms}[s{k}]")
    labels = "".join(f"[s{k}]" for k in range(len(evs)))
    limit = 10 ** (true_peak_db / 20)
    graph = (
        ";".join(chains)
        + f";{labels}amix=inputs={len(evs)}:normalize=0[fx];"
        + "[0:a][fx]amix=inputs=2:normalize=0:duration=first,"
        + f"aresample=192000,alimiter=limit={limit:.4f}:level=false:attack=1:release=50,aresample=48000[a]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", graph, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)],
        check=True,
    )  # fmt: skip
    return out
