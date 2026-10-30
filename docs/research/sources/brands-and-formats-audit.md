# Brands and formats: audit and research (2026-10-09)

What it takes to make videos for a second brand (acme.example, alongside acme.example) with the design
pulled from the brand at build time, and later a vertical 1080x1920 format.

Part A is a codebase audit (repo at HEAD, read-only). Part B is web research. Each external claim has a URL,
a date or version and a confidence level (H = primary source read, M = primary source partly read or a
reputable secondary source, L = third-party or inferred).

---

## TL;DR

1. **The pipeline has one brand and one frame size wired in.** The brand folder is `projects/<p>/brand/`,
   with Acme-shaped keys: `video1920`, logo variants `main/on_navy/navy`, exactly two families
   (heading + body) from Google Fonts at weights 400..700, and fixed style names. `1920x1080` appears in
   config, `_base.css` and roughly 40 hard-coded template pixel values. Acme rules sit in global config: the
   accent tint, the em-dash ban, one voice, captions keep-out, and glyphs. The real film kit (camera rig,
   captions, assemble) is in R2, not in git.
2. **Recommendation:** a shared `brands/<brand>/` folder, referenced from `brief.yaml: brand: acme`.
   The brand becomes an *external input* in `lens/stages.py` (`brands/{brand}/**`), just as
   `projects/{project}/brand/**` is today. No stage writes there, so the guard hook and `lens dag --check`
   keep working. Per-frame output goes in `projects/{p}/tokens.json`, keyed by frame (`landscape`,
   `vertical`). This needs one CLAUDE.md edit plus an ADR, because the logo-SVG exception names
   `projects/*/brand/logo/`.
3. **acme.example, measured today:** a Next.js site using **Geist + Geist Mono** (OFL 1.1, on Google Fonts).
   The palette is ink `#0A0A0A`, paper `#FFFFFF`, **cobalt `#A70056`** (7.56:1 on white), cobalt-soft
   `#FFE4F0`, neutrals `#262626/#525252/#737373/#A3A3A3`, and "prism" accents lav `#8A7CFF`, mint `#7CE7C8`
   and sky `#7CC1FF`. Radii are 6 px (button) and 8 px (card). The favicon is `prism.svg`. Geist covers ș ț ă î â ≈ →
   but **has no ✓**, so the same fallback problem as Space Grotesk applies. The font licence raises no
   problem.
4. **Capture tools:** `hyperframes capture <url> --skip-vision` (0.8.137, verified in the package source)
   writes `extracted/tokens.json` (cssVariables, fonts, colors, headings, ctas, svgs, sections) and
   `extracted/design-styles.json` (typography, spacing, radius, shadows, buttons, cards, nav), plus
   screenshots and assets. Dembrandt (MIT) adds `--dtcg`, `--design-md`, `--wcag`, `--dark-mode`, `--mobile` and
   `--crawl`. Both are fine as intake tools. Neither replaces a human-checked `video.yaml`.
5. **DTCG reached a stable 2025.10** (Format and Resolver modules, Final CG Reports dated 2025-10-28). It is
   not a W3C Standard. Its Resolver "modifiers" (brand, mode, frame) map almost exactly onto our needs, so
   new brand files should be written in DTCG `$value/$type` with three tiers: primitive → semantic → video
   component.
6. **Fonts:** OFL fonts are fine. **Adobe Fonts cannot be used by our pipeline as built.** `bundle.py`
   copies font files into a local bundle, and the Adobe terms forbid self-hosting and copying fonts. The
   Monotype/MyFonts desktop licence is described as covering "static design materials". Video and streaming
   usually need an extension, and audience caps vary by foundry. See the checklist in B2.
7. **Vertical** (*superseded*: the safe-zone numbers below are third-party; use the measured official
   profile in `docs/research/vertical-footage-brands.md` §1): no platform publishes pixel safe zones as text. TikTok gives downloadable safe-zone files,
   and third-party figures disagree. Plan to a conservative house profile (about 150 px top, 480 px bottom,
   300 px right in the lower half, 60–90 px left). Set captions at 56–72 px. Our 1080p minimums (24 px)
   are too small on a phone: derive about 44 px as the minimum for anything that must be read.

---

## A. Codebase audit: what blocks a second brand or a vertical format

### A1. Brand location and resolution (blocks a second brand and sharing a brand)

| Where | What is hard-wired | Why it blocks |
|---|---|---|
| `lens/stages.py:45` | `EXTERNAL_INPUTS` has `projects/{project}/brand/**` | Brand is per project. Two acme videos would need two copies. |
| `lens/stages.py:281, 299, 346` | c1 / c3 / c8 read `projects/{project}/brand/**` | Same. |
| `create/project.py:15, 52-54` | `BRAND_REQUIRED = ("tokens.json","DESIGN.md","logo")` under `projects/<p>/brand` | Status and init look only there, and `video.yaml` is not even required. |
| `create/cli.py:27` | `create init` makes `projects/<slug>/brand/` | Same. |
| `create/tokens.py:186-188` | `run_tokens` reads `projects/<p>/brand/tokens.json` + `video.yaml` | Same. |
| `create/build.py:383-385` | logos read from `projects/<p>/brand/` | Same. |
| `lens/validate/__init__.py:428` | tokens check resolves `projects/<p>/brand` | Same. |
| `CLAUDE.md:15`, `docs/decisions/0019…:14` | SVG-logo exception scoped to `projects/*/brand/logo/` | A `brands/` folder needs Robert to edit CLAUDE.md (agents may not) plus a new ADR. |
| `lens/schemas/create.py:25-29` (`Product`) | brief has `product{name, spoken, url, one_liner}` and no `brand` field | Nothing links a project to a shared brand. A personal brand is a person, not a "product". |

### A2. Token schema and C3 code (Acme-shaped)

