// frames: landscape  (laid out for 1920x1080; a vertical layout is a separate milestone)
// Cards triptych: three cards rise left to right on their cue words; the last one carries the accent.
function render(root, D, tl, K) {
  const S = D.slots;
  K.chrome(root);
  const stage = K.el("div", "stage", root);
  stage.style.gap = "56px";
  if (D.title) K.inUp(tl, K.el("div", "label", stage, D.title), K.cue("layout"));
  const row = K.el("div", "row", stage);
  Object.assign(row.style, { gap: "36px", alignItems: "stretch" });
  const icons = ["≡", "→", "✓"];  // report lines, link arrow, check (glyphs checked in tokens)
  const tc = K.cues("cards");
  S.cards.forEach((text, i) => {
    const last = i === S.cards.length - 1;
    const c = K.el("div", "card col", row);
    Object.assign(c.style, { flex: "1", gap: "28px", minHeight: "360px", padding: "48px",
      boxShadow: last ? "inset 0 0 0 3px var(--accent), var(--card-shadow)" : "" });
    const ic = K.el("div", "", c, icons[i] || "");
    Object.assign(ic.style, { width: "88px", height: "88px", borderRadius: "22px", display: "grid", placeItems: "center",
      font: "700 48px var(--font-body)", background: last ? "var(--accent-fill)" : "var(--chip)",
      color: last ? "var(--surface)" : "var(--ink)" });
    if (S.card_labels && S.card_labels[i]) K.el("div", "label", c, S.card_labels[i]);
    K.el("div", "headline", c, text).style.fontSize = "56px";
    K.inUp(tl, c, tc[i] ?? 1 + i, { duration: K.M.card, y: 120 });
    if (last) K.pop(tl, ic, (tc[i] ?? 1 + i) + 0.3);
  });
}
