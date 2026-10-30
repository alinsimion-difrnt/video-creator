---
name: draft-reel-plan
description: Draft projects/<p>/reel.yaml for a presenter video (Robert's own footage) from the edited take's words — layout blocks, animated widgets timed to his words, punch-ins — then check it with `create reel --check` until it has no errors. Use before `create reel` renders a layout (product on top) or overlay (widgets on his video) version.
---

# draft-reel-plan

Run it as the `reel-planner` agent (`.claude/agents/reel-planner.md`) to keep the drafting out of the main
session's context.

You write the plan; code times and places everything. A plan names, from a word on, where the presenter is and
which widget shows what he is saying. Read Robert's taste and the rules with numbers first: sections 0-c2, d1
and f2 of the playbook and its big-low-face rule (the rest is process and fixed traps),
`sed -n '/^## 0\./,/^## d\./p;/^## d1\./,/^## d2\./p;/A big, low face/,/Reviewers misjudge/p;/^## f2\./,/^## g\./p' docs/learnings/presenter-reels.md`,
and look at `docs/examples/reel-layout.yaml` and `docs/examples/reel-overlay.yaml`.

## Inputs
- `uv run create words <p>`: every word with its index (`41:Budapest,`), one line per scene, and the cuts.
  Indexes are the only way to say "when". Never write times.
- `projects/<p>/brief.yaml` (brand, language, destination) and any notes from Robert.
- `brands/<brand>/DESIGN.md`: what the brand fixes and what a video may change. For acme (ADR 0031) the
  captions, logo, end card and brand text are fixed, and widgets, props and fx may take a topic palette and
  style. Pick one that fits the topic and say why in a `# look:` comment at the top of reel.yaml, together
  with the motion style (below): `# look: paper cards in the brand's cobalt, motion paper: a calm how-to`.
- The type wanted: **layout** (split: product on top, Robert below) or **overlay** (widgets on his own video,
  optionally a few short full-screen cutaways with `layout: "off"`).

## The plan (schema `ReelPlan`, lens/schemas/create.py)
```yaml
layout:                       # from this word on, the presenter is ...; must start at word 0
  - {word: 0, layout: split}  # full | split | pip | "off" (quote off: YAML reads it as false)
captions: top                 # above the head in full shots (never on the face or chest)
split_seam: 1040              # layout type
push: 1.05                    # slow push-in per shot
punches: [21, 28]             # key words: a quick zoom on the face (full shots)
grade: {contrast: 1.08, saturate: 1.14, brightness: 1.01, warmth: 0.05}
product_bg: ink               # dark product area (layout) and cutaways
overlay_zone: auto            # auto | left | chest (overlay type)
motion: {style: paper}        # how the whole video moves (ADR 0033, table below); acme: never classic
items:
  - {word: 110, until: 122, kind: chat, where: product, marks: [111, 115, 116, 122],
     spec: {step: "1", kicker: "Ask ChatGPT", app: ChatGPT, prompt: "...", answer: ["...", "..."]}}
```
`where: product` draws in the product area (split, pip, off); otherwise the widget is an overlay. Overlays can
say `position: left` (beside the face, stickers) or `chest` (cards with content).

## Motion styles (ADR 0033, config `create.footage.reel.styles`)
`motion: {style: <name>}` sets, for the whole video, the entrance of each kind of widget, how one product card
hands over to the next, whether cards in a row share one step label, the background and how the frame behaves
at cuts. Code applies it; you choose it for the topic and name the reason in `# look:`.

| style | cards | stickers | numbers | hand-over | background | fits |
|---|---|---|---|---|---|---|
| paper | rise | pop | pop | morph: one surface becomes the next card | drifting soft shapes | acme's default: how-tos, tool tips, anything calm and clear |
| editorial | wipe | slide | unfold | push: the deck scrolls | none | ranked lists, steps, comparisons, before/after |
| playful | pop | pop | pop | stack: cards pile up | drifting | gags, reactions, wins; with props and pixel art |
| terminal | pixel | pixel | pixel | cut | none | code, command lines, retro; with the code widget and sprites |
| classic | rise | pop | pop | cut: the last leaves, then the next lands | none | client brands (Acme); plans written before ADR 0033 |

- Any part can be overridden: `motion: {style: paper, handover: stack, bg: none}`. A single card can choose its
  own hand-over with `handover: push` on the item (for instance a punchline that should land on the last card).
- In every style but classic: shots push in and out in turn (the zoom carries over the cut), the product
  background and the cards react to each cut, and a card whose word starts just after a cut enters on the cut.
- Cards in a row with the same `kicker` share one step label (it enters once, its `step` flips as the step
  changes, it leaves with the last card) and sit under it, top-aligned. Give every card of a sequence the same
  kicker and change only `step`.
- Pick the style **for the topic and against the last video**: read the brand's other projects' plans
  (`projects/*/reel-*.yaml`, `brand: acme` in brief.yaml) and do not repeat their style unless the topic
  asks for it. Two videos in a row may share a palette or a style, never both.

## Widgets (create/kit/motion.js) and their beats (`marks`: word indexes inside word..until)
| kind | spec | marks |
|---|---|---|
| chat | app, prompt, answer [lines, `**bold**`], sources [names], highlight | type start, type end, answer, sources |
| search | query, results [lines], highlight | type start, type end, results, highlight |
| sources | title, icon, items [{name, sub, icon, verdict}], highlight, highlight_sub (a line that appears under the highlighted row with the ring); `verdict`: yes (check, default), half, no (cross) | one per row (it lights up), then the highlight |
| review | name, label, stars (1-5), text, highlights [phrases inside text] | stars, text, highlight |
| counter | value (number), suffix ("years", "%"), label | none: it counts up as it lands |
| chart | title, to (optional number), suffix, label | none: it draws as it lands |
| queries | vague (one line, struck out), specific [lines, `**bold**`] | strike, then one per specific line |
| tiles | items [{name, icon}] (2-3) | one per tile |
| pins | city, river (a label), places [{name, icon}] (2-3) | one per pin (it jumps) |
| cta | text (button), url | click |
| sticker | text (under ~28 characters), icon, tilt (-4..4), accent (true: orange), peel (true: it peels off on its mark) | peel |
| bars | title, items [{name, value}] (2-4), suffix, max (default 100), highlight, label | one per bar (it grows and counts up) |
| logo | height (px), tagline (shown under the logo, e.g. the URL); `where: product` (a cutaway or split) | none |
| pixel | sprite (robot trophy heart coin rocket pin chat search crown arrow check bulb fire star claude salesman), label (pixel font, ≤ ~10 characters: "ASK AI", "+128%"), text (a normal line under it), card (true: a dark tile; use it on his video), build (rows, dissolve, pop), idle (bob, spin, none), size | burst (the sprite jumps, pixels fly out) |
| handoff | giver, receiver, item (pixel sprites; default salesman, claude, coin), label (pixel font, short), text, card (false: no dark tile) | walk in, hand over, react |
- Every widget takes `spec.footer`: a small mono source line at the bottom of the card ("Bing Webmaster blog,
  Oct 13 2026 · beta"). It sits under the size minimum on purpose (a citation); the check warns, that is fine.
- `highlight` is a 0-based index into the rows / results / chips. A row whose mark is the same word as the
  highlight just lights and gets the ring together.
- Entrances: the motion style sets one per kind of widget; `spec.motion` overrides it on one widget: rise,
  pop, slide (`from: left` or right), flip, focus (blur to sharp), pixel (stepped, retro), wipe (a straight
  edge reveals it), unfold (hinges down from its top). Override for a reason (a reveal that should feel like
  a stamp, a number that should pop), and keep one style per kind of beat.
- Pixel art is for playful beats (a win, an idea, "ask AI", a number going up): one every 15-20 s at most;
  the product cards stay the main graphics. A label is short; the claim itself goes in captions or `text`.
- Icons: sparkle pin star search check chat globe cursor fork bed museum trend thumb bot eye person folder play, or `px:<sprite>` for a pixel
  sprite as the icon (stickers, tiles, source rows). No third-party logos: names
  appear as text. Example numbers and names are made up: say so to Robert, and prefer his real numbers.
- `step` + `kicker` (a step label above a card) are for **product cards in split** only. Overlays hide them,
  and in a cutaway they push a tall card out of its box.
- Leave `w` unset. It is the width a widget is laid out at before it is fitted to its box: product cards default
  to 640 and grow up to 1.6x; overlays default to their zone's width. A smaller `w` on an overlay makes it wrap
  and shrink (smaller text), not bigger. Use `w: 760` only for a product card with long rows.

### Explainer widgets (ADR 0027)
| kind | spec | marks |
|---|---|---|
| shredder | videos [2-4 made-up titles], label ("a frame every 0.5 s"), machine (word on it), step | videos drop, strips fall, grid of frames |
| code | file, lines ["key: value"], edits [{line (0-based), to}] | one per edit (the value is retyped; a `#rrggbb` gets a swatch) |
| bucket | title ("R2 bucket"), name, folders [{name, count}] | one per folder (it lights and counts up) |
| agents | maker, reviewers [names], scores [numbers], you, verdict (up/down), meter (label), meter_value (0-1) | maker, reviewers, you, meter |
- Pair a `code` edit with an effect on the same word so the video changes as the value is typed:
  `{kind: caption_font, spec: {accent: "#22c55e"}}` for a colour (the spoken word, tags and cards take the new
  accent), `{kind: caption_font, spec: {family: mono}}` for a font. Never pair a colour edit with a `grade`
  hue: a hue rotation turns the presenter's skin green (lab v04).
- These are tall cards: give them a cutaway (`layout: "off"`, `where: product`) or the product area in split.

## Props: characters in the room (ADR 0027, create/kit/props.js)
`props:` puts characters on the couch with Robert. They live in **room space** (pixels on his original
footage), so they stay put through push-ins, punch-ins and cuts. Code draws them (`art: fish` or `cat`) or
styles his PNG (`art: image`, `image: fred.png` in `projects/<p>/assets/`, never committed).
```yaml
props:
  - id: fred
    art: image                 # image | fish | cat
    image: fred.png
    word: 15                   # appears as "fish" is said
    until: 120                 # gone by the end of this word
    at: lap                    # lap left right shoulder_left shoulder_right floor_left floor_right above centre, or [x, y] shares of the master
    size: 0.22                 # width as a share of the master's width
    style: photo               # photo | illustrated | pixel | toon3d
    enter: pop                 # pop drop fade slide_left slide_right walk_left walk_right none
    exit: pop                  # pop fade fall run_left run_right swim_left swim_right none
    idle: bob                  # bob breathe swim none
    behind: false              # true: behind Robert (needs `create matte`)
    points: {head: [0.6, 0.15], face: [0.8, 0.45], mouth: [0.95, 0.55]}   # only for a PNG: where hats etc. sit
    beats:
      - {word: 25, style: toon3d}            # "3D"
      - {word: 27, style: illustrated}
      - {word: 30, style: pixel}
      - {word: 40, tag: Fred, do: jump}      # name tag; do: jump spin wiggle blink flip squash look
      - {word: 47, add: [moustache]}         # top_hat moustache sunglasses crown bow_tie
      - {word: 50, add: [top_hat]}
      - {word: 60, move: shoulder_right}     # travels there by the end of the word
      - {word: 62, say: "blub"}              # a speech bubble
      - {word: 70, follow: hand}             # rides his hand down and stays where he puts it (pose, ADR 0030)
  - id: pixie
    art: cat
    word: 300
    until: 316
    at: floor_right
    enter: walk_right                        # walks in from the right edge
    exit: run_left                           # runs out with whatever it carries
    beats:
      - {word: 306, tag: Pixie}
      - {word: 312, move: lap}               # goes to Fred
      - {word: 314, carry: fred}             # Fred leaves the lap and is in Pixie's mouth from here
```
### Fred, the upright fish (`art: fred`, create/kit/fred.js)
`art: fred` is a cartoon fish standing on his tail with fins for arms, drawn live (styles illustrated, toon3d,
pixel by filters). `style: photo` shows `image` (Robert's fish PNG) instead: start as the photo, then switch.
```yaml
  - id: fred
    art: fred
    image: fred.png            # the photo he starts as ("even this fish? AI")
    style: photo
    size: 0.18
    beats:
      - {word: 25, style: toon3d}
      - {word: 40, do: wave}                       # wave | clap | dance | jump | spin | wiggle | blink | look
      - {word: 60, hold: book}                     # book | pencil | phone | hammer (builds blocks) | none
      - {word: 70, hold: none, add: [moustache]}
      - {word: 74, add: [top_hat]}
      - {word: 90, add: [automail], do: clap}      # steel fin and tail; pair with fx alchemy (below)
      - {word: 120, ride: boat, path: [above, shoulder_left, left, lap]}   # rows "S.S. FRED" through the air
      - {word: 140, ride: none, move: lap}
```
- `style: pixel` shows true pixel-art Fred (create/pixel/fred.py: idle, hop, wave, clap, with his accessories);
  his book / pencil / phone / hammer and the boat are drawn only in his other styles.
- A `path` takes `path_leg_s` (config) per spot; without a boat he hops along on his tail.
- Keep paths clear of the captions (`above` is under them only when the head is low): look at a preview.

### Pixie, the kitten (`art: cat`)
Drawn by create/pixel/kitten.py (skill pixel-art): idle, walk, run and grab cycles play by themselves (walk
while she moves, run on a run exit, grab on a carry). A tiny pixel kitten (big head, big eyes; an original drawing, homage to "Pixie and Brutus" by Ben Hed in spirit,
not a copy). Her default look follows Pixie on the comic's cover: peach fur, bold dark stripes, big
light-blue eyes, a white muzzle, a pink bandana. `colors` (fur stripe belly nose eyes iris bandana, #rrggbb)
recolours her.

- Named spots are offsets from Robert's median face (config `create.footage.reel.props.anchors`) and are kept
  on screen in every shot they span. Use `[x, y]` after looking at a preview when a spot is off.
- The check warns `prop-offscreen` when a punch-in crops a prop away: move it, or drop the punch-in there.

### Timing that reads (the animation lab, ADR 0029; skill character-animation)
- Code times every move from distance and speed. A beat starts a move; it does not set its length.
  - Give a walk-in plus a walk to Fred about 3 s before a `carry` word; otherwise she runs.
  - When the plan leaves no time for an exit, the prop stays and the check warns `prop-exit-cut`.
- A carry happens on arrival plus the cat's pounce (about 0.6 s):
  - she stops beside her prey, on its surface;
  - the prey stays until it is snatched;
  - a `shake` on the carry's word lands on the grab.
- A move up or down more than half a prop's height is a jump: shoulder to floor, floor to lap.
- `behind: true` props are raised until half of them shows over the presenter (they peek). Run
  `create matte` first.
- Give a payoff a beat of stillness: don't start the winner's exit on the punchline (v11).
- Hook first. Something on screen in the first second: the qa check allows 3 s, and v12's 5.7 s open was
  the weakest part of the lab.
- 3D Fred spins once (the first time he becomes 3D). In the boat, the drawing stands in for 3D.
- Process cutaways (`layout: "off"`) stay 2-4 s each. One 15 s cutaway of cards felt like another video
  (v14).

## Effects (`fx:`)
```yaml
fx:
  - {word: 90, until: 95, kind: anime, spec: {label: "anime mode"}}   # toon filter, big eyes, blush, sparkles, speed lines
  - {word: 100, until: 104, kind: blocky, spec: {block: 28}}          # pixelated Robert, hearts and a hotbar
  - {word: 120, until: 140, kind: grade, spec: {hue: 40, saturate: 1.2}}
  - {word: 125, until: 140, kind: caption_font, spec: {family: mono, hue: 0}}
  - {word: 315, kind: shake}                                          # one hit: shake | flash | glitch
  - {word: 316, kind: fade_black}                                     # to black by the end (or `until`)
  - {word: 90, kind: alchemy, spec: {at: fred}}                       # a transmutation circle under a prop or spot, 2.4 s
  - {word: 91, kind: automail, spec: {limbs: [right_arm]}}            # his limbs turn to steel, keyed to his pose (ADR 0030)
  - {word: 94, kind: automail, spec: {limbs: [left_leg]}}             # Edward's automail: right arm, left leg
```
- Anime puts speed lines behind Robert when a matte covers it (`create matte`), and around the frame's edges
  when not. Keep anime and blocky to 2-4 s and ask Robert to hold still there (the eyes follow his median face).

## Where things go (boxes, so you can size cards)
- Split (layout type): the product box is about y 320 to the seam minus the caption strip (about 830 at
  `split_seam: 1040`), 768 px wide. Three rows of a sources card, or a chat with two answer lines, fit.
- Cutaways (`layout: "off"`, overlay type): the card box is about y 540-1220 with the captions on top. Keep
  them 2-4 s (the reviews: "remove him" for longer feels like another video); widgets in them need
  `where: product`. A chat with a prompt and three lines fits without a kicker.
- Overlays (`position`): `auto` (the roomiest zone for the widget's shape), `chest` (under the chin to y 1224;
  only ~250 px tall in wide shots), `left` (beside the face, under the captions; used only when ≥ 380 px wide),
  `top` (above the head, only when `captions: band`). On the chest, keep cards to 1-2 rows: tiles and
  multi-row cards come out under 30 px text there (the check warns).
- A name sticker over his own introduction is fine; captions are what must stay off his face and chest.

## Example (overlay type, with a cutaway)
```yaml
layout: [{word: 0, layout: full}, {word: 111, layout: "off"}, {word: 123, layout: full}]
captions: top
push: 1.05
punches: [9, 28]
product_bg: ink
items:
  - {word: 0, until: 9, kind: search, position: chest, marks: [0, 4, 6, 9],
     spec: {query: "best restaurant", highlight: 0, results: ["**Your restaurant** · top pick"]}}
  - {word: 21, until: 26, kind: sticker, position: left, spec: {text: "Robert Vîja, marketer", tilt: 2}}
  - {word: 28, until: 31, kind: counter, spec: {value: 10, suffix: "years", label: "in marketing"}}
  - {word: 111, until: 122, kind: chat, where: product, marks: [111, 115, 116, 122],
     spec: {app: ChatGPT, prompt: "Best Chinese restaurant in Budapest",
            answer: ["Budapest: **Jade Garden**", "Bucharest: **Golden Dragon**", "New York: **Jade Palace**"]}}
```

## Rules (each one came from a review of the first take)
1. A widget shows what he says while he says it: type the query he speaks, list every name he lists, light
   rows on their words. The check warns on capitalised words said but not shown: fix the ones that matter
   (places, products, a list he counts through); a name said once in passing (his own, "ChatGPT" while a chart
   is up) can stay.
2. Something new on screen at least every ~5 s; no card with nothing new for more than ~6 s (split it, or add
   marks). In split, the product area is never empty: one card hands over to the next.
3. Start a card near its first beat, never minutes early; numbers and charts animate as they land.
4. Overlays: stickers short (under ~28 characters), beside the face; cards with content on the chest. Never
   on the face; the check measures it.
5. Hook in the first 3 s (a typed search or a chat); end on the brand (logo + URL) with the CTA's URL on screen
   long enough to read.
6. Full shots for his introduction and personal lines; split or overlays for every how-to step.
7. One motion style per video, chosen for the topic and different from the brand's last video (ADR 0033).
   Cards of one sequence share a kicker so they share one step label; the hand-over does the rest. Robert
   (2026-10-17): the animations were "repeating from one video to another" with no "flowing animation from
   one cut to the other".

## Steps
- Cuts: Robert's own instructions (where it starts and ends, silences to keep, extra cuts) go in
  `projects/<p>/cut-notes.yaml` (schema `CutNotes`), applied by `create cuts` over its proposals (ADR 0030).
0. Props behind Robert or anime backgrounds: after the plan is drafted, `uv run create matte <p>` (a few
   minutes per span on the cloud CPU; faster on his Mac).
1. Read the words; mark the beats (each claim, step, name, number, list) and the hook and CTA.
2. Write the layout blocks, then one item per beat, with marks on the spoken words.
3. `uv run create reel <p> --plan <file> --check` — fix every ERROR; judge every WARN (a name that is fine
   unshown, like the presenter's own, can stay).
4. `uv run create reel <p> --plan <file> --preview 2,8,15,...` — look at the contact sheet at the beats.
5. Render with `uv run create reel <p> --plan <file> --out <mp4>`, then `uv run create qa <p> --video <mp4>`
   and `uv run create review <p> --video <mp4>` for a fresh-eyes review.
