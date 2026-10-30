// Shared runtime for scene templates. Each template defines `render(root, D, tl, K)`.
// D = { scene, duration, title, slots, cues: [{t, target, do}], example_data, accent, motion, logo, brand,
//       strings }  (strings: the brand's UI copy, video.yaml)
// Cue times are seconds from the scene's start, taken from the narration's word timings (never guessed).
const K = (() => {
  const D = JSON.parse(document.getElementById("scene-data").textContent);
  const M = D.motion;
  const el = (tag, cls, parent, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  };
  // n-th cue aimed at a slot (0-based); falls back to `fallback` seconds when the storyboard has none.
  const cue = (target, n = 0, fallback = 0) => {
    const list = D.cues.filter((c) => c.target === target);
    return list.length > n ? list[n].t : (list.length ? list[list.length - 1].t : fallback);
  };
  const cues = (target) => D.cues.filter((c) => c.target === target).map((c) => c.t);
  // Split text into word spans inside overflow masks, for a word-by-word reveal.
  const words = (parent, text, cls) => text.split(/(\s+)/).filter((w) => w.length).map((w) => {
    if (/^\s+$/.test(w)) { parent.appendChild(document.createTextNode(" ")); return null; }
    const mask = el("span", "mask", parent);
    return el("span", "word" + (cls ? " " + cls : ""), mask, w);
  }).filter(Boolean);
  const inUp = (tl, targets, t, opts = {}) => tl.fromTo(targets, { y: opts.y ?? 40, opacity: 0 },
    { y: 0, opacity: 1, duration: opts.duration ?? M.text, ease: opts.ease ?? M.ease_out, stagger: opts.stagger ?? 0 }, t);
  const pop = (tl, targets, t, opts = {}) => tl.fromTo(targets, { scale: 0.6, opacity: 0 },
    { scale: 1, opacity: 1, duration: opts.duration ?? M.chip, ease: M.ease_overshoot, stagger: opts.stagger ?? 0 }, t);
  const logo = (parent, height, variant = "primary") => {
    const box = el("div", "logo", parent);
    box.innerHTML = D.logo[variant];
    box.style.height = height + "px";
    return box;
  };
  const chrome = (root) => {
    const c = el("div", "chrome", root);
    el("div", "label", c, D.brand.name);
    el("div", "label", c, D.brand.host);
    return c;
  };
  const example = (root) => (D.example_data ? el("div", "label example", root, D.strings.example_data) : null);
  return { D, M, el, cue, cues, words, inUp, pop, logo, chrome, example };
})();

// Runs a template: builds the DOM, the paused timeline, holds to the scene's full length, registers it.
function runScene(render) {
  const root = document.getElementById(K.D.scene);
  const tl = gsap.timeline({ paused: true });
  render(root, K.D, tl, K);
  tl.set({}, {}, K.D.duration);  // the timeline spans the whole scene, so the last state holds
  window.__timelines = window.__timelines || {};
  window.__timelines[K.D.scene] = tl;
}
