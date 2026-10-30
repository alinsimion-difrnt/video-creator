# ruff: noqa: E501  (widget specs read best one per line)
"""The motion kit (create/kit/motion.js) in Chromium: every widget and entrance style is seek-safe.

HyperFrames renders by seeking the paused timeline to each frame, not by playing it, so a widget must look
the same at a time whichever way the playhead got there. This builds every kind, scrubs its timeline
forwards, backwards and in a shuffled order, and compares the full state of every element (opacity,
display, visibility, transform, fill) at each time. It also checks the contract every widget keeps:
invisible before t0, on screen between, hidden after t1.
"""

import json
import random

import pytest

from lens.config import REPO_ROOT

KIT = REPO_ROOT / "create" / "kit"
GSAP = sorted((REPO_ROOT / "data" / "create" / "_cache").glob("gsap-*.min.js"))
T0, T1 = 0.5, 4.5
SPECS = {
    "chat": {"app": "ChatGPT", "prompt": "Best restaurant in Budapest", "answer": ["**Jade Garden**", "Two"],
             "sources": ["Maps", "Reviews"], "highlight": 0, "marks": [0.6, 1.4, 1.8, 3.0]},
    "search": {"query": "best ramen", "results": ["**One**", "Two"], "highlight": 0, "marks": [0.6, 1.2, 1.6, 3.0]},
    "sources": {"title": "Sources", "items": [{"name": "Maps"}, {"name": "Blog", "icon": "px:star"}],
                "highlight": 1, "marks": [1.0, 1.6, 2.6]},
    "review": {"name": "Ana", "stars": 5, "text": "Great view and the duck was good.", "highlights": ["view"]},
    "counter": {"value": 10, "suffix": "years", "label": "in marketing"},
    "chart": {"title": "More sales", "to": 128, "suffix": "%"},
    "cta": {"text": "Start free trial", "url": "acme.example", "marks": [2.5]},
    "sticker": {"text": "Budapest", "icon": "px:pin", "accent": True, "tilt": -3},
    "queries": {"vague": "restaurant", "specific": ["**ramen** near me", "late **dinner**"], "marks": [1, 2, 3]},
    "tiles": {"items": [{"name": "Food", "icon": "fork"}, {"name": "Hotels", "icon": "bed"}], "marks": [1, 2]},
    "pins": {"city": "Budapest", "places": [{"name": "Jade"}, {"name": "Duna"}], "marks": [2.0, 3.0]},
    "logo": {"src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10'/%3E"},
    "pixel": {"sprite": "robot", "label": "ASK AI", "card": True, "marks": [3.0]},
    "shredder": {"videos": ["Tour", "Pricing"], "label": "a frame every 0.3 s", "machine": "Claude",
                 "marks": [1.0, 2.0, 2.6]},
    "code": {"file": "video.yaml", "lines": ["font: Inter", "accent: \"#ff7a1a\""],
             "edits": [{"line": 0, "to": "mono"}, {"line": 1, "to": "\"#22c55e\""}], "marks": [1.5, 2.8]},
    "bucket": {"title": "R2 bucket", "name": "free plan", "folders": [{"name": "videos", "count": 100},
               {"name": "frames", "count": 12000}], "marks": [1.5, 2.8]},
    "agents": {"maker": "Creator agent", "reviewers": ["Reviewer"], "scores": [7, 9], "you": "Robert",
               "verdict": "up", "meter": "Learns your taste", "marks": [0.8, 1.6, 2.4, 3.2]},
    "bars": {"title": "Got an AI answer", "items": [{"name": "Questions", "value": 97}, {"name": "Local", "value": 34}],
             "suffix": "%", "highlight": 1, "marks": [1.0, 2.0]},
    "handoff": {"giver": "salesman", "receiver": "claude", "item": "coin", "label": "#1", "marks": [0.8, 2.0, 2.8]},
}  # fmt: skip
CASES = [(k, s) for k, s in SPECS.items()] + [
    ("chat", {**SPECS["chat"], "motion": m, "from": "left"}) for m in ("slide", "flip", "focus", "pixel", "wipe", "unfold")
] + [
    ("pixel", {"sprite": "trophy", "build": b, "idle": i}) for b, i in (("dissolve", "spin"), ("pop", "none"))
] + [("search", {**SPECS["search"], "step": "1", "kicker": "Ask"})] + [
    ("tiles", {**SPECS["tiles"], "step": "3", "kicker": "Write down", "footer": "method", "footer_site": "acme.example"}),
    ("chat", {**SPECS["chat"], "footer": "method"}),
    ("queries", {"specific": ["**ramen** near me", "late **dinner**"], "marks": [1, 2, 3]}),
    ("search", {"query": "ai answers", "answer": ["Links were **small**"], "link": "example.com",
                "marks": [0.6, 1.2, 1.6, 3.0]}),
    ("search", {"query": "ai answers", "answer": ["Links were **small**"], "link": "example.com",
                "marks": [0.6, 1.2, 1.6, 2.2, 3.0]}),
] + [
    ("sources", {**SPECS["sources"], "items": [{"name": "Research", "verdict": "yes"}, {"name": "Ads", "verdict": "half"},
                 {"name": "Next step", "verdict": "no"}], "marks": [1.0, 1.6, 2.2]}),
    ("sticker", {**SPECS["sticker"], "peel": True, "marks": [2.5]}),
    ("handoff", {"marks": [0.6, 1.6, 2.2], "card": False}),
]  # fmt: skip

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
:root { --ink:#3E0863; --accent:#00AA90; --accent-fill:#00AA90; --second:#6733FD; --success:#16A34A; --error:#DC2626; --muted:#6B7280;
  --surface:#fff; --fill:#F3F4F6; --chip:#E5E7EB; --tint:rgba(0,170,144,.12); --hl:rgba(0,170,144,.3);
  --map:#E8EEF3; --river:#BFD7EA; --body:sans-serif; --heading:sans-serif; }
</style><style>CSS</style></head><body><div id="stage"></div>
<script>GSAP</script><script>MOTION</script>
<script>
window.run = function (cases, t0, t1) {
  return cases.map(function (c, i) {
    const spec = Object.assign({}, c[1], { kind: c[0], w: 640, t0: t0, t1: t1 });
    const w = MK.build(spec);
    const box = document.createElement("div"); box.id = "c" + i; box.appendChild(w.el);
    document.getElementById("stage").appendChild(box);
    const tl = gsap.timeline({ paused: true }); w.play(tl); tl.set({}, {}, t1 + 1);
    window["tl" + i] = tl;
    return i;
  });
};
// Reel flow (ADR 0033): two product cards in boxes like reel.html's, carried into each other by MK.handover;
// a shared step label; the drifting background.
window.runPair = function (i, kinds, specs, how, T, H) {
  const layer = document.createElement("div"); layer.id = "p" + i;
  layer.style.cssText = "position:relative;width:1080px;height:900px;overflow:hidden";
  document.getElementById("stage").appendChild(layer);
  const place = function (spec) {
    const bx = document.createElement("div"); bx.className = "box";
    bx.style.cssText = "position:absolute;left:120px;top:60px;width:760px;height:700px;display:flex;align-items:flex-start;justify-content:center";
    const fit = document.createElement("div"); bx.appendChild(fit); layer.appendChild(bx);
    const w = MK.build(spec); fit.appendChild(w.el); return { w: w, bx: bx };
  };
  const a = place(Object.assign({}, specs[0], { kind: kinds[0], w: 640, t0: 0.5, t1: T + H, handover_out: how, handover_s: H }));
  const b = place(Object.assign({}, specs[1], { kind: kinds[1], w: 640, t0: T, t1: T + 3, handover_in: how, handover_s: H }));
  const tl = gsap.timeline({ paused: true }); a.w.play(tl); b.w.play(tl);
  MK.handover(tl, { root: a.w.root, box: a.bx, t0: 0.5, t1: T + H }, { root: b.w.root, box: b.bx, t0: T, t1: T + 3 }, how, H, layer);
  tl.set({}, {}, T + 4);
  window["ptl" + i] = tl; window["pa" + i] = a.w.root; window["pb" + i] = b.w.root;
};
window.runKicker = function (i, steps, t0, t1) {
  const w = MK.kicker({ text: "SEO on a budget", steps: steps, t0: t0, t1: t1, w: 760 });
  const box = document.createElement("div"); box.id = "k" + i; box.appendChild(w.el);
  document.getElementById("stage").appendChild(box);
  const tl = gsap.timeline({ paused: true }); w.play(tl); tl.set({}, {}, t1 + 1);
  window["ktl" + i] = tl;
};
window.runAmbient = function (i, dur) {
  const w = MK.ambient({ duration: dur, loop_s: 4 });
  const box = document.createElement("div"); box.id = "a" + i; box.style.cssText = "position:relative;width:1080px;height:800px"; box.appendChild(w.el);
  document.getElementById("stage").appendChild(box);
  const tl = gsap.timeline({ paused: true }); w.play(tl); tl.set({}, {}, dur);
  window["atl" + i] = tl;
};
window.fingerprint = function (root) {
  const all = [root].concat(Array.prototype.slice.call(root.querySelectorAll("*")));
  return all.map(function (e) {
    const s = getComputedStyle(e), r = e.getBoundingClientRect();
    const tr = s.transform === "matrix(1, 0, 0, 1, 0, 0)" ? "none" : s.transform;
    return [s.opacity, s.display, s.visibility, tr, s.clipPath, Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)].join("|");
  }).join(";");
};
window.shown = function (el) {
  for (let e = el; e && e.id !== "stage"; e = e.parentElement) {
    const s = getComputedStyle(e);
    if (s.display === "none" || s.visibility === "hidden" || parseFloat(s.opacity) < 0.05) return false;
  }
  return true;
};
window.pstate = function (i, t) {
  window["ptl" + i].seek(t, false);
  const layer = document.getElementById("p" + i), car = layer.querySelector(".mk-carrier");
  return { fp: fingerprint(layer), a: shown(window["pa" + i]), b: shown(window["pb" + i]),
    bop: parseFloat(getComputedStyle(window["pb" + i]).opacity), car: car ? shown(car) : false,
    carw: car ? Math.round(car.getBoundingClientRect().width) : 0 };
};
window.kstate = function (i, t) {
  window["ktl" + i].seek(t, false);
  const root = document.getElementById("k" + i);
  const pills = Array.prototype.slice.call(root.querySelectorAll(".mk-steps b"));
  return { fp: fingerprint(root), on: shown(root.firstChild), pills: pills.map(shown) };
};
window.astate = function (i, t) {
  window["atl" + i].seek(t, false);
  return fingerprint(document.getElementById("a" + i));
};
window.state = function (i, t) {
  window["tl" + i].seek(t, false);
  const root = document.getElementById("c" + i).firstChild;
  const all = [root].concat(Array.prototype.slice.call(root.querySelectorAll("*")));
  const cs = getComputedStyle(root);
  return { op: parseFloat(cs.opacity), vis: cs.visibility, fp: all.map(function (e) {
    const s = getComputedStyle(e);
    const tr = s.transform === "matrix(1, 0, 0, 1, 0, 0)" ? "none" : s.transform;  // identity either way
    return [s.opacity, s.display, s.visibility, tr, s.fill, s.filter].join("|");
  }).join(";") };
};
</script></body></html>"""


@pytest.fixture(scope="module")
def page():
    from create.browser import available, launch

    if not available() or not GSAP:
        pytest.skip("needs playwright, Chromium and the GSAP cache (data/create/_cache)")
    from playwright.sync_api import sync_playwright

    html = (
        PAGE.replace("CSS", (KIT / "motion.css").read_text())
        .replace("GSAP", GSAP[-1].read_text())
        .replace("MOTION", (KIT / "motion.js").read_text())
    )
    with sync_playwright() as pw:
        browser = launch(pw)
        pg = browser.new_page(viewport={"width": 1080, "height": 1920})
        errors: list[str] = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.set_content(html)
        pg.evaluate("([c, a, b]) => run(c, a, b)", [CASES, T0, T1])
        yield pg, errors
        browser.close()


def test_every_widget_and_motion_builds_without_errors(page):
    pg, errors = page
    assert errors == []
    assert set(SPECS) == set(pg.evaluate("MK.kinds"))  # every kind is covered here


@pytest.mark.parametrize(
    "i", range(len(CASES)), ids=[f"{k}-{s.get('motion') or s.get('build') or ''}" for k, s in CASES]
)
def test_widgets_are_seek_safe_and_keep_their_window(page, i):
    pg, _ = page
    times = [round(T0 - 0.3 + k * 0.1, 2) for k in range(int((T1 - T0 + 1.0) / 0.1))]
    get = lambda t: pg.evaluate("([i, t]) => state(i, t)", [i, t])  # noqa: E731
    forward = {t: get(t) for t in times}
    shuffled = times[:]
    random.Random(i).shuffle(shuffled)
    for t in [*reversed(times), *shuffled]:
        assert get(t)["fp"] == forward[t]["fp"], (
            f"{CASES[i][0]}: the state at {t} s depends on the seek order"
        )
    assert forward[times[0]]["op"] == 0  # not there before t0
    assert max(s["op"] for s in forward.values()) > 0.9  # fully on screen in its window
    after = forward[max(t for t in times if t >= T1 + 0.1)]
    assert after["op"] == 0 or after["vis"] == "hidden", json.dumps(after)[:200]  # gone by t1


# Reel flow (ADR 0033): hand-overs, the shared step label and the drifting background are seek-safe too.
PAIRS = [
    ("morph", ("chat", "sources")),
    ("push", ("chat", "sources")),
    ("stack", ("search", "counter")),
    ("morph", ("sticker", "sources")),
]  # a sticker is not a card: it pushes instead of morphing
T, H = 2.5, 0.5  # on the 0.1 s sample grid below


def _scrub(get, times, label):
    forward = {t: get(t) for t in times}
    shuffled = times[:]
    random.Random(len(label)).shuffle(shuffled)
    for t in [*reversed(times), *shuffled]:
        assert get(t)["fp"] == forward[t]["fp"], f"{label}: the state at {t} s depends on the seek order"
    return forward


@pytest.mark.parametrize("i", range(len(PAIRS)), ids=[f"{h}-{a}-{b}" for h, (a, b) in PAIRS])
def test_handovers_carry_one_card_into_the_next_and_are_seek_safe(page, i):
    pg, errors = page
    how, kinds = PAIRS[i]
    specs = [SPECS[kinds[0]], SPECS[kinds[1]]]
    pg.evaluate("([i, k, s, h, T, H]) => runPair(i, k, s, h, T, H)", [i, list(kinds), specs, how, T, H])
    assert errors == []
    times = [round(0.2 + k * 0.1, 2) for k in range(int((T + 4) / 0.1))]
    get = lambda t: pg.evaluate("([i, t]) => pstate(i, t)", [i, t])  # noqa: E731
    f = _scrub(get, times, f"{how}-{kinds}")
    assert not f[0.2]["a"] and not f[0.2]["b"]  # nothing before the first card
    assert f[1.5]["a"] and not f[1.5]["b"]  # the first card alone, settled
    assert not f[round(T - 0.1, 2)]["b"]  # the second is not there before its word
    assert (
        f[round(T + H + 0.2, 2)]["bop"] > 0.99 and f[round(T + H + 0.2, 2)]["b"]
    )  # fully on once carried in
    assert not f[round(T + H + 0.3, 2)]["a"]  # the first is gone by its t1
    # never a blank product area in the hand-over: a card or the carrier is on screen at every frame
    for t in times:
        if 1.2 <= t <= T + 2.5:
            assert f[t]["a"] or f[t]["b"] or f[t]["car"], f"{how}: nothing on screen at {t} s"
    if how == "morph" and kinds[0] != "sticker":
        mid = f[round(T + 0.3, 2)]
        assert mid["car"] and mid["carw"] > 300  # the carrier is the card between the two
        assert not f[round(T + H + 0.1, 2)]["car"] and not f[round(T - 0.1, 2)]["car"]
    else:
        assert not any(s["car"] for s in f.values())


def test_a_shared_step_label_flips_its_step_and_is_seek_safe(page):
    pg, errors = page
    steps = [[1.0, "1/4"], [2.5, "2/4"], [4.0, "3/4"]]
    pg.evaluate("([s, a, b]) => runKicker(0, s, a, b)", [steps, 1.0, 6.0])
    assert errors == []
    times = [round(0.5 + k * 0.1, 2) for k in range(60)]
    get = lambda t: pg.evaluate("([i, t]) => kstate(i, t)", [0, t])  # noqa: E731
    f = _scrub(get, times, "kicker")
    assert not f[0.5]["on"] and f[1.5]["on"] and f[5.5]["on"] and not f[6.3]["on"]
    assert f[1.5]["pills"] == [True, False, False]
    assert f[3.2]["pills"] == [False, True, False]  # flipped to the second step
    assert f[4.8]["pills"] == [False, False, True]


def test_the_drifting_background_is_seek_safe(page):
    pg, errors = page
    pg.evaluate("([i, d]) => runAmbient(i, d)", [0, 9.0])
    assert errors == []
    times = [round(k * 0.3, 2) for k in range(30)]
    get = lambda t: {"fp": pg.evaluate("([i, t]) => astate(i, t)", [0, t])}  # noqa: E731
    f = _scrub(get, times, "ambient")
    assert len({s["fp"] for s in f.values()}) > 20  # it moves
