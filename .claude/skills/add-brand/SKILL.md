---
name: add-brand
description: Add the user's own brand to brands/<brand>/ (tokens.json, video.yaml, DESIGN.md, FONTS.md, REVIEW.md, SVG logos) from their logo, colours, fonts and product facts, then check it with `create tokens` until it passes. Use when the user says "add my brand", "set up my branding", "use my colours/logo", or starts a project for a brand that has no folder yet.
---

# add-brand

A brand folder is read by C1, C3 and C8 for every project of that brand; no stage writes to it. The field
reference is `brands/README.md`; `brands/acme/` is a complete working example to copy the shape from.

## 1. Collect (ask for what is missing, in one message)
- Brand slug (lowercase, hyphens), product name as written on screen, how it is spoken, URL, video language (ISO).
- Logo SVGs: primary (light backgrounds) required; on-dark and mono optional. Images go straight in the chat.
- Colours in hex with their job: canvas, surface, ink, muted ink, hairline, the one accent, success/error.
- Fonts: heading and body families on Google Fonts (OFL). A paid font: stop and explain only OFL is supported.
- What the accent means (when it is used, when never), and any do / don't they already have.

## 2. Write the folder
1. `cp -r brands/acme brands/<brand>` then rename the logo files to `<brand>-primary.svg`, `-on-dark.svg`, `-mono.svg`
   and replace them with the user's. Each SVG: single colour, no `<script>`, no external `href`, no raster images.
2. `tokens.json`: replace the colour values and families; keep the group/name shape so `video.yaml` paths resolve.
   Keep the `video1920` size sets unless the user's hand-off has its own.
3. `video.yaml`: point every colour role at a tokens.json path; list the text/background `pairs` the scenes use;
   set `type.families`, `logo`, `strings` (in the video language) and `captions`.
4. `DESIGN.md`: keep the section numbers 1-7 (sections 2-6 are copied word for word into every direction.md):
   1 system, 2 accent, 3 layout, 4 type, 5 components, 6 do / don't, 7 contrast table.
5. `FONTS.md` (families, Google Fonts source, OFL) and `REVIEW.md` (what was checked, overrides, open questions).

## 3. Check
```bash
uv run create init <brand>-check --brand <brand>
uv run create tokens <brand>-check
```
It prints the contrast table and glyph check and fails until every pair, style, string and glyph is right. Fix
by changing the pair, the colour or adding an `exception` that says why the brand accepts it (display sizes
only). Never lower thresholds in config/lens.yaml. When it passes, delete `projects/<brand>-check/`, show the
user the contrast table and get their sign-off on colours, logo and what the accent means.

## 4. Done
- `uv run lens validate --all` passes.
- Commit `brands/<brand>/` on its own branch. New projects use `uv run create init <p> --brand <brand>`.
