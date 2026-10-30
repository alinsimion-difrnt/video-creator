# 0034 — Presenter videos: a bespoke panel by default

- **Status:** accepted (Robert, 2026-10-17)
- **Date:** 2026-10-17
- **Milestone:** Phase 2, presenter reels (amends ADR 0026 for the product half; extends ADR 0031)

## Context
acme-reel (Robert's London trip video, 2026-10-17) went through four rounds of kit-widget plans
(`create reel` with chat, sources, tiles, sticker, pixel items). Fresh-eyes reviews plateaued at 6/10 and Robert's
verdict was: "Animations are boring… too narrow and nothing is of high quality… simple, useless animations… this
looks like AI slop." His specific asks: real logos (Acme, ChatGPT), a real chat interface, a big moment for the
1M euro, real pint and coffee icons, clients like Decathlon and Flip, smooth Apple-like motion, no pixel art.

v2 replaced the widgets with one hand-built HTML panel over a split base render: a different visual device per
sentence, real logos and team photos fetched from the companies' own sites, 3D icons, text sized for a phone,
the full 1080 x 840 product area. Robert: "NOW, NOW THIS IS GREAT… this is amazing, compared to others", and
"Make this the default".

Why the kit lost: its widgets are generic templates (every video reads the same); its boxes are fitted inside
TikTok's safe area (660 x 580 px of a 1080 x 1920 frame), so cards were narrow; its icons are drawn, not the real
brands; and its text sizes are tuned for small cards.

## Decision
- **Default for presenter videos:** a split base render (`panel: true` plan: presenter, captions, audio) plus a
  bespoke panel page per project (`projects/<p>/panel/index.html`, committed), rendered and laid over it by
  `create panel` (create/footage/panel.py). The `build-panel` skill holds the process: ideate three ideas per beat
  and break patterns, fetch real assets, write the page, review stills, render, QA.
- **Kit widgets** (`create reel` items, with the motion styles and hand-overs of ADR 0033) stay for when Robert
  asks for them, and for quick drafts. ADR 0033 made the kit flow better; this ADR makes the default bespoke.
- **Assets** (logos, photos, 3D icons, fonts) live in `data/create/<p>/panel/assets/` and are never committed
  (third-party media; CLAUDE.md hard rule). The page that uses them is ours and is committed.
- **acme.example look:** start from the brand palette (ink, paper, cobalt, the prism gradient, mint) and
  interpret it freely; borrow a product's look (Acme) when a beat is about that product. The anchors of
  ADR 0031 (captions, end card, logo, brand type) do not change. DESIGN.md gets the section "Animations: start
  from the brand, then play".

## Consequences
- More work per video (one page per script) and a higher bar; the beat sheet and the stills review keep it
  quick (a stills round takes seconds).
- `create reel --check` skips the empty-product and static checks for panel plans (the panel owns that area);
  `create qa` still checks the composite (loudness, captions, face, length).
- `create review` contact sheets now sample each tile at its stamped time (ffmpeg `fps` with `round=up`); the
  old sheets showed each tile ~1.25 s late, which misled every earlier review round.
