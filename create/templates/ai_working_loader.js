// frames: landscape  (laid out for 1920x1080; a vertical layout is a separate milestone)
// AI working loader: a browser window opens each app in turn, then settles on the answer a customer sees.
function render(root, D, tl, K) {
  const S = D.slots;
  K.chrome(root);
  const stage = K.el("div", "stage", root);
  stage.style.gap = "36px";
  stage.style.justifyContent = "flex-start";
  stage.style.paddingTop = "40px";
  K.inUp(tl, K.el("div", "headline", stage, S.status_label), K.cue("status_label"));
  const win = K.el("div", "card", stage);
  Object.assign(win.style, { width: "1300px", alignSelf: "center", padding: "0", overflow: "hidden" });
  const bar = K.el("div", "row", win);
  Object.assign(bar.style, { padding: "18px 24px", borderBottom: "var(--hair) solid var(--hairline)", gap: "12px" });
  for (let i = 0; i < 3; i++) {
    const d = K.el("span", "", bar);
    Object.assign(d.style, { width: "14px", height: "14px", borderRadius: "50%", background: "var(--chip)" });
  }
  const url = K.el("div", "caption", bar);
  Object.assign(url.style, { marginLeft: "20px", flex: "1", background: "var(--fill-subtle)", borderRadius: "10px",
    padding: "8px 18px", position: "relative", height: "40px" });
  const body = K.el("div", "col", win);
  Object.assign(body.style, { padding: "40px 56px", gap: "18px", height: "420px" });
  const tWin = K.cue("working_icon");
  K.inUp(tl, win, tWin, { duration: K.M.card, y: 60 });
  // Status cycles through the apps between the cycle cue and the result cue.
  const states = S.status_cycle || [];
  const t0 = K.cue("status_cycle", 0, tWin + 0.5), t1 = K.cue("result_view", 0, t0 + 3);
  const step = (t1 - t0) / Math.max(1, states.length);
  const spinRow = K.el("div", "row", body);
  spinRow.style.gap = "18px";
  const spin = K.el("span", "", spinRow);
  Object.assign(spin.style, { width: "30px", height: "30px", borderRadius: "50%", border: "4px solid var(--chip)",
    borderTopColor: "var(--ink)" });
  const status = K.el("div", "", spinRow);
  Object.assign(status.style, { position: "relative", height: "44px", width: "700px" });
  tl.fromTo(spin, { rotation: 0 }, { rotation: 360 * Math.ceil(t1 - t0), duration: t1 - t0, ease: "none" }, t0);
  states.forEach((s, i) => {
    const lab = K.el("div", "strong", status, s + "…");
    Object.assign(lab.style, { position: "absolute", left: "0", top: "0", opacity: "0" });
    const app = s.replace(/^Opening\s+/, "");
    const u = K.el("span", "", url, "https://" + app.toLowerCase() + (app === "ChatGPT" ? ".com" : app === "Gemini" ? ".google.com" : ".ai"));
    Object.assign(u.style, { position: "absolute", left: "18px", top: "8px", opacity: "0" });
    const t = t0 + i * step;
    tl.fromTo([lab, u], { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.3, ease: K.M.ease_out }, t);
    if (i < states.length - 1) tl.to([lab, u], { opacity: 0, y: -16, duration: 0.25, ease: K.M.ease_in }, t + step - 0.25);
    else tl.to(spinRow, { opacity: 0, duration: 0.25 }, t1 - 0.1);
  });
  // The finished answer, drawn as the app shows it: lines of text, one chip naming the source.
  const ans = K.el("div", "col", body);
  ans.style.gap = "16px";
  const widths = [96, 88, 92, 60];
  const lines = widths.map((w) => {
    const l = K.el("div", "", ans);
    Object.assign(l.style, { height: "22px", width: w + "%", background: "var(--chip)", borderRadius: "8px" });
    return l;
  });
  const cap = K.el("div", "caption", ans, S.result_view);
  cap.style.marginTop = "14px";
  K.inUp(tl, lines, t1, { y: 12, stagger: 0.08 });
  K.inUp(tl, cap, t1 + 0.4, { y: 12 });
}
