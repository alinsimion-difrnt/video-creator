"""Card-style graphic layer for a TikTok (skill card-style).

A transparent 1080x1920 GSAP page, stepped frame by frame in headless Chromium and laid over a base video
whose speaker sits in y 960-1920.

  card_style.py init   <dir> --words words.json        # starter page, GSAP, Montserrat, data.js
  card_style.py qa     <dir>                           # layout check every 0.1 s (prints clean)
  card_style.py stills <dir> --base b.mp4 --at 1.2,6.0  # stills + sheetN.jpg for a reviewer
  card_style.py render <dir> --base b.mp4 --out o.mp4 [--audio mix.wav]
(run as `uv run python scripts/card_style.py ...`)

words.json: {"words": [{"w": "ChatGPT", "t0": 0.15, "t1": 0.55, "seg": "A"}, ...], "end": 65.1,
"drop": 56.2 | null, "glue": ["wall street", ...]}. Times are the edited video's clock, never guesses.
`render` also writes <dir>/sfx_cues.json: the [kind, t] pairs the page pushed
(card | pop | swipe | hit | boom | whoosh), for the mixer.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FPS = 30
MONTSERRAT = "Montserrat:wght@600;800;900"
ENCODE = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-maxrate", "16M", "-bufsize", "32M"]


def init(d: Path, words: Path) -> None:
    from create.bundle import fonts, gsap
    from create.footage.panel import google_css

    d.mkdir(parents=True, exist_ok=True)
    page = d / "index.html"
    if not page.exists():
        shutil.copy(ROOT / "create" / "kit" / "card-style.html", page)
        print(f"{page} (the starter: replace its two example scenes)")
    cache = ROOT / "data" / "create" / "_cache"
    shutil.copy(gsap(cache), d / "gsap.min.js")
    css, files = fonts(cache, google_css([MONTSERRAT]))
    (d / "fonts").mkdir(exist_ok=True)
    for f in files:
        shutil.copy(f, d / "fonts" / f.name)
    (d / "fonts" / "fonts.css").write_text(css.replace("url(fonts/", "url("))
    data = json.loads(words.read_text())
    out = {
        "words": [
            {"w": w["w"], "t0": w["t0"], "t1": w["t1"], "seg": w.get("seg", "")} for w in data["words"]
        ],
        "end": data["end"],
        "drop": data.get("drop"),
        "glue": data.get("glue", []),
    }
    (d / "data.js").write_text("window.DATA = " + json.dumps(out) + ";\n")
    print(f"{d}/data.js: {len(out['words'])} words, end {out['end']:.2f}s")


def _open(pw: Any, d: Path) -> tuple[Any, Any, list[str]]:
    from create.browser import launch

    errors: list[str] = []
    b = launch(pw)
    tab = b.new_page(viewport={"width": 1080, "height": 1920})
    tab.on("pageerror", lambda e: errors.append(str(e)))
    tab.goto((d / "index.html").as_uri())
    try:
        tab.wait_for_function("window.ready === true", timeout=20000)
    except Exception as e:  # a script error means ready never comes
        raise SystemExit(f"page never became ready: {errors or e}") from e
    return b, tab, errors


def qa(d: Path) -> int:
    from playwright.sync_api import sync_playwright

    issues: dict[str, list[float]] = {}
    with sync_playwright() as pw:
        b, tab, errors = _open(pw, d)
        print("cards (scene, height, top):", tab.evaluate("window.cards"))
        end = tab.evaluate("window.DATA.end")
        t = 0.0
        while t < end:
            tab.evaluate(f"window.seek({t:.2f})")
            for msg in tab.evaluate("window.qa()"):
                issues.setdefault(msg, []).append(round(t, 1))
            t += 0.1
        b.close()
    for k, v in sorted(issues.items(), key=lambda kv: kv[1][0]):
        print(f"{v[0]:5.1f}-{v[-1]:5.1f} ({len(v):3d}x) {k}")
    lasting = {k: v for k, v in issues.items() if len(v) > 1}  # one-frame flags are mid-transition
    print(
        "clean" if not lasting and not errors else f"{len(lasting)} lasting issues, page errors: {errors[:3]}"
    )
    return 1 if lasting or errors else 0


def stills(d: Path, base: Path, times: list[float], out: Path) -> None:
    from playwright.sync_api import sync_playwright

    out.mkdir(parents=True, exist_ok=True)
    shots: list[Path] = []
    with sync_playwright() as pw:
        b, tab, _ = _open(pw, d)
        for t in times:
            tab.evaluate(f"window.seek({t})")
            png = tab.screenshot(omit_background=True)
            p = out / f"st_{t:06.2f}.png"
            cmd = [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-ss",
                f"{t:.3f}",
                "-i",
                str(base),
                "-f",
                "image2pipe",
                "-i",
                "-",
                "-filter_complex",
                "[0:v][1:v]overlay=0:0",
                "-frames:v",
                "1",
                str(p),
            ]
            subprocess.run(cmd, input=png, check=True)
            shots.append(p)
        b.close()
    for k in range(0, len(shots), 9):  # sheets of up to 9 stills, 300 px wide each
        grp = list(range(k, min(k + 9, len(shots))))
        args: list[str] = []
        for i in grp:
            args += ["-i", str(shots[i])]
        lab = "".join(
            f"[{j}:v]scale=300:533,drawtext=text='{times[i]:.2f}':x=6:y=6:fontsize=26:fontcolor=red:box=1:"
            f"boxcolor=white@0.8[t{j}];"
            for j, i in enumerate(grp)
        )
        stack = "".join(f"[t{j}]" for j in range(len(grp)))
        stack += f"hstack=inputs={len(grp)}" if len(grp) > 1 else "null"
        sheet = out / f"sheet{k // 9 + 1}.jpg"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", lab + stack, str(sheet)], check=True
        )
    print(f"{len(shots)} stills + sheets in {out}")


def render(d: Path, base: Path, out: Path, audio: Path | None) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        b, tab, errors = _open(pw, d)
        (d / "sfx_cues.json").write_text(json.dumps(tab.evaluate("window.SFX")))
        n = round(tab.evaluate("window.DATA.end") * FPS)
        aud = ["-i", str(audio)] if audio else []
        ov = 2 if audio else 1
        cmd = [
            "ffmpeg", "-v", "error", "-y", "-i", str(base), *aud,
            "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
            "-filter_complex", f"[0:v][{ov}:v]overlay=0:0:eof_action=repeat,format=yuv420p[v]",
            "-map", "[v]", "-map", "1:a" if audio else "0:a", *ENCODE, "-r", str(FPS),
            "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", str(out),
        ]  # fmt: skip
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        assert enc.stdin is not None
        for i in range(n):
            tab.evaluate(f"window.seek({i / FPS:.5f})")
            enc.stdin.write(tab.screenshot(omit_background=True))
        enc.stdin.close()
        enc.wait()
        b.close()
    print(f"{out}: {n} frames, rc {enc.returncode}" + (f", page errors {errors[:3]}" if errors else ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("dir", type=Path)
    p.add_argument("--words", type=Path, required=True)
    p = sub.add_parser("qa")
    p.add_argument("dir", type=Path)
    p = sub.add_parser("stills")
    p.add_argument("dir", type=Path)
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--at", required=True)
    p.add_argument("--out", type=Path)
    p = sub.add_parser("render")
    p.add_argument("dir", type=Path)
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--audio", type=Path)
    a = ap.parse_args()
    if a.cmd == "init":
        init(a.dir, a.words)
    elif a.cmd == "qa":
        sys.exit(qa(a.dir))
    elif a.cmd == "stills":
        stills(a.dir, a.base, [float(x) for x in a.at.split(",")], a.out or a.dir / "stills")
    else:
        render(a.dir, a.base, a.out, a.audio)


if __name__ == "__main__":
    main()
