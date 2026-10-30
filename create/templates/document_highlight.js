// frames: landscape  (laid out for 1920x1080; a vertical layout is a separate milestone)
// Document highlight: an AI answer; brands light up in the order named, the sentiment phrase underlines,
// and topic tags slide out with their scores.
function render(root, D, tl, K) {
  const S = D.slots, doc = S.document;
  K.chrome(root);
  K.example(root);
  const stage = K.el("div", "stage", root);
  stage.style.gap = "36px";
  stage.style.justifyContent = "flex-start";
  stage.style.paddingTop = "40px";
  if (D.title) K.inUp(tl, K.el("div", "headline", stage, D.title), K.cue("document"));
  const body = K.el("div", "row", stage);
  Object.assign(body.style, { alignItems: "flex-start", gap: "48px" });
  const card = K.el("div", "card col", body);
  Object.assign(card.style, { width: "1060px", gap: "24px" });
  K.el("span", "chip", card, doc.engine).style.alignSelf = "flex-start";
  const p = K.el("p", "body", card);
  p.style.fontSize = "36px";
  p.style.lineHeight = "1.55";
  // Wrap brand names and the sentiment phrase so they can be highlighted.
  let html = doc.text.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);
  html = html.replace(doc.sentiment_phrase, '<span class="sent">' + doc.sentiment_phrase + "</span>");
  doc.brands.forEach((b, i) => { html = html.replace(b, '<span class="brand" data-i="' + i + '">' + b + "</span>"); });
  p.innerHTML = html;
  K.inUp(tl, card, K.cue("document") + 0.2, { duration: K.M.card, y: 60 });
  const brands = [...p.querySelectorAll(".brand")].sort((a, b) => a.dataset.i - b.dataset.i);
  const tB = K.cue("focus_regions", 0), tS = K.cue("focus_regions", 1, tB + 2);
  brands.forEach((b, i) => {
    const mine = b.textContent === doc.your_brand;
    Object.assign(b.style, { fontWeight: "600", borderRadius: "8px", padding: "2px 10px 2px 4px", whiteSpace: "nowrap" });
    const badge = document.createElement("span");
    badge.textContent = String(i + 1);
    b.insertBefore(badge, b.firstChild);
    Object.assign(badge.style, { display: "inline-grid", placeItems: "center", width: "34px", height: "34px",
      marginRight: "8px", verticalAlign: "3px", borderRadius: "50%", font: "700 20px var(--font-body)",
      background: mine ? "var(--accent-fill)" : "var(--ink)", color: "var(--surface)" });
    const t = tB + i * 0.45;
    tl.fromTo(b, { backgroundColor: "rgba(0,0,0,0)" }, { backgroundColor: mine ? "var(--accent-tint)" : "var(--chip)", duration: K.M.highlight, ease: K.M.ease_out }, t);
    K.pop(tl, badge, t + 0.1);
  });
  const sent = p.querySelector(".sent");
  if (sent) {
    sent.style.backgroundImage = "linear-gradient(var(--accent-text), var(--accent-text))";
    sent.style.backgroundRepeat = "no-repeat";
    sent.style.backgroundPosition = "0 100%";
    tl.fromTo(sent, { backgroundSize: "0% 4px" }, { backgroundSize: "100% 4px", duration: K.M.draw, ease: K.M.ease_out }, tS);
  }
  const side = K.el("div", "col", body);
  Object.assign(side.style, { gap: "20px", paddingTop: "40px" });
  K.inUp(tl, K.el("div", "label", side, "Sentiment by topic"), K.cue("tags", 0, tS + 1));
  const tt = K.cues("tags");
  (S.tags || []).forEach((tag, i) => {
    const m = tag.match(/^([^:]+):\s*([\d.]+)\/10\s*(.*)$/) || [null, tag, "0", ""];
    const c = K.el("div", "card col", side);
    Object.assign(c.style, { width: "520px", padding: "24px 30px", gap: "14px" });
    const h = K.el("div", "row", c);
    h.style.justifyContent = "space-between";
    K.el("span", "strong", h, m[1]);
    K.el("span", "strong", h, m[2] + "/10");
    const track = K.el("div", "", c);
    Object.assign(track.style, { height: "14px", borderRadius: "7px", background: "var(--fill-subtle)", overflow: "hidden" });
    const fill = K.el("div", "", track);
    Object.assign(fill.style, { height: "100%", width: (parseFloat(m[2]) * 10) + "%", borderRadius: "7px",
      background: parseFloat(m[2]) >= 7 ? "var(--success)" : "var(--ink-muted)", transformOrigin: "left center" });
    K.el("span", "caption", c, m[3]);
    const t = tt[i + 1] ?? (tt[0] ?? tS + 1) + 0.5 + i;
    K.inUp(tl, c, (tt[0] ?? t - 0.5) + i * 0.25, { y: 30 });
    tl.fromTo(fill, { scaleX: 0 }, { scaleX: 1, duration: K.M.card, ease: K.M.ease_out }, t);
  });
}