| Where | Hard-wired | Fix |
|---|---|---|
| `create/tokens.py:97` | `style["video1920"]` per type style | Per-frame scale: `video.yaml → frames.<frame>.type.<role>`. |
| `create/tokens.py:93-100` | exactly two families (`heading`, `body`); any other family raises | Acme uses Geist **and Geist Mono**. Allow N named families (`heading`, `body`, `mono`, `display`). |
| `create/tokens.py:73, 161` | Google Fonts query hard-coded to `wght@400..700` | Geist on the site uses weight 300. Weights must come from the brand. |
| `create/tokens.py:71-81`, `create/bundle.py:157-172` | the only font source is Google Fonts (`google_font`); bundle downloads woff2 | Needs `source: google | local | system`, which is required for any licensed font (B2). |
| `lens/schemas/create.py:264` | `fonts_css` must be an `https://` URL | Breaks local or system fonts. |
| `create/tokens.py:147-159`, `lens/schemas/create.py:234-245` | `Layout` has one width/height from config, the Acme component set (card, chip, hairline, card_shadow) and one `caption_keepout_px` | Needs per-frame layout (safe insets on 4 sides, caption band position) and optional components. |
| `create/tokens.py:225`, `create/build.py:156`, `lens/schemas/create.py:248-253` | logo variants literally `main`, `on_navy`, `navy` | Acme colour names. Use semantic names: `primary`, `on_dark`, `mono_dark`, `mono_light`, `mark` (symbol only, for vertical, avatars and stings). |
| `create/build.py:269-279` | CSS vars assume roles `accent`, `surface` and style names `display, headline, stat-number, body, caption, uppercase-label` | Implicit required-role contract. Make the required semantic roles explicit in the schema and validate them. |
| `create/templates/_base.css` (ink, ink-muted, hairline, chip, accent-text-large, fill-subtle, canvas-product) | more implicit roles | Same. |
| `create/tokens.py:37-46` | WCAG 2.x only | Fine as a gate. Optionally add APCA as information only (B6). |

### A3. 16:9 assumptions (block vertical)

| Where | Hard-wired |
|---|---|
| `config/lens.yaml:324-325` | `frame_width: 1920`, `frame_height: 1080` (a single frame for the whole create pipeline) |
| `config/lens.yaml:323` | `min_text_px: 24`, "nothing smaller on a 1920x1080 frame" (`lens/schemas/config.py:391`). Not valid for phones. |
| `config/lens.yaml:326` | `caption_keepout: 0.17`, a bottom band only. Vertical needs top, bottom and right UI insets. |
| `create/templates/_base.css:3-4` | `html, body, .scene { width:1920px; height:1080px }` |
| `create/templates/_base.css:31` | chrome `top: 48px` |
| `create/templates/*.js` | ~40 literal px sizes tuned for 1920 width: `prompt_input_card.js:15` 1080 px card, `:37` 540 px; `ai_working_loader.js:11` 1300 px, `:35` 700 px; `chat_demo_panel.js:9` 1240 px; `kinetic_statement_card.js:7` maxWidth 1500 px; `app_icon_orbit.js:8` 1100x420; `document_highlight.js:15` 1060 px; `cards_triptych.js:9` horizontal row of 3, and others |
| `create/build.py:359-361` | `data-width/height` from tokens.layout (good: already parametrised) |
| `create/tokens.py:1,6`, `create/cli.py:109`, `lens/stages.py:302`, `lens/schemas/create.py:257` | docstrings and summaries say 1920x1080 |
| `docs/learnings/readme.md:26, 175-179, 455-461` | film rules in 1080p coordinates: scale 0.92 about (960,540), 96/54 px edge margins, captions below y=930, caption pill 66 px above the bottom edge |
| corpus | all **55/55 corpus videos are landscape** (`videos/*/record.json frame_size`). Pacing, motion tokens and compare targets have no vertical reference. Grading a TikTok against them is out of distribution. |
| `config/lens.yaml:40-48, 72, 139` | lens caption detection assumes captions in the bottom 25%, and layout compare ignores the bottom 20%. Vertical captions often sit mid-frame. |
| `scripts/hyperframes_answer_key.py:123` | falls back to `(1920, 1080)` |

### A4. Destinations and format vocabulary

| Where | Hard-wired |
|---|---|
| `config/lens.yaml:259-264` | `targets.loudness` has only `linkedin`, `youtube`, and `default_destination: linkedin` |
| `lens/validate/__init__.py:336-337` | the brief's `destination` must be a loudness key, so `tiktok`, `instagram_reels` and `youtube_shorts` fail validation |
| `lens/schemas/create.py:58` | `destination: Slug` is **one** value. One script cut to 16:9 + 9:16 needs `deliverables: [{destination, frame, length}]`. |
| `lens/schemas/create.py:59`, `taxonomy/v1.yaml:2` | `format` = taxonomy content format (`narrated_explainer` …). Not a blocker, but `format` must not be reused for aspect ratio; call that `frame`. A personal brand will often be `founder_talk` or `tutorial` (both exist). |

### A5. Acme brand rules that sit in global config, schemas or templates

