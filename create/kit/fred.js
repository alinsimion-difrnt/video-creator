/* Fred (create/kit, ADR 0027): an upright cartoon fish rigged in SVG. He stands on his tail, uses his fins as
   arms, hops when he travels, rows a little boat through the air, reads, writes, texts and hammers, waves,
   claps (an alchemist's clap) and dances. Hats, a moustache, glasses, a crown, a bow tie and automail (a steel
   fin and tail) are drawn into the rig, so they move and change style with him. Styles are filters on the
   whole drawing: illustrated (as drawn), toon3d (lit like clay) and pixel (big square pixels).

   FRED.build(id, w) -> rig; FRED.play(rig, P, tl) adds his whole performance to the timeline from the prop
   track create/footage/props.py computes (holds, rides, acts, moves, accessories, styles). Seek-safe: only
   timeline tweens and sets. */
(function () {
  const NS = "http://www.w3.org/2000/svg";
  // the carp (Robert's first catch): an olive-gold body, a darker back, a golden belly, a net of scales, orange
  // fins and a forked orange tail, peach lips and barbels, a gold-ringed round eye
  const OLIVE = "#8a8236", BACK = "#55542a", GOLD = "#e9bd5c", FINC = "#ff8c1a", DEEP = "#e2600e", DORSAL = "#b9873a",
    LIP = "#eba27a", IRIS = "#e6b740", INK = "#1d1a24";
  const PIV_F = "142 158", PIV_B = "64 150", ORIGIN = "100 250";
  let defs = null;

  function svgEl(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (parent) parent.appendChild(e);
    return e;
  }
  function group(parent, cls) { return svgEl("g", { class: cls }, parent); }
  // Move a group's children into an inner group (a separate layer to animate: idle sway under poses).
  function wrap(g, cls) {
    const inner = svgEl("g", { class: cls });
    while (g.firstChild) inner.appendChild(g.firstChild);
    g.appendChild(inner);
    return inner;
  }
  const LOOK = { up: { cx: 124, cy: 91 }, camera: { cx: 121, cy: 99 }, down: { cx: 126, cy: 106 }, ahead: { cx: 130, cy: 99 } };
  function look(tl, R, where, t) { tl.to([R.iris, R.pupil], { attr: LOOK[where], duration: 0.12, ease: "power2.out" }, t); }

  // Shared filters: clay lighting, and a pixelate per block size.
  function filters() {
    if (defs) return defs;
    const s = svgEl("svg", { width: 0, height: 0, style: "position:absolute" });
    document.body.appendChild(s);
    defs = svgEl("defs", {}, s);
    defs.innerHTML =
      '<filter id="fr-clay" color-interpolation-filters="sRGB" x="-10%" y="-10%" width="120%" height="120%">' +
      '<feGaussianBlur in="SourceAlpha" stdDeviation="9" result="b"/>' +
      '<feDiffuseLighting in="b" surfaceScale="9" diffuseConstant="1.1" lighting-color="#fff" result="d"><feDistantLight azimuth="235" elevation="48"/></feDiffuseLighting>' +
      '<feComposite in="d" in2="SourceAlpha" operator="in" result="d2"/>' +
      '<feSpecularLighting in="b" surfaceScale="9" specularConstant="1.1" specularExponent="26" lighting-color="#fff" result="s"><feDistantLight azimuth="235" elevation="52"/></feSpecularLighting>' +
      '<feComposite in="s" in2="SourceAlpha" operator="in" result="s2"/>' +
      '<feBlend in="SourceGraphic" in2="d2" mode="multiply" result="m"/>' +
      // a softer highlight and a saturation lift: the drawing stands in for 3D Fred (in the boat) and must
      // match his rendered frames; at k2 0.9 the specular washed him out pale (lab v16)
      '<feComposite in="s2" in2="m" operator="arithmetic" k1="0" k2="0.35" k3="1" k4="0" result="lit0"/>' +
      '<feColorMatrix in="lit0" type="saturate" values="1.3" result="lit"/>' +
      '<feDropShadow in="lit" dx="4" dy="10" stdDeviation="8" flood-opacity=".35"/></filter>';
    return defs;
  }
  function pixelFilter(block) {
    const id = "fr-px-" + block;
    if (!document.getElementById(id)) {
      const half = Math.max(1, Math.floor(block / 2));
      const f = svgEl("filter", { id: id, x: "0", y: "0", width: "1", height: "1" }, filters());
      f.innerHTML = '<feFlood x="' + half + '" y="' + half + '" height="1" width="1"/>' +
        '<feComposite width="' + block + '" height="' + block + '"/><feTile result="dots"/>' +
        '<feComposite in="SourceGraphic" in2="dots" operator="in"/><feMorphology operator="dilate" radius="' + half + '"/>';
    }
    return "url(#" + id + ")";
  }

  function build(id, w) {
    filters();
    const svg = svgEl("svg", { viewBox: "0 0 200 290", width: w, height: w * 1.45, class: "fr", overflow: "visible" });
    const u = "fr-" + id;
    svgEl("defs", {}, svg).innerHTML =
      // counter-shading across him (back on the left, belly on the right: he faces right), a soft key light on
      // top, a scale net (arcs opening toward the tail, staggered rows), fins from orange roots to deep tips
      '<linearGradient id="' + u + '-b" x1="0" y1="0" x2="1" y2="0.15"><stop offset="0" stop-color="' + BACK + '"/><stop offset=".42" stop-color="' + OLIVE + '"/><stop offset=".78" stop-color="' + GOLD + '"/><stop offset="1" stop-color="#f6d98e"/></linearGradient>' +
      '<radialGradient id="' + u + '-k" cx="40%" cy="22%" r="55%"><stop offset="0" stop-color="#fff6c8" stop-opacity=".55"/><stop offset="1" stop-color="#fff6c8" stop-opacity="0"/></radialGradient>' +
      '<pattern id="' + u + '-sc" width="18" height="13" patternUnits="userSpaceOnUse"><path d="M0 0 Q 9 13 18 0 M-9 6.5 Q 0 19.5 9 6.5 M9 6.5 Q 18 19.5 27 6.5" fill="none" stroke="#3d3a17" stroke-width="2" stroke-opacity=".34"/></pattern>' +
      '<linearGradient id="' + u + '-f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffb04a"/><stop offset=".55" stop-color="' + FINC + '"/><stop offset="1" stop-color="' + DEEP + '"/></linearGradient>' +
      '<linearGradient id="' + u + '-s" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e9edf2"/><stop offset=".5" stop-color="#9aa4b1"/><stop offset="1" stop-color="#5d6672"/></linearGradient>';
    const all = group(svg, "fr-all");
    const R = { svg: svg, id: id, w: w };
    // tail (his feet), and its steel version
    const TAIL = "M100 220 C 90 244, 64 262, 42 289 C 70 286, 90 278, 100 262 C 110 278, 130 286, 158 289 C 136 262, 110 244, 100 220 Z";
    R.tail = group(all, "fr-tail");
    svgEl("path", { d: TAIL, fill: "url(#" + u + "-f)", stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" }, R.tail);
    svgEl("path", { d: "M100 236 L62 280 M100 240 L80 280 M100 240 L120 280 M100 236 L138 280", stroke: DEEP, "stroke-width": 2, opacity: 0.6 }, R.tail);
    R.steelTail = group(all, "fr-steel");
    svgEl("path", { d: TAIL, fill: "url(#" + u + "-s)", stroke: INK, "stroke-width": 4 }, R.steelTail);
    [[100, 250], [80, 272], [120, 272]].forEach(function (p) { svgEl("circle", { cx: p[0], cy: p[1], r: 3.5, fill: "#3b4250" }, R.steelTail); });
    R.torso = group(all, "fr-torso");
    // back fin (behind the body), with an oar for the boat
    R.finB = group(R.torso, "fr-finb");
    R.oarB = group(R.finB, "fr-oar");
    svgEl("line", { x1: 40, y1: 215, x2: 10, y2: 285, stroke: "#8a5a33", "stroke-width": 6, "stroke-linecap": "round" }, R.oarB);
    svgEl("ellipse", { cx: 8, cy: 284, rx: 9, ry: 16, fill: "#a8703e", stroke: INK, "stroke-width": 3 }, R.oarB);
    svgEl("path", { d: "M64 150 C 40 165, 30 195, 38 222 C 52 205, 62 185, 70 165 Z", fill: "url(#" + u + "-f)", stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" }, R.finB);
    svgEl("path", { d: "M64 82 C 34 74, 22 120, 26 176 C 34 150, 42 128, 52 112 Z", fill: DORSAL, stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" }, R.torso);
    svgEl("path", { d: "M58 90 L32 110 M52 104 L30 134 M48 120 L28 156", stroke: "#7a5a24", "stroke-width": 2, opacity: 0.6 }, R.torso);
    svgEl("ellipse", { cx: 100, cy: 148, rx: 56, ry: 88, fill: "url(#" + u + "-b)" }, R.torso);
    // scales below the gill line only (the head is smooth), then the light, then the outline on top
    svgEl("clipPath", { id: u + "-cl" }, svg.querySelector("defs")).innerHTML = '<path d="M30 40 L96 40 C 88 92, 100 138, 150 152 L170 250 L30 250 Z"/>';
    svgEl("ellipse", { cx: 100, cy: 148, rx: 54, ry: 86, fill: "url(#" + u + "-sc)", "clip-path": "url(#" + u + "-cl)" }, R.torso);
    svgEl("ellipse", { cx: 100, cy: 148, rx: 56, ry: 88, fill: "url(#" + u + "-k)" }, R.torso);
    svgEl("path", { d: "M99 68 C 92 100, 104 138, 148 152", fill: "none", stroke: "#4a4520", "stroke-width": 3.5, "stroke-linecap": "round", opacity: 0.75 }, R.torso);
    svgEl("ellipse", { cx: 100, cy: 148, rx: 56, ry: 88, fill: "none", stroke: INK, "stroke-width": 4 }, R.torso);
    // head: eye, lid, mouth, cheek, and the accessories
    R.head = group(R.torso, "fr-head");
    svgEl("circle", { cx: 122, cy: 98, r: 21, fill: "#fff", stroke: INK, "stroke-width": 3.5 }, R.head);
    R.iris = svgEl("circle", { cx: 128, cy: 100, r: 13, fill: IRIS, stroke: "#9a7420", "stroke-width": 1.5 }, R.head);
    R.pupil = svgEl("circle", { cx: 128, cy: 100, r: 8.5, fill: INK }, R.head);
    svgEl("circle", { cx: 124, cy: 94, r: 4, fill: "#fff" }, R.head);
    R.lid = svgEl("path", { d: "M100 98 A 22 22 0 0 1 144 98 Z", fill: OLIVE, stroke: INK, "stroke-width": 3 }, R.head);
    R.barbels = group(R.head, "fr-barbels");
    svgEl("path", { d: "M140 136 C 139 142, 136 146, 132 148 M149 137 C 150 143, 148 148, 145 151", fill: "none", stroke: INK, "stroke-width": 5, "stroke-linecap": "round" }, R.barbels);
    svgEl("path", { d: "M140 136 C 139 142, 136 146, 132 148 M149 137 C 150 143, 148 148, 145 151", fill: "none", stroke: LIP, "stroke-width": 2.5, "stroke-linecap": "round" }, R.barbels);
    svgEl("path", { d: "M137 129 C 147 124, 158 126, 160 131 C 158 137, 147 139, 137 135 Z", fill: LIP, stroke: INK, "stroke-width": 2.5, "stroke-linejoin": "round" }, R.head);
    R.mouth = svgEl("path", { d: "M139 132 Q 149 136 159 131", fill: "none", stroke: INK, "stroke-width": 3, "stroke-linecap": "round" }, R.head);
    svgEl("ellipse", { cx: 136, cy: 120, rx: 7, ry: 4, fill: "#ff8a6a", opacity: 0.45 }, R.head);
    R.acc = {};
    let a = R.acc.top_hat = group(R.head, "fr-acc");
    a.innerHTML = '<g transform="rotate(-10 100 60)"><rect x="74" y="12" width="52" height="46" rx="4" fill="' + INK + '"/><rect x="74" y="42" width="52" height="9" fill="#d6283c"/>' +
      '<ellipse cx="100" cy="60" rx="44" ry="8" fill="' + INK + '"/><rect x="80" y="16" width="5" height="26" fill="#5a5868"/></g>';
    a = R.acc.crown = group(R.head, "fr-acc");
    a.innerHTML = '<path d="M72 62 L72 30 L86 46 L100 24 L114 46 L128 30 L128 62 Z" fill="#f8c62a" stroke="' + INK + '" stroke-width="3"/><circle cx="100" cy="52" r="5" fill="#d6283c"/>';
    a = R.acc.moustache = group(R.head, "fr-acc");
    a.innerHTML = '<path d="M147 124 C 140 116, 126 118, 124 128 C 120 122, 112 124, 114 132 C 124 128, 134 134, 147 128 C 160 134, 170 128, 180 132 C 182 124, 174 122, 170 128 C 168 118, 154 116, 147 124 Z" fill="' + INK + '"/>';
    a = R.acc.sunglasses = group(R.head, "fr-acc");
    a.innerHTML = '<rect x="98" y="86" width="50" height="24" rx="11" fill="' + INK + '"/><rect x="104" y="90" width="12" height="5" rx="2" fill="#fff" opacity=".7"/><line x1="98" y1="94" x2="72" y2="90" stroke="' + INK + '" stroke-width="4"/>';
    a = R.acc.bow_tie = group(R.torso, "fr-acc");
    a.innerHTML = '<path d="M122 196 L100 184 L100 208 Z M122 196 L144 184 L144 208 Z" fill="#d6283c" stroke="' + INK + '" stroke-width="3"/><circle cx="122" cy="196" r="6" fill="#9c1426"/>';
    // front fin (his arm) with what it can hold; its steel version
    R.finF = group(R.torso, "fr-finf");
    const FIN = "M142 152 C 166 160, 178 186, 172 214 C 160 200, 148 184, 136 166 Z";
    svgEl("path", { d: FIN, fill: "url(#" + u + "-f)", stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" }, R.finF);
    R.steelFin = group(R.finF, "fr-steel");
    svgEl("path", { d: FIN, fill: "url(#" + u + "-s)", stroke: INK, "stroke-width": 4, "stroke-linejoin": "round" }, R.steelFin);
    [[150, 168], [163, 190]].forEach(function (p) { svgEl("circle", { cx: p[0], cy: p[1], r: 3.5, fill: "#3b4250" }, R.steelFin); });
    R.hold = {};
    let it = R.hold.pencil = group(R.finF, "fr-item");
    it.innerHTML = '<g transform="rotate(25 172 212)"><rect x="168" y="196" width="9" height="44" fill="#f8c62a" stroke="' + INK + '" stroke-width="2"/><path d="M168 240 L172.5 252 L177 240 Z" fill="#f3d2a2" stroke="' + INK + '" stroke-width="2"/><rect x="168" y="190" width="9" height="7" fill="#ff8fa3"/></g>';
    it = R.hold.phone = group(R.finF, "fr-item");
    it.innerHTML = '<rect x="160" y="192" width="26" height="44" rx="5" fill="' + INK + '"/><rect x="163" y="197" width="20" height="32" rx="2" fill="#5ab4ff"/><circle cx="173" cy="232" r="2" fill="#666"/>';
    R.screen = it.querySelector("rect:nth-child(2)");
    it = R.hold.hammer = group(R.finF, "fr-item");
    it.innerHTML = '<rect x="168" y="186" width="7" height="58" rx="3" fill="#a8703e" stroke="' + INK + '" stroke-width="2"/><rect x="156" y="236" width="32" height="16" rx="3" fill="#6b7280" stroke="' + INK + '" stroke-width="2"/>';
    R.oarF = group(R.finF, "fr-oar");
    svgEl("line", { x1: 168, y1: 210, x2: 196, y2: 284, stroke: "#8a5a33", "stroke-width": 6, "stroke-linecap": "round" }, R.oarF);
    svgEl("ellipse", { cx: 198, cy: 284, rx: 9, ry: 16, fill: "#a8703e", stroke: INK, "stroke-width": 3 }, R.oarF);
    // things in front of him: a book, a notepad, the blocks he builds, his boat
    R.boat = group(all, "fr-boat");
    R.boat.innerHTML = '<path d="M22 232 L178 232 L162 278 Q100 292 38 278 Z" fill="#a8703e" stroke="' + INK + '" stroke-width="4" stroke-linejoin="round"/>' +
      '<path d="M26 242 L174 242" stroke="#7a4e2a" stroke-width="4"/><path d="M34 258 L166 258" stroke="#7a4e2a" stroke-width="3" opacity=".7"/>' +
      '<text x="100" y="274" text-anchor="middle" font-family="sans-serif" font-weight="800" font-size="15" fill="#ffe3b8">S.S. FRED</text>';
    R.hold.book = group(all, "fr-item");
    R.hold.book.innerHTML = '<path d="M104 170 L140 162 L140 210 L104 218 Z" fill="#fff" stroke="' + INK + '" stroke-width="3"/><path d="M140 162 L176 170 L176 218 L140 210 Z" fill="#f4f1ea" stroke="' + INK + '" stroke-width="3"/>' +
      '<path d="M110 180 L134 175 M110 190 L134 185 M110 200 L130 196 M146 175 L170 180 M146 185 L170 190" stroke="#9aa3b5" stroke-width="2.5"/><path d="M100 214 L140 206 L180 214 L180 222 L140 214 L100 222 Z" fill="#3a6fc8" stroke="' + INK + '" stroke-width="3"/>';
    R.page = R.hold.book.querySelector("path:nth-child(2)");
    R.hold.pad = group(all, "fr-item");
    R.hold.pad.innerHTML = '<rect x="104" y="176" width="44" height="52" rx="3" fill="#fffbe6" stroke="' + INK + '" stroke-width="3" transform="rotate(-8 126 202)"/>';
    R.scribble = svgEl("path", { d: "M112 192 q6 -6 12 0 t12 0 M112 204 q6 -6 12 0 t10 0 M112 216 q5 -5 10 0", fill: "none", stroke: "#3a6fc8", "stroke-width": 3, "stroke-linecap": "round", transform: "rotate(-8 126 202)" }, R.hold.pad);
    R.blocks = [0, 1, 2].map(function (k) {
      const b = svgEl("rect", { x: 152 + (k === 2 ? 12 : k * 24), y: k === 2 ? 236 : 262, width: 22, height: 24, rx: 2, fill: ["#3a6fc8", "#5d9b3a", "#f8c62a"][k], stroke: INK, "stroke-width": 3 }, all);
      return b;
    });
    R.finFs = wrap(R.finF, "fr-sway");
    R.finBs = wrap(R.finB, "fr-sway");
    gsap.set([R.steelTail, R.steelFin, R.boat, R.oarB, R.oarF, R.blocks].flat(), { autoAlpha: 0 });
    Object.keys(R.acc).forEach(function (k) { gsap.set(R.acc[k], { autoAlpha: 0 }); });
    Object.keys(R.hold).forEach(function (k) { gsap.set(R.hold[k], { autoAlpha: 0 }); });
    gsap.set(R.lid, { scaleY: 0, svgOrigin: "122 76" });
    return R;
  }

  const POSE = {  // front fin / back fin rotation (degrees) for each activity
    rest: [0, 0], book: [-48, 22], pencil: [-38, 26], phone: [-118, 0], hammer: [-40, 0], boat: [-10, 10],
  };
  function pose(tl, R, name, t, d) {
    const p = POSE[name] || POSE.rest;
    tl.to(R.finF, { rotation: p[0], svgOrigin: PIV_F, duration: d || 0.3, ease: "back.out(1.6)" }, t);
    tl.to(R.finB, { rotation: p[1], svgOrigin: PIV_B, duration: d || 0.3, ease: "back.out(1.6)" }, t);
  }
  const ITEM = 1.45;
  function loops(n, per) { return Math.max(0, Math.floor(n / per) - 1); }

  // An activity from t to t1: its item appears, the fins take the pose, and it loops.
  function activity(tl, R, what, t, t1) {
    const d = Math.max(0.4, t1 - t);
    if (what === "none") return;
    const items = { book: [R.hold.book], pencil: [R.hold.pencil, R.hold.pad], phone: [R.hold.phone], hammer: [R.hold.hammer] }[what] || [];
    // items drawn at fin scale were unreadable on a phone (lab v05): they show 1.45x, about their centre
    tl.fromTo(items, { autoAlpha: 0, scale: 0.5, transformOrigin: "50% 50%" }, { autoAlpha: 1, scale: ITEM, duration: 0.25, ease: "back.out(2.5)", immediateRender: false }, t);
    pose(tl, R, what, t);
    const t2 = t + 0.35, span = t1 - t2 - 0.3;
    if (span > 0.2) {
      if (what === "book") {
        tl.fromTo(R.page, { scaleX: 1, svgOrigin: "140 190" }, { scaleX: -1, duration: 0.4, ease: "power1.inOut", repeat: loops(span, 1.6), repeatDelay: 1.2, immediateRender: false }, t2 + 0.6);
        tl.to([R.iris, R.pupil], { attr: { cy: 106, cx: 126 }, duration: 0.2 }, t2);
      }
      if (what === "pencil") {
        tl.fromTo(R.finF, { rotation: -38 }, { rotation: -30, svgOrigin: PIV_F, duration: 0.09, yoyo: true, repeat: loops(span, 0.09), ease: "sine.inOut", immediateRender: false }, t2);
        tl.fromTo(R.scribble, { strokeDasharray: 200, strokeDashoffset: 200 }, { strokeDashoffset: 0, duration: span, ease: "none", immediateRender: false }, t2);
      }
      if (what === "phone") {
        tl.fromTo(R.finF, { rotation: -118 }, { rotation: -112, svgOrigin: PIV_F, duration: 0.12, yoyo: true, repeat: loops(span, 0.12), ease: "none", immediateRender: false }, t2);
        tl.fromTo(R.screen, { fill: "#5ab4ff" }, { fill: "#ffd166", duration: 0.5, yoyo: true, repeat: loops(span, 0.5), ease: "none", immediateRender: false }, t2);
        tl.to([R.iris, R.pupil], { attr: { cy: 104, cx: 132 }, duration: 0.2 }, t2);
      }
      if (what === "hammer") {
        const n = Math.max(1, Math.floor(span / 0.5));
        for (let k = 0; k < n; k++) {
          tl.to(R.finF, { rotation: -135, svgOrigin: PIV_F, duration: 0.2, ease: "power2.out" }, t2 + k * 0.5);
          tl.to(R.finF, { rotation: -30, svgOrigin: PIV_F, duration: 0.12, ease: "power3.in" }, t2 + k * 0.5 + 0.22);
          if (k < R.blocks.length) tl.fromTo(R.blocks[k], { autoAlpha: 1, scale: 0, transformOrigin: "50% 100%" }, { autoAlpha: 1, scale: 1, duration: 0.2, ease: "back.out(3)", immediateRender: false }, t2 + k * 0.5 + 0.34);
        }
      }
    }
    tl.to(items, { autoAlpha: 0, scale: 0.4, duration: 0.2, ease: "power2.in" }, t1 - 0.2);
    look(tl, R, "camera", t1 - 0.2);
    pose(tl, R, "rest", t1 - 0.15, 0.25);
  }

  function act(tl, R, what, t) {
    if (what === "wave") {
      // side on, a raised near fin lies across his face (it read as a beak, lab v03): he waves with the far fin,
      // up behind his head where it breaks the silhouette, as pixel Fred does
      tl.to(R.finB, { rotation: 150, svgOrigin: PIV_B, duration: 0.25, ease: "back.out(2)" }, t);
      tl.to(R.finB, { rotation: 118, svgOrigin: PIV_B, duration: 0.15, yoyo: true, repeat: 5, ease: "sine.inOut" }, t + 0.25);
      tl.to(R.finB, { rotation: 0, svgOrigin: PIV_B, duration: 0.3, ease: "power2.inOut" }, t + 1.2);
    }
    if (what === "clap") {  // fins over his head, together: the alchemist's clap (wind down first: anticipation)
      tl.to(R.finF, { rotation: 28, svgOrigin: PIV_F, duration: 0.14, ease: "power2.out" }, t - 0.16);
      tl.to(R.finB, { rotation: -28, svgOrigin: PIV_B, duration: 0.14, ease: "power2.out" }, t - 0.16);
      tl.to(R.torso, { scaleY: 0.9, svgOrigin: ORIGIN, duration: 0.14, ease: "power2.out" }, t - 0.16);
      tl.to(R.finF, { rotation: -172, svgOrigin: PIV_F, duration: 0.14, ease: "power3.in" }, t);
      tl.to(R.finB, { rotation: 176, svgOrigin: PIV_B, duration: 0.14, ease: "power3.in" }, t);
      tl.to(R.torso, { scaleY: 1.1, svgOrigin: ORIGIN, duration: 0.14, ease: "power3.in" }, t);
      tl.to(R.torso, { scaleY: 1, svgOrigin: ORIGIN, duration: 0.45, ease: "elastic.out(1, 0.4)" }, t + 0.14);
      look(tl, R, "up", t);
      look(tl, R, "camera", t + 1.2);
      tl.to(R.finF, { rotation: 0, svgOrigin: PIV_F, duration: 0.35, ease: "power2.inOut" }, t + 1.0);
      tl.to(R.finB, { rotation: 0, svgOrigin: PIV_B, duration: 0.35, ease: "power2.inOut" }, t + 1.0);
    }
    if (what === "dance") {
      tl.fromTo(R.torso, { rotation: -10 }, { rotation: 10, svgOrigin: ORIGIN, duration: 0.25, yoyo: true, repeat: 5, ease: "sine.inOut", immediateRender: false }, t);
      tl.fromTo(R.finF, { rotation: -140 }, { rotation: -20, svgOrigin: PIV_F, duration: 0.25, yoyo: true, repeat: 5, ease: "sine.inOut", immediateRender: false }, t);
      tl.to([R.torso, R.finF], { rotation: 0, duration: 0.2 }, t + 1.55);
    }
    if (what === "blink") tl.fromTo(R.lid, { scaleY: 0 }, { scaleY: 1, duration: 0.06, yoyo: true, repeat: 1, svgOrigin: "122 76", immediateRender: false }, t);
  }

  function setStyle(tl, R, style, t, cells) {
    // pixel and 3D Fred are frames (create/pixel/fred.py, create/render3d/fred3d.py) that hide this drawing; the
    // filter still matters where the drawing stands in for them (in a boat, in a cat's mouth)
    const f = style === "toon3d" ? "url(#fr-clay)" : style === "pixel" ? pixelFilter(Math.max(4, Math.round(R.w / cells))) :
      "drop-shadow(0 8px 10px rgba(0,0,0,.35))";
    tl.set(R.svg, { filter: f }, t);
  }

  function accessory(tl, R, name, on, t, animate) {
    if (name === "automail") {  // a steel fin and tail: a flash, then metal
      tl.set([R.steelFin, R.steelTail], { autoAlpha: on ? 1 : 0 }, t);
      // a flash on the layer above the drawing: the drawing's own filter is its style (v02: it was lost)
      const host = R.svg.parentNode || R.svg;
      if (on && animate) tl.fromTo(host, { filter: "brightness(1.7)" }, { filter: "brightness(1)", duration: 0.28, ease: "power2.out", immediateRender: false }, t);
      return;
    }
    const g = R.acc[name];
    if (!g) return;
    if (!on) { tl.to(g, { autoAlpha: 0, duration: 0.2 }, t); return; }
    if (!animate) { tl.set(g, { autoAlpha: 1 }, t); return; }
    if (name === "top_hat" || name === "crown") {
      tl.fromTo(g, { autoAlpha: 1, y: -220, rotation: -20, svgOrigin: "100 60" }, { autoAlpha: 1, y: 0, rotation: 0, duration: 0.55, ease: "bounce.out", immediateRender: false }, t);
      // follow-through: he squashes as it lands, and blinks
      tl.to(R.torso, { scaleY: 0.88, scaleX: 1.06, svgOrigin: ORIGIN, duration: 0.06, ease: "power2.out" }, t + 0.2);
      tl.to(R.torso, { scaleY: 1, scaleX: 1, svgOrigin: ORIGIN, duration: 0.4, ease: "elastic.out(1, 0.4)" }, t + 0.26);
      act(tl, R, "blink", t + 0.2);
      look(tl, R, "up", t);  // he looks up at what lands on his head, then back at us
      look(tl, R, "camera", t + 0.9);
    }
    else tl.fromTo(g, { autoAlpha: 1, scale: 0, transformOrigin: "50% 50%" }, { autoAlpha: 1, scale: 1, duration: 0.35, ease: "back.out(3)", immediateRender: false }, t);
  }

  // His whole performance from the prop track.
  function play(R, P, tl, cells, shadow) {
    // styles: photo is the picture (an <img> the caller shows), the rest are this drawing with a filter
    P.styles.forEach(function (s) { if (s.style !== "photo") setStyle(tl, R, s.style, s.t, cells); });
    P.acc.forEach(function (a) {
      a.add.forEach(function (n) { accessory(tl, R, n, true, a.t, a.t > P.t0 + 0.05); });
      a.remove.forEach(function (n) { accessory(tl, R, n, false, a.t, true); });
    });
    // breathing and blinking for his whole stay
    const life = Math.max(0.6, P.t1 - P.t0);
    // breathing lives on the <svg> (its own layer): a later squash on the torso never freezes it
    gsap.set(R.svg, { transformOrigin: "50% 100%" });
    tl.fromTo(R.svg, { scaleY: 1 }, { scaleY: 1.025, duration: 0.8, yoyo: true, repeat: loops(life, 0.8), ease: "sine.inOut", immediateRender: false }, P.t0);
    // overlapping action: the fins drift on their own, out of phase with each other and the breath
    tl.fromTo(R.finFs, { rotation: -5 }, { rotation: 5, svgOrigin: PIV_F, duration: 0.95, yoyo: true, repeat: loops(life, 0.95), ease: "sine.inOut", immediateRender: false }, P.t0);
    tl.fromTo(R.finBs, { rotation: 6 }, { rotation: -4, svgOrigin: PIV_B, duration: 1.15, yoyo: true, repeat: loops(life, 1.15), ease: "sine.inOut", immediateRender: false }, P.t0 + 0.3);
    // blinks at irregular intervals (a metronome blink reads as a machine)
    const gaps = [1.6, 2.9, 2.2, 3.6, 1.9, 3.1, 2.5];
    for (let t = P.t0 + 1.1, k = 0; t < P.t1 - 0.3; t += gaps[k++ % gaps.length]) act(tl, R, "blink", t);
    // acting: he looks at us; up at the presenter only briefly, when named (a pupil parked at the top of a big
    // eye read as eye-rolling, lab v05)
    gsap.set([R.iris, R.pupil], { attr: LOOK.camera });
    P.tags.forEach(function (g) { if (g.kind === "tag") { look(tl, R, "up", g.t + 0.5); look(tl, R, "camera", g.t + 1.3); } });
    // rides: the boat appears around him with oars in his fins
    let riding = false;
    P.rides.forEach(function (r) {
      riding = r.ride === "boat";
      if (shadow) tl.to(shadow, { autoAlpha: riding ? 0 : 1, duration: 0.3 }, r.t);  // in the air: no contact
      tl.to([R.boat, R.oarB, R.oarF], { autoAlpha: riding ? 1 : 0, duration: 0.2 }, r.t);
      if (riding) tl.fromTo(R.boat, { scale: 0.3, svgOrigin: "100 260" }, { scale: 1, duration: 0.35, ease: "back.out(2.5)", immediateRender: false }, r.t);
      pose(tl, R, riding ? "boat" : "rest", r.t);
    });
    // moves: hop on his tail, or row (and bob) in the boat
    P.moves.forEach(function (m) {
      if (!m.d || !m.gait) return;
      if (m.gait === "hop") {
        // each hop an arc (up: ease out, down: ease in); a crouch before the first (anticipation), a stretch
        // on take-off and a squash on landing; the shadow shrinks while he is up
        const n = Math.max(1, Math.round(m.d / 0.36)), hp = m.d / n, H = R.w * 0.24;
        tl.to(R.torso, { scaleY: 0.84, scaleX: 1.08, svgOrigin: ORIGIN, duration: 0.1, ease: "power2.out" }, Math.max(P.t0, m.t - 0.1));
        for (let k = 0; k < n; k++) {
          const tk = m.t + k * hp;
          tl.to(R.torso, { scaleY: 1.12, scaleX: 0.93, svgOrigin: ORIGIN, duration: hp * 0.2, ease: "power2.out" }, tk);
          tl.to(R.svg, { y: -H, duration: hp * 0.45, ease: "power2.out" }, tk);
          tl.to(R.torso, { scaleY: 1, scaleX: 1, svgOrigin: ORIGIN, duration: hp * 0.25, ease: "sine.inOut" }, tk + hp * 0.2);
          tl.to(R.svg, { y: 0, duration: hp * 0.45, ease: "power2.in" }, tk + hp * 0.45);
          tl.to(R.torso, { scaleY: 0.86, scaleX: 1.07, svgOrigin: ORIGIN, duration: hp * 0.1, ease: "power2.out" }, tk + hp * 0.9);
          if (shadow) tl.to(shadow, { scale: 0.62, opacity: 0.55, duration: hp * 0.45, ease: "power2.out", yoyo: true, repeat: 1 }, tk);
        }
        tl.to(R.torso, { scaleY: 1, scaleX: 1, svgOrigin: ORIGIN, duration: 0.35, ease: "elastic.out(1, 0.45)" }, m.t + m.d);
      } else if (m.gait === "boat") {
        tl.fromTo(R.finF, { rotation: -40 }, { rotation: 25, svgOrigin: PIV_F, duration: 0.3, yoyo: true, repeat: loops(m.d, 0.3), ease: "sine.inOut", immediateRender: false }, m.t);
        tl.fromTo(R.finB, { rotation: 40 }, { rotation: -20, svgOrigin: PIV_B, duration: 0.3, yoyo: true, repeat: loops(m.d, 0.3), ease: "sine.inOut", immediateRender: false }, m.t);
        tl.fromTo(R.svg, { rotation: -5 }, { rotation: 5, duration: 0.45, yoyo: true, repeat: loops(m.d, 0.45), ease: "sine.inOut", immediateRender: false }, m.t);
        tl.set(R.svg, { rotation: 0 }, m.t + m.d);
        pose(tl, R, "boat", m.t + m.d, 0.2);
      }
    });
    // activities, each until the next hold (or his exit)
    P.holds.forEach(function (h, k) {
      const end = k + 1 < P.holds.length ? P.holds[k + 1].t : P.exit.t;
      activity(tl, R, h.hold, h.t, end);
    });
    P.acts.forEach(function (a) { act(tl, R, a.do, a.t); });
  }

  window.FRED = { build: build, play: play, setStyle: setStyle, accessory: accessory, act: act };
})();
