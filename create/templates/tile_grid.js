// frames: landscape  (laid out for 1920x1080; a vertical layout is a separate milestone)
// Tile grid: the first tile appears and steps back, the hero tile pops large, others join with chips,
// then one marker lands across the tiles.
function render(root, D, tl, K) {
  const S = D.slots;
  K.chrome(root);
  const stage = K.el("div", "stage", root);
  stage.style.gap = "40px";
  stage.style.justifyContent = "flex-start";
  stage.style.paddingTop = "40px";
  if (S.caption) K.inUp(tl, K.el("div", "headline", stage, S.caption), K.cue("caption"));
  const grid = K.el("div", "", stage);
  Object.assign(grid.style, { display: "grid", gridTemplateColumns: "0.75fr 1.35fr 1fr 1fr", gap: "32px", alignItems: "end" });
  const chips = S.status_chip || [];
  const others = S.tiles.filter((t) => t !== S.hero_tile && t !== S.tiles[0]);
  const tile = (name, big) => {
    const c = K.el("div", "card col", grid);
    Object.assign(c.style, { gap: "20px", minHeight: big ? "460px" : "360px", justifyContent: "flex-end" });
    const mono = K.el("div", "", c, name[0]);
    Object.assign(mono.style, { width: big ? "88px" : "64px", height: big ? "88px" : "64px", borderRadius: "18px",
      background: "var(--chip)", display: "grid", placeItems: "center",
      font: "700 " + (big ? 44 : 32) + "px var(--font-heading)" });
    K.el("div", "headline", c, name).style.fontSize = big ? "56px" : "36px";
    return c;
  };
  const first = tile(S.tiles[0], false);
  const tT = K.cues("tiles");
  K.inUp(tl, first, tT[0] ?? 0, { duration: K.M.card, y: 40 });
  tl.to(first, { opacity: 0.45, scale: 0.92, duration: K.M.card, ease: K.M.ease_out }, (tT[0] ?? 0) + 1.2);
  const hero = tile(S.hero_tile, true);
  K.pop(tl, hero, K.cue("hero_tile"), { duration: K.M.card });
  const tC = K.cues("status_chip");
  others.forEach((name, i) => {
    const c = tile(name, false);
    if (chips[i]) {
      const ch = K.el("span", "chip", c, chips[i]);
      ch.style.alignSelf = "flex-start";
    }
    K.inUp(tl, c, tC[i] ?? K.cue("hero_tile") + 1 + i, { duration: K.M.card, y: 40 });
  });
  const marker = K.el("div", "chip brand", stage, "Show up here next");
  Object.assign(marker.style, { alignSelf: "center", fontSize: "var(--body-size)", padding: "14px 28px" });
  K.pop(tl, marker, tT[1] ?? (tC[tC.length - 1] ?? 0) + 1.5);
}
