// frames: landscape  (laid out for 1920x1080; a vertical layout is a separate milestone)
// Chat demo panel: an AI answer card; the question types in, ranked answers stagger in, one row is ours.
function render(root, D, tl, K) {
  const S = D.slots;
  K.chrome(root);
  K.example(root);
  const stage = K.el("div", "stage", root);
  stage.style.alignItems = "center";
  const card = K.el("div", "card col", stage);
  Object.assign(card.style, { width: "1240px", gap: "28px" });
  const head = K.el("div", "row", card);
  head.style.justifyContent = "space-between";
  K.el("span", "chip", head, (S.panel_chrome || "ChatGPT").split(" ")[0]);
  K.el("span", "label", head, "Answer");
  const prompt = K.el("div", "body muted", card);
  Object.assign(prompt.style, { background: "var(--fill-subtle)", borderRadius: "16px", padding: "20px 28px",
    whiteSpace: "nowrap", overflow: "hidden" });
  const typed = K.el("span", "", prompt, "“" + S.messages[0] + "”");
  typed.style.display = "inline-block";
  const list = K.el("div", "col", card);
  list.style.gap = "14px";
  const rows = S.answer_body.map((line) => {
    const m = line.match(/^(\d+)\s+([^:]+):?\s*(.*)$/) || [null, "", line, ""];
    const r = K.el("div", "row", list);
    Object.assign(r.style, { gap: "20px", padding: "10px 16px", borderRadius: "12px", position: "relative" });
    K.el("span", "strong muted", r, m[1]).style.width = "32px";
    K.el("span", "strong", r, m[2]);
    if (m[3]) K.el("span", "body muted", r, m[3]);
    return r;
  });
  const ours = rows[rows.length - 1];
  const ring = K.el("div", "", ours);
  Object.assign(ring.style, { position: "absolute", inset: "0", borderRadius: "12px",
    boxShadow: "inset 0 0 0 3px var(--accent)", background: "var(--accent-tint)", zIndex: "-1" });
  ours.style.zIndex = "0";
  ours.children[1].classList.add("accent");

  K.inUp(tl, card, K.cue("panel_chrome"), { duration: K.M.card, y: 80 });
  const tq = K.cue("messages");
  tl.fromTo(typed, { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 1.2, ease: "none" }, tq);
  const rt = K.cues("answer_body");
  K.inUp(tl, rows.slice(0, -1), rt[0] ?? tq + 1.5, { stagger: 0.22, y: 24 });
  if (rt[1] !== undefined) tl.fromTo(rows.slice(-2, -1), { scale: 1 }, { scale: 1.04, duration: 0.25, yoyo: true, repeat: 1, ease: K.M.ease_out }, rt[1]);
  const tOurs = rt[2] ?? rt[rt.length - 1];
  K.inUp(tl, ours, tOurs, { y: 24 });
  tl.fromTo(ring, { opacity: 0 }, { opacity: 1, duration: K.M.text, ease: K.M.ease_out }, tOurs + 0.2);
}
