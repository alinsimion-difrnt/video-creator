// frames: landscape  (laid out for 1920x1080; a vertical layout is a separate milestone)
// Logo close: the logo resolves, the tagline and the address follow; the frame holds to the end.
function render(root, D, tl, K) {
  const S = D.slots;
  const stage = K.el("div", "stage", root);
  Object.assign(stage.style, { alignItems: "center", gap: "48px" });
  const mark = K.logo(stage, 200);
  tl.fromTo(mark, { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: K.M.card, ease: K.M.ease_out }, K.cue("logo_mark"));
  if (S.tagline) K.inUp(tl, K.el("div", "headline", stage, S.tagline), K.cue("tagline"));
  if (S.url_or_price) K.inUp(tl, K.el("div", "strong muted", stage, S.url_or_price), K.cue("url_or_price"));
}
