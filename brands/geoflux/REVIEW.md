# Review of the GEOflux brand

Taken from geoflux.ai on 2026-11-16 (site CSS variables and the inline header logo), not from a hand-off. Owner
sign-off pending: confirm the colours and the logo files before using this brand outside one video.

## Sources
- Colours: `--primary` hsl(24 100% 50%) = #FF6600, `--brand-ink` #C46000, `--accent-ink` hsl(24 100% 35%) =
  #B24700, `--secondary` hsl(210 35% 17%) = #1C2B3B (navy ink), `--background` hsl(210 25% 97%) = #F5F7F9.
- Fonts: Space Grotesk (headings) and Inter (body), as the site loads them.
- Logo: the GEOflux.ai wordmark from the site header (single colour, `currentColor` on the site, rendered orange).
  primary = #FF6600, on-dark = white, mono = navy.

## Video overrides
- `uppercase-label` raised from 22px to 24px (the video minimum in config `create.design.min_text_px`).
- ✓ falls back to Inter (Space Grotesk lacks it).
- Orange accent text on light backgrounds allowed at display size only (exception in video.yaml pairs).
