// frames: landscape  (laid out for 1920x1080; a vertical layout is a separate milestone)
// Kinetic statement card: a headline builds word by word; one word takes the accent; options cycle below.
function render(root, D, tl, K) {
  const S = D.slots;
  K.chrome(root);
  const stage = K.el("div", "stage", root);
  const h = K.el("h1", "display", stage);
  h.style.maxWidth = "1500px";
  const spans = K.words(h, S.headline);
  const emph = spans.find((s) => S.emphasis_word && s.textContent.replace(/[.,!?]/g, "") === S.emphasis_word);
  let bar = null;
  if (emph) {
    emph.style.position = "relative";
    bar = K.el("span", "", emph.parentNode);
    Object.assign(bar.style, { position: "absolute", left: "0", right: "0", bottom: "0.08em", height: "0.22em",
      background: "var(--accent-tint)", zIndex: "-1", transformOrigin: "left center" });
    emph.parentNode.style.position = "relative";
    emph.parentNode.style.zIndex = "0";
  }
  K.inUp(tl, spans, K.cue("headline"), { y: "110%", stagger: K.M.word_stagger, duration: K.M.text });
  if (emph) {
    const t = K.cue("emphasis_word");
    tl.to(emph, { color: "var(--accent)", duration: K.M.text, ease: K.M.ease_out }, t);
    tl.fromTo(bar, { scaleX: 0 }, { scaleX: 1, duration: K.M.draw, ease: K.M.ease_out }, t);
  }
  const opts = S.cycling_options || [];
  if (opts.length) {
    const slot = K.el("div", "", stage);
    Object.assign(slot.style, { position: "relative", height: "96px", marginTop: "72px" });
    const times = K.cues("cycling_options");
    opts.forEach((text, i) => {
      const q = K.el("div", "card strong", slot, "“" + text + "”");
      Object.assign(q.style, { position: "absolute", left: "0", top: "0", padding: "20px 36px", opacity: "0" });
      const t = times[i] ?? (times[times.length - 1] ?? 0) + i;
      K.inUp(tl, q, t, { duration: K.M.card });
      if (i < opts.length - 1) {
        const next = times[i + 1] ?? t + 1;
        tl.to(q, { y: -40, opacity: 0, duration: K.M.text, ease: K.M.ease_in }, next - K.M.text * 0.6);
      }
    });
  }
}
