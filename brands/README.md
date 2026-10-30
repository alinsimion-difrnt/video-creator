# Brands

One folder per brand, shared by every project of that brand (ADR 0022). A project's `brief.yaml` names its
brand (`brand: acme`); C1, C3 and C8 read the folder, and no stage writes to it. Brand changes go through a
normal PR. Start a project with `uv run create init <project> --brand <brand>`.

```
brands/<brand>/
  tokens.json   the design hand-off: colours, type styles with their video size sets, spacing, radii, shadows
  video.yaml    how the hand-off maps to video roles (schema `BrandVideo`, lens/schemas/create.py)
  DESIGN.md     the rules in plain words: what the accent means, do's and don'ts, layout
  FONTS.md      families, where they come from, licence evidence, glyph coverage
  REVIEW.md     what was checked at intake, overrides, open questions
  logo/*.svg    owner-supplied single-colour SVGs, no scripts or external references (ADR 0019)
```
Never commit fonts or reference images. Fonts load from Google Fonts at build time (ADR 0019); only OFL fonts
are supported (`source: google`). For a paid font, check its licence first (`docs/research/sources/brands-and-formats-audit.md` B2).

## tokens.json (what C3 reads)
- `color.<group>.<name>`: hex values. `video.yaml` points at them as `group.name`.
- `type.styles.<style>`: `family`, `weight`, and one size set per frame, e.g. `video1920: {size: "72px",
  lineHeight: 1.08, tracking: "-0.03em"}`. Add `transform: uppercase` for label styles.
- Any other group (`spacing`, `radius`, `shadow`) can be referenced from `video.yaml` layout by its path.

## video.yaml
```yaml
colors:                 # role -> tokens.json path; every role the templates use is required:
  canvas: neutral.paper #   canvas canvas_product surface fill_subtle chip ink ink_muted hairline
  ink: neutral.ink      #   accent accent_text accent_text_large success (more roles are fine)
pairs:                  # text/background pairs scenes use; C3 computes WCAG 2.1 contrast for each
  - {text: ink, bg: canvas, size: normal, use: "headline and body"}   # quote text that has commas
  - {text: accent, bg: canvas, size: display, use: "accent word", exception: "why the brand allows it"}
type:
  families:             # role -> family; heading and body are required, more roles (mono) are optional
    heading: {family: Geist, weights: "400..700"}
    body: {family: Geist, weights: "300..700"}
    mono: {family: Geist Mono, weights: "400", fallback: monospace}
  sizes: video1920      # which size set of tokens.json type styles this frame uses
  overrides: {uppercase-label: {size: 24}}   # nothing under config create.design.min_text_px
  glyph_fallback: {"✓": Inter}               # a family that has the glyph
  extra_glyphs: "ăâîșțĂÂÎȘȚ"                  # glyphs the brand's copy needs beyond the house set
layout:                 # tokens.json paths or literal values
  safe_margin: spacing.video.safe
  section_gap: 96
  stack_gap: 24
  card_padding: 48
  card_radius: 20
  chip_radius: 999
  card_shadow: "0 8px 24px rgba(10,10,10,0.08)"
  hairline_width: 1
accent_tint_alpha: 0.08 # optional; config default otherwise
logo:
  primary: logo/<brand>-primary.svg   # required (light backgrounds)
  on_dark: logo/<brand>-on-dark.svg   # optional
  mono: logo/<brand>-mono.svg         # optional
  min_height_corner: 48
  min_height_hero: 120
frames:                 # other frames than landscape (ADR 0023); the brief's destination picks the frame
  vertical:
    sizes: video1080x1920              # a size set in tokens.json type styles, every style >= 44 px
    overrides: {}
    layout: {safe_margin: 120}         # BrandLayout fields that differ on this frame
captions:               # burned-in captions per frame (ADR 0024); checked for size, band width and contrast
  landscape: {kind: pill, family: body, weight: 600, size_px: 44, line_height: 1.23, text: ink, active: ink,
              dim_opacity: 0.35, background: surface, background_alpha: 0.92, max_width_px: 1400}
  vertical: {kind: karaoke, family: heading, weight: 700, size_px: 76, line_height: 1.1, uppercase: true,
             text: surface, active: accent, stroke: ink, stroke_px: 8, max_width_px: 640, padding_px: [0, 0]}
strings:                # template UI copy, in the brand's language (all five are required)
  example_data: Example data
  own_prompt: Yours
  suggested_prompt: AI suggested
  asked_as: Asked as
  own_brand: Your brand
```

## Adding a brand
1. `uv run create init <project> --brand <brand>` creates `brands/<brand>/`.
2. Optional capture on the Mac (the sandbox browser cannot): `npx hyperframes capture <url> --skip-vision`,
   or `npx dembrandt <domain> --dtcg`. Keep the output in `data/`; it is a draft, never the source of truth.
3. Write `tokens.json`, `video.yaml`, `DESIGN.md`, `FONTS.md`, and add the logo SVGs. Get the brand owner's sign-off on
   colours, logo files and what the accent means.
4. The brief says `brand: <brand>` and `language: <iso>`. Then `uv run create tokens <project>` prints the
   contrast table and glyph check, and fails until every pair, style, string and glyph is right.
5. Write `REVIEW.md` and open one PR for the brand.
