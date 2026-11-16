# GEOflux design rules for video

From geoflux.ai (site CSS read 2026-11-16): orange primary, navy ink, near-white canvas, Space Grotesk + Inter.

## 1. The system in one paragraph

Calm, light product frames: near-white canvases, white cards with a hairline, navy ink, one orange accent. Space
Grotesk for headlines and numbers, Inter for everything people read. Depth only when something floats.

## 2. How the accent is used

- One orange: **#FF6600** (`accent`, the site's `--primary`). Pressed: #E65C00.
- The accent is for **emphasis and state**, not decoration: the one key word in a headline, the hero stat number, the focal brand in a chart, checked/selected states, the brand chip, the primary button.
- **Orange text on white is not AA for normal text** (under 3:1). It is allowed for the accent word and the hero stat at display sizes only. For orange text that must pass: `brand-ink` #C46000 (large text) or `site-accent-ink` #B24700 (normal text).
- **One accent moment per frame.** The orange logo in a corner counts as half a moment.
- Orange tints: 8% for a chip background, 4% for a selected row. Never a solid orange panel behind body copy.
- Charts: the customer's brand is orange; competitors use their own colour, never orange.

## 3. Layout rules

- Canvas: white or `surface-2` #FAFAFA for product frames; `site-canvas` #F5F7F9 for marketing frames. One register per scene.
- Cards: white, 1px hairline, radius 20px on a 1920 canvas, soft card shadow.
- Hairline dividers, never heavier than 1px. Uppercase labels bold, tracked, grey (#6B7280), never orange.
- Left-align text. Video grid: 96px safe margin, 64px between sections, 24px stack gap, 40px card padding.

## 4. Type

| Style | Family / weight | 1920x1080 video |
|---|---|---|
| Display | Space Grotesk 700 | 128px / 1.02 / -0.03em |
| Headline | Space Grotesk 700 | 72px / 1.08 / -0.03em |
| Stat number | Space Grotesk 700 | 200px / 1.0 / -0.04em |
| Body | Inter 400 / 600 | 32px / 1.4 |
| Caption | Inter 400 | 24px / 1.4 |
| Uppercase label | Inter 700, caps | 24px / 1.0 / 0.08em |

Minimum text size in video: 24px.

## 5. Components, as they are

- **Headline with accent word**: navy headline, one span in orange, same weight.
- **Stat number**: Space Grotesk bold with a delta badge on the baseline (green up, red down). Sign + colour, never colour alone.
- **Chip**: radius 6px, Inter 500. Default grey bg + navy text; brand chip orange 8% bg + #C46000 text.
- **Card**: white, hairline, card shadow; header with icon, title, muted subtitle.
- **Bar row**: label left, track in `fill-subtle`, orange fill for the focal brand, value right in tabular numerals.

## 6. Do / Don't

Do
- Pair every status colour with text or an icon.
- Keep one hairline weight and one orange.
- Count numbers up rather than cutting.

Don't
- Don't use gradients, glass, or glows as decoration.
- Don't put small orange text on white.
- Don't recolour the logo.
- Don't use an em dash in copy.

## 7. Contrast table

`uv run create tokens <project>` computes it from video.yaml pairs; copy its output here.
