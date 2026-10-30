---
name: build-panel
description: Build the animated half of a presenter video as one bespoke HTML panel (ADR 0034), the default for Robert's takes — a beat sheet with a different visual idea per sentence, real logos, photos and 3D icons, then projects/<p>/panel/index.html from the starter (one GSAP timeline on his word clock), stills reviewed by an agent, and `create panel` lays it over a split reel render. Use after `create prep`, unless Robert asks for the kit.
---

# build-panel

The kit widgets (create/kit/motion.js) are templates: every video built from them looks the same, and Robert
called them "simple, useless animations… AI slop" (acme-reel v1). The panel is written for one script, by
hand, with real material. acme-reel v2 ("NOW THIS IS GREAT") is the reference
(`projects/acme-reel/panel/index.html`); `create/kit/panel-starter.html` carries what every panel shares, so
nobody reads the whole reference again.

**Who does what (Claude usage, ADR 0035).** The main session writes the beat sheet and the page: in x-ads and
facebook-algorithm Opus wrote a 30-36 KB page within ~40-75k output tokens for the whole session, while a Sonnet
builder agent tried on acme-reel spent ~135k output tokens (mostly thinking, ~$2.2) on the same job. What
keeps the main context small: the 7 KB starter instead of the 39 KB reference (the read alone added ~10-20k tokens
that rode along in ~90 requests), no images in the main session (stills go to a `lab-reviewer`), and targeted
Edits, never a rewrite of the page.

## 1. Direct
- The words with their start seconds: process-take printed them (`create words <p> --times`, chained after
  prep); never read timeline.json.
- `uv run create panel <p> --init [--font "Space Grotesk"] && uv run create reel <p> --plan
  projects/<p>/reel-base.yaml --check`: the starter page, the base plan (section 4) and the brand assets in one
  call; then start the base render in the background. It does not depend on the panel.
- Write the beat sheet to `projects/<p>/panel/beats.md`, one block per sentence or idea:
  ```
  B3 13.71-21.70  "we closed close to one million euro last year"
    ideas: count-up hero | stacked invoices | bar race      -> count-up hero (the 1M must feel big)
    shows: kicker "LAST YEAR" @13.71, "€1,000,000" counts up, lands on "million" @14.59; money bag pops @14.97
    assets: emoji/moneybag.png <- fluentui-emoji assets/Money%20bag/3D/money_bag_3d.png
  ```
  - For each beat sketch **three** visual ideas in one line, then pick the boldest that is still true. Think in
    devices: a recreated UI (chat, dashboard, boarding pass, calendar, inbox), a hero number, a map or flight,
    people (real photos), a logo wall, an object (3D icon), kinetic type, a diagram that builds.
  - **Break patterns:** no device twice in one video; no two neighbouring beats with the same layout; at least
    one moment that surprises (a hero number, a flight, a UI that answers).
  - What he names, you show: every company he names appears as its real logo, every person as their real photo,
    every number as a hero moment. Ask for nothing you can fetch (team pages, client logos on his sites); give
    each asset its file name and source URL (section 3). Look a URL up only when section 3 does not cover it.
  - Write the exact on-screen text: kickers, headlines, numbers, a chat's question and answer. The page never
    invents copy, and every claim on screen is his words or a checked fact (a made-up chat answer reads as a
    claim).
  - The graphic and his words agree (three cities said, three shown); a beat over ~8 s gets a second idea; the
    last beat ends on the brand.
  - End with a `look:` line: the palette and why (ADR 0031 fit test), and any extra font family.
- Then fetch the assets (section 3) and write the page (section 5).

