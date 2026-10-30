// frames: landscape  (laid out for 1920x1080; a vertical layout is a separate milestone)
// Prompt input card: your question types in, suggestions append, then personas get different short lists.
function render(root, D, tl, K) {
  const S = D.slots;
  K.chrome(root);
  K.example(root);
  const stage = K.el("div", "stage", root);
  stage.style.gap = "36px";
  stage.style.justifyContent = "flex-start";
  stage.style.paddingTop = "40px";
  const title = K.el("div", "headline", stage, S.greeting || "");
  K.inUp(tl, title, K.cue("greeting"));
  const body = K.el("div", "row", stage);
  Object.assign(body.style, { alignItems: "flex-start", gap: "40px" });
  const listCard = K.el("div", "card col", body);
  Object.assign(listCard.style, { width: "1080px", gap: "16px" });
  const row = (text, chipText, chipCls) => {
    const r = K.el("div", "row", listCard);
    Object.assign(r.style, { justifyContent: "space-between", padding: "14px 20px", borderRadius: "12px",
      background: "var(--fill-subtle)", gap: "24px" });
    const t = K.el("span", "body", r, text);
    t.style.minWidth = "0";
    K.el("span", "chip " + chipCls, r, chipText);
    return [r, t];
  };
  const [first, firstText] = row(S.prompt_text, D.strings.own_prompt, "outline");
  const tq = K.cue("prompt_text");
  K.inUp(tl, first, tq - 0.2, { y: 20, duration: K.M.text });
  tl.fromTo(firstText, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 1.3, ease: "none" }, tq);
  const sug = (S.preset_menu || []).map((q) => row(q, D.strings.suggested_prompt, "brand")[0]);
  K.inUp(tl, sug, K.cue("preset_menu"), { y: 20, stagger: 0.3 });
  const people = (S.context_ui && S.context_ui.personas) || [];
  const side = K.el("div", "col", body);
  side.style.gap = "20px";
  const t3 = K.cues("context_ui");
  people.forEach((p, i) => {
    const c = K.el("div", "card col", side);
    Object.assign(c.style, { width: "540px", gap: "10px", padding: "24px 32px" });
    const h = K.el("div", "row", c);
    h.style.justifyContent = "space-between";
    K.el("span", "label", h, D.strings.asked_as);
    K.el("span", "chip", h, p.name);
    p.list.forEach((b, j) => {
      const line = K.el("div", "row body", c);
      line.style.gap = "16px";
      K.el("span", "muted strong", line, String(j + 1)).style.width = "24px";
      K.el("span", b === D.strings.own_brand ? "strong accent" : "strong", line, b);
    });
    K.inUp(tl, c, t3[i + 1] ?? (t3[0] ?? 0) + 1 + i, { duration: K.M.card, y: 50 });
  });
}
