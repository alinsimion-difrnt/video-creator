"""Build a measurement answer key from a HyperFrames project's source (our own renders only).

    uv run --with playwright python scripts/hyperframes_answer_key.py PROJECT_DIR OUT.json [--gsap gsap.min.js]

Reads `index.html` (scene, voice, music and SFX clips with data-start/data-duration) and runs each scene
composition in headless Chromium to walk its live GSAP timeline: every tween's absolute start, duration,
ease, tweened properties and its targets' on-screen boxes at the tween's end. Times are seconds on the
render's clock; boxes are in the composition's pixels (data-width x data-height).

The output is ground truth for lens' measurements (BUILD_PLAN 11.1, M4): transitions, SFX placement,
eases and durations. No media is read or written.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

GSAP_URL = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
CHROMIUM = os.environ.get("CHROMIUM", "/opt/pw-browsers/chromium")


class _Clips(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.clips: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        if "data-start" in a:
            self.clips.append({"tag": tag, **a})


def clips(index_html: str) -> dict[str, list[dict[str, object]]]:
    p = _Clips()
    p.feed(index_html)
    scenes, sfx, voice, music = [], [], [], []
    for c in p.clips:
        start, dur = round(float(c["data-start"]), 4), round(float(c.get("data-duration", "0")), 4)
        if c["tag"] == "div" and "data-composition-src" in c and "frames/" in c["data-composition-src"]:
            scenes.append({"id": c["data-composition-id"], "src": c["data-composition-src"], "start_s": start,
                           "duration_s": dur, "end_s": round(start + dur, 4)})  # fmt: skip
        elif c["tag"] == "audio":
            item = {"id": c.get("id", ""), "file": Path(c.get("src", "")).name, "start_s": start,
                    "duration_s": dur, "volume": float(c.get("data-volume", "1"))}  # fmt: skip
            track = int(c.get("data-track-index", "0"))
            (sfx if track >= 20 else voice if track == 10 else music).append(item)
    scenes.sort(key=lambda s: s["start_s"])  # type: ignore[arg-type,return-value]
    transitions = []
    for a, b in itertools.pairwise(scenes):
        overlap = round(float(a["end_s"]) - float(b["start_s"]), 4)  # type: ignore[arg-type]
        transitions.append({"into": b["id"], "start_s": b["start_s"], "duration_s": max(overlap, 0.0)})
    return {"scenes": scenes, "transitions": transitions, "sfx": sfx, "voice": voice, "music": music}


# Walk a GSAP timeline; returns tweens with scene-local start, then seeks to each end to read boxes.
WALK_JS = r"""
(id) => {
  const tl = window.__timelines[id];
  const out = [];
  const defaults = (tl.vars && tl.vars.defaults) || {};
  const META = new Set(["ease","duration","delay","stagger","onComplete","onStart","onUpdate","immediateRender",
    "overwrite","repeat","yoyo","repeatDelay","startAt","paused","id","callbackScope","lazy","data","runBackwards",
    "keyframes","inherit","transformOrigin","defaults"]);
  const plain = (v) => (typeof v === "number" || typeof v === "string") ? v : undefined;
  const props = (vars) => { const o = {}; for (const k in (vars || {})) { if (!META.has(k)) { const v = plain(vars[k]);
    if (v !== undefined) o[k] = v; } } return o; };
  const name = (el) => !el || !el.tagName ? "object" :
    (el.id ? "#" + el.id : el.tagName.toLowerCase() + (el.classList.length ? "." + [...el.classList].join(".") : ""));
  function walk(t, offset) {
    for (const c of t.getChildren(false, true, true)) {
      const start = offset + c.startTime();
      if (c.getChildren) { walk(c, start); continue; }
      const v = c.vars || {};
      let ease = v.ease !== undefined ? v.ease : (defaults.ease !== undefined ? defaults.ease : "power1.out");
      if (c.duration() === 0) ease = "set"; else if (typeof ease === "function") ease = "custom";
      const targets = (c.targets() || []).filter(x => x && x.tagName);
      out.push({ start: start, duration: c.duration(), ease: String(ease), to: props(v),
        from: props(v.startAt), stagger: plain(v.stagger) ?? (v.stagger ? "object" : null),
        targets: targets.map(name), n_targets: targets.length, _t: targets });
    }
  }
  walk(tl, 0);
  const root = document.querySelector("#stage");
  const r0 = root.getBoundingClientRect();
  for (const tw of out) {
    tl.seek(tw.start + tw.duration, false);
    tw.boxes = tw._t.slice(0, 12).map(el => { const r = el.getBoundingClientRect();
      return [r.left - r0.left, r.top - r0.top, r.right - r0.left, r.bottom - r0.top].map(x => Math.round(x * 10) / 10); });
    delete tw._t;
  }
  return { tweens: out, duration: tl.duration() };
}
"""


def _page(template_html: str, gsap: str, width: int, height: int) -> str:
    inner = re.search(r"<template>(.*)</template>", template_html, re.S)
    body = inner.group(1) if inner else template_html
    body = re.sub(r'<script[^>]*src="[^"]*gsap[^"]*"[^>]*>\s*</script>', "", body)
    return (
        "<!doctype html><html><head><meta charset=utf-8>"
        f"<style>html,body{{margin:0}}#stage{{position:relative;width:{width}px;height:{height}px;"
        f"overflow:hidden}}</style><script>{gsap}</script></head><body><div id=stage>{body}</div></body></html>"
    )


def scene_tweens(project: Path, scenes: list[dict[str, object]], gsap: str) -> dict[str, dict[str, object]]:
    from playwright.sync_api import sync_playwright

    result: dict[str, dict[str, object]] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM)
        for s in scenes:
            html = (project / str(s["src"])).read_text(encoding="utf-8")
            m = re.search(r'data-width="(\d+)"\s+data-height="(\d+)"', html)
            w, h = (int(m.group(1)), int(m.group(2))) if m else (1920, 1080)
            page = browser.new_page(viewport={"width": w, "height": h})
            errors: list[str] = []
            page.on("pageerror", lambda e, errs=errors: errs.append(str(e)))
            page.set_content(_page(html, gsap, w, h), wait_until="domcontentloaded")
            # Scene scripts run synchronously while the page parses, so the timeline exists by now.
            if not page.evaluate(f"!!(window.__timelines && window.__timelines[{json.dumps(s['id'])}])"):
                found = page.evaluate("Object.keys(window.__timelines || {})")
                raise SystemExit(f"{s['id']}: no timeline (found {found}); page errors: {errors}")
            data = page.evaluate(WALK_JS, s["id"])
            data["errors"] = errors
            data["size"] = [w, h]
            result[str(s["id"])] = data
            page.close()
        browser.close()
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--gsap", type=Path, help="local gsap.min.js (default: download 3.14.2 from jsDelivr)")
    args = ap.parse_args()
    key = clips((args.project / "index.html").read_text(encoding="utf-8"))
    if args.gsap:
        gsap = args.gsap.read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(GSAP_URL, timeout=30) as r:
            gsap = r.read().decode()
    per_scene = scene_tweens(args.project, key["scenes"], gsap)
    tweens = []
    for s in key["scenes"]:
        data = per_scene[str(s["id"])]
        for i, tw in enumerate(data["tweens"]):  # type: ignore[arg-type]
            tw["scene"] = s["id"]
            tw["id"] = f"{s['id']}#{i:02d}"
            tw["start_s"] = round(float(s["start_s"]) + tw.pop("start"), 4)  # type: ignore[arg-type]
            tw["duration_s"] = round(tw.pop("duration"), 4)
            tweens.append(tw)
        s["timeline_errors"] = data["errors"]
    key["tweens"] = tweens
    key["frame_size"] = per_scene[str(key["scenes"][0]["id"])]["size"] if key["scenes"] else None
    key["source"] = "HyperFrames project (index.html + compositions/frames/*.html), GSAP 3.14.2 timelines"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(key, indent=1) + "\n", encoding="utf-8")
    print(f"{len(key['scenes'])} scenes, {len(key['transitions'])} transitions, {len(key['sfx'])} SFX, "
          f"{len(tweens)} tweens -> {args.out}")  # fmt: skip


if __name__ == "__main__":
    main()