| Where | Rule | Belongs in |
|---|---|---|
| `config/lens.yaml:329` | `accent_tint_alpha: 0.08` ("orange at 8%", Acme DESIGN.md §2) | brand `video.yaml` |
| `config/lens.yaml:334`, `lens/validate/__init__.py:473` | em-dash ban ("brand DESIGN.md §6") | brand copy rules (keep the slogan and antithesis bans global: they are house style) |
| `config/lens.yaml:327` | `required_glyphs: "≈✓→%“”‘’"` | global base + brand/language extra (acme: `ăâîșț`, and the î in "vîja") |
| `config/lens.yaml:299-305` | one global voice (Hope, `WZlYpi1yf6zJhNWXih74`) | brand (a personal brand probably wants Robert's own or cloned voice, or a fixed narrator) |
| `lens/schemas/create.py:283` | `canvas: Literal["marketing","product"]` (Acme DESIGN.md §3) | a brand-defined list of canvas roles |
| `lens/schemas/create.py:286` | `accent` "the one orange moment" | wording only; the rule "one accent moment per frame" is reusable |
| `create/build.py:121` | `<html lang="en">` | brief language (Romanian content → `ro`, which matters for hyphenation and glyph shaping) |
| `create/build.py:386` | brand chrome = `product.name` + host | fine, but a personal brand wants the person's name or handle |
| `create/templates/_kit.js:42` | "Example data" label, English, literal | brand/locale string table |
| `create/templates/prompt_input_card.js:29,40,46` | "AI suggested", "Asked as", `"Your brand"` → accent | Acme product copy inside a template. Move to slots. |
| `create/templates/_base.css:31` | comment "labels are grey, never orange" | Acme rule |
| `docs/learnings/readme.md:133-137, 172, 182-191, 455` | white + orange world, `#EEF1F5` floor, Space Grotesk/Inter, orange means "you", captions Inter 600 44 px navy on a white pill | the learnings are written as universal checklists but mix Acme tokens in. Split into "house rules" (pace, frame use, seams, honesty) and a "Acme brand profile". |
| `docs/learnings/readme.md:137, 204` | fictional data universe: Acme CRM = "you"; rivals Northwind, Contoso, Fabrikam, Tailspin | per-brand `data_universe` (a personal brand may need none, or "your company" placeholders) |

### A6. Film kit outside the repo

`PROGRESS.md` (last section) and `docs/learnings/readme.md:663` say this. The premium Acme film was hand-built outside the pipeline. Its
camera rig, captions comp, edge audit and `assemble.sh` exist only in R2 (`create/acme-v2/source/`). The
committed C8 templates were "not premium enough". For a second brand, the reusable kit must first move into
`create/` (a milestone already listed as open), *parametrised by brand tokens and frame*. Otherwise the second
brand inherits Acme colours buried in scratch code.

### A7. Can several projects share one brand?

Not today: every path is `projects/{project}/brand/`. Options:

| Option | Pros | Cons |
|---|---|---|
| Copy into each project (status quo) | zero code change | drift, double review, logos committed N times |
| Symlink `projects/x/brand → ../../brands/y` | small code change | symlinks in git on case-insensitive or Windows checkouts, guard-hook path resolution (`resolve()` follows links, so writes resolve to `brands/`), confusing |
| **`brands/<brand>/` + `brief.yaml: brand: <slug>`** (recommended) | one source of truth; brand reviewed once; projects stay small; matches DTCG resolver thinking | the brand dir is resolved at runtime, so stage path templates need a `{brand}` placeholder |

**How it fits the stage rules.** `lens/stages.py` already treats the brand as an external input that no stage
writes. Add `"brands/{brand}/**"` to `EXTERNAL_INPUTS` and to the `reads` of c1, c3 and c8.
`template_regex` already accepts any `{name}` placeholder, and `check_dag` exempts reads that overlap
external inputs, so `lens dag --check` passes. No stage gets write access to `brands/`, so the guard hook keeps
blocking writes there whenever `LENS_STAGE` is set. Brand edits happen only in normal building sessions or by
hand, and are reviewed in a PR, which is the right ownership.
The `{brand}` value comes from `brief.yaml` at runtime (in `create/project.py` and `create/tokens.py`). The
stage registry stays declarative and standard-library only.

Keep `projects/{p}/brand/` working for one release as a fallback (acme-v2), or move it to
`brands/acme/` in the same PR. Moving is simpler: one code path.

Optional, for later: brand **variants** (for example `brands/acme/` with `modes: light|dark`, or
`brands/acme/` with `personal|studio`) as DTCG resolver modifiers instead of more folders.

---

## B. Research

### B1. Capturing a brand from a live site

| Tool | What it gives | Licence | Notes | Source / confidence |
|---|---|---|---|---|
| **HyperFrames `capture`** 0.8.137 (npm latest 0.8.143, 2026-10-08) | `hyperframes capture [URL] -o dir [--skip-assets] [--skip-vision] [--max-screenshots 24] [--json]`. Writes `screenshots/` (scroll-*.png, contact-sheet.jpg), `assets/` (images, `svgs/`, `lottie/`, `videos/`, contact sheets), `extracted/tokens.json` = `{title, description, cssVariables, fonts, colors, headings, ctas, svgs, sections}`, `extracted/design-styles.json` = `{typography, spacing{observed, baseUnit}, radius, shadows, buttons, cards, nav}`, `extracted/visible-text.txt`, `extracted/asset-descriptions.md`, optional `shaders.json` and `lottie-manifest.json`, plus an agent README that points to the `product-launch-video` skill. Default viewport 1920x1080. | Apache-2.0 | `--skip-vision` avoids the Gemini/OpenRouter captioning (pay-per-use). In the cloud sandbox it fails on the proxy CA, so run it on Robert's Mac (external-facts §15). The package also has `hyperframes figma tokens <fileKey>`, which imports Figma variables (Enterprise only; it falls back to published styles). | `npx hyperframes@0.8.137 capture --help` and the package `dist/capture-*.js`, `agentPromptGenerator-*.js`, `tokens-*.js`, read 2026-10-09. H |
| **Dembrandt** (`npm dembrandt`, CI example mentions v0.38.0) | Playwright, computed styles: logo, colours (semantic, palette, CSS vars, gradients), typography, spacing, borders, shadows, motion, components, breakpoints. Output flags: `--dtcg`, `--design-md`, `--tailwind`, `--shadcn`, `--html`, `--brand-guide` (PDF), `--json-only`. Analysis: `--wcag`, `--compare <baseline>` (drift check, exit 1), `--dark-mode`, `--mobile` (390x844), `--crawl N`, `--sitemap`. | MIT | README: use it only on sites whose ToS allow automated access, or on your own, and "do not reproduce third-party brand identities". Fine for Robert's own sites. Canvas/WebGL is not analysed. | https://github.com/dembrandt/dembrandt (read 2026-10-09). H |
| **Project Wallace** design tokens | Static CSS analysis: colours, font sizes and families, line heights, gradients, shadows, radii, animation durations and timing functions, units. Input is a URL, file or pasted CSS. | analyser lib `@projectwallace/css-analyzer` listed MIT; licence of the web tool not stated | Good for "what is really used, how often" (frequency ranking separates primitives from noise). Output format not stated as DTCG on the page. | https://www.projectwallace.com/design-tokens (2026-10-09). M; licence: jsDelivr listing. M |
| **Figma Variables REST API** | `GET /v1/files/:file_key/variables/local` | Figma plan | **Enterprise plan + Full seat only**, for GET and POST. Below Enterprise, use a plugin (Tokens Studio) or the published styles. | https://developers.figma.com/docs/rest-api/variables (search 2026-10-09). M-H |
| **Tokens Studio** (Figma plugin) | Tokens in JSON, multi-file sync to Git, themes; `sd-transforms` for Style Dictionary | free + Pro (€16/user/month on the pricing page; date not shown). Pro adds multi-dimensional themes (e.g. platform × brand) and colour modifiers. | A DTCG reference implementation per the DTCG announcement | https://tokens.studio/pricing , https://docs.tokens.studio/get-started/pro-licence . M |
| **Style Dictionary** | token build tool: DTCG → CSS / JSON / anything | Apache-2.0 (npm/Homebrew listings; 5.x current, 5.5.0 seen) | "First-class DTCG support since v4". **Full 2025.10 support is still in progress in v5** (their docs). We don't need it: our C3 is ~200 lines of Python and must stay standard. | https://styledictionary.com/info/dtcg/ (2026-10-09). H |

**Acme.com, captured with curl (no browser, today):** Next.js app; fonts self-hosted by `next/font` (Geist, Geist Mono; `--font-geist-sans`, `--font-geist-mono`). CSS custom properties found: `--color-ink:#0a0a0a`, `--color-ink-2:#262626`, `--color-paper:#fff`, `--color-paper-3:#f4f4f5`, `--color-cobalt:#A70056`, `--color-cobalt-soft:#FFE4F0`, greys `--color-g1:#e5e5e5 … g3:#525252`, `--color-prism-lav:#8a7cff`, `--color-prism-mint:#7ce7c8`, `--color-prism-sky:#7cc1ff`, `--radius-btn:6px`, `--radius-card:8px`, weights 400/500/600 (300 also loaded). Title: "acme. – building, writing, research in bucharest". Favicon `/prism.svg`. Cookiebot, GTM and Klaviyo scripts are present (irrelevant to video).
Contrast measured (WCAG 2.x): ink on paper 19.8; `#525252` 7.81; `#737373` 4.74 (passes normal text); `#A3A3A3` 2.52 (fails, decoration only); **cobalt on white 7.56**, cobalt on cobalt-soft 6.34, white on cobalt 7.56; prism-lav on white 3.28 (large/display only); mint under ink 13.31. Glyphs (fontTools on the Google Fonts files): Geist and Geist Mono have ș ț ă î â ≈ → “ ” %, **no ✓** (needs a fallback such as an icon or Inter, like Acme). Run `hyperframes capture` / `dembrandt --dtcg --crawl 5` on the Mac to confirm what curl missed (rendered shadows, real component styles, logo files).

### B2. Font licensing for rendering into video

Our pipeline: headless Chrome renders HTML; `create/bundle.py` **downloads the woff2 files into
`data/create/<p>/bundle/assets/fonts/`** and the render loads them from there; the video is published.
That is "self-hosting a copy of the font file" plus "video/streaming use".

| Source | Video use | Self-hosted copy in our bundle | Confidence |
|---|---|---|---|
| **OFL 1.1** (Google Fonts: Inter, Space Grotesk, Geist) | Yes: "books, graphics, **videos**, websites…", no attribution needed. Restrictions apply only to selling or modifying the font itself. | Yes (redistribution allowed with the licence) | H: https://openfontlicense.org/how-to-use-ofl-fonts/ ; Geist OFL: https://github.com/vercel/geist-font |
| **Adobe Fonts** (Product Specific Terms, effective 2024-06-18) | Adobe's FAQ (via search; helpx returned 403) says video/broadcast/YouTube is OK with desktop-synced fonts, **only while the subscription is uninterrupted** (§3.1). | **No.** §3.4(E)(1) prohibits "hosting the Licensed Content on your own server or other self-hosting"; (7) prohibits copying fonts "from the locations… where we have installed such Licensed Fonts"; Web Fonts may be used only for "Websites" via a Web Project (§3.1(B), "No other web usage is permitted"). Each virtual environment counts as a separate "Computer" (§1.3). | H for the terms (https://wwwimages2.adobe.com/content/dam/cc/en/legal/servicetou/Adobe-Fonts-Product-Specific-Terms-en_US-20240618.pdf); M for the video FAQ |
| **Monotype / MyFonts desktop** | MyFonts describes Desktop as: install "to create, print, and distribute **static** design materials". Video, broadcast and streaming are typically a separate licence or extension; the terms are per-foundry EULA. One foundry's Desktop terms allow video titles up to 250,000 viewers, beyond which a Broadcast/Streaming extension is needed (example only, not Monotype). | Web licences cover a website by pageviews, not a render farm. Server/app licences are separate products. | M (MyFonts licence pages), L (YouWorkForThem example: https://www.youworkforthem.com/help/?p=246) |

**What Robert must check if a brand uses a paid font** (put the answers in `brands/<b>/FONTS.md`):
1. Who holds the licence (Robert, the client, the agency) and which licence type: desktop, web, app, server, or broadcast/video.
2. Does it allow **use in video/motion graphics published online** (YouTube, LinkedIn, TikTok, ads)? Any audience or impression cap? Paid ads vs organic?
3. Does it allow **rendering on a machine through a browser engine** (headless Chrome), and on how many computers or VMs (CI vs Robert's Mac)?
4. May the font file be **copied into a project folder or bundle** (not committed, but on disk)? If not, rendering must use the system-installed font on Robert's Mac (`source: system`), and the render must be on that machine.
5. Is the licence perpetual or subscription-bound (Adobe)? What happens to published videos if it lapses?
6. Glyph coverage for the brand's languages (Romanian ș ț, not the cedilla forms ş ţ).
7. If any answer is unclear: use an OFL substitute for video and log it as a brand exception.

For acme.example none of this applies: Geist is OFL and on Google Fonts, so the current Google Fonts path works with the weight range opened to 300..700 and a mono family added.

### B3. What a motion brand guideline contains (with public examples)

| Example | What it shows | Source / confidence |
|---|---|---|
| **IBM Carbon** | Two personalities: *productive* (efficient, subtle) vs *expressive* (vibrant, for significant moments). Easing: productive standard `cubic-bezier(0.2,0,0.38,0.9)`, entrance `(0,0,0.38,0.9)`, exit `(0.2,0,1,0.9)`; expressive standard `(0.4,0.14,0.3,1)`, entrance `(0,0,0.3,1)`, exit `(0.4,0.14,1,1)`. Durations: fast-01 70 ms, fast-02 110, moderate-01 150, moderate-02 240, slow-01 400, slow-02 700. "Larger movements take longer." | https://carbondesignsystem.com/elements/motion/overview/ (2026-10-09). H |
| **Google Material 3** | Easing and duration tokens; M3 Expressive moved to spring "motion physics" tokens (spatial vs effects, fast/default/slow). Official values not retrieved (page did not render). | m3.material.io (not readable); third-party implementations. L |
| **Shopify Polaris** | `--p-motion-*` tokens: 5 easings (ease = default for user interaction, ease-in-out for system transitions, linear for spinners, ease-in/out "use sparingly"), durations 0–500 ms; stylelint rule forbids custom values. | https://polaris.shopify.com/tokens/motion . M |
| **Atlassian** | Motion in early access; principles: human, clarifying not decorative, respect reduced motion, performant; feedback 50–150 ms, enter/exit/move 150–400 ms; "Figma does not yet support motion variables". | https://atlassian.design/foundations/motion . M |
| **athenahealth** (brand site) | Principles (precise, elegant, deliberate), do/don't, motion curves (anticipation, overshoot, bounce), **logo animations delivered in 16:9, 4:5 and 9:16**, intro and outro animations, loaders. | https://brand.athenahealth.com/guidelines/motion . H |
| **ResMed brand sting** | Sting = logo animation + **sonic logo** (the audio-only part); exactly 5 s (≥ 4 s with approval), ~1.5 s rest; no cross-dissolve, no scaling or repositioning, no text over it, no mixing with other motion; ProRes 29.97 fps, 48 kHz; **landscape, portrait and square** versions. | https://brand.resmed.com/brand-sting . H |
| **Agrana** | Logo intro and outro are locked master assets; both only in videos > 3 min. | https://brand.agrana.com/brand-elements/motion (search snippet). M |
| **Stripe** | No public motion guideline found; job posts confirm an internal system ("principles, timing tokens, animation guidelines"). | stripe.com/jobs listing. M |

Note: corporate *UI* motion (Carbon, Polaris, Atlassian: 70–700 ms) is web-UI motion, which REVIEW.md
override 4 already rejects for film. The film's motion comes from the corpus (`exports/motion-tokens.json`)
and the learnings grammar. What a brand should contribute is **personality**, not durations. That means:
which corpus ease family (calm `power2/3.out` vs snappy `expo.out`), whether overshoot is allowed (Acme:
no back/bounce), the direction convention ("current is LEFT"), and its signature moves.

**Contents of a motion brand file for video** (synthesised from the examples):
1. Motion principles (3 adjectives + do/don't).
2. Easing personality → a choice among corpus ease tokens (GSAP + cubic-bezier + spring) and an overshoot policy.
3. Tempo: allowed range around corpus medians (e.g. "use the fast end").
4. Logo: lockups and variants, clear space, min size per frame, **logo animation / sting** (length, how it resolves on the spoken name), and versions for 16:9, 9:16 and 1:1.
5. Sonic logo: motif (notes, length), where it plays, and loudness relative to the voice (Acme's weak spot: the sting was −28.5 dBFS under the first syllable).
6. Colour on screen: canvas, accent meaning (what the accent is *for*), max accent moments per frame, data colours.
7. Type scale **per frame** (landscape, vertical, square), min sizes, tracking at display sizes.
8. Captions: font, weight, size, colour, pill or stroke, active-word highlight colour, position per frame, words per group.
9. Lower thirds / name tag (person videos), chrome (handle or URL), end card / CTA.
10. Cover frame / thumbnail template.
11. Copy rules (em dash, forbidden words, how the name is written and spoken: "acme." vs "Robert Vîja").
12. Data universe (fictional companies, "Example data" label wording, language).

### B4. Personal brand specifics

- **Presenter name lower third.** Inside the graphics-safe area (EBU R 95: action safe 3.5% and graphics safe 5% inset per edge, i.e. 96 px and 54 px at 1920x1080; https://tech.ebu.ch/publications/r095 , v1.1 2017. H). Name + one-line role ("Robert Vîja · builder, Bucharest"), on screen ~3–4 s on first appearance only. On vertical, place it above the bottom UI band (about y < 1440). (Durations are house practice. L)
- **Consistent intro/outro.** A ≤ 1.5 s sting (ResMed allows 4–5 s, but in short-form the hook must land by 0.3 s per our learnings), so the intro becomes a corner mark with the hook and the full sting goes at the end. Lock it as master assets per format, as Agrana and ResMed do.
- **Caption highlight colour.** One brand colour for the active word. For acme use cobalt `#A70056` on white pills (7.56:1) or ink on a cobalt-soft pill; never prism-lav for small text (3.28:1).
- **Thumbnails / covers.** YouTube: 16:9 for videos, **9:16 for Shorts**, JPG/PNG, min width 640 px (videos) / min height 640 px (Shorts); recommended 3840x2160 / 2160x3840; 2 MB limit on mobile uploads, 50 MB on desktop (https://support.google.com/youtube/answer/72431 , read 2026-10-09. H). Pick the cover from a designed frame (code picks the frame; the cover template is a brand asset): face or mark + ≤ 4 words.
- **Voice.** A personal brand is defined by its voice. Decide between Robert's own recorded voice (then C4 changes from TTS to alignment of a recording) and an ElevenLabs voice clone, which is allowed under the subscription rule. Check the ElevenLabs terms for cloning your own voice before relying on it (not verified here).

### B5. Multi-brand theming: token tiers and how they map to our files

The common model (Abyss / UHG docs, Design Systems Collective, Rangle. M; the original framing is often attributed to Nathan Curtis: "primitive tokens are the options; semantic tokens are the choices"):

1. **Primitive (core):** raw palette and scales with no meaning (`cobalt.600 = #A70056`, `font.geist`, `radius.8`). Never used directly by scenes.
2. **Semantic:** roles that reference primitives (`color.ink`, `color.canvas`, `color.accent`, `color.accent-text`, `type.heading.family`). **This is our `video.yaml colors:`, which already maps Acme's names to roles.** Scenes and templates use only this tier.
3. **Component (video):** `caption.pill.bg`, `lower-third.name.size`, `card.radius`, `chip.bg`, per frame.

**DTCG 2025.10 maps onto this directly** (Format module: `$value`, `$type`, `$description`, groups, aliases `{group.token}`, `$extends`, types color/dimension/fontFamily/fontWeight/duration/cubicBezier/number/shadow/typography/transition; media type `application/design-tokens+json`, `.tokens.json`; https://www.w3.org/community/reports/design-tokens/CG-FINAL-format-20251028/ . H). The **Resolver module** (`.resolver.json`) has `sets` (merged in order) and `modifiers` with named `contexts` (e.g. `brand: {acme, acme}`, `frame: {landscape, vertical}`) and a `resolutionOrder` (https://www.w3.org/community/reports/design-tokens/CG-FINAL-resolver-20251028/ . H). Caveat: the resolver report states the version string inconsistently ("2025-11-01" in §4.1.2, "2025-10-01" in the root table). Both reports: "not a W3C Standard nor on the W3C Standards Track"; announcement 2025-10-28 (https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/ . H). Tools listed as reference implementations: Style Dictionary, Tokens Studio, Terrazzo.

**Applying this here (no new dependency):** keep C3 in our own Python, but read DTCG-shaped JSON (`$value`, alias
`{a.b}` resolution: about 30 lines). The modifiers are implemented by our own files rather than a generic resolver:
- `brands/<b>/tokens.json` = primitive tier (DTCG; can come straight from `dembrandt --dtcg`, then cleaned by hand).
- `brands/<b>/video.yaml` = semantic + component tier, with `frames.landscape` / `frames.vertical` blocks for type scale, safe insets and caption style.
- `projects/<p>/tokens.json` (C3 output) = resolved values for the frames the brief asks for: `{frames: {landscape: {...}, vertical: {...}}}`, with contrast pairs computed once (colours do not change per frame).
Theme switching then becomes a change to `brief.yaml: brand:`, with no copied folders.

### B6. Contrast and legibility for video text

- **WCAG 2.2 AA** is the current normative reference (contrast unchanged from 2.1: 4.5:1 normal, 3:1 large ≥ 24 px regular or ≥ 18.66 px bold). Our C3 already implements it. WCAG 3 is an incomplete Working Draft (latest 2026-03-03); "final requirements… will be different" (https://www.w3.org/WAI/news/2026-03-03/wcag3 . H).
- **APCA** is not normative. The reference library apca-w3 is 0.1.9 beta (July 2022), "licensed to the W3/AGWG… with specific limitations and exclusions" (https://github.com/Myndex/apca-w3 . H). APCA-guidance levels as reproduced by third parties: Lc 90 preferred for body text, Lc 75 minimum for body columns (≥ 18 px/400), Lc 60 for other content text, Lc 45 for large headlines (M-L, values vary by source). **Recommendation:** keep WCAG 2.x as the gate (written exceptions as today). Optionally *report* APCA Lc for display pairs, because WCAG 2 over-penalises saturated accents like `#00AA90` and is lenient with mid-greys on white. Do not vendor the APCA code until its licence is checked.
- **Video adds what web contrast ignores:** compression (thin weights and hairlines smear at ~2.5 Mbps), motion (text on screen < 1.5 s must be larger), and captions over moving backgrounds. Use pills or plates and do not rely on outline strokes.
- **Phone legibility for 1080x1920 (derived; no official spec found, L-M):** a 1080-wide video plays roughly full-width on a phone (iPhone logical width ~390–430 pt), so **1 video px ≈ 0.36–0.40 pt**. Apple's HIG default body text is 17 pt and the smallest text styles are 11 pt (https://developer.apple.com/design/human-interface-guidelines/typography , via search. M). That gives:
  - absolute minimum for anything that must be read: 11 pt ≈ **30 px**; use **≥ 44 px** for labels (≈ 17 pt body);
  - captions **56–72 px** (third-party vertical guides converge on 60–75 px; https://blitzcutai.com/blog/best-caption-size-tiktok-2026 . L);
  - headlines 88–140 px; hero numbers 160–260 px;
  - landscape 1080p seen on a phone (1920 px across ~390 pt ≈ 0.2 pt/px) shows why the learnings already raised 1080p minimums to 28–44 px (`docs/learnings/readme.md:167`).
- **Vertical safe zones:** TikTok's ad specs say the safe zone depends on the dimension and provide downloadable safe-zone files (with an RTL variant for Arabic and a version for "anchors") rather than numbers (https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads . H). Third-party figures for 1080x1920 disagree widely (top 100–270 px, bottom 250–672 px, right 100–300 px; Meta "14% / 35% / 6%" from blogs. L). A conservative **house profile** covers TikTok, Reels and Shorts: top 160 px, bottom 480 px, left 72 px, right 180 px (300 px below y = 1100), captions centred around y ≈ 1150–1300. Verify against TikTok's safe-zone PNG and an in-app preview before the first release.
- **Loudness for TikTok, Reels and Shorts:** not researched here. Like LinkedIn and YouTube (external-facts §11), expect no official LUFS target; add house targets marked `source: house`.

---

## C. Recommendations

### C1. Brand intake checklist (about 1–2 h for an existing site; Robert answers the ⚑ items)

1. **Identity:** brand slug; on-screen name and how it is spoken (`acme.` vs "Robert Vîja"); URL or handle per platform; one-line descriptor; language(s) (ro/en). ⚑
2. **Capture (on the Mac):** `npx hyperframes@<pinned> capture https://acme.example --skip-vision -o data/brand-intake/acme` and `npx dembrandt acme.example --dtcg --design-md --wcag --crawl 5` (plus `--dark-mode` if the site has one). Keep the outputs in `data/` (never committed).
3. **Logo files:** official SVGs from the owner (not scraped): primary, on-dark, mono, mark/symbol; clear space; min sizes. Check the SVGs are single-colour paths with no scripts or external refs (ADR 0019 checks). ⚑
4. **Fonts:** families, weights and source; licence evidence per B2 → `FONTS.md`; glyph check including the language's diacritics (code). ⚑ if not OFL.
5. **Colour roles:** map captured primitives to semantic roles (`canvas, surface, ink, ink_muted, hairline, accent, accent_text, data.*`). Define what the **accent means** (Acme: "you"). Set max accent moments per frame. C3 computes the contrast table; every failing pair needs a written exception. ⚑ accent meaning.
6. **Type scale per frame** (landscape and vertical) at or above the phone minimums in B6. Set the fallback for glyphs the font lacks (✓ for Geist).
7. **Motion personality:** pick an ease family and overshoot policy from the corpus tokens, a direction convention, and 1–3 signature moves; logo sting length and resolve rule. ⚑ taste.
8. **Sound:** voice (Robert's own, a clone, or a stock voice), sonic logo yes/no, music style references. ⚑
9. **Captions:** style (font, weight, size per frame, pill colour, active-word colour) and position per frame.
10. **Person furniture (personal brand):** lower third (name, role), end card / CTA, cover/thumbnail template, presenter footage yes/no. ⚑
11. **Copy rules:** banned punctuation and words, tone words, name spelling.
12. **Data universe:** fictional companies and names for demos, and the wording of the "Example data" label in each language.
13. **Destinations and frames:** which platforms (LinkedIn 16:9 or 1:1/4:5, YouTube, Shorts, TikTok, Reels) → frames and length bands. ⚑
14. **Review:** a `REVIEW.md` like Acme's: what was checked, overrides, open questions. One PR per brand.

### C2. Minimal brand file set (`brands/<brand>/`)

```
brands/acme/
  brand.yaml        # identity: name, spoken, url/handles, languages, voice, data universe, copy rules, accent meaning
  tokens.json       # primitive tier, DTCG ($value/$type); may start from `dembrandt --dtcg`, hand-cleaned
  video.yaml        # semantic roles + contrast pairs + families/sources + frames.{landscape,vertical}:
                    #   type scale, safe insets, caption style, lower third, logo min sizes; motion personality
  DESIGN.md         # rules in plain words (accent meaning, do/don't), the human-readable source of video.yaml
  FONTS.md          # families, source, licence evidence (B2 answers), glyph coverage
  REVIEW.md         # intake review: what was checked, overrides, open questions
  logo/*.svg        # primary, on-dark, mono, mark (+ clear-space), owner-supplied, ADR-checked
  # optional later: MOTION.md (sting storyboard), sonic.yaml (motif spec; audio stays in R2)
```
And in each project: `brief.yaml` gains `brand: acme` and `deliverables: [{destination: tiktok, frame: vertical, length: {min_s, max_s}}, …]`.

### C3. Code changes, prioritised

| # | Change | Files | Effort |
|---|---|---|---|
| 1 | **ADR + CLAUDE.md edit** (Robert): `brands/<brand>/` is the brand home; logo exception becomes `brands/*/logo/`; projects reference a brand. | `docs/decisions/0021-*.md`, `CLAUDE.md:15` | S |
| 2 | **Brand resolution:** `Brief.brand: Slug` (and `product` optional or renamed `subject` for person brands); `brands/{brand}/**` in `EXTERNAL_INPUTS` and in the reads of c1, c3 and c8; one `brand_dir(root, project)` helper used by tokens, build, project status, validate; move `projects/acme-v2/brand/` → `brands/acme/`. `lens dag --check` + tests. | `lens/schemas/create.py`, `lens/stages.py`, `create/{project,tokens,build,cli}.py`, `lens/validate/__init__.py:428` | M |
| 3 | **Frame profiles in config:** `create.frames: {landscape: {w:1920,h:1080, min_text_px, safe:{t,r,b,l}, caption_band}, vertical: {w:1080,h:1920, …}}` replacing `frame_width/height/caption_keepout/min_text_px`; `Tokens.frames{name: {type, layout}}`; `deliverables` in the brief. | `config/lens.yaml:318-329`, `lens/schemas/config.py:384-397`, `lens/schemas/create.py:234-268`, `create/tokens.py` | M |
| 4 | **Generalise the C3 inputs:** DTCG `$value`/alias reading; N font families with per-family weights and `source: google|local|system`; semantic logo variant names; required semantic roles validated; brand-level `accent_tint_alpha`, extra glyphs, copy bans, canvas roles; `lang` from the brief. | `create/tokens.py`, `create/bundle.py`, `create/build.py:121,156,269-279`, `lens/schemas/create.py:248-286`, `config/lens.yaml:327-334` | M |
| 5 | **Destinations:** add `tiktok`, `instagram_reels`, `youtube_shorts` loudness entries (`source: house`, after a quick check of the facts) and let `deliverables` carry several destinations. Log the platform facts in external-facts §11. | `config/lens.yaml:259-264`, `lens/validate/__init__.py:336`, `docs/external-facts.md` | S |
| 6 | **Bring the film kit into `create/`** (camera rig, captions comp, edge audit, assemble), parametrised by brand tokens and frame. Captions read `caption.*` component tokens and the frame's caption band; the edge audit reads the frame's safe insets. This is the real "premium" path, and the C8 templates are secondary. | new `create/kit/`, from R2 `create/acme-v2/source/` | L |
| 7 | **Templates frame-aware:** replace literal px with tokens or frame-relative units (`--frame-w`, `--safe-*`, `--col` grid), add a vertical layout per archetype (stacking instead of rows; `cards_triptych` → column), move product copy ("AI suggested", "Asked as", "Your brand", "Example data") into slots or a brand string table. | `create/templates/*.js`, `_base.css:3-4,31`, `_kit.js:36-42` | M-L |
| 8 | **Split the learnings** into house rules and per-brand profiles (Acme colours, Acme universe, Inter/Space Grotesk captions) so the next builder brief does not inherit Acme. | `docs/learnings/readme.md` §b-c | S |
| 9 | **Brand intake helper:** `create brand import <brand> --from capture-dir|dembrandt.json` writes a *draft* `tokens.json` + `video.yaml` with roles proposed by frequency (Robert/Claude confirm), never overwriting reviewed files. Runs only locally (capture needs a real browser). | new `create/brand_intake.py` | M |
| 10 | **Vertical reference corpus:** ingest 10–20 premium vertical SaaS or founder clips; tag them `frame: vertical` so `lens compare` grades verticals against verticals; make the lens caption band configurable per frame. | `sources/sources.yaml`, `config/lens.yaml:40-48,72,139` | M |
| 11 | Optional: report APCA Lc next to WCAG for display pairs (information only; check the licence first). | `create/tokens.py` | S |

**Order:** 1 → 2 → 4 → 3 → 5 is enough to run C1–C5 for acme in 16:9 using today's templates. Item 6 is
what makes it premium. Items 3, 7 and 10 are needed before the first TikTok.

---

## Sources (accessed 2026-10-09)
- HyperFrames: https://github.com/heygen-com/hyperframes ; `npx hyperframes@0.8.137 capture --help` and package dist sources; npm `hyperframes` latest 0.8.143 (modified 2026-10-08)
- Dembrandt: https://github.com/dembrandt/dembrandt
- Project Wallace: https://www.projectwallace.com/design-tokens ; https://www.jsdelivr.com/package/npm/@projectwallace/css-analyzer
- Figma Variables API: https://developers.figma.com/docs/rest-api/variables
- Tokens Studio: https://tokens.studio/pricing ; https://docs.tokens.studio/get-started/pro-licence
- Style Dictionary: https://styledictionary.com/info/dtcg/
- DTCG: https://www.w3.org/community/reports/design-tokens/CG-FINAL-format-20251028/ ; https://www.w3.org/community/reports/design-tokens/CG-FINAL-resolver-20251028/ ; https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/ ; https://www.designtokens.org/
- OFL: https://openfontlicense.org/how-to-use-ofl-fonts/ ; Geist: https://github.com/vercel/geist-font
- Adobe Fonts terms (2024-06-18): https://wwwimages2.adobe.com/content/dam/cc/en/legal/servicetou/Adobe-Fonts-Product-Specific-Terms-en_US-20240618.pdf
- MyFonts licence pages, e.g. https://www.myfonts.com/products/monotype-grotesque-1-volume-package-431493/licenses ; foundry example https://www.youworkforthem.com/help/?p=246
- Carbon motion: https://carbondesignsystem.com/elements/motion/overview/
- Polaris motion: https://polaris.shopify.com/tokens/motion ; Atlassian: https://atlassian.design/foundations/motion
- athenahealth: https://brand.athenahealth.com/guidelines/motion ; ResMed: https://brand.resmed.com/brand-sting ; Agrana: https://brand.agrana.com/brand-elements/motion
- EBU R 95: https://tech.ebu.ch/publications/r095
- YouTube thumbnails: https://support.google.com/youtube/answer/72431
- TikTok ad specs: https://ads.tiktok.com/help/article/tiktok-auction-in-feed-ads ; third-party safe-zone figures, e.g. https://sovran.ai/blog/tiktok-video-ad-specs , https://www.firstpier.com/resources/instagram-ad-safe-zones (L)
- WCAG 3 draft: https://www.w3.org/WAI/news/2026-03-03/wcag3 ; APCA: https://github.com/Myndex/apca-w3
- Apple HIG typography: https://developer.apple.com/design/human-interface-guidelines/typography
- Token tiers: https://abyss.uhc.com/web/theme-customization/tokens/tokens-intro ; https://www.designsystemscollective.com/when-semantic-tokens-are-no-longer-semantic-d65ef16fadd7
- acme.example homepage + `/_next/static/chunks/0wii68z77ea1q.css` (fetched with curl; fonts checked with fontTools on Google Fonts files)
