// frames: landscape  (laid out for 1920x1080; a vertical layout is a separate milestone)
// App icon orbit: the product mark in the centre, the apps it covers orbiting in, a status badge below.
function render(root, D, tl, K) {
  const S = D.slots;
  K.chrome(root);
  const stage = K.el("div", "stage", root);
  stage.style.alignItems = "center";
  const ring = K.el("div", "", stage);
  Object.assign(ring.style, { position: "relative", width: "1100px", height: "420px", marginTop: "60px" });
  const hub = K.logo(ring, 120);
  Object.assign(hub.style, { position: "absolute", left: "50%", top: "50%", transform: "translate(-50%, -50%)" });
  tl.fromTo(hub, { opacity: 0, scale: 0.85 }, { opacity: 1, scale: 1, duration: K.M.card, ease: K.M.ease_out }, K.cue("hub"));
  const n = S.icons.length;
  const times = K.cues("icons");
  S.icons.forEach((name, i) => {
    const a = Math.PI + (i * Math.PI) / Math.max(1, n - 1);  // left, top, right across the upper arc
    const x = Math.cos(a) * 440, y = Math.sin(a) * 150;
    const chip = K.el("div", "card row", ring);
    Object.assign(chip.style, { position: "absolute", left: "50%", top: "50%", padding: "18px 30px", gap: "14px" });
    const dot = K.el("span", "", chip);
    Object.assign(dot.style, { width: "44px", height: "44px", borderRadius: "50%", background: "var(--chip)",
      display: "grid", placeItems: "center", font: "700 22px var(--font-heading)" });
    dot.textContent = name[0];
    K.el("span", "strong", chip, name);
    tl.set(chip, { xPercent: -50, yPercent: -50 }, 0);
    tl.fromTo(chip, { x: 0, y: 0, opacity: 0, scale: 0.6 },
      { x, y, opacity: 1, scale: 1, duration: K.M.card, ease: K.M.ease_overshoot }, times[i] ?? K.cue("hub") + 1 + i * 0.4);
  });
  const foot = K.el("div", "col", stage);
  Object.assign(foot.style, { alignItems: "center", gap: "20px", marginTop: "8px" });
  if (S.status_badge) {
    const b = K.el("div", "chip", foot);
    const d = K.el("span", "", b);
    Object.assign(d.style, { width: "12px", height: "12px", borderRadius: "50%", background: "var(--success)" });
    b.appendChild(document.createTextNode(S.status_badge));
    K.pop(tl, b, K.cue("status_badge"));
  }
  if (S.caption) K.inUp(tl, K.el("div", "body muted", foot, S.caption), K.cue("caption"));
}
