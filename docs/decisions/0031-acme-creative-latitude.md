# 0031 — acme.example: fixed anchors, free animation

- **Status:** accepted (Robert, 2026-10-17)
- **Date:** 2026-10-17
- **Milestone:** Phase 2, brands (amends the acme hand-off of 2026-10-12, ADR 0022)

## Context
The acme hand-off (brands/acme/DESIGN.md) was written as a corporate identity: monochrome, cobalt as
the one accent, "one cobalt element per frame", no bounces, no blur-ins, no warm gradients, no emoji. Applied to
reels, that makes every video look the same whatever it is about, and it fights the reel kit (Fred, Pixie, pixel
art, comic bursts, 3D) that the TikTok study says works.

Robert, 2026-10-17: "allow animations in other colors and styles as long as it fits the topics. This is my
personal brand so I don't need to act like a corporation. You can be creative in future videos."

What the research says:
- **Flexible visual systems** keep a few constants so the identity stays recognisable and let the rest vary
  with the content (Martin Lorenz, *Flexible Visual Systems*, 2021; https://www.grafik.net/flexi-time/).
  Personal and creator identities built this way fix type, a mark and a few rules, and let layout, colour and
  density change.
- **Distinctive brand assets** (Romaniuk, Ehrenberg-Bass) need consistent use before they can be played with;
  https://www.marketingweek.com/play-distinctive-assets/. acme.example is new, so the assets that carry the
  name (logo, end card, captions, type, the slash) stay fixed; the illustrations around them do not carry it.
- **The TikTok study** (studies/tiktok/findings.md, 194 videos): stickers, emoji, mascots, memes and props are
  common devices; the main weakness is "too static" (87 of 194), and clutter is layers competing, not colour.
  The rules that matter are one visual per idea, one new animated element at a time, readable text.

## Decision
DESIGN.md gets a **constants / variables** split (section "Personal brand: what stays, what can change").
- **Constants (every video):** the logo files and their rules, the end card, the lower third, burned-in captions
  (style and colours from video.yaml), Geist / Geist Mono for brand text, the slash, lowercase titles, the voice
  rules (no fake stats, banned words), contrast and size minimums, safe areas.
- **Variables (per video, chosen for the topic):** the colours, style and motion of animations, widgets,
  props, characters, illustrations, backgrounds and cutaways. Any palette, warm gradients, the prism colours as
  fills in illustrations, pixel art, comic, hand-drawn, 3D, emoji and stickers inside graphics, springs and
  bounces on characters and playful props, blur and glow effects.
- **The fit test:** each choice has a one-line reason tied to the topic (a Claude video can use warm clay, a
  space metaphor can go dark and starry, a retro-search joke can be pixel art). Write it as a `# look:` comment
  at the top of reel.yaml (the plan schema is strict, so a comment, not a field). "It looks cool" alone is
  not a reason; "it is what the thing looks like" or "it is the joke" is.
- **Guardrails that stay:** one topic palette per video (up to 3 hues plus neutrals, plus the brand anchors);
  one new animated element at a time (TikTok rule 6); text in animations still passes contrast (4.5:1, 3:1 at
  24 px+) and the size minimums; no third-party logos recoloured or redrawn, product UI shown as it is; a topic
  palette never replaces the brand on the end card or the captions.
- Reviewers judge "brand consistency" on the constants only; a topic colour or style that fits is not a fault
  (review-reel skill).

## Consequences
- No code change: the reel kit already takes per-item colours (`spec.color`, `spec.accent` on fx, prop
  colours, pixel palettes). video.yaml keeps its roles; the captions and end card read them as before.
- Acme is a client brand and keeps its stricter rules; this ADR covers acme only.
- If the name gets known, the variables can grow; if videos stop being recognisable as his, tighten the
  constants (more cobalt, the slash in every title label) before tightening the animations.
