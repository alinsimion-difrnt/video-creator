# build-panel: the page

The rules for projects/<p>/panel/index.html; with SKILL.md sections 2-4 (look, assets, geometry).

## 1. The page (projects/<p>/panel/index.html, committed)
- Start from the starter `--init` copied in: keep its head, background, fade, type scale and helpers (`scene`,
  `up`, `pop`, `mword`, `float`, `type`, `count`, `draw`); replace its example scene; put the beat sheet in its
  top comment.
- Every word on screen is the beat sheet's: its exact kickers, headlines, numbers, chat question and answer.
  Add no copy that is not there (an invented chat answer reads as a claim): put it in the beat sheet first.
- simple-icons are single-colour marks: show them black, white or in the brand's own colour, nothing else.
- Relative URLs (`logos/x.svg`, `emoji/beer.png`): `create panel` injects a `<base>` at the assets folder.
- One paused GSAP timeline for the whole video; `window.seek = (t) => { tl.seek(t, false); }` returns nothing
  (a returned timeline hangs the renderer). Deterministic: no Math.random, Date, CSS animations or rAF loops
  (seed any scatter). Times are word starts from `create words --times`, never guesses.
- Each scene: an absolute layer, faded in over ~0.18 s and out over 0.25 s before the next; content enters on
  the word that names it. Never a frame with nothing on it: put a kicker or a small line on lead-in words.
- Motion vocabulary that worked: masked word reveals (yPercent 110 → 0, power4.out), cards rising with a soft
  spring (back.out 1.2-1.6), 3D icons popping with rotation, count-ups landing on the word with a small
  scale punch, SVG paths drawing (dashoffset), objects flying along a path, staggered rows, an ambient
  background drift so no frame is dead.
- Seek safety (frames and stills seek in any order; presenter-reels §e): text that changes only through the
  starter's `type()` and `count()` (painted from the playhead, never a tween's onUpdate); never two tweens on one
  property at once; hide with opacity, never `visibility`; every property in both states of a `fromTo`, and every
  `from` reset in its `to` (a `y` left at 80 misaligned the founders).
- The graphic and the words agree (he says three cities, it shows three); anything held over ~8 s gets a second
  beat or a highlight; the last beat ends on the brand (presenter-reels §c).
- For a device the starter lacks, use the Grep tool on `projects/acme-reel/panel/index.html` (`boarding`,
  `arcPts`, `chat`) and read that range only.
- Ids: the starter's background uses `bg-*`; give each scene's elements a scene prefix (`a-name`, `h-answer`).
