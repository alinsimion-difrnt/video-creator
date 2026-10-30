"""C8 audit: measure where critical text and logos sit in each built scene, then check the frame's safe area.

Runs each scene of the render bundle (data/create/<project>/bundle/<scene>/index.html) in headless Chromium,
seeks its paused GSAP timeline every `audit_step_s` and reads the boxes of visible text and logos (clipped by
overflow masks, with every ancestor's opacity). `create.safezone` decides what breaks the frame's rules.
Output: projects/<project>/audit/safe-zones.json. Needs `uv run --with playwright` (not a project
dependency); the browser is found by create/browser.py (CHROMIUM=<path> to choose one).

Scene markup can opt out per element: `data-safe-exempt="reason"` (decoration) or `data-role="caption"`.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from create.safezone import persistent, violations
from lens import __version__
from lens.hashing import cache_key
from lens.schemas.common import Annotator, Provenance
from lens.schemas.config import LensConfig
from lens.schemas.create import Box, SafeZoneReport, Storyboard, Tokens

STAGE = "c8_audit"

BOXES_JS = """
([scene, t, minOpacity]) => {
  const root = document.getElementById(scene) || document.body;
  const tl = window.__timelines && window.__timelines[scene];
  if (tl) tl.seek(t, false);
  const frame = root.getBoundingClientRect();
  const path = (el) => {
    const parts = [];
    for (let e = el; e && e !== root; e = e.parentElement) {
      const cls = [...e.classList].slice(0, 2).map((c) => "." + c).join("");
      const i = e.parentElement ? [...e.parentElement.children].indexOf(e) + 1 : 1;
      parts.unshift(e.tagName.toLowerCase() + cls + ":nth-child(" + i + ")");
    }
    return parts.join(">");
  };
  const visible = (el) => {
    let op = 1;
    for (let e = el; e; e = e.parentElement) {
      const cs = getComputedStyle(e);
      if (cs.display === "none" || cs.visibility === "hidden") return 0;
      op *= parseFloat(cs.opacity);
      if (e === root) break;
    }
    return op;
  };
  const clip = (el, r) => {
    let [x0, y0, x1, y1] = [r.left, r.top, r.right, r.bottom];
    for (let e = el.parentElement; e && e !== root.parentElement; e = e.parentElement) {
      const cs = getComputedStyle(e);
      if (cs.overflow !== "visible" || cs.overflowX !== "visible" || cs.overflowY !== "visible") {
        const c = e.getBoundingClientRect();
        x0 = Math.max(x0, c.left); y0 = Math.max(y0, c.top); x1 = Math.min(x1, c.right); y1 = Math.min(y1, c.bottom);
      }
    }
    return x1 - x0 > 0.5 && y1 - y0 > 0.5 ? [x0, y0, x1, y1] : null;
  };
  const out = [];
  const add = (el, kind, rect, text) => {
    if (el.closest("[data-safe-exempt]")) return;
    const op = visible(el);
    if (op < minOpacity) return;
    const c = clip(el, rect);
    if (!c) return;
    const role = el.closest("[data-role=caption]") ? "caption" : kind;
    out.push({ element: path(el), kind: role, text: text.slice(0, 60), opacity: Math.min(1, op),
      x0: c[0] - frame.left, y0: c[1] - frame.top, x1: c[2] - frame.left, y1: c[3] - frame.top });
  };
  root.querySelectorAll(".logo").forEach((el) => add(el, "logo", el.getBoundingClientRect(), ""));
  root.querySelectorAll("*").forEach((el) => {
    if (el.closest(".logo") || el.tagName === "SCRIPT" || el.tagName === "STYLE") return;
    const nodes = [...el.childNodes].filter((n) => n.nodeType === 3 && n.textContent.trim());
    if (!nodes.length) return;
    const range = document.createRange();
    range.setStartBefore(nodes[0]); range.setEndAfter(nodes[nodes.length - 1]);
    const r = range.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) add(el, "text", r, nodes.map((n) => n.textContent.trim()).join(" "));
  });
  return { boxes: out, duration: tl ? tl.duration() : 0 };
}
"""


def probe_scene(
    index_html: Path, scene: str, width: int, height: int, step_s: float, min_opacity: float
) -> list[Box]:
    """Boxes of visible text and logos at every sample time of one scene."""
    from playwright.sync_api import sync_playwright

    from create.browser import launch

    boxes: list[Box] = []
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page(viewport={"width": width, "height": height})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(index_html.resolve().as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready.then(() => true)")
        if errors:
            raise RuntimeError(f"{scene}: page errors: {errors}")
        duration = float(page.evaluate(BOXES_JS, [scene, 0, min_opacity])["duration"])
        n = max(0, round(duration / step_s))
        for i in range(n + 1):
            t = round(min(i * step_s, duration), 3)
            data = page.evaluate(BOXES_JS, [scene, t, min_opacity])
            boxes += [Box(scene=scene, t=t, **b) for b in data["boxes"]]
        browser.close()
    return boxes


def run_audit(root: Path, project: str, cfg: LensConfig) -> tuple[Path, SafeZoneReport]:
    design = cfg.create.design
    base = root / "projects" / project
    tokens = Tokens.model_validate(json.loads((base / "tokens.json").read_text()))
    board = Storyboard.model_validate(json.loads((base / "storyboard.json").read_text()))
    frame = design.frames[tokens.frame]
    bundle = root / "data" / "create" / project / "bundle"
    scenes = [s.scene for s in board.scenes if (bundle / s.scene / "index.html").exists()]
    if not scenes:
        raise FileNotFoundError(
            f"no built scenes in {bundle.relative_to(root)} (run: uv run create build {project})"
        )
    boxes: list[Box] = []
    for sc in scenes:
        boxes += probe_scene(
            bundle / sc / "index.html",
            sc,
            frame.width,
            frame.height,
            design.audit_step_s,
            design.audit_min_opacity,
        )
    hits = violations(boxes, frame, design.audit_tolerance_px)
    issues = persistent(hits, design.audit_step_s, design.audit_min_hold_s)
    sources = {sc: (bundle / sc / "index.html").read_text() for sc in scenes}
    report = SafeZoneReport(
        provenance=Provenance(
            tool_version=__version__,
            stage=STAGE,
            annotator=Annotator.CODE,
            input_hash=cache_key(
                {"scenes": sources, "frame": frame.model_dump(), "design": design.model_dump()}
            ),
            created_at=datetime.now(UTC),
        ),
        project=project,
        frame=tokens.frame,
        step_s=design.audit_step_s,
        min_hold_s=design.audit_min_hold_s,
        scenes=scenes,
        boxes_checked=len(boxes),
        issues=issues,
        ok=not issues,
    )
    path = base / "audit" / "safe-zones.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(report.model_dump_json(indent=1) + "\n")
    return path, report
