/* Props and effects for presenter reels (create/kit, ADR 0027), drawn from the data create/footage/props.py
   computes: characters in the room (Fred the fish, Pixie the cat) and effects on the presenter (anime,
   blocky, grade, shake, flash, glitch, caption font, fade to black).

   Props live in two room layers inside the presenter's zoom (#room in front, #room-back behind the matte
   cut-out), sized as the take's master and mapped to the frame per edit segment, so a prop stays put on
   the couch through push-ins, punch-ins, layout moves and jump cuts. Every change is a timeline tween or
   set at a time Python gave (seek-safe: the renderer seeks frame by frame). */
(function () {
  const FILES = "assets/props/";

  function el(tag, cls, parent) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (parent) parent.appendChild(e);
    return e;
  }
  function img(src, cls, parent) {
    const i = el("img", cls, parent); i.src = FILES + src; i.draggable = false; return i;
  }

  // Rooms: one transform per edit segment (master pixels -> frame pixels).
  function rooms(D, tl) {
    const layers = ["#room", "#room-back"].filter(function (s) { return document.querySelector(s); });
    D.rooms.forEach(function (r) {
      tl.set(layers, { x: r.tx, y: r.ty, scale: r.k, width: r.mw, height: r.mh, transformOrigin: "0 0" }, r.t0);
    });
  }

  // Accessories sit on the prop's points: hats and crowns on the head, glasses and moustaches on the face,
  // bow ties on the neck. Sizes are shares of the prop's width.
  const ACC_AT = { top_hat: "head", crown: "head", moustache: "face", sunglasses: "face", bow_tie: "neck" };
  function accessory(name, P, pixel, box, w, h, pts) {
    const a = P.acc[name];
    if (!a) return null;  // an expression: drawn into pixel Fred's own frames, nothing to overlay
    const aw = a.width * w, ah = aw * (pixel ? a.pixel_aspect : a.aspect);
    const pt = pts[ACC_AT[name]] || [0.5, 0.3];
    const i = img(pixel ? a.pixel : a.smooth, "pp-acc" + (pixel ? " px" : ""), box);
    const onHead = ACC_AT[name] === "head";
    Object.assign(i.style, { width: aw + "px", height: ah + "px", left: (pt[0] * w - aw / 2) + "px",
      top: (pt[1] * h - (onHead ? ah * 0.88 : ah / 2)) + "px" });
    return i;
  }

  function sparkles(parent, n, size) {
    const out = [];
    for (let k = 0; k < n; k++) {
      const s = el("div", "pp-spark", parent);
      s.style.width = s.style.height = size + "px";
      out.push(s);
    }
    return out;
  }
  // A cartoon puff of smoke: soft circles that swell and fade around the prop (covers a swap or an arrival).
  function cloud(parent, w, h) {
    // puffs ring the middle of the body (v02: they sat above the head and never covered the swap); smaller
    // and fewer than v03's eight big ones, which hid him for 0.4 s and read as a cotton ball
    const out = [];
    for (let k = 0; k < 7; k++) {
      const c = el("div", "pp-puff", parent);
      const a = (k / 7) * Math.PI * 2 + 0.3;
      const size = w * (0.17 + 0.04 * (k % 3));  // a bigger Fred made bigger puffs a cotton ball again (r05, r06)
      const rx = w * 0.26, ry = h * 0.24;
      Object.assign(c.style, { width: size + "px", height: size + "px",
        left: (w / 2 + Math.cos(a) * rx - size / 2) + "px", top: (h * 0.52 + Math.sin(a) * ry - size / 2) + "px" });
      gsap.set(c, { autoAlpha: 0 });
      c.dx = Math.cos(a) * w * 0.35; c.dy = Math.sin(a) * h * 0.25 - h * 0.08;  // out, and drifting up
      out.push(c);
    }
    return out;
  }
  function poof(tl, puffs, t, w) {
    // a cartoon poof: the puffs pop in fast (0.07 s, the swap happens under them), then burst outward,
    // shrinking and fading (0.3 s), so the new look is seen within about 4 frames
    puffs.forEach(function (c, k) {
      const t0 = t - 0.05 + 0.008 * k;
      tl.fromTo(c, { autoAlpha: 0, scale: 0.4, x: 0, y: 0 }, { autoAlpha: 0.8, scale: 1, x: 0, y: 0, duration: 0.07, ease: "power2.out", immediateRender: false }, t0);
      tl.to(c, { autoAlpha: 0, scale: 0.55, x: c.dx, y: c.dy, duration: 0.3, ease: "power2.out" }, t0 + 0.09);
    });
  }
  function burst(tl, sp, t, r) {
    sp.forEach(function (s, k) {
      const a = (k / sp.length) * Math.PI * 2 + 0.4;
      tl.fromTo(s, { x: 0, y: 0, scale: 0.2, opacity: 1, rotation: 0 },
        { x: Math.cos(a) * r, y: Math.sin(a) * r, scale: 1, opacity: 0, rotation: 90, duration: 0.5, ease: "power2.out", immediateRender: false }, t);
    });
  }

  function prop(P, D, tl) {
    const layer = document.getElementById(P.behind ? "room-back" : "room");
    const w = P.w, h = P.h;
    const root = el("div", "pp", layer); root.id = "prop-" + P.id;
    Object.assign(root.style, { width: w + "px", height: h + "px" });
    // a soft contact shadow on the surface under it: it stays on the ground, shrinks and fades as the prop
    // leaves it (jumps, hops, the boat), and is what makes a drawn prop sit on a real lap
    const shadow = el("div", "pp-shadow", root);
    P.shadowEl = shadow;
    const act = el("div", "pp-act", root);
    const idle = el("div", "pp-idle", act);
    const body = el("div", "pp-body", idle);
    // one image per style / frame, shown one at a time
    const imgs = {};
    Object.keys(P.files).forEach(function (k) {
      const i = img(P.files[k], "pp-img" + (P.pixel || k === "pixel" || P.files[k].indexOf("-px-") >= 0 ? " px" : ""), body);
      imgs[k] = i;
    });
    let R = null;  // fred: the rigged drawing (create/kit/fred.js); his photo style stays an image
    if (P.rig) { R = FRED.build(P.id, w); R.svg.classList.add("pp-rig"); body.appendChild(R.svg); imgs.rig = R.svg; }
    const base = function (style) {
      if (P.rig) return style === "photo" ? "photo" : "rig";
      return P.files[style] ? style : (P.files.stand ? "stand" : "photo");
    };
    const all = Object.keys(imgs).map(function (k) { return imgs[k]; });
    tl.set(root, { autoAlpha: 0 }, 0);
    gsap.set(all, { display: "none" });
    gsap.set(root, { left: P.moves[0].x, top: P.moves[0].y, xPercent: -50, yPercent: -100 });
    let facing = P.flip ? -1 : 1;
    gsap.set(body, { scaleX: facing });
    let shown = null;
    function show(k, t) {
      if (shown === k) return;
      if (shown) tl.set(imgs[shown], { display: "none" }, t);
      tl.set(imgs[k], { display: "block" }, t);
      shown = k;
    }
    // styles (a poof of sparkles on each change after the first)
    const sp = sparkles(act, 8, Math.max(10, w * 0.06));
    const puffs = cloud(root, w, h);
    let styleNow = base(P.styles[0].style);
    if (!P.sched) show(styleNow, P.t0);
    P.styles.slice(1).forEach(function (s) {
      styleNow = base(s.style);
      // a transformation: squash (anticipation), a puff of smoke that hides the swap, a stretch as the new look
      // appears, then an elastic settle
      tl.to(act, { scaleY: 0.82, scaleX: 1.12, duration: 0.1, ease: "power2.out" }, s.t - 0.12);
      tl.to(act, { scaleY: 1.16, scaleX: 0.9, duration: 0.08, ease: "power2.in" }, s.t - 0.02);
      tl.to(act, { scaleY: 1, scaleX: 1, duration: 0.5, ease: "elastic.out(1, 0.45)" }, s.t + 0.06);
      poof(tl, puffs, s.t - 0.06, w);
      burst(tl, sp, s.t, w * 0.7);
      if (!P.sched) show(styleNow, s.t);
    });
    // sprite props (the kitten, pixel Fred): Python scheduled every frame (create/footage/props.py)
    if (P.sched) P.sched.forEach(function (e) { if (imgs[e[1]]) show(e[1], e[0]); });
    // accessories: two versions each (smooth and pixel), the one matching the style at that time
    const accEls = {};
    const pixelAt = function (t) {
      let st = P.styles[0].style;
      P.styles.forEach(function (s) { if (s.t <= t) st = s.style; });
      return P.pixel || st === "pixel";
    };
    const on = {};
    function accEl(name, px) {
      const key = name + (px ? "-px" : "");
      if (!accEls[key]) { accEls[key] = accessory(name, D.props_kit, px, body, w, h, P.points) || el("div", "pp-acc", body); gsap.set(accEls[key], { autoAlpha: 0 }); }
      return accEls[key];
    }
    if (!P.rig) P.acc.forEach(function (a) {
      a.add.forEach(function (name) {
        const e = accEl(name, pixelAt(a.t));
        on[name] = true;
        if (ACC_AT[name] === "head" && a.t > P.t0 + 0.05) {
          tl.fromTo(e, { autoAlpha: 1, y: -h * 1.4, rotation: -12 }, { autoAlpha: 1, y: 0, rotation: 0, duration: 0.55, ease: "bounce.out", immediateRender: false }, a.t);
        } else if (a.t > P.t0 + 0.05) {
          tl.fromTo(e, { autoAlpha: 1, scale: 0 }, { autoAlpha: 1, scale: 1, duration: 0.35, ease: "back.out(3)", immediateRender: false }, a.t);
        } else {
          tl.set(e, { autoAlpha: 1 }, a.t);
        }
      });
      a.remove.forEach(function (name) {
        [accEl(name, false), accEl(name, true)].forEach(function (e) { tl.to(e, { autoAlpha: 0, scale: 0.2, duration: 0.25, ease: "power2.in" }, a.t); });
        on[name] = false;
      });
    });
    // accessories follow a change between smooth and pixel styles
    if (!P.rig) P.styles.slice(1).forEach(function (s) {
      const px = P.pixel || s.style === "pixel";
      Object.keys(on).forEach(function (name) {
        if (!on[name]) return;
        tl.set(accEl(name, !px), { autoAlpha: 0 }, s.t);
        tl.set(accEl(name, px), { autoAlpha: 1, y: 0, scale: 1, rotation: 0 }, s.t);
      });
    });
    // entrance
    tl.set(root, { autoAlpha: 1 }, P.t0);
    const e = P.enter;
    if (e.kind === "pop") tl.fromTo(act, { scale: 0 }, { scale: 1, duration: 0.4, ease: "back.out(2.2)", immediateRender: false }, P.t0);
    if (e.kind === "drop") {  // falls (stretched), lands with a squash, settles: bounce.out rebounded 75% (v05)
      tl.fromTo(act, { y: -h * 2.2, scaleY: 1.15, scaleX: 0.9 }, { y: 0, scaleY: 1.15, scaleX: 0.9, duration: 0.32, ease: "power2.in", immediateRender: false }, P.t0);
      tl.to(act, { scaleY: 0.72, scaleX: 1.2, duration: 0.07, ease: "power2.out" }, P.t0 + 0.32);
      tl.to(act, { scaleY: 1, scaleX: 1, duration: 0.45, ease: "elastic.out(1, 0.4)" }, P.t0 + 0.39);
      tl.fromTo(shadow, { scale: 0.3, opacity: 0.2 }, { scale: 1, opacity: 1, duration: 0.32, ease: "power2.in", immediateRender: false }, P.t0);
    }
    if (e.kind === "fade") tl.fromTo(act, { opacity: 0 }, { opacity: 1, duration: 0.4, ease: "none", immediateRender: false }, P.t0);
    if (e.kind === "pop") burst(tl, sp, P.t0 + 0.05, w * 0.6);
    if (e.kind === "drop") burst(tl, sp, P.t0 + 0.32, w * 0.5);  // dust on the landing
    if (e.kind === "pop") poof(tl, puffs, P.t0 - 0.04, w);
    // moves (walk / run frames while moving, facing the way it goes)
    P.moves.forEach(function (m, k) {
      if (k === 0 || m.d === 0) { tl.set(root, { left: m.x, top: m.y }, m.t); return; }
      if (m.dir && m.dir !== facing * (P.flip ? -1 : 1)) {
        facing = m.dir * (P.flip ? -1 : 1);
        tl.set(body, { scaleX: facing }, m.t);
      }
      tl.to(root, { left: m.x, top: m.y, duration: m.d, ease: m.ease }, m.t);
      if (m.gait === "jump") {  // an arc on top of the straight line: up fast, down falling (lab v08)
        tl.to(act, { y: -h * 0.45, duration: m.d / 2, ease: "power2.out", yoyo: true, repeat: 1 }, m.t);
        tl.to(shadow, { scale: 0.5, opacity: 0.4, duration: m.d / 2, ease: "power2.out", yoyo: true, repeat: 1 }, m.t);
      }
      const cyc = !P.sched && m.gait && P.frames[m.gait];
      if (cyc) {
        const step = m.gait === "run" ? 0.08 : 0.13;
        const keys = cyc.map(function (f) { return Object.keys(P.files).find(function (k2) { return P.files[k2] === f; }); });
        for (let t = m.t, n = 0; t < m.t + m.d - 0.01; t += step, n++) show(keys[n % keys.length], t);
        show(P.carry && P.carry.t <= m.t ? "grab" : styleNow, m.t + m.d);
      } else if (!P.pixel && !P.rig && !P.sched) {  // a fish swims: a wiggle while it travels
        tl.fromTo(idle, { rotation: -6 }, { rotation: 6, duration: 0.18, ease: "sine.inOut", yoyo: true, repeat: Math.max(1, Math.round(m.d / 0.18)), immediateRender: false }, m.t);
        tl.set(idle, { rotation: 0 }, m.t + m.d);
      }
    });
    // idle motion for the whole stay
    const life = Math.max(0.5, P.t1 - P.t0);
    if (P.idle === "bob" && D.beats && D.beats.times.length) {  // on the music (n06): down on each beat
      const bt = D.beats.times.filter(function (t) { return t >= P.t0 && t < P.t1; });
      bt.forEach(function (t, k) {
        const next = k + 1 < bt.length ? bt[k + 1] : t + 0.5;
        tl.fromTo(idle, { y: h * 0.02, scaleY: 0.94 }, { y: -h * 0.06, scaleY: 1, duration: Math.max(0.08, (next - t) * 0.5), ease: "power2.out", transformOrigin: "50% 100%", immediateRender: false }, t);
        tl.to(idle, { y: h * 0.02, scaleY: 0.94, duration: Math.max(0.08, (next - t) * 0.5), ease: "power2.in" }, t + (next - t) * 0.5);
      });
    } else if (P.idle === "bob") tl.fromTo(idle, { y: 0 }, { y: -h * 0.06, duration: 0.7, ease: "sine.inOut", yoyo: true, repeat: Math.floor(life / 0.7), immediateRender: false }, P.t0);
    if (P.idle === "breathe") tl.fromTo(idle, { scaleY: 1 }, { scaleY: 1.04, duration: 0.9, ease: "sine.inOut", yoyo: true, repeat: Math.floor(life / 0.9), transformOrigin: "50% 100%", immediateRender: false }, P.t0);
    if (P.idle === "swim") tl.fromTo(idle, { y: 0, rotation: -3 }, { y: -h * 0.08, rotation: 3, duration: 0.8, ease: "sine.inOut", yoyo: true, repeat: Math.floor(life / 0.8), immediateRender: false }, P.t0);
    // actions
    P.acts.forEach(function (a) {
      const t = a.t;
      if (a.do === "jump") {
        tl.to(act, { y: -h * 0.6, duration: 0.2, ease: "power2.out", yoyo: true, repeat: 1 }, t);
        tl.to(shadow, { scale: 0.6, opacity: 0.5, duration: 0.2, ease: "power2.out", yoyo: true, repeat: 1 }, t);
      }
      if (a.do === "spin") tl.fromTo(act, { rotation: 0 }, { rotation: 360, duration: 0.5, ease: "power2.inOut", immediateRender: false }, t);
      if (a.do === "wiggle") tl.fromTo(act, { rotation: -10 }, { rotation: 10, duration: 0.08, ease: "sine.inOut", yoyo: true, repeat: 5, immediateRender: false }, t), tl.set(act, { rotation: 0 }, t + 0.5);
      if ((a.do === "blink" && !P.rig) || a.do === "squash") tl.to(act, { scaleY: 0.72, scaleX: 1.15, duration: 0.08, ease: "power2.out", yoyo: true, repeat: 1, transformOrigin: "50% 100%" }, t);
      if (a.do === "flip") { facing = -facing; tl.set(body, { scaleX: facing }, t); }
      if (a.do === "look") { tl.set(body, { scaleX: -facing }, t); tl.set(body, { scaleX: facing }, t + 0.8); }
    });
    if (R) FRED.play(R, P, tl, D.pixel_cells || 28, shadow);
    // gags (ADR 0030): a pixel item beside him at his own pixel size: on the floor to his left, held at his
    // fin, over his head, over his eyes (the censor bar slams on), or instead of him (a dog, a bird: a poof)
    (P.gags || []).forEach(function (g) {
      const iw = g.rel * w, ih = iw * g.aspect;
      const pos = {
        left: [g.flip_left ? 0.95 * w : 0.05 * w - iw, h - ih], held: [(g.mirror ? 0.12 : 0.88) * w - iw / 2, 0.62 * h - ih / 2], above: [-0.15 * w - iw / 2, -0.05 * h - ih],  // over his left shoulder: the right edge cut it (r05)
        swap: [Math.min((w - iw) / 2, w - iw), h - ih],  // a wide swap (the bird) grows left, never past his right side (r16)
        face: [0.61 * w - iw / 2, 0.66 * w - ih / 2],  // the carp sprite's eye (r09: 0.46, from the old sprite, sat on the hat brim)
      }[g.place] || [0, 0];
      if (g.spot) { pos[0] = g.spot[0] - iw / 2; pos[1] = g.spot[1] - ih / 2; }  // a frame spot (plan gag_spot)
      if (g.place === "swap" && g.name === "bird") pos[1] -= h * 0.55;  // a bird flies: up out of the description zone (r18)
      const box = el("div", "pp-gag", g.place === "swap" ? root : act);
      Object.assign(box.style, { left: pos[0] + "px", top: pos[1] + "px", width: iw + "px", height: ih + "px" });
      const fr = g.files.map(function (f) { const i = img(f, "pp-gag-img px", box); gsap.set(i, { display: "none" }); return i; });
      gsap.set(box, { autoAlpha: 0 });
      const t0 = g.t, t1 = g.t + g.d;
      tl.set(box, { autoAlpha: 1 }, t0);
      if (g.place === "face") {
        tl.fromTo(box, { scale: 2.6, rotation: -14 }, { scale: 1, rotation: -4, duration: 0.12, ease: "power4.in", immediateRender: false }, t0);
        tl.to(act, { y: 6, duration: 0.05, yoyo: true, repeat: 1 }, t0 + 0.12);
      } else {
        tl.fromTo(box, { scale: 0, transformOrigin: "50% 100%" }, { scale: 1, duration: 0.25, ease: "back.out(2.5)", immediateRender: false }, t0);
      }
      const step = 1 / (g.fps || 6);
      let k = 0;
      for (let t = t0; t < t1 - 0.01; t += step, k++) {
        tl.set(fr[k % fr.length], { display: "block" }, t);
        if (fr.length > 1) tl.set(fr[k % fr.length], { display: "none" }, Math.min(t + step, t1));
      }
      if (fr.length === 1) tl.set(fr[0], { display: "block" }, t0);
      if (g.place === "swap") {  // he turns into it under a poof, and back
        poof(tl, puffs, t0 - 0.04, w);
        tl.set(act, { autoAlpha: 0 }, t0);
        tl.set(act, { autoAlpha: 1 }, t1);
        poof(tl, puffs, t1 - 0.04, w);
        tl.set(box, { autoAlpha: 0 }, t1);
      } else {
        tl.to(box, { scale: 0, duration: 0.18, ease: "back.in(2)" }, t1 - 0.18);
        tl.set(box, { autoAlpha: 0 }, t1);
      }
    });
    if (R) P.acc.forEach(function (a) {  // pixel / 3D frames swap the hat in: give it a landing (lab v07)
      let st = P.styles[0].style;
      P.styles.forEach(function (s) { if (s.t <= a.t) st = s.style; });
      if ((st !== "pixel" && st !== "toon3d") || !a.add.length || a.t <= P.t0 + 0.05) return;
      tl.to(act, { scaleY: 0.8, scaleX: 1.12, duration: 0.07, ease: "power2.out", transformOrigin: "50% 100%" }, a.t);
      tl.to(act, { scaleY: 1, scaleX: 1, duration: 0.4, ease: "elastic.out(1, 0.4)" }, a.t + 0.07);
      burst(tl, sp, a.t, w * 0.45);
    });
    // name tags and speech bubbles
    P.tags.forEach(function (g) {
      if (g.kind === "emote") {  // over the head: pops, floats up a little, gone (no bubble: it reads bigger)
        const m = el("div", "pp-emote", root);
        m.textContent = g.text;
        m.style.fontSize = (130 / D.room_k) + "px";
        gsap.set(m, { autoAlpha: 0, xPercent: -50 });
        tl.fromTo(m, { autoAlpha: 1, scale: 0, y: 0, rotation: -15 }, { autoAlpha: 1, scale: 1, rotation: 0, duration: 0.3, ease: "back.out(3)", immediateRender: false }, g.t);
        tl.to(m, { y: -h * 0.15, duration: g.d, ease: "sine.out" }, g.t);
        tl.to(m, { autoAlpha: 0, duration: 0.2 }, g.t + g.d - 0.2);
        return;
      }
      const b = el("div", g.kind === "tag" ? "pp-tag" + (g.side ? " side" : g.lift ? " lift" : "") : "pp-say" + (g.flip ? " flip" : ""), root);
      b.textContent = g.text;
      b.style.fontSize = ((g.kind === "say" ? 84 : 60) / D.room_k) + "px";  // 46 px read as specks (r07); bubbles still tiny (r13)
      gsap.set(b, { autoAlpha: 0, xPercent: g.kind === "tag" && !g.side ? (g.lift ? -85 : -50) : 0 });
      tl.fromTo(b, { autoAlpha: 1, scale: 0 }, { autoAlpha: 1, scale: 1, duration: 0.3, ease: "back.out(2.5)", immediateRender: false }, g.t);
      tl.to(b, { autoAlpha: 0, scale: 0.6, duration: 0.2, ease: "power2.in" }, Math.min(P.t1 - 0.05, g.t + g.d));
    });
    // carrying another prop: it appears in the mouth (in its look at that moment)
    if (P.carry) {
      const c = P.carry;
      const cw = c.w_rel * w, ch = cw * c.aspect;
      const mouth = P.points.mouth || [0.95, 0.5];
      const hold = el("div", "pp-carried", body);
      Object.assign(hold.style, { width: cw + "px", height: ch + "px", left: (mouth[0] * w - cw * 0.5) + "px", top: (mouth[1] * h - ch * 0.42) + "px" });
      if (c.rig && c.style !== "photo") {  // fred, flailing his fins in the cat's mouth
        const CR = FRED.build(c.id + "-carried", cw); CR.svg.classList.add("pp-rig"); hold.appendChild(CR.svg);
        FRED.setStyle(tl, CR, c.style, 0, D.pixel_cells || 28);
        c.acc.forEach(function (name) { FRED.accessory(tl, CR, name, true, 0, false); });
        tl.fromTo(CR.finF, { rotation: -150 }, { rotation: -40, svgOrigin: "142 158", duration: 0.12, yoyo: true, repeat: 30, ease: "none", immediateRender: false }, c.t);
        tl.fromTo(CR.finB, { rotation: 150 }, { rotation: 40, svgOrigin: "64 150", duration: 0.12, yoyo: true, repeat: 30, ease: "none", immediateRender: false }, c.t);
      } else {
        const ci = el("img", "pp-img" + (c.pixel ? " px" : ""), hold); ci.src = FILES + c.file; ci.style.display = "block";
        c.acc.forEach(function (name) { accessory(name, D.props_kit, c.pixel, hold, cw, ch, c.points); });
      }
      // a cat carries a fish crosswise by the middle: the hold is centred on the mouth and lies near
      // horizontal, head forward (upright, he read as standing beside her: v07; pivoted at his end, he
      // covered her head: v08)
      gsap.set(hold, { autoAlpha: 0, rotation: 78, transformOrigin: "50% 50%" });
      tl.set(hold, { autoAlpha: 1 }, c.t);
      tl.fromTo(hold, { scale: 0.6 }, { scale: 1, duration: 0.25, ease: "back.out(3)", immediateRender: false }, c.t);
      if (imgs.grab && !P.sched) show("grab", c.t);
      tl.to(act, { scaleY: 0.85, duration: 0.08, yoyo: true, repeat: 1, transformOrigin: "50% 100%" }, c.t);
    }
    // exit
    const x = P.exit;
    if (x.kind === "pop") tl.to(act, { scale: 0, duration: x.d, ease: "back.in(2)" }, x.t);
    if (x.kind === "fade") tl.to(act, { opacity: 0, duration: x.d, ease: "none" }, x.t);
    if (x.kind === "fall") tl.to(act, { y: h * 4, rotation: 70, duration: x.d, ease: "power2.in" }, x.t);
    tl.set(root, { autoAlpha: 0 }, P.t1);
  }

  // ---- effects --------------------------------------------------------------------------------------------

  function filters(D, tl) {
    // the presenter's filter at each change: grade tweens; anime and blocky switch with a flash
    const base = D.grade;
    const kinds = ["grade", "anime", "blocky", "comic"];
    const fx = D.fx.filter(function (f) { return kinds.indexOf(f.kind) >= 0; });
    if (!fx.length) return;
    const pts = [0];
    fx.forEach(function (f) { pts.push(f.t0, f.t1); });
    pts.sort(function (a, b) { return a - b; });
    function at(t) {
      const g = Object.assign({}, base, { hue: 0 });
      let url = "", fgurl = null;  // fgurl: the cut-out's own filters when they differ (a room-only effect)
      fx.forEach(function (f) {
        if (t < f.t0 - 1e-6 || t >= f.t1 - 1e-6) return;
        if (f.kind === "grade") ["hue", "saturate", "contrast", "brightness"].forEach(function (k) { if (f.spec[k] != null) g[k] = f.spec[k]; });
        if (f.kind === "anime") { url += " url(#toon)"; g.saturate = Math.max(g.saturate, 1.18); }
        if (f.kind === "blocky") { url += " url(#blocky)"; if (f.spec.room_only) fgurl = (fgurl || "") + "|skip-blocky"; }
        if (f.kind === "comic") { url += " url(#comic)"; g.contrast = Math.max(g.contrast, 1.1); }
      });
      const css = "contrast(" + g.contrast + ") saturate(" + g.saturate + ") brightness(" + g.brightness + ") sepia(" + g.warmth + ") hue-rotate(" + g.hue + "deg)";
      // a room-only effect (n02: the room turns pixel art, Robert stays real) leaves the cut-out unfiltered
      const fg = fgurl ? css + url.replace(" url(#blocky)", "") : css + url;
      return { s: css + url, fg: fg, url: url };
    }
    const face = ["#face"], fgs = Array.prototype.slice.call(document.querySelectorAll(".fg"));
    let prev = at(0);
    gsap.set(face, { filter: prev.s });
    if (fgs.length) gsap.set(fgs, { filter: prev.fg });
    pts.forEach(function (t) {
      const cur = at(t);
      if (cur.s === prev.s && cur.fg === prev.fg) return;
      if (!cur.url && !prev.url) {
        tl.fromTo(face, { filter: prev.s }, { filter: cur.s, duration: 0.5, ease: "power2.inOut", immediateRender: false }, t);
        if (fgs.length) tl.fromTo(fgs, { filter: prev.fg }, { filter: cur.fg, duration: 0.5, ease: "power2.inOut", immediateRender: false }, t);
      } else {
        const into = cur.url.indexOf("#blocky") >= 0 && prev.url.indexOf("#blocky") < 0;
        const outof = prev.url.indexOf("#blocky") >= 0 && cur.url.indexOf("#blocky") < 0;
        if (into || outof) {  // the room builds into (or out of) pixels in steps, with a flash (n02 review)
          const fine = (into ? cur.s : prev.s), steps = into ? ["#bk0", "#bk1"] : ["#bk1", "#bk0"];
          steps.forEach(function (id, k) { tl.set(face, { filter: fine.replace("#blocky", id) }, t + k * 0.12); });
          tl.set(face, { filter: cur.s }, t + 0.24);
        } else tl.set(face, { filter: cur.s }, t);
        if (fgs.length) tl.set(fgs, { filter: cur.fg }, t);
      }
      prev = cur;
    });
  }

  function anime(f, D, tl) {
    // big sparkly eyes and blush on the face (room space, per segment), sparkles, and speed lines behind the
    // presenter when the matte is there (in front, round the edges, when not)
    const room = document.getElementById("room");
    const g = el("div", "an-face", room);
    gsap.set(g, { autoAlpha: 0 });
    const eyes = [-1, 1].map(function (s) { const e = el("div", "an-eye", g); e.dataset.side = s; e.innerHTML = EYE; return e; });
    const blush = [-1, 1].map(function () { return el("div", "an-blush", g); });
    const sp = sparkles(g, 10, 34 / D.room_k);
    const R = 1 / D.room_k;
    f.faces.forEach(function (fc) {
      tl.set(g, { left: fc.cx, top: fc.cy, width: fc.fw, height: fc.fh, xPercent: -50, yPercent: -50 }, fc.t0);
      eyes.forEach(function (e) {
        const s = +e.dataset.side;
        tl.set(e, { left: fc.fw * (0.5 + s * 0.2) - fc.fw * 0.15, top: fc.fh * 0.36 - fc.fw * 0.18, width: fc.fw * 0.3, height: fc.fw * 0.36 }, fc.t0);
      });
      blush.forEach(function (b, k) {
        tl.set(b, { left: fc.fw * (k ? 0.68 : 0.08), top: fc.fh * 0.62, width: fc.fw * 0.24, height: fc.fw * 0.1 }, fc.t0);
      });
    });
    tl.set(g, { autoAlpha: 1 }, f.t0);
    tl.fromTo(eyes, { scale: 0 }, { scale: 1, duration: 0.3, ease: "back.out(3)", immediateRender: false }, f.t0);
    sp.forEach(function (s, k) {
      const a = k / sp.length * Math.PI * 2;
      gsap.set(s, { left: "50%", top: "40%" });
      tl.fromTo(s, { x: Math.cos(a) * 60 * R, y: Math.sin(a) * 60 * R, scale: 0, opacity: 1 },
        { x: Math.cos(a) * 260 * R, y: (Math.sin(a) * 300 - 40) * R, scale: 1.4, opacity: 0, duration: 1.2, ease: "power1.out", repeat: Math.max(0, Math.floor((f.t1 - f.t0) / 1.2) - 1), immediateRender: false }, f.t0 + k * 0.05);
    });
    tl.set(g, { autoAlpha: 0 }, f.t1);
    const lines = el("div", D.matte ? "an-lines behind" : "an-lines", document.getElementById(D.matte ? "bgfx" : "fxtop"));
    if (f.spec.label) { const lb = el("div", "an-label", document.getElementById("fxtop")); lb.textContent = f.spec.label;
      gsap.set(lb, { autoAlpha: 0 }); tl.fromTo(lb, { autoAlpha: 1, scale: 0, rotation: -8 }, { autoAlpha: 1, scale: 1, duration: 0.35, ease: "back.out(2.5)", immediateRender: false }, f.t0); tl.set(lb, { autoAlpha: 0 }, f.t1); }
    gsap.set(lines, { autoAlpha: 0 });
    tl.set(lines, { autoAlpha: 1 }, f.t0);
    tl.fromTo(lines, { rotation: 0 }, { rotation: 8, duration: f.t1 - f.t0, ease: "none", immediateRender: false }, f.t0);
    tl.set(lines, { autoAlpha: 0 }, f.t1);
    flash(tl, f.t0, 0.5);
    flash(tl, f.t1, 0.4);
  }

  function blocky(f, D, tl) {
    flash(tl, f.t0, 0.45);
    flash(tl, f.t1, 0.35);
    if (f.spec.hud === false) return;  // the room alone (n02 i1: the hotbar sat on his lap)
    const top = document.getElementById("fxtop");
    const hud = el("div", "bk-hud", top);
    const hearts = el("div", "bk-hearts", hud);
    for (let k = 0; k < 10; k++) el("i", "", hearts);
    const bar = el("div", "bk-bar", hud);
    for (let k = 0; k < 9; k++) { const s = el("i", k === 0 ? "on" : "", bar); if (k === 0) s.textContent = f.spec.item || "⛏"; }
    gsap.set(hud, { autoAlpha: 0 });
    tl.set(hud, { autoAlpha: 1 }, f.t0);
    tl.fromTo(hud, { y: 60 }, { y: 0, duration: 0.3, ease: "back.out(2)", immediateRender: false }, f.t0);
    tl.set(hud, { autoAlpha: 0 }, f.t1);
  }

  // A transmutation circle (an original drawing) lights up on the floor: drawn in, glowing, sparks, a flash.
  function alchemy(f, D, tl) {
    // on the floor under his feet: behind the presenter's cut-out when there is one (Robert: "under my feet,
    // not over it"); without the matte it can only be drawn over him
    const room = document.getElementById(D.matte ? "room-back" : "room");
    const box = el("div", "al-box");
    room.insertBefore(box, room.firstChild);
    const r = f.r;
    Object.assign(box.style, { left: (f.x - r) + "px", top: (f.y - r) + "px", width: 2 * r + "px", height: 2 * r + "px" });
    const tri = [0, 1, 2].map(function (k) { const a = -Math.PI / 2 + k * 2 * Math.PI / 3; return [Math.cos(a) * 84, Math.sin(a) * 84]; });
    const sq = [0, 1, 2, 3].map(function (k) { const a = Math.PI / 4 + k * Math.PI / 2; return [Math.cos(a) * 58, Math.sin(a) * 58]; });
    let ticks = "";
    for (let k = 0; k < 24; k++) { const a = k * Math.PI / 12; ticks += "M" + (Math.cos(a) * 88).toFixed(1) + " " + (Math.sin(a) * 88).toFixed(1) + " L" + (Math.cos(a) * (k % 2 ? 93 : 96)).toFixed(1) + " " + (Math.sin(a) * (k % 2 ? 93 : 96)).toFixed(1) + " "; }
    box.innerHTML = '<svg viewBox="-100 -100 200 200" width="100%" height="100%" overflow="visible"><g class="al-lines" fill="none" stroke="#9ff0ff" stroke-width="2.6" stroke-linecap="round">' +
      '<circle r="96"/><circle r="86"/><circle r="30"/><circle r="12"/>' +
      '<path class="al-in" d="M' + tri.map(function (p) { return p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" L") + ' Z"/>' +
      '<path class="al-in" d="M' + sq.map(function (p) { return p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" L") + ' Z"/>' +
      tri.map(function (p) { return '<circle cx="' + p[0].toFixed(1) + '" cy="' + p[1].toFixed(1) + '" r="9"/>'; }).join("") +
      '<path d="' + ticks + '" stroke-width="2"/></g></svg>';
    const lines = box.querySelector(".al-lines");
    const parts = box.querySelectorAll(".al-lines > *");
    const sparks = [];
    for (let k = 0; k < 6; k++) {
      const s = el("div", "al-spark", box);
      s.style.left = (50 + 46 * Math.cos(k)) + "%"; s.style.top = (50 + 30 * Math.sin(k * 1.7)) + "%";
      s.style.transform = "rotate(" + (k * 61) + "deg)";
      sparks.push(s);
    }
    gsap.set(box, { autoAlpha: 0, scaleY: 0.36, transformOrigin: "50% 50%" });
    gsap.set(sparks, { autoAlpha: 0 });
    tl.set(box, { autoAlpha: 1 }, f.t0);
    tl.fromTo(parts, { strokeDasharray: 700, strokeDashoffset: 700 }, { strokeDashoffset: 0, duration: 0.5, stagger: 0.03, ease: "power2.out", immediateRender: false }, f.t0);
    tl.fromTo(lines, { filter: "drop-shadow(0 0 2px #9ff0ff)" }, { filter: "drop-shadow(0 0 16px #5fd8ff)", duration: 0.3, yoyo: true, repeat: loops(f.t1 - f.t0 - 0.6, 0.3), ease: "sine.inOut", immediateRender: false }, f.t0 + 0.5);
    tl.fromTo(box.querySelectorAll(".al-in"), { rotation: 0, transformOrigin: "50% 50%" }, { rotation: 60, duration: f.t1 - f.t0, ease: "none", immediateRender: false }, f.t0);
    sparks.forEach(function (s, k) {
      for (let t = f.t0 + 0.55 + k * 0.07; t < f.t1 - 0.3; t += 0.42) { tl.set(s, { autoAlpha: 1 }, t); tl.set(s, { autoAlpha: 0 }, t + 0.08); }
    });
    flash(tl, f.t0 + 0.55, 0.35);
    tl.to(box, { autoAlpha: 0, duration: 0.35 }, f.t1 - 0.35);
  }
  function loops(n, per) { return Math.max(0, Math.floor(n / per) - 1); }

  // Automail (a Fullmetal Alchemist homage; an original drawing): the presenter's limbs turn to steel. Each limb
  // segment is a steel plate keyed to the pose's joints (master pixels, record time), so it follows him.
  // Gunmetal like Edward Elric's automail (studied from a reference sheet Robert shared; drawn, not copied):
  // segmented plates with bands and a raised ridge, a ringed joint, a mechanical hand.
  const STEEL = '<linearGradient id="amg" x1="0" y1="0" x2="0" y2="1">' +
    '<stop offset="0" stop-color="#c3cad3"/><stop offset=".2" stop-color="#8b939d"/><stop offset=".55" stop-color="#4a5059"/>' +
    '<stop offset=".82" stop-color="#626a74"/><stop offset="1" stop-color="#9aa3ad"/></linearGradient>';
  const PLATE = '<svg viewBox="0 0 100 40" preserveAspectRatio="none"><defs>' + STEEL + '</defs>' +
    '<rect x="0" y="2" width="100" height="36" rx="10" fill="url(#amg)" stroke="#1a1d22" stroke-width="3" vector-effect="non-scaling-stroke"/>' +
    '<path d="M4 13 L96 13" stroke="#e8edf2" stroke-opacity=".75" stroke-width="2.5" vector-effect="non-scaling-stroke"/>' +
    '<path d="M24 3 L24 37 M27 3 L27 37 M62 3 L62 37 M65 3 L65 37" stroke="#262a30" stroke-width="2" vector-effect="non-scaling-stroke"/>' +
    '<path d="M6 30 L96 30" stroke="#2b3036" stroke-opacity=".6" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>';
  const HANDP = '<svg viewBox="0 0 100 40" preserveAspectRatio="none"><defs>' + STEEL + '</defs>' +
    '<path d="M0 6 L40 2 L100 8 L100 32 L40 38 L0 34 Z" fill="url(#amg)" stroke="#1a1d22" stroke-width="3" vector-effect="non-scaling-stroke" stroke-linejoin="round"/>' +
    '<path d="M40 2 L40 38 M55 12 L100 12 M55 20 L100 20 M55 28 L100 28" stroke="#262a30" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>';
  const JOINT = '<svg viewBox="-10 -10 20 20"><defs>' + STEEL + '</defs><circle r="9" fill="url(#amg)" stroke="#1a1d22" stroke-width="1.6"/>' +
    '<circle r="5.5" fill="none" stroke="#262a30" stroke-width="1.2"/><circle r="2.4" fill="#2b3036"/></svg>';
  function automail(f, D, tl) {
    const room = document.getElementById("room");
    const box = el("div", "am-box");
    room.insertBefore(box, room.firstChild);  // over the presenter, under the props
    gsap.set(box, { autoAlpha: 0 });
    tl.set(box, { autoAlpha: 1 }, f.t0);
    Object.keys(f.limbs || {}).forEach(function (limb, li) {
      const K = f.limbs[limb];
      if (!K.length) return;
      const arm = limb.indexOf("arm") >= 0;
      const segs = arm ? [[0, 1], [1, 2], [2, 3]] : [[0, 1], [1, 2]];
      const lens = K.map(function (k) { return Math.hypot(k[1][2][0] - k[1][1][0], k[1][2][1] - k[1][1][1]); }).sort(function (a, b) { return a - b; });
      const thick = lens[Math.floor(lens.length / 2)] * (arm ? 0.36 : 0.3);  // a seated thigh is foreshortened: size from the lower segment
      const parts = segs.map(function (sg, j) {
        const d = el("div", "am-seg", box);
        d.innerHTML = j === 2 ? HANDP : PLATE;  // the arm's last segment is the mechanical hand
        gsap.set(d, { height: thick * (j === 2 ? 0.9 : 1), yPercent: -50, transformOrigin: "0% 50%" });
        return d;
      });
      const joint = el("div", "am-joint", box);
      gsap.set(joint, { width: thick * 0.9, height: thick * 0.9, xPercent: -50, yPercent: -50 });
      joint.innerHTML = JOINT;
      const rot = parts.map(function () { return null; });
      K.forEach(function (k, n) {
        const t = k[0], P = k[1];
        const dt = n + 1 < K.length ? K[n + 1][0] - t : 0;
        segs.forEach(function (sg, j) {
          const a = P[sg[0]], b = P[sg[1]];
          let r = Math.atan2(b[1] - a[1], b[0] - a[0]) * 180 / Math.PI;
          if (rot[j] !== null) { while (r - rot[j] > 180) r -= 360; while (r - rot[j] < -180) r += 360; }  // no spins
          rot[j] = r;
          const v = { x: a[0], y: a[1], rotation: r, width: Math.max(4, Math.hypot(b[0] - a[0], b[1] - a[1]) * (j === 2 ? 1.1 : 1)) };
          if (n === 0) tl.set(parts[j], v, f.t0);
          else tl.to(parts[j], Object.assign(v, { duration: Math.max(0.01, K[n][0] - K[n - 1][0]), ease: "none" }), K[n - 1][0]);
        });
        const m = P[1];
        if (n === 0) tl.set(joint, { x: m[0], y: m[1] }, f.t0);
        else tl.to(joint, { x: m[0], y: m[1], duration: Math.max(0.01, K[n][0] - K[n - 1][0]), ease: "none" }, K[n - 1][0]);
      });
      // the transmutation: the steel spreads from the shoulder (hip) down the limb, a segment at a time
      const inner = parts.map(function (d) { return d.firstChild; });
      gsap.set(inner, { transformOrigin: "0% 50%" });
      tl.fromTo(inner, { scaleX: 0 }, { scaleX: 1, duration: 0.18, stagger: 0.12, ease: "power2.out", immediateRender: false }, f.t0 + li * 0.15);
      tl.fromTo(joint, { scale: 0 }, { scale: 1, duration: 0.2, ease: "back.out(3)", immediateRender: false }, f.t0 + li * 0.15 + 0.15);
    });
    flash(tl, f.t0, 0.6);
    if (f.t1 < D.duration - 0.05) tl.to(box, { autoAlpha: 0, duration: 0.3 }, f.t1 - 0.3);
  }

  // Which image shows a prop "as it is now" for an effect: Fred's pixel idle frame with his accessories,
  // a cat's idle frame, or its photo.
  function propImage(D, id, t) {
    const P = (D.props || []).find(function (q) { return q.id === id; });
    if (!P) return null;
    if (P.pixel_sets) {
      let on = [];
      P.acc.forEach(function (a) { if (a.t <= t) on = on.filter(function (x) { return a.remove.indexOf(x) < 0; }).concat(a.add); });
      const key = "px-" + (on.filter(function (x, k) { return on.indexOf(x) === k; }).sort().join("-") || "plain");
      const set = P.pixel_sets[key] || P.pixel_sets[Object.keys(P.pixel_sets).find(function (k) { return k.indexOf("px-") === 0; })];
      if (set && set.idle) return { src: set.idle[0], px: true, aspect: P.aspect };
    }
    if (P.files.idle0) return { src: P.files.idle0, px: true, aspect: P.aspect };
    return { src: P.files.photo || P.files[Object.keys(P.files)[0]], px: false, aspect: P.aspect };
  }

  // A black-hole mini explainer (original drawing): a starfield, a black disc with a glowing, turning
  // accretion disk and photon ring, labels on the narration, and a victim (Fred) pulled in: he drifts in on
  // a spiral, stretches toward the hole (spaghettification) and is gone. Full frame, over the presenter.
  function blackhole(f, D, tl) {
    const top = document.getElementById("fxtop");
    const box = el("div", "bh-box", top);
    let stars = "";
    for (let k = 0; k < 140; k++) {
      const x = (k * 137.508) % 100, y = (k * 61.8034 * 1.7) % 100, r = (k % 7 === 0) ? 2.2 : (k % 3 === 0 ? 1.4 : 0.9);
      stars += '<circle cx="' + x.toFixed(2) + '%" cy="' + y.toFixed(2) + '%" r="' + r + '" fill="#fff" opacity="' + (0.35 + (k % 5) * 0.13).toFixed(2) + '"/>';
    }
    box.innerHTML = '<svg class="bh-stars" width="100%" height="100%">' + stars + '</svg>' +
      '<div class="bh-hole"><div class="bh-glow"></div><div class="bh-disk"><div class="bh-spin"></div></div><div class="bh-core"></div><div class="bh-ring"></div><div class="bh-disk bh-front"><div class="bh-spin"></div></div></div>' +
      '<div class="bh-title">HOW BLACK HOLES WORK</div><div class="bh-label"></div>';
    const label = box.querySelector(".bh-label");
    gsap.set(box, { autoAlpha: 0 });
    const d = Math.max(1, f.t1 - f.t0);
    tl.set(box, { autoAlpha: 1 }, f.t0);
    flash(tl, f.t0, 0.6);  // into and out of space on a flash (r09: the cut in read abrupt)
    flash(tl, f.t1 - 0.05, 0.5);
    tl.fromTo(box, { clipPath: "circle(0% at 50% 50%)" }, { clipPath: "circle(75% at 50% 50%)", duration: 0.45, ease: "power3.out", immediateRender: false }, f.t0);
    if (!f.spec.presenter)  // with the presenter inside it, the hole is there at once: he starts at full size
      tl.fromTo(box.querySelector(".bh-hole"), { scale: 0.2 }, { scale: 1, duration: 0.8, ease: "back.out(1.6)", immediateRender: false }, f.t0);
    // one camera "shot" per label, cut on the label, each a slow push (r07/r08: one slow push for 7 s read as
    // three identical frames): wide, then a tilted close-up, then a low angle for the spaghetti
    const hole = box.querySelector(".bh-hole");
    const SHOTS = f.spec.shots || [[1, 0, 0, 0], [1.6, -60, -150, -12], [1.3, 60, -90, 14]];  // [scale, x, y, rotation]  // clear of the label (r09 preview)
    const labs = f.spec.labels || [];
    labs.forEach(function (L, k) {
      const s = SHOTS[k % SHOTS.length], a = k === 0 ? f.t0 + 0.8 : f.t0 + L[0] * d;
      const b = k + 1 < labs.length ? f.t0 + labs[k + 1][0] * d : f.t1;
      if (k > 0) tl.set(hole, { scale: s[0], x: s[1], y: s[2], rotation: s[3] }, a);
      tl.to(hole, { scale: s[0] * 1.15, duration: Math.max(0.3, b - a), ease: "sine.in" }, a);
    });
    if (!labs.length) tl.to(hole, { scale: 1.35, duration: Math.max(0.5, d - 0.8), ease: "sine.in" }, f.t0 + 0.8);
    // "not even light escapes": streaks of light fall into the core during the second label
    if (labs.length > 1) {
      const ta = f.t0 + labs[1][0] * d, tb = labs.length > 2 ? f.t0 + labs[2][0] * d : f.t1;
      for (let k = 0; k < 9; k++) {
        const ray = el("div", "bh-ray", hole), ang = k * 40 + 10;
        gsap.set(ray, { rotation: ang, autoAlpha: 0 });
        tl.fromTo(ray, { autoAlpha: 1, x: 900 * Math.cos(ang * Math.PI / 180), y: 900 * Math.sin(ang * Math.PI / 180), scaleX: 1 },
          { autoAlpha: 1, x: 0, y: 0, scaleX: 0.2, duration: 0.7, ease: "power2.in", repeat: Math.max(0, Math.floor((tb - ta) / 0.9) - 1),
            repeatDelay: 0.2, immediateRender: false }, ta + (k % 3) * 0.25);
        tl.set(ray, { autoAlpha: 0 }, tb);
      }
    }
    tl.fromTo(box.querySelector(".bh-stars"), { scale: 1 }, { scale: 1.25, rotation: 8, transformOrigin: "50% 47%", duration: d, ease: "none", immediateRender: false }, f.t0);
    // the light turns inside a fixed, tilted ellipse (r02: turning the ellipse itself tilted the whole disk)
    tl.fromTo(box.querySelectorAll(".bh-spin"), { rotation: 0 }, { rotation: 360 * d / 3, duration: d, ease: "none", immediateRender: false }, f.t0);
    tl.fromTo(box.querySelector(".bh-glow"), { opacity: 0.6, scale: 0.95 }, { opacity: 1, scale: 1.06, duration: 0.6, yoyo: true, repeat: Math.max(1, Math.floor(d / 0.6)), ease: "sine.inOut", immediateRender: false }, f.t0);
    (f.spec.labels || []).forEach(function (L, k, all) {
      const t = f.t0 + L[0] * d;
      tl.call(function () { label.textContent = L[1]; }, null, t);
      // a hard cut with the shot, then a pop (r09: a crossfade between labels caught mid-way read as muddy)
      tl.fromTo(label, { autoAlpha: 1, scale: 0.85 }, { autoAlpha: 1, scale: 1, duration: 0.2, ease: "back.out(3)", immediateRender: false }, t);
      const next = k + 1 < all.length ? f.t0 + all[k + 1][0] * d : f.t1 - 0.3;
      tl.set(label, { autoAlpha: 0 }, next - 0.01);
    });
    // the presenter is pulled in too (tournament n01): his own cut-out (the matte clip of this silence) is
    // moved into the hole and spirals in on a wider, slower orbit than the victim, stretched at the end
    if (f.spec.presenter) {
      const me = Array.prototype.slice.call(document.querySelectorAll(".fg")).find(function (v) {
        const a = +v.dataset.start, b = a + +v.dataset.duration;
        return a <= f.t0 + 0.05 && b >= f.t1 - 0.05;
      });
      if (me) {
        hole.appendChild(me);
        me.classList.add("bh-me");
        // he starts where he sat (full size, over his own chair as the iris opens on space), is torn off it
        // and flung onto the orbit, then spirals in (n01 i0: a small figure at the edge read as a sticker)
        const n = 28, pull = 0.9, t0 = f.t0 + pull, dur = Math.max(1.5, d * 0.92 - pull), s0 = f.spec.presenter_scale || 0.5;
        const H = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--h")) || 1920;
        gsap.set(me, { xPercent: -50, yPercent: -50, left: 0, top: 0, x: 0, y: H * 0.03, rotation: 0, scaleX: 1, scaleY: 1 });
        const a0 = 2.4, r0 = 700 * 0.6;  // on screen the whole way (n01 i1: the wide orbit left the frame)
        tl.to(me, { x: Math.cos(a0) * r0, y: Math.sin(a0) * 700 * 0.35, scaleX: s0, scaleY: s0, rotation: -8, duration: pull, ease: "power2.in" }, f.t0);
        // he orbits upright (a wobble, never upside down) and stays recognisable; only in the last quarter
        // does he turn to point at the hole and stretch along that line (spaghettification: long and thin
        // toward the hole), then vanish on a flash (n01 i3 review: a spinning streak read as nothing)
        for (let k = 1; k <= n; k++) {
          const u = k / n, ang = 2.4 + u * 2.6 * Math.PI, rad = 700 * Math.pow(1 - u, 1.2) + 4;
          const x = Math.cos(ang) * rad * 0.6, y = Math.sin(ang) * rad * 0.35;
          const late = Math.max(0, (u - 0.72) / 0.28);  // 0 .. 1 over the last 28%
          const toHole = Math.atan2(-y, -x) * 180 / Math.PI - 90;  // his feet toward the hole
          const wob = -8 + 14 * Math.sin(u * 9);
          tl.to(me, { x: x, y: y, rotation: wob + (toHole - wob) * late,
            scaleX: s0 * (1 - 0.15 * u - 0.7 * late), scaleY: s0 * (1 + 2.2 * late * late), duration: dur / n, ease: "none" },
            t0 + dur * Math.pow((k - 1) / n, 0.8));
        }
        tl.to(me, { autoAlpha: 0, duration: 0.1 }, t0 + dur);
        flash(tl, t0 + dur, 0.6);
      }
    }
    if (f.spec.victim) {
      const im = propImage(D, f.spec.victim, f.t0);
      if (im) {
        // inside the hole, so each shot frames him with it
        const v = img(im.src, "bh-victim" + (im.px ? " px" : ""), hole);
        // a spiral in: a wide arc around the hole that tightens, faster near the end; stretched toward it
        const n = 24, t0 = f.t0 + 0.3, dur = Math.max(1.2, d * 0.85);  // stretched on the last label (r09)
        gsap.set(v, { xPercent: -50, yPercent: -50, left: 0, top: 0, x: 380, y: -520, rotation: 0, scaleX: 1, scaleY: 1 });
        for (let k = 1; k <= n; k++) {
          const u = k / n, ang = -1.2 + u * 3.6 * Math.PI, rad = 560 * Math.pow(1 - u, 1.4) + 6;  // flatter: clear of the label (r06)
          const vx = Math.cos(ang) * rad * 0.75, vy = Math.sin(ang) * rad * 0.3 - 20 * (1 - u);
          const late = Math.max(0, (u - 0.7) / 0.3), toHole = Math.atan2(-vy, -vx) * 180 / Math.PI - 90;
          const spin = f.spec.presenter ? 20 * Math.sin(u * 7) : u * 540;  // with the presenter: readable, not a blur
          tl.to(v, { x: vx, y: vy, rotation: f.spec.presenter ? spin + (toHole - spin) * late : spin,
            scaleX: 1 - 0.85 * u * u, scaleY: 1 + 1.6 * u * u, duration: dur / n, ease: "none" }, t0 + dur * Math.pow((k - 1) / n, 0.7));
        }
        tl.to(v, { autoAlpha: 0, duration: 0.12 }, t0 + dur);
        flash(tl, t0 + dur, 0.3);
      }
    }
    tl.to(box, { clipPath: "circle(0% at 50% 50%)", duration: 0.35, ease: "power3.in" }, f.t1 - 0.35);
    tl.set(box, { autoAlpha: 0 }, f.t1);
  }

  // The closing card: a title over the last shot, the winner happy (a crown, a bounce), a credit line.
  function endcard(f, D, tl) {
    const top = document.getElementById("fxtop");
    const box = el("div", "ec-box", top);
    box.innerHTML = '<div class="ec-dim"></div><div class="ec-title"></div><div class="ec-sub"></div><div class="ec-credit"></div>';
    box.querySelector(".ec-title").textContent = f.spec.title || "";
    box.querySelector(".ec-sub").textContent = f.spec.sub || "";
    box.querySelector(".ec-credit").textContent = f.spec.credit || "";
    if (f.spec.cta) {  // a follow line under the subtitle: the card ends on a hook, not a dead frame (r23 reviews)
      const c = el("div", "ec-cta", box);
      c.textContent = f.spec.cta;
      tl.fromTo(c, { autoAlpha: 0, scale: 0.4 }, { autoAlpha: 1, scale: 1, duration: 0.4, ease: "back.out(2.5)", immediateRender: false }, f.t0 + 0.9);
      tl.to(c, { scale: 1.06, duration: 0.45, yoyo: true, repeat: Math.max(1, Math.floor((f.t1 - f.t0 - 1.3) / 0.45)), ease: "sine.inOut" }, f.t0 + 1.3);
    }
    gsap.set(box, { autoAlpha: 0 });
    tl.set(box, { autoAlpha: 1 }, f.t0);
    tl.fromTo(box.querySelector(".ec-dim"), { opacity: 0 }, { opacity: 1, duration: 0.6, ease: "power1.out", immediateRender: false }, f.t0);
    tl.fromTo(box.querySelector(".ec-title"), { autoAlpha: 0, scale: 1.6 }, { autoAlpha: 1, scale: 1, duration: 0.45, ease: "back.out(1.8)", immediateRender: false }, f.t0 + 0.2);
    tl.fromTo(box.querySelector(".ec-sub"), { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.3, immediateRender: false }, f.t0 + 0.6);
    tl.fromTo(box.querySelector(".ec-credit"), { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.25, immediateRender: false }, f.t0 + 0.35);  // readable for the whole card (r15)
    if (f.spec.cat) {
      const im = propImage(D, f.spec.cat, f.t0);
      if (im) {
        const wrap = el("div", "ec-cat", box);
        img(im.src, "ec-cat-img" + (im.px ? " px" : ""), wrap);
        el("div", "ec-crown", wrap).textContent = "👑";
        tl.fromTo(wrap, { autoAlpha: 0, y: 120 }, { autoAlpha: 1, y: 0, duration: 0.45, ease: "back.out(2)", immediateRender: false }, f.t0 + 0.45);
        tl.fromTo(wrap, { rotation: -4 }, { rotation: 4, duration: 0.35, yoyo: true, repeat: Math.max(1, Math.floor((f.t1 - f.t0) / 0.35)), ease: "sine.inOut", immediateRender: false }, f.t0 + 0.9);
      }
    }
    // his ghost (a halo, see-through) rises out of the empty chair and waves goodbye: the card keeps moving
    // to the last frame (reviews: a static 2.5 s end card)
    if (f.spec.ghost) {
      const im = propImage(D, f.spec.ghost, f.t0 - 2);
      if (im) {
        const g = el("div", "ec-ghost", box);
        img(im.src, "ec-ghost-img" + (im.px ? " px" : ""), g);
        el("div", "ec-halo", g);
        gsap.set(g, { autoAlpha: 0 });  // hidden until it rises (it showed early in a forward seek)
        const d = f.t1 - f.t0;
        tl.fromTo(g, { autoAlpha: 0, y: 260 }, { autoAlpha: 0.9, y: -130, duration: d - 0.6, ease: "sine.inOut", immediateRender: false }, f.t0 + 0.6);
        tl.fromTo(g, { x: -30, rotation: -6 }, { x: 30, rotation: 6, duration: 0.6, yoyo: true, repeat: Math.max(1, Math.floor(d / 0.6)), ease: "sine.inOut", immediateRender: false }, f.t0 + 0.6);
      }
    }
  }

  let flashEl = null;
  function flash(tl, t, peak) {
    if (!flashEl) { flashEl = el("div", "fx-flash", document.getElementById("fxtop")); gsap.set(flashEl, { opacity: 0 }); }
    tl.fromTo(flashEl, { opacity: peak === undefined ? 0.85 : peak }, { opacity: 0, duration: 0.3, ease: "power2.out", immediateRender: false }, t);
  }

  // A film look over the frame (variants tournament): letterbox bars, a vignette, moving grain, a flicker, a
  // multiplied tint. Under the captions' layer is not possible here (fxtop is above), so the bars stay thin.
  function look(f, tl, top) {
    const s = f.spec, box = el("div", "fx-look", top);
    gsap.set(box, { autoAlpha: 0 });
    tl.set(box, { autoAlpha: 1 }, f.t0);
    tl.set(box, { autoAlpha: 0 }, f.t1);
    if (s.tint) { const t = el("div", "fx-look-tint", box); t.style.background = s.tint; }
    if (s.vignette) { const v = el("div", "fx-look-vig", box); v.style.opacity = s.vignette; }
    if (s.grain) {
      const g = el("div", "fx-look-grain", box); g.style.opacity = 0.35 * s.grain;
      for (let t = f.t0, k = 0; t < f.t1; t += 1 / 12, k++) tl.set(g, { backgroundPosition: ((k * 73) % 200) + "px " + ((k * 151) % 200) + "px" }, t);
    }
    if (s.flicker) {
      const fl = el("div", "fx-look-flick", box);
      for (let t = f.t0, k = 0; t < f.t1; t += 1 / 8, k++) tl.set(fl, { opacity: s.flicker * 0.12 * (((k * 37) % 7) / 6) }, t);
    }
    if (s.letterbox) {
      ["top", "bottom"].forEach(function (side) {
        const b = el("div", "fx-look-bar", box); b.style[side] = 0; b.style.height = s.letterbox + "px";
        tl.fromTo(b, { scaleY: 0, transformOrigin: side === "top" ? "50% 0%" : "50% 100%" }, { scaleY: 1, duration: 0.5, ease: "power2.out", immediateRender: false }, f.t0);
      });
    }
  }

  // A game HUD in the top left: a label and a value that changes with a pop on its words.
  function hud(f, tl, top) {
    const box = el("div", "fx-hud", top);
    box.innerHTML = '<span class="fx-hud-label"></span><span class="fx-hud-val"></span>';
    box.querySelector(".fx-hud-label").textContent = f.spec.label || "SCORE";
    const val = box.querySelector(".fx-hud-val");
    gsap.set(box, { autoAlpha: 0 });
    tl.fromTo(box, { autoAlpha: 0, y: -30 }, { autoAlpha: 1, y: 0, duration: 0.3, ease: "back.out(2)", immediateRender: false }, f.t0);
    val.textContent = f.spec.start || "";
    (f.steps || []).forEach(function (st) {
      tl.call(function () { val.textContent = st[1]; }, null, st[0]);
      tl.fromTo(val, { scale: 1.6, color: "#ffe14d" }, { scale: 1, color: "#ffffff", duration: 0.35, ease: "back.out(3)", immediateRender: false }, st[0]);
    });
    tl.to(box, { autoAlpha: 0, duration: 0.2 }, f.t1 - 0.2);
  }

  // A comic sound word in a starburst: slams in rotated, shakes, gone (tournament n07)
  function burst2(f, tl, top) {
    const s = f.spec, b = el("div", "fx-burst", top);
    b.innerHTML = '<div class="fx-burst-star"></div><div class="fx-burst-txt"></div>';
    b.querySelector(".fx-burst-txt").textContent = s.text || "POW!";
    if (s.color) b.querySelector(".fx-burst-star").style.background = s.color;
    const at = s.at || [0.5, 0.45];
    Object.assign(b.style, { left: (at[0] * 100) + "%", top: (at[1] * 100) + "%" });
    gsap.set(b, { autoAlpha: 0, xPercent: -50, yPercent: -50 });
    const rot = s.rotation != null ? s.rotation : -12;
    tl.fromTo(b, { autoAlpha: 1, scale: 0.2, rotation: rot - 25 }, { autoAlpha: 1, scale: 1, rotation: rot, duration: 0.18, ease: "back.out(3)", immediateRender: false }, f.t0);
    tl.to(b, { scale: 1.08, duration: 0.08, yoyo: true, repeat: 3, ease: "none" }, f.t0 + 0.2);
    tl.to(b, { autoAlpha: 0, scale: 1.3, duration: 0.15, ease: "power2.in" }, f.t1 - 0.15);
  }

  // A comic page recap: freeze-frames of the presenter's video slam in as tilted panels on paper, each with a
  // caption box, then hold (tournament n07)
  function panels(f, tl, top) {
    const pg = el("div", "fx-page", top);
    gsap.set(pg, { autoAlpha: 0 });
    tl.set(pg, { autoAlpha: 1 }, f.t0);
    const n = f.files.length, caps = f.spec.captions || [];
    const gap = 0.5, H = 1920 * 0.62 / Math.max(1, n);
    f.files.forEach(function (src, k) {
      const p = el("div", "fx-panel", pg);
      Object.assign(p.style, { top: (330 + k * (H + 24)) + "px", height: H + "px" });
      const im = el("img", "fx-panel-img", p); im.src = src; im.draggable = false;  // not a prop asset
      im.style.objectPosition = "50% " + (f.spec.focus_y != null ? f.spec.focus_y : 40) + "%";
      if (caps[k]) { const c = el("div", "fx-panel-cap", p); c.textContent = caps[k]; }
      const rot = (k % 2 ? 1.6 : -1.6);
      gsap.set(p, { autoAlpha: 0 });
      tl.fromTo(p, { autoAlpha: 1, x: (k % 2 ? 1 : -1) * 1200, rotation: rot * 6 }, { autoAlpha: 1, x: 0, rotation: rot, duration: 0.28, ease: "power3.out", immediateRender: false }, f.t0 + 0.15 + k * gap);
      tl.fromTo(pg, { x: 0 }, { x: k % 2 ? 10 : -10, duration: 0.05, yoyo: true, repeat: 1, ease: "none", immediateRender: false }, f.t0 + 0.43 + k * gap);
    });
    tl.set(pg, { autoAlpha: 0 }, f.t1);
  }

  // Words painted on the room's wood (tournament n08): a flat card of stacked letters mapped onto the
  // measured surface (matrix3d), masked to the wood so the gaps between the slats stay dark; in room space,
  // so the cuts and pushes carry it like the wall itself. Each word replaces the last, letter by letter.
  function wall(f, tl) {
    const room = document.getElementById("room-back");
    const b = f.bbox, wrap = el("div", "fx-wall", room);
    Object.assign(wrap.style, { left: b[0] + "px", top: b[1] + "px", width: b[2] + "px", height: b[3] + "px",
      webkitMaskImage: "url(" + f.mask + ")", maskImage: "url(" + f.mask + ")" });
    const card = el("div", "fx-wall-card", wrap);
    Object.assign(card.style, { width: f.card[0] + "px", height: f.card[1] + "px", transform: f.matrix });
    if (f.spec.color) card.style.color = f.spec.color;
    gsap.set(wrap, { autoAlpha: 0 });
    tl.set(wrap, { autoAlpha: 1 }, f.t0);
    tl.set(wrap, { autoAlpha: 0 }, f.t1);
    const steps = f.steps || [];
    steps.forEach(function (st, k) {
      const word = el("div", "fx-wall-word", card);
      const n = st[1].length;
      word.style.fontSize = Math.min(f.card[0] * 0.95, f.card[1] / Math.max(n, 1) * 0.92) + "px";
      const ls = st[1].split("").map(function (ch) { const s = el("span", "fx-wall-l", word); s.textContent = ch; return s; });
      gsap.set(ls, { autoAlpha: 0 });
      ls.forEach(function (s, j) {  // painted down the slats, a letter at a time
        tl.fromTo(s, { autoAlpha: 0, scaleY: 0.2, transformOrigin: "50% 0%" }, { autoAlpha: 1, scaleY: 1, duration: 0.12, ease: "power2.out", immediateRender: false }, st[0] + j * 0.07);
      });
      // a word fades after hold_s (n08 review: one word sat on the wall through three sentences)
      const next = Math.min(k + 1 < steps.length ? steps[k + 1][0] : f.t1, st[0] + (f.spec.hold_s || 99));
      tl.to(ls, { autoAlpha: 0, duration: 0.2 }, next - 0.2);
    });
  }

  // A second presenter (tournament n03): his own cut-out from another moment, placed beside him; it
  // materialises with a scan of light and leaves the same way; spec label tags it.
  function clone(f, tl) {
    const v = document.getElementById(f.clone_id);
    if (!v) return;
    gsap.set(v, { autoAlpha: 0 });
    tl.fromTo(v, { autoAlpha: 0, clipPath: "inset(0 0 100% 0)" }, { autoAlpha: 0.92, clipPath: "inset(0 0 0% 0)", duration: 0.45, ease: "power2.out", immediateRender: false }, f.t0);
    tl.to(v, { autoAlpha: 0, clipPath: "inset(100% 0 0 0)", duration: 0.35, ease: "power2.in" }, f.t1 - 0.35);
    if (f.spec.label) {
      const tag = el("div", "fx-clone-tag", document.getElementById("fxtop"));
      tag.textContent = f.spec.label;
      // over the clone's head, kept inside the frame (n03 i0: it ran off the right edge)
      Object.assign(tag.style, { left: Math.min(78, (0.5 + (f.spec.dx || 0.4)) * 100) + "%", top: (f.spec.label_y || 0.3) * 100 + "%" });
      gsap.set(tag, { autoAlpha: 0, xPercent: -50 });
      tl.fromTo(tag, { autoAlpha: 1, scale: 0 }, { autoAlpha: 1, scale: 1, duration: 0.3, ease: "back.out(2.5)", immediateRender: false }, f.t0 + 0.4);
      tl.to(tag, { autoAlpha: 0, duration: 0.2 }, f.t1 - 0.3);
    }
  }

  function fxAll(D, tl) {
    filters(D, tl);
    const top = document.getElementById("fxtop");
    D.fx.forEach(function (f) {
      if (f.kind === "anime") anime(f, D, tl);
      if (f.kind === "blocky") blocky(f, D, tl);
      if (f.kind === "alchemy") alchemy(f, D, tl);
      if (f.kind === "automail") automail(f, D, tl);
      if (f.kind === "blackhole") blackhole(f, D, tl);
      if (f.kind === "endcard") endcard(f, D, tl);
      if (f.kind === "rewind") {  // a VHS rewind from the flash-forward back to the start: scanlines, a jitter, the label
        const r = el("div", "fx-rewind", top);
        r.innerHTML = '<div class="fx-rw-band"></div><div class="fx-rw-label">◀◀ REWIND</div>';
        gsap.set(r, { autoAlpha: 0 });
        tl.set(r, { autoAlpha: 1 }, f.t0);
        tl.fromTo(r.querySelector(".fx-rw-band"), { top: "85%" }, { top: "5%", duration: f.t1 - f.t0, ease: "none", immediateRender: false }, f.t0);
        tl.set(r, { autoAlpha: 0 }, f.t1);
        for (let k = 0, t = f.t0; t < f.t1; k++, t += 0.05) tl.set("#punch", { x: (k % 2 ? -1 : 1) * (14 + (k * 7) % 11), skewX: (k % 3 - 1) * 4, filter: "saturate(1.6) hue-rotate(" + ((k * 37) % 40 - 20) + "deg)" }, t);
        tl.set("#punch", { x: 0, skewX: 0, filter: "none" }, f.t1);
        flash(tl, f.t1, 0.5);
      }
      if (f.kind === "look") look(f, tl, top);
      if (f.kind === "comic") {  // halftone dots over the frame while the presenter is drawn as a comic
        // on the presenter only (over captions and cards the dots dimmed them: n07 i0)
        const face = document.getElementById("face");
        const h = el("div", "fx-halftone", face.parentNode); face.parentNode.insertBefore(h, face.nextSibling);
        gsap.set(h, { autoAlpha: 0 });
        tl.set(h, { autoAlpha: 1 }, f.t0); tl.set(h, { autoAlpha: 0 }, f.t1);
      }
      if (f.kind === "burst") burst2(f, tl, top);
      if (f.kind === "panels") panels(f, tl, top);
      if (f.kind === "wall") wall(f, tl);
      if (f.kind === "clone") clone(f, tl);
      if (f.kind === "freeze") {  // bullet time: the clip shows only for its span, with a flash in and out
        const v = document.getElementById(f.media_id);
        if (v) { gsap.set(v, { autoAlpha: 0 }); tl.set(v, { autoAlpha: 1 }, f.t0); tl.set(v, { autoAlpha: 0 }, f.t1); }
        tl.set("#stage", { zIndex: 7 }, f.t0); tl.set("#stage", { zIndex: 5 }, f.t1);  // live captions over it
        flash(tl, f.t0, 0.5); flash(tl, f.t1, 0.35);
      }
      if (f.kind === "hud") hud(f, tl, top);
      if (f.kind === "flash") flash(tl, f.t0);
      if (f.kind === "shake") {
        const amp = f.spec.amp || 18;
        for (let k = 0; k < 8; k++) tl.to("#punch", { x: (k % 2 ? -1 : 1) * amp * (1 - k / 8), y: ((k * 7) % 3 - 1) * amp * 0.5, duration: 0.04, ease: "none" }, f.t0 + k * 0.04);
        tl.to("#punch", { x: 0, y: 0, duration: 0.06 }, f.t0 + 0.32);
      }
      if (f.kind === "glitch") {
        const bars = [];
        for (let k = 0; k < 6; k++) { const b = el("div", "fx-glitch", top); b.style.top = (180 + k * 270) + "px"; b.style.background = k % 2 ? "rgba(255,0,90,.55)" : "rgba(0,230,255,.55)"; bars.push(b); gsap.set(b, { autoAlpha: 0 }); }
        bars.forEach(function (b, k) { tl.set(b, { autoAlpha: 1, x: (k % 2 ? -1 : 1) * 60 }, f.t0 + k * 0.03); tl.set(b, { autoAlpha: 0 }, f.t0 + 0.12 + k * 0.03); });
        tl.to("#punch", { skewX: 8, duration: 0.05, yoyo: true, repeat: 3 }, f.t0);
        tl.set("#punch", { skewX: 0 }, f.t0 + 0.25);
      }
      if (f.kind === "fade_black") {
        const b = el("div", "fx-black", top); gsap.set(b, { opacity: 0 });
        tl.to(b, { opacity: 1, duration: Math.max(0.2, f.t1 - f.t0), ease: "power1.in" }, f.t0);
      }
      if (f.kind === "caption_font") {
        const fam = D.fonts[f.spec.family] || f.spec.family || D.fonts.heading;
        const was = getComputedStyle(document.documentElement).getPropertyValue("--font");
        tl.set("#stage", { "--font": fam }, f.t0);
        if (f.spec.hue) tl.set("#stage", { filter: "hue-rotate(" + f.spec.hue + "deg)" }, f.t0);
        tl.set("#stage", { "--font": was }, f.t1);
        if (f.spec.hue) tl.set("#stage", { filter: "none" }, f.t1);
        if (f.spec.accent) {  // the brand accent (spoken words, tags, cards) becomes this colour, then back.
          // On #canvas, the parent of captions, props and widgets alike (#stage reached captions only: audit)
          const st = getComputedStyle(document.getElementById("canvas"));
          const was2 = { "--cap-active": st.getPropertyValue("--cap-active").trim() || D.active, "--accent": st.getPropertyValue("--accent").trim() };
          tl.set("#canvas", { "--cap-active": f.spec.accent, "--accent": f.spec.accent }, f.t0);
          tl.set("#canvas", was2, f.t1);
        }
      }
    });
  }

  const EYE = '<svg viewBox="0 0 100 120" width="100%" height="100%"><defs><radialGradient id="ir" cx="50%" cy="60%" r="60%">' +
    '<stop offset="0" stop-color="#7fd1ff"/><stop offset=".55" stop-color="#3a6cf0"/><stop offset="1" stop-color="#1b1f5e"/></radialGradient></defs>' +
    '<ellipse cx="50" cy="66" rx="44" ry="50" fill="#fff"/><ellipse cx="50" cy="70" rx="34" ry="44" fill="url(#ir)"/>' +
    '<ellipse cx="50" cy="74" rx="16" ry="22" fill="#0d0f2b"/><ellipse cx="36" cy="50" rx="13" ry="15" fill="#fff"/>' +
    '<circle cx="64" cy="92" r="6" fill="#fff"/><path d="M2 40 Q50 0 98 40 L98 30 Q50 -10 2 30Z" fill="#1a1020"/>' +
    '<path d="M86 30 L100 14 L94 36Z M78 22 L88 4 L86 28Z" fill="#1a1020"/></svg>';

  window.PROPS = {
    play: function (D, tl) {
      if (!D.rooms) return;
      rooms(D, tl);
      // the matte cut-out shows only while something is behind the presenter
      if (D.matte) {
        const fg = document.querySelectorAll(".fg");
        gsap.set(fg, { autoAlpha: 0 });
        D.fg_spans.forEach(function (s, k) { tl.set(fg[k], { autoAlpha: 1 }, s[0]); tl.set(fg[k], { autoAlpha: 0 }, s[1]); });
      }
      (D.props || []).forEach(function (P) { prop(P, D, tl); });
      fxAll(D, tl);
    },
  };
})();