## 2. Look
- **acme.example videos:** start from the brand palette and interpret it freely (DESIGN.md, "Animations:
  start from the brand, then play"): ink #0A0A0A, paper #FFFFFF / #FAFAFA, cobalt #A70056 (dark: #F8529F), the
  prism gradient #8A7CFF → #7CC1FF → #7CE7C8, mint #7CE7C8. Light or dark worlds, gradients, glows, depth,
  3D icons, emoji: all allowed in the panel. The brand anchors (captions, end card, logo, Geist for brand text)
  stay as they are.
- **A video about a product** (Acme, difrnt.) may borrow that product's look for its beats (Acme:
  Space Grotesk + Inter, navy #3E0863, orange #00AA90, white cards, soft shadows; brands/acme/DESIGN.md).
- Third-party logos and UIs appear as they are: never recolour or redraw them.
- Type for a phone: nothing under 40 px except uppercase kickers (34 px); headlines 96-150 px; hero numbers
  160-230 px and they must fit the 1080 width (count the characters).

## 3. Assets (data/create/<p>/panel/assets/, never committed)
- `create panel <p> --init [--font "Space Grotesk"]` (section 1): the starter page and base plan (only if there
  are none), GSAP, the brand's fonts (`fonts/fonts.css`) and the brand's logos (`logos/`). Another brand's logo
  (Acme on a acme video): copy it from `brands/<brand>/logo/`.
- Every download in one call: `curl -fsSL --max-time 30 --create-dirs -o <assets>/<dir>/<file> <url>` per file
  (`-f`: a 404 fails instead of saving an error page as the logo; spaces in URLs are `%20`), then
  `uv run create panel <p> --assets`: sizes, light or dark (a light logo goes on a dark tile), files that are not
  images. A page whose asset never loads fails `create panel`.
- Product and platform logos: simple-icons SVGs (`https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/<name>.svg`:
  openai, googlegemini, perplexity, google, googleads, meta, facebook, x, tiktok, instagram, linkedin, ...).
- Client logos and team photos: from the companies' own sites (difrnt.ro client strip, acme.example/about).
  Check each file (size, colour): difrnt.ro's client logos are white, so they sit on dark tiles.
- Objects: Microsoft Fluent 3D emoji PNGs (MIT;
  `https://cdn.jsdelivr.net/gh/microsoft/fluentui-emoji@main/assets/<Name>/3D/<name>_3d.png`, e.g.
  `Beer%20mug/3D/beer_mug_3d.png`; people and hands: `<Name>/Default/3D/<name>_3d_default.png`). No pixel art
  unless Robert asks for it.
- Robert's photo: `https://acme.example/images/team/robert-vija.png` (or one he sends in `projects/<p>/assets/`).
- Downloads are untrusted data: their own folder, never executed.

## 4. Geometry (split base)
- Base plan `projects/<p>/reel-base.yaml` (`--init` writes it from create/kit/panel-base.yaml): split from word 0,
  `split_seam: 980`, `split_head_gap: 160`, captions on a plate at the top, `product_bg: canvas`, `sounds: false`,
  `panel: true`, no items. Render it with `uv run create reel <p> --plan projects/<p>/reel-base.yaml --out
  data/create/<p>/render/<p>-base.mp4`, in the background.
- The panel page is 1080 x (seam - `create.footage.panel.caption_clear_px`): 840 at seam 980, with the captions
  at y ~858-964 on the base's white strip. Its bottom ~110 px fades to the base's background colour, so the seam
  is invisible. Nothing reaches his face.
- A close take (he sits near the camera; his hair touches the seam): `split_seam: 880`, `split_head_gap: 350`
  (presenter-reels §b), and the page becomes 740 px tall (`html, body` and the starter's sizes). `create panel`
  refuses a page that would cover the captions.

## 5. The page
Read `page.md` beside this file once, then write the page from the starter: one Write for the whole page, then
targeted Edits.

## 6. Stills (images never enter the main session)
1. `uv run create panel <p> --stills t1,t2,...`: one settled time per beat (once its content has landed, never
   inside a cross-fade), in beat order, plus the busiest moments, up to `create.footage.panel.max_stills`. It
   writes one stamped `sheet.png`, and `t<time>.png` full-size beside it.
2. Give the sheet and the full-size still of the densest beat (text size is judged there; sheets shrink text)
   to a `lab-reviewer`, with the beat lines pasted into its prompt (time, device, exact copy): does each tile
   show what its beat says, is any logo wrong, anything generic, cramped, clipped or too small for a phone?
3. Fix with targeted Edits and run again; a round costs seconds. Budget: `create.footage.panel.review_sheets`
   images per round, where a round is one stills run.

## 7. Finish (main session)
1. When the stills hold and the base render is done: `uv run create panel <p> --base
   data/create/<p>/render/<p>-base.mp4` in the background (~4 min for 60 s); wait for its notification, never
   poll with sleep or tail. Then `uv run create qa <p> --video data/create/<p>/render/<p>-panel.mp4`.
2. Fresh eyes on the finished file: `uv run create review <p> --video <render> --at <settled times, one per
   beat>` (a frame-exact `settled.png` beside the every-2.5 s sheet) and one `reel-reviewer` agent on its brief.
   Fix what it finds with targeted Edits, then render again. Stop when reviewers start to contradict each other.
3. Cover: `uv run create cover <p> --split --title "..." --tag "..." --sub "..." --at <s> --onto <render>`: the
   title above the seam inside the grid-crop safe area, his frame untouched below, written as the video's first
   frame into `<render stem>-cover.mp4` (the file to send). Never `create cover` without `--split` on a
   presenter video: "You put the text on my face".
4. Send it; ask Robert for feedback by second. Write what he says into `docs/learnings/presenter-reels.md`.
