/* Motion kit (create/kit): animated widgets for presenter videos, built in the browser from a spec.
   Shared by product scenes (split / full-frame product) and overlays (create/footage/reel.py). Every widget
   is drawn from the brand's CSS variables, uses no third-party logos or media, and is timed from word
   times passed in by Python (`t0`, `t1`, `marks`): code measures the timing, the plan names what to show.

   MK.build(spec) -> { el, play(tl) }: `el` is laid out at spec.w px wide; play() adds its tweens to the
   paused GSAP timeline. Every widget enters at t0, exits by t1, and is hard-hidden after its exit. */
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const ICONS = {
    sparkle: '<path d="M12 2l2.2 6.3L20.5 10l-6.3 2.2L12 18.5l-2.2-6.3L3.5 10l6.3-1.7z"/>',
    pin: '<path d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/>',
    star: '<path d="M12 2.5l2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17.3l-5.9 3.3 1.3-6.6L2.5 9.4l6.6-.8z"/>',
    search: '<path d="M10 3a7 7 0 1 0 4.2 12.6l5.1 5.1 1.4-1.4-5.1-5.1A7 7 0 0 0 10 3zm0 2a5 5 0 1 1 0 10 5 5 0 0 1 0-10z"/>',
    check: '<path d="M9.2 16.6L4.6 12l-1.4 1.4 6 6L21 7.6l-1.4-1.4z"/>',
    chat: '<path d="M4 4h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-5 4v-4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/>',
    globe: '<path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm6.9 9h-3a15 15 0 0 0-1.3-5.6A8 8 0 0 1 18.9 11zM12 4c.9 1.3 1.8 3.7 2 7h-4c.2-3.3 1.1-5.7 2-7zM9.4 5.4A15 15 0 0 0 8.1 11h-3a8 8 0 0 1 4.3-5.6zM5.1 13h3a15 15 0 0 0 1.3 5.6A8 8 0 0 1 5.1 13zm6.9 7c-.9-1.3-1.8-3.7-2-7h4c-.2 3.3-1.1 5.7-2 7zm2.6-1.4a15 15 0 0 0 1.3-5.6h3a8 8 0 0 1-4.3 5.6z"/>',
    cursor: '<path d="M5 2l14 10.5-6.2 1.2 3.7 7.3-2.7 1.4-3.7-7.4L5 19.5z"/>',
    fork: '<path d="M7 2v7a3 3 0 0 0 2 2.8V22h2V11.8A3 3 0 0 0 13 9V2h-1.5v6h-1V2h-1v6h-1V2zm9 0c-1.7 0-3 2.2-3 5v6h2v9h2V2z"/>',
    bed: '<path d="M3 6v13h2v-2h14v2h2v-6a3 3 0 0 0-3-3h-7v5H5V6zm4 1.5A2 2 0 1 0 7 11.5a2 2 0 0 0 0-4z"/>',
    museum: '<path d="M12 2L2 7v2h20V7zM4 10v7h2v-7zm5 0v7h2v-7zm4 0v7h2v-7zm5 0v7h2v-7zM2 19v2h20v-2z"/>',
    thumb: '<path d="M2 21h4V9H2zm20-11a2 2 0 0 0-2-2h-6.3l1-4.6v-.3a1.5 1.5 0 0 0-.4-1.1L13.2 1 6.6 7.6A2 2 0 0 0 6 9v10a2 2 0 0 0 2 2h9a2 2 0 0 0 1.8-1.2l3-7.1c.1-.2.2-.5.2-.7z"/>',
    bot: '<path d="M11 2h2v3h4a3 3 0 0 1 3 3v9a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V8a3 3 0 0 1 3-3h4zM8.5 10a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm7 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM8 15v2h8v-2zM1 10h2v5H1zm20 0h2v5h-2z"/>',
    eye: '<path d="M12 5C6.5 5 2.7 9.3 1.5 12c1.2 2.7 5 7 10.5 7s9.3-4.3 10.5-7C21.3 9.3 17.5 5 12 5zm0 11a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm0-6a2 2 0 1 0 0 4 2 2 0 0 0 0-4z"/>',
    person: '<path d="M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0 2c-5 0-9 2.5-9 6v2h18v-2c0-3.5-4-6-9-6z"/>',
    folder: '<path d="M2 5a2 2 0 0 1 2-2h6l2 2h8a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"/>',
    play: '<path d="M8 5v14l11-7z"/>',
    trend: '<path d="M3 17l6-6 4 4 7-7v5h2V3h-10v2h5l-4.9 4.9-4-4L1.6 15.6z"/>',
    cross: '<path d="M6.4 4.9L4.9 6.4 10.5 12l-5.6 5.6 1.5 1.5 5.6-5.6 5.6 5.6 1.5-1.5-5.6-5.6 5.6-5.6-1.5-1.5-5.6 5.6z"/>',
    half: '<path d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm0 2v14a7 7 0 0 1 0-14z"/>',
  };
  function icon(name, size, color) {
    if (name && name.indexOf("px:") === 0) return sprite(name.slice(3), size).svg;  // a pixel sprite as the icon
    const s = document.createElementNS(NS, "svg");
    s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("width", size); s.setAttribute("height", size);
    s.style.fill = color || "currentColor"; s.style.flex = "none";
    s.innerHTML = ICONS[name] || ICONS.sparkle;
    return s;
  }
  // Pixel art, drawn in code: each sprite is a grid of fill colours only ("." is empty). Code adds what
  // pixel artists do by hand, the same way on every sprite: a one-pixel ink outline around the shape, a
  // darker shade along its lower edge and a lighter one along its upper edge (light from the top).
  // Colours are the brand's CSS variables, so a sprite takes on the project's palette.
  const PAL = { k: "var(--ink)", w: "#fff", a: "var(--accent-fill)", s: "var(--second)", g: "var(--success)",
    r: "var(--error)", m: "var(--muted)", y: "#F5B301", d: "#C98A00", b: "#BFE0FF", c: "#D97757", p: "#F2C29B" };
  const shade = (c) => "color-mix(in srgb, " + c + " 74%, #3E0863)";
  const light = (c) => "color-mix(in srgb, " + c + " 62%, #fff)";
  const PX = {
    robot: ["....aa....", "....ww....", ".wwwwwwww.", ".wkwwwwkw.", ".wkwwwwkw.", ".wwwwwwww.", ".wwwaawww.",
      ".wwwwwwww.", "....ss....", ".ssssssss.", ".sassssas."],
    trophy: [".yyyyyyyyyy.", "y.ywyyyyyy.y", "y.ywyyyyyy.y", ".yywyyyyyyy.", "..yyyyyyyy..", "...yyyyyy...",
      ".....yy.....", ".....dd.....", "....dddd....", "...ssssss..."],
    heart: [".aa....aa.", "awaa..aaaa", "awaaaaaaaa", "aaaaaaaaaa", ".aaaaaaaa.", "..aaaaaa..", "...aaaa...",
      "....aa...."],
    coin: ["...yyyy...", ".yywyyyyy.", ".ywyyddyy.", "yyyyyddyyy", "yyyyyddyyy", "yyyyyddyyy", ".yyyyddyy.",
      ".yyyyyyyy.", "...yyyy..."],
    rocket: ["...ww...", "..wwww..", "..wssw..", "..wssw..", "..wwww..", ".awwwwa.", "aawwwwaa", "a.wwww.a",
      "...aa...", "...yy..."],
    pin: ["..aaaaaa..", ".aaawwaaa.", "aaawwwwaaa", "aaawwwwaaa", ".aaawwaaa.", "..aaaaaa..", "...aaaa...",
      "....aa...."],
    chat: ["wwwwwwwwwwww", "wwsswsswssww", "wwsswsswssww", "wwwwwwwwwwww", "..ww........", "..w........."],
    search: ["..bbbb....", ".bwbbbb...", "bwbbbbbb..", "bbbbbbbb..", "bbbbbbbb..", ".bbbbbb...", "..bbbb.k..",
      ".......kk.", "........kk"],
    crown: ["y....y....y", "yy..yyy..yy", "yyyyyyyyyyy", "yyayyyyyayy", "yyyyyyyyyyy", "ddddddddddd"],
    arrow: ["...gg...", "..gggg..", ".gggggg.", "gggggggg", "...gg...", "...gg...", "...gg...", "...gg..."],
    check: ["........gg", ".......ggg", "......ggg.", "gg...ggg..", "ggg.ggg...", ".ggggg....", "..ggg.....",
      "...g......"],
    bulb: ["..yyyy..", ".ywyyyy.", "ywyyyyyy", "yyyyyyyy", "yyyyyyyy", ".yyyyyy.", "..yyyy..", "..mmmm..",
      "..mmmm..", "...mm..."],
    fire: ["....a....", "...aa....", "...aaa.a.", "..aayaaaa", ".aayyyaaa", ".ayyyyyaa", "aayywyyaa", "aayyyyyaa",
      ".aayyyaa.", "..aaaaa.."],
    star: [".....y.....", "....yyy....", "...yyyyy...", "yyyyyyyyyyy", ".yyyyyyyyy.", "..yyyyyyy..", "..yyyyyyy..",
      ".yyyy.yyyy.", ".yy.....yy."],
    // the Claude character (Robert's call: OK to use) and a made-up salesman for the bribe gag
    claude: ["..cc......cc..", "..cccccccccc..", "..cwwccccwwc..", "..cwkccccwkc..", "..cccccccccc..",
      "cccccccccccccc", "cccccccccccccc", "..cccccccccc..", "..c..c..c..c..", "..c..c..c..c.."],
    salesman: ["...mmmm...", "..mmmmmm..", "..pppppp..", "..pkppkp..", "..pppppp..", "...pmmp...", ".sssawsss.",
      "ssssaassss", "ss.saas.ss", "pp.ssss.pp", "...s..s...", "...k..k..."],
  };
  // The grid with its outline: one empty pixel of margin, then every empty pixel that touches the shape
  // (4-neighbours: chunky, rounded corners) becomes ink.
  function outlined(g) {
    const rows = g.length + 2, cols = g[0].length + 2;
    const at = (x, y) => (y >= 1 && y <= g.length && x >= 1 && x <= g[0].length ? g[y - 1][x - 1] : ".");
    const out = [];
    for (let y = 0; y < rows; y++) {
      let row = "";
      for (let x = 0; x < cols; x++) {
        const c = at(x, y);
        const touches = [[1, 0], [-1, 0], [0, 1], [0, -1]].some((d) => at(x + d[0], y + d[1]) !== ".");
        row += c !== "." ? c : touches ? "k" : ".";
      }
      out.push(row);
    }
    return out;
  }
  // A sprite as an SVG of one crisp square per pixel (`cells` in reading order, for builds and shines).
  function sprite(name, size) {
    const g = outlined(PX[name] || PX.star);
    const cols = g[0].length, rows = g.length;
    const s = document.createElementNS(NS, "svg");
    s.setAttribute("viewBox", "0 0 " + cols + " " + rows); s.setAttribute("shape-rendering", "crispEdges");
    s.setAttribute("width", size); s.setAttribute("height", size * rows / cols); s.style.flex = "none";
    s.style.overflow = "visible";
    const cells = [];
    g.forEach(function (row, y) {
      Array.from(row).forEach(function (c, x) {
        if (c === ".") return;
        const base = PAL[c] || PAL.k;
        const below = (g[y + 1] || "")[x], above = (g[y - 1] || "")[x];
        // only on the shape's outer edge (next to the outline): shade along the bottom, light along the top.
        // Inner colour boundaries stay flat; shading them read as speckle.
        const edge = (n) => n === "k" || n === undefined;
        const fill = c === "k" ? base : edge(below) && !edge(above) ? shade(base) : edge(above) && !edge(below) ? light(base) : base;
        const r = document.createElementNS(NS, "rect");
        r.setAttribute("x", x); r.setAttribute("y", y); r.setAttribute("width", 1.02); r.setAttribute("height", 1.02);
        r.setAttribute("fill", fill);
        s.appendChild(r); cells.push({ el: r, x: x, y: y, fill: fill, ink: c === "k" });
      });
    });
    return { svg: s, cells: cells, cols: cols, rows: rows };
  }
  // A 3x5 pixel font (A-Z, 0-9, a little punctuation) for short labels such as "LEVEL UP" or "+128%".
  const FONT = {
    A: "010101111101101", B: "110101110101110", C: "011100100100011", D: "110101101101110", E: "111100110100111",
    F: "111100110100100", G: "011100101101011", H: "101101111101101", I: "111010010010111", J: "001001001101010",
    K: "101101110101101", L: "100100100100111", M: "101111111101101", N: "110101101101101", O: "010101101101010",
    P: "110101111100100", Q: "010101101110011", R: "110101110101101", S: "011100010001110", T: "111010010010010",
    U: "101101101101111", V: "101101101101010", W: "101101111111101", X: "101101010101101", Y: "101101010010010",
    Z: "111001010100111", 0: "111101101101111", 1: "010110010010111", 2: "110001010100111", 3: "110001010001110",
    4: "101101111001001", 5: "111100110001110", 6: "011100111101111", 7: "111001010010010", 8: "111101111101111",
    9: "111101111001110", "!": "010010010000010", "?": "110001010000010", ".": "000000000000010",
    "+": "000010111010000", "-": "000000111000000", "%": "101001010100101", "$": "011110010011110",
    ":": "000010000010000", "/": "001001010100100", "#": "101111101111101", " ": "000000000000000",
  };
  // Text in the pixel font: one SVG, a group of squares per character (shown one by one when typed).
  function pixelText(text, px, color) {
    const chars = Array.from(String(text).toUpperCase());
    const s = document.createElementNS(NS, "svg");
    const w = Math.max(1, chars.length * 4 - 1);
    s.setAttribute("viewBox", "0 0 " + w + " 5"); s.setAttribute("shape-rendering", "crispEdges");
    s.setAttribute("width", w * px); s.setAttribute("height", 5 * px); s.style.overflow = "visible";
    s.setAttribute("role", "img"); s.setAttribute("aria-label", text);
    const groups = chars.map(function (c, i) {
      const gr = document.createElementNS(NS, "g"); gr.setAttribute("fill", color || "currentColor");
      Array.from(FONT[c] || FONT["?"]).forEach(function (bit, k) {
        if (bit !== "1") return;
        const r = document.createElementNS(NS, "rect");
        r.setAttribute("x", i * 4 + (k % 3)); r.setAttribute("y", Math.floor(k / 3));
        r.setAttribute("width", 1.02); r.setAttribute("height", 1.02); gr.appendChild(r);
      });
      s.appendChild(gr); return gr;
    });
    return { svg: s, groups: groups };
  }
  // Frame grid: stepped animations (pixel builds, shines) change on whole frames, one step per frame at
  // most, so no step is skipped or doubled by the render's frame sampling.
  const frame = () => 1 / (window.MK && MK.fps ? MK.fps : 30);
  const onFrame = (t) => Math.round(t / frame()) * frame();
  // A light band sweeps across a sprite's pixels, one diagonal per frame (a "shine" on landing or a win).
  function shine(tl, sp, t) {
    const t0 = onFrame(t), f = frame();
    sp.cells.forEach(function (c) {
      if (c.ink) return;
      const at = t0 + (c.x + c.y) * f;
      tl.set(c.el, { attr: { fill: "#fff" } }, at);
      tl.set(c.el, { attr: { fill: c.fill } }, at + 2 * f);
    });
    return t0 + (sp.cols + sp.rows) * f;
  }
  // A seeded shuffle (the same order on every render and every seek).
  function shuffled(n, seed) {
    const idx = Array.from({ length: n }, function (_, i) { return i; });
    let h = seed || 7;
    for (let i = n - 1; i > 0; i--) { h = (h * 1103515245 + 12345) & 0x7fffffff; const j = h % (i + 1); const t = idx[i]; idx[i] = idx[j]; idx[j] = t; }
    return idx;
  }

  function el(tag, cls, parent, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  // Text as one span per character, revealed in order (typing) by display toggles: seek-safe, and the
  // caret that follows the last shown character is a sibling span.
  function typed(parent, text, cls) {
    const box = el("span", cls || "", parent);
    const chars = Array.from(text).map(function (c) { const s = el("span", "", box, c); s.style.display = "none"; return s; });
    const caret = el("span", "mk-caret", box);
    return { box: box, chars: chars, caret: caret };
  }
  function typeOn(tl, t, from, to) {
    const n = t.chars.length;
    if (!n) return;
    const step = Math.max(0.012, (to - from) / n);
    t.chars.forEach(function (c, i) { tl.set(c, { display: "inline" }, from + i * step); });
    tl.set(t.caret, { opacity: 1 }, from);
    // caret blinks while idle after typing, then goes
    const end = from + n * step;
    for (let k = 0; k < 3; k++) { tl.set(t.caret, { opacity: 0 }, end + 0.25 + k * 0.5); tl.set(t.caret, { opacity: 1 }, end + 0.5 + k * 0.5); }
    tl.set(t.caret, { opacity: 0 }, end + 1.8);
    return end;
  }
  // Rich line: "**bold**" segments become <b>.
  function rich(parent, text, cls) {
    const line = el("div", cls, parent);
    text.split(/(\*\*[^*]+\*\*)/).forEach(function (part) {
      if (!part) return;
      if (part.startsWith("**")) el("b", "", line, part.slice(2, -2)); else line.appendChild(document.createTextNode(part));
    });
    return line;
  }
  // A count-up: the number is shown as whole values swapped in ~12 steps (display toggles, seek-safe), so
  // every frame shows clean digits (a rolling odometer read as broken glyphs mid-roll).
  function counter(parent, value) {
    const box = el("span", "mk-count", parent);
    const n = Math.max(1, Math.min(12, Math.round(value)));
    const steps = [];
    for (let k = 0; k <= n; k++) {
      const v = Math.round(value * (1 - Math.pow(1 - k / n, 2)));  // ease-out: fast first, settling
      const sp = el("span", "", box, v.toLocaleString("en-US")); sp.style.display = k === 0 ? "inline" : "none"; steps.push(sp);
    }
    return steps;
  }
  function countUp(tl, steps, t, dur) {
    steps.forEach(function (sp, k) {
      if (k === 0) return;
      const at = t + dur * (k / (steps.length - 1));
      tl.set(steps[k - 1], { display: "none" }, at);
      tl.set(sp, { display: "inline" }, at);
    });
  }
  const mark = (s, k, frac) => (s.marks && s.marks[k] != null ? s.marks[k] : s.t0 + (s.t1 - s.t0) * frac);

  const outAt = (s) => Math.max(s.t0 + 0.7, s.t1 - 0.25);  // gone by t1
  // A hand-over (ADR 0033, MK.handover) owns the outgoing card from the moment the next one starts: its
  // drift ends there, and its exit is the hand-over's (spec.handover_out, spec.handover_s set by reel.py).
  const driftEnd = (s) => (s.handover_out ? s.t1 - (s.handover_s || 0.55) : outAt(s));
  // Entrances (spec.motion overrides the widget's own): rise (cards), pop (stickers, numbers), slide (in from
  // a side, spec.from), flip (tips up from its bottom edge), focus (blur to sharp), pixel (stepped, retro),
  // wipe (revealed left to right behind a straight edge), unfold (hinges down from its top edge).
  // Opacity is always fast and linear while the move springs: a slow fade reads as a grey ghost.
  const MOTIONS = ["rise", "pop", "slide", "flip", "focus", "pixel", "wipe", "unfold"];
  const motionOf = (s, how) => (MOTIONS.indexOf(s.motion) >= 0 ? s.motion : how || "rise");
  const side = (s) => (s.from === "left" ? -1 : 1);
  const DRIFT = { y: -16, scale: 1.035 };  // where the on-screen drift leaves a card (a hand-over starts there)
  function enter(tl, node, s, how) {
    const t = s.t0, m = motionOf(s, how);
    if (s.handover_in) {  // the hand-over brings it in (MK.handover); here only the drift once it has landed
      const from = t + (s.handover_s || 0.55) + 0.1, drift = driftEnd(s) - from;
      if (drift > 0.6 && m !== "pixel") tl.fromTo(node, { y: 0, scale: 1 }, { y: DRIFT.y, scale: DRIFT.scale, duration: drift, ease: "sine.inOut", immediateRender: false }, from);
      return;
    }
    // while on screen, drift slowly up and in: a card never sits dead still (ends before its exit)
    const drift = driftEnd(s) - (t + 0.6);
    if (drift > 0.6 && m !== "pixel") tl.fromTo(node, { y: 0, scale: 1 }, { y: DRIFT.y, scale: DRIFT.scale, duration: drift, ease: "sine.inOut", immediateRender: false }, t + 0.6);
    const fade = (d) => tl.fromTo(node, { opacity: 0 }, { opacity: 1, duration: d, ease: "none", immediateRender: false }, t);
    if (m === "wipe") {
      // a straight edge reveals it left to right (clip-path from numeric custom properties: --wr is the
      // revealed share, --wl the share wiped away on exit; the insets stay negative so the shadow shows)
      node.classList.add("mk-wipe");
      fade(0.06);
      tl.fromTo(node, { "--wr": 0 }, { "--wr": 1, duration: 0.55, ease: "expo.out", immediateRender: false }, t);
    } else if (m === "unfold") {
      fade(0.1);
      tl.fromTo(node, { rotationX: 90, transformPerspective: 1400, transformOrigin: "50% 0%" }, { rotationX: 0, transformPerspective: 1400, duration: 0.6, ease: "back.out(1.2)", immediateRender: false }, t);
      tl.fromTo(node, { transformPerspective: 1400 }, { transformPerspective: 0, duration: 0, immediateRender: false }, t + 0.6);  // flat once down
    } else if (m === "pop") {
      fade(0.1);
      tl.fromTo(node, { scale: 0.35, rotation: s.tilt ? s.tilt * 3 : -8 }, { scale: 1, rotation: s.tilt || 0, duration: 0.5, ease: "back.out(3.2)", immediateRender: false }, t);  // springier (r12 review)
    } else if (m === "slide") {
      fade(0.12);
      tl.fromTo(node, { x: 300 * side(s), skewX: -10 * side(s) }, { x: 0, skewX: 0, duration: 0.55, ease: "expo.out", immediateRender: false }, t);
    } else if (m === "flip") {
      fade(0.12);
      tl.fromTo(node, { rotationX: -80, y: 60, transformPerspective: 1400, transformOrigin: "50% 100%" }, { rotationX: 0, y: 0, transformPerspective: 1400, duration: 0.6, ease: "back.out(1.4)", immediateRender: false }, t);
      tl.fromTo(node, { transformPerspective: 1400 }, { transformPerspective: 0, duration: 0, immediateRender: false }, t + 0.6);  // flat once landed
    } else if (m === "focus") {
      fade(0.1);
      tl.fromTo(node, { scale: 1.18, filter: "blur(14px)" }, { scale: 1, filter: "blur(0px)", duration: 0.4, ease: "power3.out", immediateRender: false }, t);
      tl.set(node, { filter: "none" }, t + 0.42);
    } else if (m === "pixel") {
      tl.fromTo(node, { opacity: 0 }, { opacity: 1, duration: 0.2, ease: "steps(3)", immediateRender: false }, t);
      tl.fromTo(node, { scale: 0.3 }, { scale: 1, duration: 0.3, ease: "steps(5)", immediateRender: false }, t);
    } else {
      fade(0.12);
      tl.fromTo(node, { y: 120, scale: 0.72 }, { y: 0, scale: 1, duration: 0.5, ease: "back.out(1.8)", immediateRender: false }, t);
    }
  }
  function leave(tl, node, s, how) {
    const out = outAt(s), m = motionOf(s, how);
    if (s.handover_out) { hide(tl, node, s.t1); return; }  // the hand-over (MK.handover) takes it away
    if (m === "wipe") {
      tl.fromTo(node, { "--wl": 0 }, { "--wl": 1, duration: 0.28, ease: "power2.in", immediateRender: false }, out);
      tl.to(node, { opacity: 0, duration: 0.06, ease: "none" }, out + 0.24);
    } else if (m === "unfold") tl.fromTo(node, { rotationX: 0, transformPerspective: 1400, transformOrigin: "50% 0%" }, { opacity: 0, rotationX: -90, transformPerspective: 1400, duration: 0.26, ease: "power2.in", immediateRender: false }, out);
    else if (m === "slide") tl.to(node, { opacity: 0, x: -260 * side(s), duration: 0.25, ease: "power2.in" }, out);
    else if (m === "flip") tl.fromTo(node, { rotationX: 0, transformPerspective: 1400 }, { opacity: 0, rotationX: 70, transformPerspective: 1400, transformOrigin: "50% 0%", duration: 0.25, ease: "power2.in", immediateRender: false }, out);
    else if (m === "pixel") tl.to(node, { opacity: 0, scale: 0.4, duration: 0.24, ease: "steps(4)" }, out);
    else tl.to(node, { opacity: 0, y: -90, scale: 0.6, duration: 0.14, ease: "power3.in" }, out);  // quick: a slow fade read as a grey ghost (r15/r16)
    hide(tl, node, out + 0.3);
  }
  // Hold a widget at zero opacity after its exit. Only opacity, never visibility: visibility is inherited,
  // so GSAP restored a hidden parent's value onto its children when a render scrubbed backwards (a step
  // label's card went missing depending on seek order, found by tests/test_motion_kit.py).
  function hide(tl, node, at) {
    tl.fromTo(node, { opacity: 0 }, { opacity: 0, duration: 0, immediateRender: false }, at);
  }
  // A ring that pulses out from an element once (an attention beat on a highlight or a final value).
  function pulse(tl, node, t, color) {
    const r = el("i", "mk-pulse", node);
    r.style.borderColor = color || "var(--accent)";
    gsap.set(r, { opacity: 0 });
    tl.fromTo(r, { opacity: 0.8, scale: 0.96 }, { opacity: 0, scale: 1.16, duration: 0.6, ease: "power2.out", immediateRender: false }, t);  // stays by its row (a 1.5 ring overhung the card: ADR 0033 reviews)
  }

  const W = {};

  // An AI chat: the question types in, the assistant thinks, the answer lines arrive, sources pop.
  // spec: app, prompt, answer [lines], sources [names]; marks: [type start, type end, answer, sources]
  W.chat = function (s) {
    const root = el("div", "mk-card mk-chat");
    const head = el("div", "mk-head", root);
    const av = el("div", "mk-avatar", head); av.appendChild(icon("sparkle", 30, "#fff"));
    el("div", "mk-app", head, s.app || "AI assistant");
    if (s.chip) el("div", "mk-chip", head, s.chip);
    const q = el("div", "mk-q", root);
    const tq = typed(q, s.prompt || "");
    const ans = el("div", "mk-ans", root);
    const dots = el("div", "mk-dots", ans); [0, 1, 2].forEach(function () { el("i", "", dots); });
    const lines = (s.answer || []).map(function (l) { return rich(ans, l, "mk-line"); });
    const src = el("div", "mk-sources", root);
    const chips = (s.sources || []).map(function (n, i) {
      const c = el("div", "mk-src", src); c.appendChild(icon(i % 2 ? "star" : "pin", 26)); el("span", "", c, n); return c;
    });
    return { el: root, play: function (tl) {
      gsap.set(q, { opacity: 0 }); gsap.set([dots].concat(lines, chips), { opacity: 0 });
      enter(tl, root, s);
      const ts = mark(s, 0, 0.08), te = mark(s, 1, 0.42);
      tl.fromTo(q, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.25, ease: "power2.out", immediateRender: false }, ts - 0.05);
      const end = typeOn(tl, tq, ts, te);
      const ta = Math.max(end + 0.15, mark(s, 2, 0.55));
      tl.fromTo(dots, { opacity: 0 }, { opacity: 1, duration: 0.15, immediateRender: false }, end + 0.1);
      tl.fromTo(dots.children, { y: 0 }, { y: -10, duration: 0.18, ease: "sine.inOut", yoyo: true, repeat: Math.max(1, Math.floor((ta - end) / 0.36) * 2 - 1), stagger: 0.08, immediateRender: false }, end + 0.1);
      tl.set(dots, { opacity: 0, display: "none" }, ta);
      const tsrc = mark(s, 3, 0.8);
      const gap = Math.min(0.5, Math.max(0.15, (tsrc - ta) / Math.max(1, lines.length)));
      lines.forEach(function (l, i) {
        tl.fromTo(l, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out", immediateRender: false }, ta + i * gap);
      });
      chips.forEach(function (c, i) {
        tl.fromTo(c, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2.5)", immediateRender: false }, tsrc + i * 0.35);
      });
      if (s.highlight != null && chips[s.highlight]) tl.to(chips[s.highlight], { backgroundColor: "var(--accent-fill)", color: "#fff", duration: 0.25 }, tsrc + chips.length * 0.35 + 0.2);
      leave(tl, root, s);
    } };
  };

  // A search bar: the query types in, then results slide in under it.
  // spec: query, results [..], highlight, stagger (row i lands on marks[2+i]), strike (row index whose bold
  // part is struck through on marks[2+rows], "kinda useless": the vague number)
  // answer [lines] + link: an AI answer box under the bar (lands on marks[2]) holding one faded website link
  // that lights up on marks[3], or shows up faded on marks[3] and lights up on marks[4] ("small and easy to
  // miss" ... "right inside the answer")
  W.search = function (s) {
    const root = el("div", "mk-card mk-search");
    const bar = el("div", "mk-bar", root); bar.appendChild(icon("search", 40));
    const tq = typed(bar, s.query || "", "mk-query");
    const ai = s.answer ? el("div", "mk-aians", root) : null;
    let link = null;
    if (ai) {
      const lab = el("div", "mk-ailabel", ai); lab.appendChild(icon("sparkle", 30, "var(--accent)")); el("span", "", lab, s.label || "AI answer");
      (s.answer || []).forEach(function (l) { rich(ai, l, "mk-line"); });
      if (s.link) {
        link = el("div", "mk-ailink", ai); link.appendChild(icon("globe", 30)); el("span", "", link, s.link);
        const lit = el("div", "mk-ailit", link); lit.appendChild(icon("globe", 30, "#fff")); el("span", "", lit, s.link);
      }
    }
    const res = (s.results || []).map(function (r, i) {
      const row = el("div", "mk-res", root);
      el("div", "mk-rank", row, String(i + 1));
      rich(row, r, "mk-rtext");
      return row;
    });
    const sk = s.strike != null && res[s.strike] ? el("i", "mk-strike", res[s.strike].querySelector("b") || res[s.strike].querySelector(".mk-rtext")) : null;
    return { el: root, play: function (tl) {
      gsap.set(res, { opacity: 0 });
      if (sk) gsap.set(sk, { scaleX: 0 });
      enter(tl, root, s);
      const end = typeOn(tl, tq, mark(s, 0, 0.1), mark(s, 1, 0.5));
      if (ai) {
        const ta = Math.max(end + 0.2, mark(s, 2, 0.55));
        gsap.set(ai, { opacity: 0 });
        tl.fromTo(ai, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.35, ease: "power3.out", immediateRender: false }, ta);
        if (link) {
          // faded (half opacity) and small while it is "easy to miss", then lit in the accent with a ring
          // marks[3]: the link shows up faded (default with the answer); marks[4]: it lights up
          const tf = s.marks && s.marks.length > 4 ? Math.max(ta + 0.3, mark(s, 3, 0.7)) : ta;
          const tl0 = Math.max(tf + 0.4, mark(s, s.marks && s.marks.length > 4 ? 4 : 3, 0.8));
          const lit = link.querySelector(".mk-ailit");
          gsap.set(link, { opacity: 0, scale: 0.92 }); gsap.set(lit, { opacity: 0 });
          tl.fromTo(link, { opacity: 0, y: 16 }, { opacity: 0.5, y: 0, duration: 0.3, ease: "power2.out", immediateRender: false }, tf);
          tl.fromTo(link, { opacity: 0.5, scale: 0.92 }, { opacity: 1, scale: 1.08, duration: 0.3, ease: "power2.out", immediateRender: false }, tl0);
          tl.fromTo(lit, { opacity: 0 }, { opacity: 1, duration: 0.2, ease: "none", immediateRender: false }, tl0);
          tl.fromTo(link, { scale: 1.08 }, { scale: 1, duration: 0.25, ease: "back.out(3)", immediateRender: false }, tl0 + 0.3);
          pulse(tl, link, tl0 + 0.1);
        }
      }
      res.forEach(function (r, i) {
        const at = s.stagger ? Math.max(end + 0.2, mark(s, 2 + i, 0.6 + i * 0.15)) : Math.max(end + 0.2, mark(s, 2, 0.6)) + i * 0.3;
        tl.fromTo(r, { opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 0.35, ease: "power3.out", immediateRender: false }, at);
      });
      if (sk) {
        const ts = mark(s, 2 + res.length, 0.8);
        tl.fromTo(sk, { scaleX: 0 }, { scaleX: 1, duration: 0.3, ease: "power2.inOut", immediateRender: false }, ts);
        tl.to(res[s.strike], { opacity: 0.5, duration: 0.3 }, ts + 0.2);
      }
      if (s.highlight != null && res[s.highlight]) tl.to(res[s.highlight], { backgroundColor: "var(--tint)", boxShadow: "inset 0 0 0 4px var(--accent)", duration: 0.3 }, mark(s, 3, 0.8));
      leave(tl, root, s);
    } };
  };

  // A list of sources: rows arrive, then a highlight ring jumps to the one that matters.
  // spec: title, items [{name, sub, icon}], highlight; marks: [rows..., highlight]
  W.sources = function (s) {
    const verdicts = (s.items || []).some(function (it) { return it.verdict; });
    const root = el("div", "mk-card mk-list" + (s.hero ? " mk-hero" : "") + (s.compact ? " mk-compact" : "") + (verdicts ? " verdicts" : ""));
    const head = el("div", "mk-title", root); head.appendChild(icon(s.icon || "globe", 44, "var(--accent)")); el("span", "", head, s.title || "Sources");
    const rows = (s.items || []).map(function (it, i) {
      const row = el("div", "mk-row", root);
      const ic = el("div", "mk-ic", row); ic.appendChild(icon(it.icon || "pin", 34, "#fff"));
      const tx = el("div", "mk-rowtext", row); el("div", "mk-name", tx, it.name); if (it.sub) el("div", "mk-sub", tx, it.sub);
      // highlight_sub: a sub-line that appears under the highlighted row when the ring lands
      const hs = i === s.highlight && s.highlight_sub ? el("div", "mk-sub mk-hsub", tx, s.highlight_sub) : null;
      // a verdict per row: yes (a check, the default), no (a cross) or half
      const v = it.verdict === "no" ? "cross" : it.verdict === "half" ? "half" : "check";
      const ck = el("div", "mk-check" + (v === "check" ? "" : " " + it.verdict), row); ck.appendChild(icon(v, it.verdict ? 48 : 34, "#fff"));
      return { row: row, ck: ck, hs: hs };
    });
    return { el: root, play: function (tl) {
      gsap.set(rows.map(function (r) { return r.row; }), { opacity: 0 });
      gsap.set(rows.map(function (r) { return r.ck; }), { scale: 0, opacity: 0 });
      enter(tl, root, s);
      // the highlight sub-line is folded away from t0 (a timeline set, so the card is fitted at its full height)
      rows.forEach(function (r) { if (r.hs) tl.set(r.hs, { opacity: 0, fontSize: 0 }, s.t0); });
      rows.forEach(function (r, i) {
        // every row is there from the start (dimmed), and lights up with its check on its word
        const tin = s.t0 + 0.3 + i * 0.15;
        const t = Math.max(tin + 0.3, s.marks && s.marks[i] != null ? s.marks[i] : s.t0 + 0.6 + i * 0.45);
        tl.fromTo(r.row, { opacity: 0, x: 40 }, { opacity: 0.55, x: 0, duration: 0.35, ease: "power3.out", immediateRender: false }, tin);
        tl.to(r.row, { opacity: 1, duration: 0.2, ease: "none" }, t);
        tl.fromTo(r.ck, { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.3, ease: "back.out(3)", immediateRender: false }, t);
      });
      if (s.highlight != null && rows[s.highlight]) {
        const th = s.marks && s.marks[rows.length] != null ? s.marks[rows.length] : s.t0 + (s.t1 - s.t0) * 0.75;
        tl.to(rows[s.highlight].row, { boxShadow: "0 0 0 5px var(--accent)", backgroundColor: "var(--tint)", scale: 1.04, duration: 0.3, ease: "back.out(2)" }, th);
        pulse(tl, rows[s.highlight].row, th + 0.1);
        const hs = rows[s.highlight].hs;
        if (hs) tl.fromTo(hs, { opacity: 0, fontSize: 0 }, { opacity: 1, fontSize: 40, duration: 0.3, ease: "power2.out", immediateRender: false }, th + 0.15);
      }
      leave(tl, root, s);
    } };
  };

  // A review: stars fill one by one, the text types in, the context phrases get a marker sweep.
  // spec: name, stars, text, highlights [phrases], label; marks: [stars, text, highlight]
  W.review = function (s) {
    const root = el("div", "mk-card mk-review");
    const head = el("div", "mk-rhead", root);
    el("div", "mk-initial", head, (s.name || "A").slice(0, 1));
    const who = el("div", "", head); el("div", "mk-name", who, s.name || "Guest"); el("div", "mk-sub", who, s.label || "Review on Google Maps");
    const stars = el("div", "mk-stars", root);
    const st = [];
    for (let i = 0; i < 5; i++) { const w = el("div", "mk-star", stars); w.appendChild(icon("star", 64, "var(--chip)")); const f = icon("star", 64, "#F5B301"); f.classList.add("mk-fill"); w.appendChild(f); st.push(f); }
    const body = el("div", "mk-rbody", root);
    const hl = [];
    const text = s.text || "";
    const parts = [];
    let rest = text;
    (s.highlights || []).forEach(function (h) {
      const k = rest.indexOf(h);
      if (k < 0) return;
      parts.push([rest.slice(0, k), false], [h, true]); rest = rest.slice(k + h.length);
    });
    parts.push([rest, false]);
    parts.forEach(function (p) {
      if (!p[0]) return;
      if (p[1]) { const m = el("span", "mk-hl", body); const bg = el("i", "", m); el("span", "", m, p[0]); hl.push(bg); }
      else body.appendChild(document.createTextNode(p[0]));
    });
    return { el: root, play: function (tl) {
      gsap.set(st, { scale: 0, transformOrigin: "50% 50%" }); gsap.set(body, { opacity: 0 }); gsap.set(hl, { scaleX: 0 });
      enter(tl, root, s);
      const ts = mark(s, 0, 0.12);
      st.slice(0, s.stars || 5).forEach(function (f, i) { tl.fromTo(f, { scale: 0 }, { scale: 1, duration: 0.3, ease: "back.out(3)", immediateRender: false }, ts + i * 0.12); });
      tl.fromTo(body, { opacity: 0, y: 12 }, { opacity: 0.3, y: 0, duration: 0.35, ease: "power3.out", immediateRender: false }, s.t0 + 0.35);
      tl.to(body, { opacity: 1, duration: 0.3, ease: "none" }, Math.max(s.t0 + 0.7, mark(s, 1, 0.35)));
      hl.forEach(function (h, i) { tl.fromTo(h, { scaleX: 0 }, { scaleX: 1, duration: 0.4, ease: "power2.out", immediateRender: false }, mark(s, 2, 0.55) + i * 0.6); });
      leave(tl, root, s);
    } };
  };

  // A number that rolls up. spec: value, prefix, suffix, label; marks: [roll start]
  W.counter = function (s) {
    const root = el("div", "mk-card mk-counter");
    const num = el("div", "mk-num", root);
    if (s.prefix) el("span", "", num, s.prefix);
    const cols = counter(num, Number(s.value != null ? s.value : 0));
    if (s.suffix) el("span", "mk-suffix", num, s.suffix);
    el("div", "mk-label", root, s.label || "");
    return { el: root, play: function (tl) {
      enter(tl, root, s, "pop");
      const t = s.t0 + 0.05;  // a number counts as it lands: a "0" never sits on screen
      // a mark is the word the number lands on (r14 review: it reached 100 after "hundred" was said)
      const dur = s.marks && s.marks.length ? Math.max(0.3, s.marks[0] - t) : Math.min(1.0, (s.t1 - t) * 0.5);
      countUp(tl, cols, t, dur);
      // the final value lands with a small punch and a pulse
      tl.fromTo(num, { scale: 1 }, { scale: 1.08, duration: 0.1, ease: "power2.out", yoyo: true, repeat: 1, immediateRender: false }, t + dur);
      if (s.t1 - (t + dur) > 0.9) pulse(tl, root, t + dur);
      leave(tl, root, s, "pop");
    } };
  };

  // A city map: roads, a river, pins drop in with their labels. spec: city, places [{name, icon}]
  W.pins = function (s) {
    const root = el("div", "mk-card mk-map");
    const map = el("div", "mk-mapbg", root);
    map.innerHTML = '<svg viewBox="0 0 800 460" preserveAspectRatio="xMidYMid slice"><rect width="800" height="460" fill="var(--map)"/>' +
      '<path d="M-20 300 C 150 250, 260 380, 420 300 S 700 180, 820 230" stroke="var(--river)" stroke-width="46" fill="none"/>' +
      '<g stroke="#fff" stroke-width="14" fill="none" stroke-linecap="round"><path d="M80 -10 L 160 470"/><path d="M-10 120 L 810 70"/><path d="M520 -10 L 600 470"/><path d="M-10 400 L 810 420"/><path d="M300 -10 C 320 150, 280 300, 340 470"/></g>' +
      (s.river ? '<text x="640" y="236" font-size="30" font-style="italic" font-weight="600" fill="#5E86AD" font-family="var(--body)">' + s.river + '</text>' : '') + '</svg>';
    el("div", "mk-city", root, s.city || "");
    const spots = [[0.22, 0.45], [0.6, 0.42], [0.78, 0.62], [0.38, 0.7], [0.66, 0.84]];  // pins hang above their spot: keep the first rows low enough not to clip at the card top
    const pins = (s.places || []).map(function (p, i) {
      const pin = el("div", "mk-pin", map);
      gsap.set(pin, { xPercent: -50, yPercent: -100 });  // centred on its spot by GSAP, not a CSS transform it would parse
      const xy = spots[i % spots.length];
      pin.style.left = (xy[0] * 100) + "%"; pin.style.top = (xy[1] * 100) + "%";
      const b = el("div", "mk-pinhead", pin); b.appendChild(icon(p.icon || "pin", 30, "#fff"));
      el("div", "mk-pinlabel", pin, p.name);
      return pin;
    });
    return { el: root, play: function (tl) {
      gsap.set(pins, { opacity: 0 });
      enter(tl, root, s);
      pins.forEach(function (p, i) {
        // the pins drop in as the map lands, then each one jumps on its word
        tl.fromTo(p, { opacity: 0, y: -60 }, { opacity: 1, y: 0, duration: 0.45, ease: "bounce.out", immediateRender: false }, s.t0 + 0.35 + i * 0.12);
        const t = s.marks && s.marks[i] != null ? s.marks[i] : null;
        if (t != null && t > s.t0 + 1) {
          tl.to(p, { y: -26, scale: 1.18, duration: 0.18, ease: "power2.out" }, t);
          tl.to(p, { y: 0, scale: 1, duration: 0.35, ease: "bounce.out" }, t + 0.18);
        }
      });
      leave(tl, root, s);
    } };
  };

  // A line chart that draws up, with its value rolling. spec: title, to, suffix, label
  W.chart = function (s) {
    const root = el("div", "mk-card mk-chart");
    const head = el("div", "mk-title", root); head.appendChild(icon("trend", 44, "var(--accent)")); el("span", "", head, s.title || "");
    const big = s.to != null ? el("div", "mk-num", root) : null;  // a trend can be drawn without a number
    const cols = big ? counter(big, Number(s.to)) : [];
    if (big && s.suffix) el("span", "mk-suffix", big, s.suffix);
    const svgw = document.createElement("div"); svgw.className = "mk-plot"; root.appendChild(svgw);
    const pts = [[0, 150], [90, 140], [180, 146], [270, 118], [360, 112], [450, 84], [540, 70], [630, 40], [720, 18]];
    const d = "M" + pts.map(function (p) { return p.join(" "); }).join(" L ");
    svgw.innerHTML = '<svg viewBox="-10 0 740 170"><path d="' + d + ' L 720 170 L 0 170 Z" fill="var(--tint)"/><path class="mk-line" d="' + d + '" fill="none" stroke="var(--accent)" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/><circle class="mk-dot" cx="720" cy="18" r="11" fill="var(--accent)"/></svg>';
    if (s.label) el("div", "mk-label", root, s.label);
    return { el: root, play: function (tl) {
      const line = svgw.querySelector(".mk-line"), dot = svgw.querySelector(".mk-dot"), area = svgw.querySelector("path");
      const len = 900;
      gsap.set(line, { strokeDasharray: len, strokeDashoffset: len }); gsap.set(dot, { opacity: 0 }); gsap.set(area, { opacity: 0 });
      enter(tl, root, s);
      const t = s.t0 + 0.3, dur = Math.min(2.4, (s.t1 - t) * 0.6);  // draws as it lands: never "00"
      tl.fromTo(line, { strokeDashoffset: len }, { strokeDashoffset: 0, duration: dur, ease: "power2.inOut", immediateRender: false }, t);
      tl.fromTo(area, { opacity: 0 }, { opacity: 1, duration: dur, ease: "none", immediateRender: false }, t);
      tl.fromTo(dot, { opacity: 0, scale: 0 }, { opacity: 1, scale: 1, duration: 0.3, ease: "back.out(3)", transformOrigin: "50% 50%", immediateRender: false }, t + dur);
      tl.to(dot, { attr: { r: 15 }, duration: 0.3, ease: "sine.inOut", yoyo: true, repeat: 3 }, t + dur + 0.3);  // the latest value breathes
      countUp(tl, cols, t, dur);
      leave(tl, root, s);
    } };
  };

  // A call to action: the button lands, a cursor clicks it, a ripple. spec: text, url, cursor (false: no cursor)
  W.cta = function (s) {
    const root = el("div", "mk-cta");
    const btn = el("div", "mk-btn", root, s.text || "Start free trial");
    const url = el("div", "mk-url", root); url.appendChild(icon("globe", 36)); el("span", "", url, s.url || "");
    const rip = el("div", "mk-ripple", btn);
    const cur = el("div", "mk-cursor", root); cur.appendChild(icon("cursor", 64, "var(--ink)"));
    return { el: root, play: function (tl) {
      gsap.set(cur, { opacity: 0 }); gsap.set(rip, { scale: 0, opacity: 0 }); gsap.set(url, { opacity: 0 });
      enter(tl, root, s, "pop");
      const tc = mark(s, 0, 0.45);
      if (s.cursor !== false) {  // cursor: false — the button pulses on its own (a cursor over a long text hid it)
        tl.fromTo(cur, { opacity: 0, x: 220, y: 140 }, { opacity: 1, x: 0, y: 0, duration: 0.5, ease: "power3.out", immediateRender: false }, tc - 0.5);
      }
      tl.to(btn, { scale: 0.94, duration: 0.08, ease: "power1.in" }, tc);
      tl.to(btn, { scale: 1, duration: 0.25, ease: "back.out(3)" }, tc + 0.08);
      tl.fromTo(rip, { scale: 0, opacity: 0.5 }, { scale: 3, opacity: 0, duration: 0.6, ease: "power2.out", immediateRender: false }, tc);
      tl.fromTo(url, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out", immediateRender: false }, tc + 0.15);
      leave(tl, root, s, "pop");
    } };
  };

  // A sticker: chunky label that pops in tilted and wobbles once. spec: text, icon, tilt, accent
  W.sticker = function (s) {
    const root = el("div", "mk-sticker" + (s.accent ? " accent" : ""));
    if (s.icon) root.appendChild(icon(s.icon, 56));
    el("span", "", root, s.text || "");
    const curl = s.peel ? el("i", "mk-curl", root) : null;  // the peeled corner's underside
    return { el: root, play: function (tl) {
      if (curl) gsap.set(curl, { scale: 0, transformOrigin: "100% 100%" });
      enter(tl, root, s, "pop");
      // lands with a squash and stretch, then wobbles once
      // (after the pop's scale has finished: two tweens on one property make the frame depend on seek order)
      tl.fromTo(root, { scaleX: 1, scaleY: 1 }, { scaleX: 1.08, scaleY: 0.9, duration: 0.08, ease: "power2.out", yoyo: true, repeat: 1, immediateRender: false }, s.t0 + 0.43);
      tl.to(root, { rotation: (s.tilt || -4) * -1, duration: 0.18, ease: "sine.inOut", yoyo: true, repeat: 1 }, s.t0 + 0.6);
      if (s.peel) {
        // peels off on its word (marks[0]): the top-left corner lifts, then it drops away. After the wobble, and
        // yPercent for the drop (the entrance's drift owns y): one tween per property at any time.
        const tp = Math.max(s.t0 + 1.0, Math.min(mark(s, 0, 0.6), outAt(s) - 1.05));
        // lift (the corner curls up, its light underside showing), a short hold, then a turning fall
        tl.set(root, { transformOrigin: "0% 0%" }, tp);
        tl.fromTo(curl, { scale: 0 }, { scale: 1, duration: 0.25, ease: "back.out(2)", immediateRender: false }, tp);
        tl.fromTo(root, { rotation: s.tilt || 0, rotationX: 0, transformPerspective: 900, boxShadow: "8px 8px 0 #3E0863, 0px 0px 0 rgba(62,8,99,0)" },
          { rotation: 6, rotationX: 22, transformPerspective: 900, boxShadow: "8px 8px 0 #3E0863, 22px 30px 0 rgba(62,8,99,.4)", duration: 0.25, ease: "power2.out", immediateRender: false }, tp);
        tl.fromTo(root, { yPercent: 0 }, { yPercent: 320, duration: 0.6, ease: "power2.in", immediateRender: false }, tp + 0.4);
        tl.fromTo(root, { rotation: 6 }, { rotation: 38, duration: 0.6, ease: "power1.in", immediateRender: false }, tp + 0.4);
        tl.fromTo(root, { opacity: 1 }, { opacity: 0, duration: 0.15, ease: "none", immediateRender: false }, tp + 0.85);
        hide(tl, root, tp + 1.05);
        return;
      }
      leave(tl, root, s, "pop");
    } };
  };

  // Queries: the vague one is struck through, the specific ones pop in. spec: vague, specific [..]
  W.queries = function (s) {
    const root = el("div", "mk-card mk-queries");
    // no vague query: just the specific ones (a follow-up beat after the strike has been shown)
    const vague = s.vague ? el("div", "mk-qpill vague", root) : null;
    if (vague) vague.appendChild(icon("search", 36));
    const strike = vague ? el("i", "mk-strike", el("span", "", vague, s.vague)) : null;
    const rows = (s.specific || []).map(function (q) { const p = el("div", "mk-qpill", root); p.appendChild(icon("search", 36, "var(--accent)")); rich(p, q, "mk-qtext"); return p; });
    return { el: root, play: function (tl) {
      gsap.set(rows, { opacity: 0 });
      enter(tl, root, s);
      if (vague) {
        gsap.set(strike, { scaleX: 0 });
        tl.fromTo(strike, { scaleX: 0 }, { scaleX: 1, duration: 0.35, ease: "power2.inOut", immediateRender: false }, mark(s, 0, 0.2));
        tl.to(vague, { opacity: 0.45, duration: 0.3 }, mark(s, 0, 0.2) + 0.3);
      }
      rows.forEach(function (r, i) {
        const t = s.marks && s.marks[i + 1] != null ? s.marks[i + 1] : s.t0 + (s.t1 - s.t0) * (0.35 + i * 0.25);
        tl.fromTo(r, { opacity: 0, y: 30, scale: 0.9 }, { opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "back.out(2)", immediateRender: false }, t);
      });
      leave(tl, root, s);
    } };
  };

  // Places: icon tiles that pop in a row (restaurants, hotels, museums). spec: items [{name, icon}]
  W.tiles = function (s) {
    const root = el("div", "mk-tiles");
    const tiles = (s.items || []).map(function (it) {
      const t = el("div", "mk-tile", root); const b = el("div", "mk-tileic", t); b.appendChild(icon(it.icon || "pin", 64, "#fff")); el("div", "mk-tilename", t, it.name); return t;
    });
    return { el: root, play: function (tl) {
      gsap.set(tiles, { opacity: 0 });
      // the row itself appears at t0 like every widget (its tiles then pop in one by one)
      tl.fromTo(root, { opacity: 0 }, { opacity: 1, duration: 0.01, ease: "none", immediateRender: false }, s.t0);
      tiles.forEach(function (t, i) {
        const tin = s.t0 + i * 0.12;
        const at = Math.max(tin + 0.3, s.marks && s.marks[i] != null ? s.marks[i] : s.t0 + i * 0.4);
        tl.fromTo(t, { opacity: 0, y: 40, scale: 0.7 }, { opacity: 0.35, y: 0, scale: 0.9, duration: 0.35, ease: "power3.out", immediateRender: false }, tin);
        tl.to(t, { opacity: 1, scale: 1.08, duration: 0.2, ease: "power2.out" }, at);
        tl.to(t, { scale: 1, duration: 0.25, ease: "back.out(3)" }, at + 0.2);
      });
      leave(tl, root, s);
    } };
  };

  // Pixel art: a code-drawn sprite builds in, idles, and can burst on a word; an optional label in the pixel
  // font types in under it, and an optional line of normal text (readable at any size) below that.
  // spec: sprite, label, text, size (sprite width px), build (rows | dissolve | pop), idle (bob | spin | none),
  // card (true: a dark tile behind it); marks: [burst]
  W.pixel = function (s) {
    const root = el("div", "mk-pixel" + (s.card ? " card" : ""));
    const size = s.size || 288;
    const sp = sprite(s.sprite, size);
    const holder = el("div", "mk-pxsprite", root); holder.appendChild(sp.svg);
    const unit = size / sp.cols;
    const bits = [];
    for (let k = 0; k < 8; k++) {  // burst particles: squares of the sprite's pixel size
      const b = el("i", "mk-pxbit", holder);
      b.style.width = b.style.height = Math.round(unit) + "px";
      b.style.background = k % 2 ? "var(--accent-fill)" : "#F5B301";
      bits.push(b);
    }
    const lab = s.label ? pixelText(s.label, Math.max(6, Math.round(unit * 0.5)), s.card ? "#fff" : "var(--ink)") : null;
    if (lab) el("div", "mk-pxlabel", root).appendChild(lab.svg);
    if (s.text) el("div", "mk-pxtext", root, s.text);
    return { el: root, play: function (tl) {
      const t = s.t0, build = s.build || "rows";
      gsap.set(bits, { opacity: 0, x: 0, y: 0, xPercent: -50, yPercent: -50 });
      enter(tl, root, s, "pixel");
      // the sprite builds in steps on whole frames (display toggles: seek-safe, every frame shows whole pixels)
      let ready = onFrame(t + 0.3);
      if (build !== "pop") {
        const f = frame();
        sp.cells.forEach(function (c) { gsap.set(c.el, { opacity: 0 }); });
        if (build === "dissolve") {
          const order = shuffled(sp.cells.length, sp.cells.length);
          const frames = Math.max(1, Math.round(0.5 / f)), per = Math.ceil(order.length / frames);
          order.forEach(function (ci, n) { tl.set(sp.cells[ci].el, { opacity: 1 }, onFrame(t) + Math.floor(n / per) * f); });
          ready = onFrame(t) + frames * f;
        } else {  // rows, top down: one row per step, never two rows in one frame
          const step = Math.max(f, onFrame(0.5 / sp.rows) || f);
          sp.cells.forEach(function (c) { tl.set(c.el, { opacity: 1 }, onFrame(t) + c.y * step); });
          ready = onFrame(t) + sp.rows * step;
        }
      }
      if (s.t1 - ready > 1.2) shine(tl, sp, ready + 0.1);  // it lands with a shine
      if (lab) {
        lab.groups.forEach(function (gr) { gsap.set(gr, { opacity: 0 }); });
        lab.groups.forEach(function (gr, i) { tl.set(gr, { opacity: 1 }, onFrame(ready + i * 0.05)); });
      }
      const idle = s.idle || "bob";
      const until = outAt(s) - 0.05;
      const n = Math.floor((until - ready) / 0.4);
      if (idle === "bob" && n >= 2) tl.to(holder, { y: -unit, duration: 0.4, ease: "steps(1)", yoyo: true, repeat: n - 1 }, ready);
      if (idle === "spin" && n >= 2) tl.to(holder, { scaleX: -1, duration: 0.4, ease: "steps(2)", yoyo: true, repeat: n - 1 }, ready);
      if (s.marks && s.marks[0] != null) {  // a burst: the sprite jumps and pixels fly out
        const tb = Math.max(ready, s.marks[0]);
        tl.fromTo(sp.svg, { scale: 1 }, { scale: 1.15, duration: 0.24, ease: "steps(2)", yoyo: true, repeat: 1, immediateRender: false }, tb);
        shine(tl, sp, tb);
        bits.forEach(function (b, k) {
          // from the sprite's edge outwards, behind it: a ring of pixels, never a blob over the sprite
          const ang = (k / bits.length) * Math.PI * 2 + 0.4, r0 = size * 0.45, r1 = size * 0.85;
          // every property in both states: a from-only property is not restored the same way on every seek
          tl.fromTo(b, { opacity: 1, x: Math.cos(ang) * r0, y: Math.sin(ang) * r0 }, { opacity: 1, x: Math.cos(ang) * r1, y: Math.sin(ang) * r1, duration: 0.45, ease: "steps(5)", immediateRender: false }, tb);
          tl.fromTo(b, { opacity: 1 }, { opacity: 0, duration: 0, immediateRender: false }, tb + 0.5);
        });
      }
      leave(tl, root, s, "pixel");
    } };
  };

  // Bars: two to four values side by side, each growing and counting up on its word (a comparison, where a
  // chart is one trend). spec: title, items [{name, value}], suffix, max (default 100), highlight, label;
  // marks: one per bar
  W.bars = function (s) {
    const root = el("div", "mk-card mk-bars");
    if (s.title) { const head = el("div", "mk-title", root); head.appendChild(icon("trend", 44, "var(--accent)")); el("span", "", head, s.title); }
    const max = s.max || Math.max(100, ...(s.items || []).map(function (it) { return Number(it.value) || 0; }));
    const bars = (s.items || []).map(function (it, i) {
      const row = el("div", "mk-vbar" + (i === s.highlight ? " hl" : ""), root);
      const top = el("div", "mk-bartop", row);
      el("div", "mk-barname", top, it.name);
      const num = el("div", "mk-barnum", top);
      const steps = counter(num, Number(it.value) || 0);
      if (s.suffix) el("span", "mk-suffix", num, s.suffix);
      const track = el("div", "mk-bartrack", row);
      const fill = el("div", "mk-barfill", track);
      return { row: row, fill: fill, steps: steps, to: Math.min(1, (Number(it.value) || 0) / max) };
    });
    if (s.label) el("div", "mk-label", root, s.label);
    return { el: root, play: function (tl) {
      gsap.set(bars.map(function (b) { return b.row; }), { opacity: 0.35 });
      gsap.set(bars.map(function (b) { return b.fill; }), { scaleX: 0, transformOrigin: "0% 50%" });
      enter(tl, root, s);
      bars.forEach(function (b, i) {
        const t = Math.max(s.t0 + 0.4 + i * 0.3, mark(s, i, 0.15 + i * 0.3));
        tl.to(b.row, { opacity: 1, duration: 0.15, ease: "none" }, t);
        tl.fromTo(b.fill, { scaleX: 0 }, { scaleX: b.to, duration: 0.7, ease: "power2.out", immediateRender: false }, t);  // the count's own ease
        countUp(tl, b.steps, t, 0.7);
        if (i === s.highlight) pulse(tl, b.row, t + 0.7);
      });
      leave(tl, root, s);
    } };
  };

  // A pixel gag: the giver walks in, hands the item over (it hops across on a stepped arc), the receiver
  // jumps with a shine and a pixel label, the giver sneaks off. spec: giver, receiver, item (sprites),
  // label (pixel font, short), text; marks: [walk in, hand over, react]
  W.handoff = function (s) {
    const root = el("div", "mk-handoff" + (s.card === false ? "" : " card"));
    const size = s.size || 220;
    const stage = el("div", "mk-hostage", root);
    const giver = sprite(s.giver || "salesman", size), recv = sprite(s.receiver || "claude", size * 1.15);
    const thing = sprite(s.item || "coin", size * 0.32);
    const gBox = el("div", "mk-hogiver", stage); gBox.appendChild(giver.svg);
    const rBox = el("div", "mk-horecv", stage); rBox.appendChild(recv.svg);
    const iBox = el("div", "mk-hoitem", stage); iBox.appendChild(thing.svg);
    const unit = size / giver.cols;
    const star = sprite("star", size * 0.4);
    const sBox = el("div", "mk-hostar", rBox); sBox.appendChild(star.svg);
    el("i", "mk-hoshadow", gBox); el("i", "mk-hoshadow", rBox);
    const lab = s.label ? pixelText(s.label, Math.max(8, Math.round(unit * 0.9)), "#F5B301") : null;
    const labBox = lab ? el("div", "mk-pxlabel", root) : null;
    if (lab) labBox.appendChild(lab.svg);
    if (s.text) el("div", "mk-pxtext", root, s.text);
    return { el: root, play: function (tl) {
      // how far the giver walks; how far the item hops (giver hand -> receiver's middle: the CSS gap is 120 px)
      const walk = size * 1.4, gap = size + 120 + size * 0.575 - 150 - size * 0.16;
      enter(tl, root, s, "pixel");
      const tw = onFrame(Math.max(s.t0 + 0.2, mark(s, 0, 0.1)));
      const th = onFrame(Math.max(tw + 0.9, mark(s, 1, 0.4)));
      const tr = onFrame(Math.max(th + 0.5, mark(s, 2, 0.55)));
      const tb = onFrame(Math.min(tr + 0.7, outAt(s) - 0.9));
      // in: stepped walk with a two-frame bob (x and y are separate tweens, never overlapping themselves)
      tl.fromTo(gBox, { x: -walk }, { x: 0, duration: 0.8, ease: "steps(6)", immediateRender: false }, tw);
      tl.fromTo(gBox, { y: 0 }, { y: -unit, duration: 0.13, ease: "steps(1)", yoyo: true, repeat: 5, immediateRender: false }, tw);
      // the hand-over: the item hops across, up then down, and is gone on arrival
      gsap.set(iBox, { opacity: 0 });
      tl.fromTo(iBox, { opacity: 0 }, { opacity: 1, duration: 0, immediateRender: false }, th);
      tl.fromTo(iBox, { x: 0 }, { x: gap, duration: 0.5, ease: "steps(6)", immediateRender: false }, th);
      tl.fromTo(iBox, { y: 0 }, { y: -size * 0.95, duration: 0.25, ease: "steps(3)", immediateRender: false }, th);  // over the head
      tl.fromTo(iBox, { y: -size * 0.95 }, { y: size * 0.2, duration: 0.25, ease: "steps(3)", immediateRender: false }, th + 0.25);  // at the chest, under the eyes
      tl.fromTo(iBox, { scaleX: 1, scaleY: 1 }, { scaleX: 1.35, scaleY: 0.6, duration: 0.08, ease: "steps(1)", immediateRender: false }, th + 0.5);  // caught
      tl.fromTo(iBox, { opacity: 1 }, { opacity: 0, duration: 0, immediateRender: false }, th + 0.6);
      // the receiver crouches, jumps and lands with a squash; a star pops above its head; the label lands
      tl.fromTo(recv.svg, { scaleY: 1 }, { scaleY: 0.85, duration: 0.1, ease: "steps(1)", yoyo: true, repeat: 1, immediateRender: false }, tr - 0.2);
      tl.fromTo(rBox, { y: 0 }, { y: -size * 0.3, duration: 0.2, ease: "steps(2)", yoyo: true, repeat: 1, immediateRender: false }, tr);
      tl.fromTo(recv.svg, { scaleX: 1 }, { scaleX: 1.12, duration: 0.1, ease: "steps(1)", yoyo: true, repeat: 1, immediateRender: false }, tr + 0.4);
      gsap.set(sBox, { opacity: 0 });
      gsap.set(sBox, { xPercent: -50 });
      tl.fromTo(sBox, { opacity: 0, scale: 0.5 }, { opacity: 1, scale: 1.3, duration: 0.14, ease: "steps(2)", immediateRender: false }, tr);  // pops gold, overshoots
      tl.fromTo(sBox, { scale: 1.3 }, { scale: 1, duration: 0.1, ease: "steps(1)", immediateRender: false }, tr + 0.14);
      tl.fromTo(sBox, { rotation: 0 }, { rotation: 90, duration: 0.6, ease: "steps(2)", immediateRender: false }, tr + 0.24);
      if (labBox) {  // the label lands whole (typed letter by letter, "#1" read as "H" first)
        gsap.set(labBox, { opacity: 0 });
        tl.fromTo(labBox, { opacity: 0, scale: 0.4 }, { opacity: 1, scale: 1, duration: 0.3, ease: "steps(4)", immediateRender: false }, tr + 0.15);
      }
      // the giver turns and sneaks off the way he came
      tl.fromTo(giver.svg, { scaleX: 1 }, { scaleX: -1, duration: 0, immediateRender: false }, tb);
      tl.fromTo(gBox, { x: 0 }, { x: -walk, duration: 0.8, ease: "steps(6)", immediateRender: false }, tb);
      tl.fromTo(gBox, { y: 0 }, { y: -unit, duration: 0.13, ease: "steps(1)", yoyo: true, repeat: 5, immediateRender: false }, tb);
      tl.fromTo(gBox, { opacity: 1 }, { opacity: 0, duration: 0.3, ease: "steps(3)", immediateRender: false }, tb + 0.5);  // fades as he reaches the edge
      leave(tl, root, s, "pixel");
    } };
  };

  // The brand's logo (an SVG file copied into the composition) with a tagline.
  W.logo = function (s) {
    const root = el("div", "mk-logo");
    const img = el("img", "", root); img.src = s.src || "assets/logo.svg"; img.style.height = (s.height || 120) + "px";
    if (s.tagline) el("div", "mk-tagline", root, s.tagline);
    return { el: root, play: function (tl) { enter(tl, root, s, "pop"); leave(tl, root, s, "pop"); } };
  };

  // A paper shredder: videos drop into it, strips fall out, the strips become a grid of frames with times.
  // spec: videos [titles], step (s between frames, default 0.5), label; marks: [feed, strips, grid]
  W.shredder = function (s) {
    const root = el("div", "mk-card mk-shred");
    if (s.title) el("div", "mk-title", root, s.title);
    const stage = el("div", "sh-stage", root);
    const feed = el("div", "sh-feed", stage);
    const hues = [210, 20, 150, 280, 45];
    const vids = (s.videos || ["Explainer A", "Explainer B", "Explainer C"]).slice(0, 4).map(function (t, i) {
      const v = el("div", "sh-vid", feed);
      v.style.background = "linear-gradient(135deg, hsl(" + hues[i % 5] + ",70%,55%), hsl(" + (hues[i % 5] + 40) + ",70%,35%))";
      const pl = el("div", "sh-play", v); pl.appendChild(icon("play", 34, "#fff"));
      el("div", "sh-vtitle", v, t);
      return v;
    });
    const machine = el("div", "sh-machine", stage);
    el("div", "sh-slot", machine);
    el("div", "sh-light", machine);
    el("div", "sh-mlabel", machine, s.machine || "frames");
    const out = el("div", "sh-out", stage);
    const strips = [];
    for (let k = 0; k < 14; k++) {
      const st = el("i", "", out);
      st.style.background = "hsl(" + hues[k % 3] + ",65%," + (45 + (k % 4) * 6) + "%)";
      st.style.left = (6 + k * 6.6) + "%";
      strips.push(st);
    }
    const grid = el("div", "sh-grid", stage);
    const step = s.step || 0.5;
    const tiles = [];
    for (let k = 0; k < 12; k++) {
      const tl0 = el("div", "sh-tile", grid);
      tl0.style.background = "linear-gradient(135deg, hsl(" + hues[Math.floor(k / 4) % 3] + ",60%," + (40 + (k % 4) * 7) + "%), hsl(" + (hues[Math.floor(k / 4) % 3] + 30) + ",60%,30%))";
      el("span", "", tl0, (k * step).toFixed(1) + "s");
      tiles.push(tl0);
    }
    if (s.label) el("div", "sh-label", stage, s.label);
    const lab = stage.querySelector(".sh-label");
    return { el: root, play: function (tl) {
      gsap.set(tiles.concat(strips), { opacity: 0 });
      if (lab) gsap.set(lab, { opacity: 0 });
      enter(tl, root, s);
      const tf = mark(s, 0, 0.12), ts = Math.max(tf + 0.5, mark(s, 1, 0.45)), tg = Math.max(ts + 0.6, mark(s, 2, 0.7));
      vids.forEach(function (v, i) {
        tl.fromTo(v, { y: -40, rotation: (i % 2 ? 6 : -6) }, { y: 300, rotation: 0, duration: 0.55, ease: "power2.in", immediateRender: false }, tf + i * 0.22);
      });
      tl.fromTo(machine, { x: 0 }, { x: 6, duration: 0.05, yoyo: true, repeat: 9, ease: "none", immediateRender: false }, tf + 0.3);
      tl.fromTo(stage.querySelector(".sh-light"), { backgroundColor: "#3c3" }, { backgroundColor: "#f33", duration: 0.12, yoyo: true, repeat: 7, immediateRender: false }, tf + 0.3);
      strips.forEach(function (st, k) {
        const at = ts + (k % 7) * 0.05;
        // opacity has its own tweens: a strip not yet out read 1 or 0 depending on the seek order
        tl.fromTo(st, { opacity: 0 }, { opacity: 0, duration: 0, immediateRender: false }, s.t0);
        tl.fromTo(st, { opacity: 0 }, { opacity: 1, duration: 0.04, ease: "none", immediateRender: false }, at);
        tl.fromTo(st, { y: -60, rotation: 0 }, { y: 40 + (k % 3) * 18, rotation: (k % 2 ? 4 : -4), duration: 0.45, ease: "power2.out", immediateRender: false }, at);
        // fromTo, not to: a .to records its start on first render, so the strip's fade depended on the seek order
        tl.fromTo(st, { opacity: 1 }, { opacity: 0, duration: 0.2, immediateRender: false }, tg);
      });
      tiles.forEach(function (t, k) {
        tl.fromTo(t, { opacity: 0, scale: 0.4, y: -40 }, { opacity: 1, scale: 1, y: 0, duration: 0.35, ease: "back.out(2)", immediateRender: false }, tg + k * 0.06);
      });
      if (lab) tl.fromTo(lab, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.3, immediateRender: false }, tg + 0.5);
      leave(tl, root, s);
    } };
  };

  // A code file whose values get retyped on their words (and the video changes with them: pair each mark
  // with a `grade` or `caption_font` effect in the plan). spec: file, lines ["key: value"], edits
  // [{line, to}]; marks: one per edit.
  W.code = function (s) {
    const root = el("div", "mk-card mk-code");
    const bar = el("div", "cd-bar", root);
    [0, 1, 2].forEach(function () { el("i", "", bar); });
    el("span", "", bar, s.file || "video.yaml");
    const body = el("div", "cd-body", root);
    const vals = [];
    (s.lines || []).forEach(function (ln, i) {
      const row = el("div", "cd-row", body);
      el("span", "cd-n", row, String(i + 1));
      const at = ln.indexOf(": ");
      if (at < 0) { el("span", "cd-k", row, ln); vals.push(null); return; }
      el("span", "cd-k", row, ln.slice(0, at));
      el("span", "cd-p", row, ": ");
      const v = el("span", "cd-v", row);
      const old = el("span", "", v, ln.slice(at + 2));
      vals.push({ row: row, v: v, old: old });
    });
    const edits = (s.edits || []).map(function (e) {
      const slot = vals[e.line];
      if (!slot) return null;
      const t = typed(slot.v, String(e.to), "cd-new");
      return { slot: slot, t: t, swatch: /^"?#[0-9a-fA-F]{6}"?$/.test(String(e.to)) ? String(e.to).replace(/"/g, "") : null };
    });
    return { el: root, play: function (tl) {
      enter(tl, root, s);
      edits.forEach(function (e, k) {
        if (!e) return;
        const t = mark(s, k, 0.3 + 0.5 * k / Math.max(1, edits.length));
        tl.to(e.slot.row, { backgroundColor: "rgba(255,255,255,.12)", duration: 0.15 }, t - 0.35);
        tl.to(e.slot.old, { backgroundColor: "rgba(80,140,255,.55)", duration: 0.12 }, t - 0.3);
        tl.set(e.slot.old, { display: "none" }, t);
        typeOn(tl, e.t, t, t + Math.min(0.6, 0.06 * e.t.chars.length));
        if (e.swatch) {
          const sw = el("i", "cd-sw", e.slot.row); sw.style.background = e.swatch;
          gsap.set(sw, { scale: 0 });
          tl.to(sw, { scale: 1, duration: 0.3, ease: "back.out(3)" }, t + 0.5);
        }
        tl.to(e.slot.row, { backgroundColor: "rgba(255,255,255,0)", duration: 0.4 }, t + 0.8);
      });
      leave(tl, root, s);
    } };
  };

  // A storage bucket: files drop in and each folder's count ticks up on its word.
  // spec: title (e.g. "R2 bucket"), name, folders [{name, count}]; marks: one per folder.
  W.bucket = function (s) {
    const root = el("div", "mk-card mk-bucket");
    const head = el("div", "bk-head", root);
    const pail = el("div", "bk-pail", head);
    pail.innerHTML = '<svg viewBox="0 0 64 64" width="100%" height="100%"><path d="M8 16h48l-6 42H14z" fill="var(--accent)"/>' +
      '<ellipse cx="32" cy="16" rx="24" ry="6" fill="#ffb26b"/><ellipse cx="32" cy="16" rx="19" ry="3.6" fill="#7a3a00"/>' +
      '<path d="M10 16 Q32 -8 54 16" fill="none" stroke="var(--ink)" stroke-width="3"/></svg>';
    const ht = el("div", "bk-ht", head);
    el("div", "mk-app", ht, s.title || "Storage bucket");
    if (s.name) el("div", "mk-sub", ht, s.name);
    const drops = [];
    for (let k = 0; k < 6; k++) { const d = el("i", "bk-drop", head); d.style.left = (12 + k * 9) + "px"; drops.push(d); }
    const rows = (s.folders || []).map(function (f) {
      const row = el("div", "mk-row bk-row", root);
      const ic = el("div", "mk-ic", row); ic.appendChild(icon("folder", 34, "#fff"));
      el("div", "mk-name", row, f.name);
      const cnt = el("div", "bk-count", row);
      return { row: row, steps: counter(cnt, f.count || 0), n: f.count || 0 };
    });
    return { el: root, play: function (tl) {
      gsap.set(rows.map(function (r) { return r.row; }), { opacity: 0.45 });
      gsap.set(drops, { opacity: 0 });
      enter(tl, root, s);
      rows.forEach(function (r, i) {
        const t = mark(s, i, 0.25 + 0.6 * i / Math.max(1, rows.length));
        tl.to(r.row, { opacity: 1, duration: 0.2 }, t);
        tl.fromTo(r.row, { scale: 1 }, { scale: 1.04, duration: 0.12, yoyo: true, repeat: 1, immediateRender: false }, t);
        countUp(tl, r.steps, t, 0.8);
        drops.forEach(function (d, k) {
          tl.fromTo(d, { opacity: 1, y: -80 - k * 14 }, { y: 30, opacity: 0, duration: 0.45, ease: "power2.in", immediateRender: false }, t + k * 0.06);
        });
      });
      leave(tl, root, s);
    } };
  };

  // Agents that make and agents that judge, then Robert: a loop that learns his taste.
  // spec: maker, reviewers [names], scores [numbers], you, verdict ("up"/"down"), meter (label);
  // marks: [maker, reviewers, you, meter]
  W.agents = function (s) {
    const root = el("div", "mk-card mk-agents");
    function node(ic, name, cls) {
      const n = el("div", "ag-node " + (cls || ""), root);
      const b = el("div", "ag-ic", n); b.appendChild(icon(ic, 46, "#fff"));
      el("div", "ag-name", n, name);
      return n;
    }
    const maker = node("bot", s.maker || "Creator agent", "ag-make");
    const prog = el("div", "ag-prog", maker); const fill = el("i", "", prog);
    el("div", "ag-arrow", root);
    const rev = node("eye", (s.reviewers || ["Reviewer agents"]).join(" · "), "ag-rev");
    const chips = el("div", "ag-chips", rev);
    const scores = (s.scores || [6.5, 7, 7.5]).map(function (v) { return el("span", "ag-score", chips, String(v)); });
    el("div", "ag-arrow", root);
    const you = node("person", s.you || "Robert", "ag-you");
    const thumb = el("div", "ag-thumb", you); thumb.appendChild(icon("thumb", 44, "#fff"));
    if (s.verdict === "down") thumb.style.transform = "rotate(180deg)";
    const loop = el("div", "ag-loop", root);
    let meter = null, mfill = null;
    if (s.meter) {
      meter = el("div", "ag-meter", root);
      el("span", "", meter, s.meter);
      const bar = el("div", "ag-mbar", meter); mfill = el("i", "", bar);
    }
    return { el: root, play: function (tl) {
      const nodes = [maker, rev, you];
      gsap.set(nodes, { opacity: 0.35 });
      gsap.set(scores.concat([thumb]), { scale: 0 });
      gsap.set(fill, { scaleX: 0 });
      if (meter) gsap.set(mfill, { scaleX: 0 });
      gsap.set(loop, { opacity: 0 });
      enter(tl, root, s);
      const t0 = mark(s, 0, 0.12), t1 = Math.max(t0 + 0.6, mark(s, 1, 0.38)), t2 = Math.max(t1 + 0.6, mark(s, 2, 0.6));
      tl.to(maker, { opacity: 1, duration: 0.2 }, t0);
      tl.to(fill, { scaleX: 1, duration: Math.max(0.4, t1 - t0 - 0.1), ease: "power1.inOut" }, t0);
      tl.to(rev, { opacity: 1, duration: 0.2 }, t1);
      scores.forEach(function (c, k) { tl.to(c, { scale: 1, duration: 0.3, ease: "back.out(3)" }, t1 + 0.15 + k * 0.15); });
      tl.to(you, { opacity: 1, duration: 0.2 }, t2);
      tl.to(thumb, { scale: 1, duration: 0.4, ease: "back.out(3)" }, t2 + 0.1);
      tl.to(loop, { opacity: 1, duration: 0.3 }, t2 + 0.4);
      if (meter) {
        const tm = Math.max(t2 + 0.6, mark(s, 3, 0.8));
        tl.to(mfill, { scaleX: s.meter_value || 0.82, duration: 0.9, ease: "power2.out" }, tm);
      }
      leave(tl, root, s);
    } };
  };

  // Hand-overs between two product cards (ADR 0033): the next card takes over from the last without a
  // blank frame, a hard swap or a crossfade. a, b: { root (the widget's own element), box (its .box) };
  // the hand-over runs from b.t0 for `dur` seconds (reel.py gives the outgoing card that much extra time).
  //   morph: a surface in the card's own look (the carrier) is left where a was and changes shape into b's
  //          rectangle while a's content drops out and b's content comes up on it;
  //   push:  a slides up and out while b slides up into its place, one motion (a deck that scrolls);
  //   stack: b lands on a from below while a shrinks back under it (cards piling up);
  //   cut:   nothing here: a leaves and b enters by their own motions.
  // Only cards (`.mk-card`) morph: a sticker or tile row pushes instead (the carrier would not match it).
  // Geometry is read when a tween first renders (function values), after the fit; reel.html invalidates
  // the returned tweens when the fonts arrive, so the rectangles are the ones on screen.
  function geometry(node, layer) {
    const r = node.getBoundingClientRect(), L = layer.getBoundingClientRect();
    const k = L.width / Math.max(1, layer.offsetWidth);  // the page may be scaled to a draft size
    return { x: (r.left - L.left) / k, y: (r.top - L.top) / k, w: r.width / k, h: r.height / k };
  }
  function handover(tl, a, b, kind, dur, layer) {
    const T = b.t0, H = dur || 0.55, out = [];
    const L = layer || a.root.parentNode;
    if (kind === "morph" && !(a.root.classList.contains("mk-card") && b.root.classList.contains("mk-card"))) kind = "push";
    if (kind === "morph") {
      const car = el("div", "mk-carrier", L);
      gsap.set(car, { opacity: 0 });
      // (opacity is its own 0 -> 1 step: a `from` of 1 would show the carrier before T once scrubbed back)
      const ga = () => geometry(a.root, L), gb = () => geometry(b.root, L);  // a's rect as drifted, on screen
      tl.fromTo(car, { opacity: 0 }, { opacity: 1, duration: 0.01, ease: "none", immediateRender: false }, T);
      out.push(tl.fromTo(car, { x: () => ga().x, y: () => ga().y, width: () => ga().w, height: () => ga().h },
        { x: () => gb().x, y: () => gb().y, width: () => gb().w, height: () => gb().h, duration: H, ease: "power3.inOut", immediateRender: false }, T));
      hide(tl, car, T + H);
      // a's own plate goes at once (the carrier is the plate from here); its content fades while the carrier
      // starts to move, and b's content comes up on the carrier as it arrives: the sheet is never empty long
      tl.set(a.root, { backgroundColor: "transparent", boxShadow: "none" }, T);
      tl.to(a.root, { opacity: 0, duration: 0.22, ease: "none" }, T);
      tl.fromTo(b.root, { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: 0.3, ease: "power2.out", immediateRender: false }, T + H - 0.3);
    } else if (kind === "stack") {
      tl.to(a.root, { scale: 0.94, y: -28, opacity: 0.6, duration: H * 0.7, ease: "power2.out" }, T);
      tl.to(a.root, { opacity: 0, duration: 0.15, ease: "none" }, T + H - 0.15);
      tl.fromTo(b.root, { opacity: 0 }, { opacity: 1, duration: 0.01, ease: "none", immediateRender: false }, T);
      tl.fromTo(b.root, { y: 180, scale: 0.92 }, { y: 0, scale: 1, duration: H, ease: "back.out(1.4)", immediateRender: false }, T);
    } else if (kind === "push") {
      const dy = () => Math.max(geometry(a.root, L).h, geometry(b.root, L).h) + 60;
      out.push(tl.to(a.root, { y: () => -dy(), duration: H, ease: "power3.inOut" }, T));
      tl.to(a.root, { opacity: 0, duration: 0.12, ease: "none" }, T + H - 0.12);
      tl.fromTo(b.root, { opacity: 0 }, { opacity: 1, duration: 0.01, ease: "none", immediateRender: false }, T);
      out.push(tl.fromTo(b.root, { y: () => dy() }, { y: 0, duration: H, ease: "power3.inOut", immediateRender: false }, T));
    }
    return out;
  }

  // A step label shared by a run of product cards (ADR 0033): "1/4  SEO ON A BUDGET" enters once, its step
  // pill flips to the next step as each card arrives, and it leaves with the last card.
  // spec: text, steps [[t, label]...], t0, t1, w
  function kicker(s) {
    const root = el("div", "mk mk-kickrun");
    root.style.width = s.w ? s.w + "px" : "";
    const k = el("div", "mk-kick", root);
    const steps = (s.steps || []).filter(function (st) { return st[1]; });
    const holder = steps.length ? el("span", "mk-steps", k) : null;
    const pills = steps.map(function (st) { return el("b", "", holder, st[1]); });
    el("span", "", k, s.text || "");
    return { el: root, play: function (tl) {
      pills.forEach(function (b, i) { gsap.set(b, { opacity: i ? 0 : 1 }); });
      tl.fromTo(root, { opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 0.35, ease: "power3.out", immediateRender: false }, s.t0);
      pills.forEach(function (b, i) {
        if (!i) return;
        const t = Math.max(s.t0 + 0.4, steps[i][0]);
        tl.fromTo(pills[i - 1], { rotationX: 0, opacity: 1, transformPerspective: 600 }, { rotationX: 80, opacity: 0, transformPerspective: 600, duration: 0.18, ease: "power2.in", immediateRender: false }, t);
        tl.fromTo(b, { rotationX: -80, opacity: 0, transformPerspective: 600 }, { rotationX: 0, opacity: 1, transformPerspective: 600, duration: 0.32, ease: "back.out(2)", immediateRender: false }, t + 0.14);
      });
      const out = Math.max(s.t0 + 0.7, s.t1 - 0.3);
      tl.to(root, { opacity: 0, duration: 0.3, ease: "power2.in" }, out);
      hide(tl, root, out + 0.3);
    } };
  }

  // A living background behind the product cards (ADR 0033, style bg: drift): two soft brand-tinted shapes
  // drift on slow sine loops for the whole video. Gradients, not blur filters: cheap per frame.
  // spec: duration (the video), loop_s
  function ambient(s) {
    const root = el("div", "mk-ambient");
    const a = el("i", "mk-blob a", root), b = el("i", "mk-blob b", root);
    const loop = Math.max(4, s.loop_s || 18), n = Math.max(1, Math.ceil((s.duration || loop) / (loop / 2)));
    return { el: root, play: function (tl) {
      tl.fromTo(root, { opacity: 0 }, { opacity: 1, duration: 0.01, ease: "none", immediateRender: false }, 0);
      tl.fromTo(a, { x: 0, y: 0, scale: 1 }, { x: 140, y: -90, scale: 1.12, duration: loop / 2, ease: "sine.inOut", yoyo: true, repeat: n, immediateRender: false }, 0);
      tl.fromTo(b, { x: 0, y: 0, scale: 1 }, { x: -120, y: 110, scale: 0.92, duration: loop * 0.7 / 2, ease: "sine.inOut", yoyo: true, repeat: Math.ceil(n / 0.7), immediateRender: false }, 0);
    } };
  }

  window.MK = {
    build: function (spec) {
      const f = W[spec.kind];
      if (!f) throw new Error("motion kit: unknown widget " + spec.kind);
      const w = f(spec);
      w.root = w.el;  // the widget's own element (a hand-over moves it; the kicker wrap below is not it)
      w.el.style.width = spec.w ? spec.w + "px" : "";
      // footer: a source line at the bottom of the card ("Bing Webmaster blog, Oct 13 2026 · beta"), or a
      // label with the site on the right (footer_site, the brand social-card footer: "method · acme.example")
      if (spec.footer && spec.footer_site) {
        const foot = el("div", "mk-foot site", w.el);
        el("span", "", foot, spec.footer); el("b", "", foot, spec.footer_site);
      } else if (spec.footer) el("div", "mk-foot", w.el, spec.footer);
      if (!spec.kicker) { w.el.classList.add("mk"); return w; }
      // A step label above the widget ("STEP 2  Check the sources"): enters first, leaves with it.
      const wrap = el("div", "mk");
      wrap.style.width = spec.w ? spec.w + "px" : "";
      const k = el("div", "mk-kick", wrap);
      if (spec.step) el("b", "", k, spec.step);
      el("span", "", k, spec.kicker);
      w.el.style.width = "100%"; wrap.appendChild(w.el);
      return { el: wrap, root: w.root, play: function (tl) {
        gsap.set(w.el, { opacity: 0 });
        tl.fromTo(wrap, { opacity: 0 }, { opacity: 1, duration: 0.01, immediateRender: false }, spec.t0);
        tl.fromTo(k, { opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 0.35, ease: "power3.out", immediateRender: false }, spec.t0);
        w.play(tl);
        const out = Math.max(spec.t0 + 0.7, spec.t1 - 0.3);
        tl.to(k, { opacity: 0, duration: 0.3, ease: "power2.in" }, out);
        hide(tl, wrap, out + 0.3);
      } };
    },
    handover: handover,
    handovers: ["morph", "push", "stack", "cut"],
    kicker: kicker,
    ambient: ambient,
    kinds: Object.keys(W),
    sprites: Object.keys(PX),
    motions: MOTIONS,
  };
})();
