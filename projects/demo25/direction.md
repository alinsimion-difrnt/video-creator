<!-- c6_direction 0.1.0 input_hash=a62e22365209d2a5ab43408254a846ba61270eedabe0f9a292b70615c33c922f -->
# Direction pack: demo25 (25 s)

## 1. The job
Product: Acme (https://acme.example). Audience: Marketing leads and agency owners at small and mid-size companies who are starting to ask whether AI assistants recommend them.
Message: AI assistants hand out short lists; Acme shows whether you are on them.
Tone: Warm, plain and specific: a person describing what the product does. No slogans, no rhetorical pairs. Zara warm (ADR 0018).
Frame: 1920x1080, 30 fps, exactly 25 s. Destination: linkedin. Language: en.
Facts you may show (nothing else is claimed):
- engines: Tracks ChatGPT, Gemini and Perplexity
- competitors: Compares you with the competitors you choose, on the same prompts
- sources: Tracks which domains and URLs the AI cites
- free_plan: Free plan, no card

## 2. Narration word clock (seconds from the film's start; cue every reveal to a word, never guess)
- s01 (hook) 0.00-8.30 s: Ask@1.00 ChatGPT@1.40 for@2.36 the@2.48 best@2.68 tool@3.00 in@3.32 your@3.48 category,@3.72 and@4.76 you@5.00 get@5.16 a@5.27 short@5.32 list.@5.76 Is@6.49 your@6.60 brand@6.92 on@7.16 it?@7.36
  - on screen: A chat prompt is typed: "Best accounting software for a small agency?"
  - on screen: The AI answer lists three brands: Ledgerly, Bookwise, Numbr
  - on screen: On "Is your brand on it?", "Your brand" is visibly missing from the list
  - notes: Brand names and numbers are example data: show the brand example-data label while they are on screen. No other companies' logos.
- s02 (mechanism) 8.30-16.80 s: Ack-me@8.30 asks@9.10 ChatGPT,@9.50 Gemini@10.70 and@11.34 Perplexity@11.50 the@12.22 questions@12.62 your@12.94 customers@13.26 ask,@13.66 and@14.30 shows@14.46 you@14.78 who@15.02 gets@15.18 recommended.@15.66
  - on screen: Acme appears
  - on screen: The engines light up on their words: ChatGPT, Gemini, Perplexity
  - on screen: Several customer questions run through them
  - on screen: The brands that get recommended are tallied
  - notes: Brand names and numbers are example data: show the brand example-data label while they are on screen. No other companies' logos.
- s03 (cta) 16.80-25.00 s: See@16.80 where@17.12 you@17.28 stand@17.44 against@17.92 your@18.12 competitors,@18.24 and@19.28 which@19.44 sources@19.68 the@20.24 AI@20.40 trusts.@20.72 Start@21.76 free,@22.08 no@22.80 card.@23.04
  - on screen: Visibility bars on "competitors": Ledgerly 72%, Your brand 41%, Bookwise 38%
  - on screen: Cited sources on "sources": Review sites 34%, Forums 22%, Videos 18%
  - on screen: On "Start free, no card." a Start free button, then the Acme logo and acme.example, held still
  - notes: Brand names and numbers are example data: show the brand example-data label while they are on screen. No other companies' logos.
- final hold: the last frame stays still for at least 1 s before 25 s

## 3. Brand (acme): CSS variables, use them verbatim
```css
:root{--canvas:#F5F7FA;--canvas-product:#FFFFFF;--surface:#FFFFFF;--surface-alt:#FAFAFA;--fill-subtle:#F3F4F6;--chip:#E5E7EB;--ink:#3E0863;--ink-muted:#6B7280;--hairline:#E5E7EB;--accent:#00AA90;--accent-text-large:#028C77;--accent-text:#01775C;--success:#16A34A;--error:#DC2626;--second:#6733FD;--accent-tint:#EBF8F6;--accent-fill:#00AA90;--font-heading:"Space Grotesk", system-ui, sans-serif;--font-body:"Inter", system-ui, sans-serif;--display-font:"Space Grotesk", system-ui, sans-serif;--display-wt:700;--display-size:128px;--display-lh:1.02;--display-tr:-0.03em;--headline-font:"Space Grotesk", system-ui, sans-serif;--headline-wt:700;--headline-size:72px;--headline-lh:1.08;--headline-tr:-0.03em;--stat-font:"Space Grotesk", system-ui, sans-serif;--stat-wt:700;--stat-size:200px;--stat-lh:1;--stat-tr:-0.04em;--body-font:"Inter", system-ui, sans-serif;--body-wt:400;--body-size:32px;--body-lh:1.4;--body-tr:0em;--caption-font:"Inter", system-ui, sans-serif;--caption-wt:400;--caption-size:24px;--caption-lh:1.4;--caption-tr:0em;--label-font:"Inter", system-ui, sans-serif;--label-wt:700;--label-size:24px;--label-lh:1;--label-tr:0.08em;--frame-w:1920px;--frame-h:1080px;--safe-x0:77px;--safe-y0:43px;--safe-x1:1843px;--safe-y1:1037px;--caption-y0:896px;--safe:96px;--keepout:184px;--stack:24px;--card-pad:40px;--card-radius:20px;--chip-radius:6px;--hair:1px;--card-shadow:0 1px 2px rgba(62,8,99,.04), 0 8px 24px -12px rgba(62,8,99,.08)}
```
Logo files: assets/logo.svg (primary), assets/logo-on-dark.svg. Fonts: assets/fonts.css. GSAP: assets/gsap.min.js. No network at render time.

Design rules (brands/acme/DESIGN.md, verbatim):

### 2. How the accent is used

- One orange: **#00AA90** (`accent`). Hover/pressed: #029778. The platform's older #00AEA6 still exists in a few kit components; do not mix the two in one frame. Use #00AA90 for the video.
- The accent is for **emphasis and state**, not decoration: the one key word in a headline, the hero stat number, the focal brand in a chart, checked/selected/focus states, the brand chip, the primary button.
- **Orange text on white is not AA at any size.** #00AA90 on white measures 2.94:1, just under the 3:1 large-text bar. The brand accepts this for the accent word and the hero stat (display sizes, bold, short), as the existing marketing assets do; keep it to those two uses. For any orange text that must pass: `brand-ink` #028C77 (4.18:1, large text only) or `site-accent-ink` #01775C (5.16:1 on site-canvas, passes normal text).
- White on orange (button label) is 2.94:1 as well. In video, keep orange buttons large (label ≥ 28px bold) and few, or use the outline button.
- **One accent moment per frame.** A headline with an accent word and an orange stat on the same frame is already the limit. The orange logo in a corner counts as half a moment: keep it small (48 px) when the frame already has an accent.
- Orange tints: 8% for a chip background, 4% for a selected row, 10% for the focus glow. Never a solid orange panel as background for body copy.
- Chart convention: the customer's brand is orange; competitors use their own colour, never orange, never grey-only.

### 3. Layout rules

- Canvas: white (#FFFFFF) or `surface-2` #FAFAFA for product frames; `site-canvas` #F5F7FA for marketing frames. Do not mix registers within one scene.
- Cards: white, 1px hairline, radius 12px (web). **(added)** On a 1920 canvas use radius 20px and the soft card shadow; keep the border at 1px.
- Depth only when something floats (dropdown, toast, tooltip). Resting cards are bordered, nearly shadowless.
- Hairline dividers between sections, never heavier than 1px.
- Uppercase labels are bold, 0.05-0.08em tracked, grey (#6B7280), never orange.
- Left-align text. Headlines use balanced wrapping; body uses pretty wrapping.
- **(added)** Video grid: 96px safe margin, 64px between sections, 24px stack gap, 40px card padding.
- Icons: Heroicons only (outline 1.5px stroke), sized to the text they sit beside.

### 4. Type

| Style | Family / weight | Web | 1920x1080 video (added) |
|---|---|---|---|
| Display | Space Grotesk 700 | 60-72px / 1.0 / -0.025em | 128px / 1.02 / -0.03em |
| Headline | Space Grotesk 700 | 30-36px / 1.2 / -0.025em | 72px / 1.08 / -0.03em |
| Stat number | Space Grotesk 700 | 30px / 1.0 / -0.025em | 200px / 1.0 / -0.04em |
| Body | Inter 400 | 14px / 1.43 | 32px / 1.4 |
| Body strong | Inter 600 | 14px / 1.43 | 32px / 1.4 |
| Caption | Inter 400 | 12px / 1.33 | 24px / 1.4 |
| Uppercase label | Inter 700, caps | 11px / 1.0 / 0.05em | 22px / 1.0 / 0.08em |

Minimum text size in video: 24px. Mono (system stack) only for code or tabular figures.

### 5. Components, as they are

- **Headline with accent word**: navy headline, one span in #00AA90, same weight, no underline.
- **Stat number**: Space Grotesk bold, navy or orange, with a DeltaBadge on the baseline (green pill +x.x pp, red for down, grey when flat). Sign + colour, never colour alone.
- **Chip / Tag**: radius 6px, Inter 500, 22/26px tall. Default: #E5E7EB bg + navy text. Brand: orange 8% bg + #028C77 text. Outline: transparent + grey border.
- **StatCard**: white, 12px radius, hairline, card shadow; header with a 20px Heroicon, title, muted subtitle; hairline divider; body 20px padding.
- **Chat / answer panel**: no dedicated kit component. **(added)** Compose from a card: engine chip in the header, Inter body, brand mentions as a brand chip or bold navy; cited sources as SourceAvatarCircle + domain in caption style.
- **Bar row with percentage**: label left (Inter), track in `fill-subtle` #F3F4F6, fill in brand orange for the focal brand (competitor colour otherwise), value right-aligned in Space Grotesk bold, tabular numerals.
- **Buttons**: not in the kit; built from tokens: orange solid with white label, orange outline, or ghost. No dark filled buttons.

### 6. Do / Don't

Do
- Pair every status colour with text or an icon.
- Keep one hairline weight and one orange.
- Use Space Grotesk for headings and numbers only; Inter for all reading text.
- Tint shadows toward navy (rgba(62,8,99,a)) when a panel floats.
- Count numbers up (AnimatedNumber) rather than cutting.

Don't
- Don't use gradients, glass, or glows as decoration.
- Don't put small orange text on white.
- Don't use dark filled buttons or a dark hero band as the default (navy band is allowed for the logo lockup only).
- Don't recolour the logo: orange #00AA90 is the main version; navy and white are the only alternates (see logo/README.md).
- Don't use Tailwind greys or any grey outside the token list.
- Don't use emoji or vendor logos; use BrandIcon-style favicons for engines and brands.
- Don't use an em dash in copy.

## 4. Motion, measured from premium explainers (seconds: median (low-high))
Pick any value inside low-high; the median is a safe default. A move longer than 1.2 s needs a reason (a carrier morph or a camera move).

- avatar: 0.64 (0.49-0.76)
- background: 0.47 (0.29-0.92)
- body_text: 0.48 (0.37-0.80)
- button: 0.46 (0.16-0.75)
- card: 0.72 (0.51-1.19)
- cursor: 0.55 (0.25-0.87)
- headline: 0.56 (0.39-0.76)
- icon: 0.39 (0.22-0.79)
- label: 0.52 (0.32-0.72)
- list_item: 0.49 (0.17-0.75)
- logo: 0.58 (0.32-0.83)
- metric: 0.13 (0.04-0.52)
- other: 0.58 (0.23-0.84)
- ui_panel: 0.41 (0.17-0.67)
- change blur_in: 0.47 (0.24-0.99)
- change blur_out: 0.46 (0.34-0.79)
- change color_shift: 0.58 (0.29-0.73)
- change draw_on: 0.63 (0.57-0.95)
- change fade: 0.58 (0.29-0.84)
- change highlight: 0.40 (0.17-0.73)
- change mask_reveal: 0.57 (0.40-1.13)
- change morph: 0.55 (0.37-0.75)
- change other: 0.39 (0.21-0.67)
- change pop: 0.56 (0.44-0.83)
- change rotate: 0.57 (0.17-0.76)
- change scale_down: 0.49 (0.27-0.80)
- change scale_up: 0.62 (0.29-0.92)
- change slide_down: 0.52 (0.23-0.84)
- change slide_left: 0.57 (0.27-0.87)
- change slide_right: 0.53 (0.24-0.85)
- change slide_up: 0.57 (0.33-0.86)
- change typewriter: 0.70 (0.36-0.96)
- eases (GSAP, share of measured moves): ease_out `circ.out` 35%, ease_in_out `back.inOut(2.5)` 23%, ease_in `circ.in` 16%, spring_overshoot `back.out(3)` 14%, linear `none` 12%
- springs: bouncy settles in 0.43 (0.24-0.69); snappy settles in 0.13 (0.07-0.18); smooth settles in 0.67 (0.48-0.92)
- word stagger: 0.08 (0.04-0.17); overshoot on 13% of moves, 9% median; 63% of groups enter all at once (stagger the rest)

## 5. Pacing
- a new visual idea every 2.7 s (range 1.6-4.5) for narrated_explainer; never idle past 4.5 s
- no empty container held for 0.8 s or more (lens flags a dead hold)

## 6. Sound
- SFX for 25 s: about 16 (range 6-24); measured 38 per minute
- SFX onset relative to its reveal (ms, negative = before): chime -31 (-208..157); click -89 (-129..189); glitch -38 (-101..32); impact 16 (-154..162); swoosh_reverse -27 (-221..196); whoosh -155 (-262..116)
- library (assets/sfx/<name>.mp3): click-soft, click, pop, whoosh-short, whoosh, whoosh-cinematic, chime, ping, sparkle, typing, key-press, riser, impact-bass-1, impact-bass-2, notification; gain -18..0 dB per cue
- the narration and a music bed built for the video are mixed by c12_mix; you only place SFX
- final mix: -16 to -14 LUFS, true peak <= -1 dBTP (c12_mix normalises)

## 7. Recipe menu (exports/patterns.json; name the ids you use)
- **match_cut_element**: A hard cut jumps to a new shot or a new framing, but a shared object or shape stays in the same place on screen, so the eye follows it across the cut and the change feels continuous. Steps: Choose the anchor element both shots share and note its screen position and size / Frame or lay out the incoming shot so that anchor lands in the same region / Cut instantly from the first shot to the second, ideally on a spoken word or beat / Right after the cut, add a short drift or settle (slight scale or outward move, a colour shift) so the new shot feels already in motion
- **layout_reframe**: Without a cut, everything on screen moves together into a new arrangement: elements slide, shrink or grow to make room, and new pieces fade in to fill the gaps, so one layout becomes the next. Steps: Group the elements that stay on screen so they can move as one unit / Decide the anchor element the viewer should track from the old layout into the new one / Move, shrink or grow the group to its new position on one shared ease / Fade and lift new elements into the space that opens, with a light stagger
- **ui_camera_push_in**: A virtual camera moves over a product screen without cutting: it pushes in to a detail, pans sideways across it, or pulls out to show the whole interface. The UI itself stays put; the frame around it travels. Steps: Put the whole UI (screenshot or live layout) inside one camera wrapper so everything moves together / Pick the end framing: the control, list or panel the narration is about, and set the transform origin there / Animate the wrapper's scale and translate together toward that framing; reverse the values for a pull-out, or translate only for a sideways pan / Time the move to a narration beat or the gap between sentences so it has a clear reason
- **scale_dissolve_transition**: One screen fades away while it grows or shrinks, and the next screen fades in while settling to its normal size, so the change feels like one continuous zoom instead of a cut. Steps: Stack the outgoing and incoming layers in the same frame / Start fading the outgoing layer while scaling it slightly up or down, optionally with a touch of blur or drift / Overlap the start of the incoming layer so both are briefly visible / Bring the incoming layer in from slightly oversized or undersized and let it settle to full size as it reaches full opacity
- **kinetic_word_reveal**: A headline appears word by word (or as one big word), each piece fading in while it slides, scales or sharpens from a blur and then settles softly into place. Steps: Split the headline into words, and the key word into letters if it gets its own accent. / Start each word invisible and offset: a little low, to one side, slightly larger, or blurred. / Bring the words in one after another with a short stagger, fading up while they travel to rest. / Let the motion decelerate so each word glides into place rather than stopping hard.
- **prompt_type_on**: Text appears character by character in a focused input or prompt field, often with a blinking caret, while the view gently drifts to keep the field centred and the cursor heads for the send button. Steps: Open or focus the input, marking focus with a ring or glow / Reveal the text character by character, in small bursts for a realistic cadence, with a caret after the last character / Let the field grow if the text wraps, and drift or scroll the view so the field stays near the centre / Move the cursor toward the send button or next field while typing finishes
- **ai_answer_stream**: An assistant's reply appears piece by piece, line by line or word by word, while the surrounding chat or page shifts up to make room, so the viewer watches the answer being generated live. Steps: Lay out the finished answer first, split into lines, bullets or words, and hide every piece / Optionally grow the reply container from a small typing-indicator pill or show a short status line with a spinner / Reveal the pieces in order with a short fade and small upward rise, at a steady cadence / As each piece lands, push the thread or page up so the newest content stays in view
- **stagger_list_reveal**: The items of a list, row or panel appear one after another in quick succession, each fading in while rising or sliding a short distance into place, so the group builds up in reading order. Steps: Lay out the final list, then offset each item slightly below or to the side and make it transparent / Optionally grow or unmask the container first, overlapping its growth with the first items / Bring each item to its resting place with a fade and short slide, starting each a beat after the previous one / Keep every item on the same distance, ease and baseline so the cascade reads as one rhythm
- **chip_append**: A small tag, chip, badge or attachment pill pops onto an existing input, field, list or headline, and the things around it shift aside to make room, showing that something was just added or selected. Steps: Show the cause first: a click, a drag and drop, or the narrated line that introduces the item / Close any menu or dropdown at the same moment the chip appears / Pop the chip in from slightly smaller with a quick fade, or slide it up into place if it lands over footage / Shift neighbouring words, labels or form rows aside or down so the layout reflows around the chip
- **spotlight_focus**: Out of a busy screen, one item is singled out: the rest dims, shrinks or loses colour while the chosen item grows, lights up or gains a selection mark, often with a gentle camera push toward it. Steps: Lay out the full context so the viewer sees the whole view first / Pick the one focus item and keep it on its own layer / Dim, desaturate or shrink everything else, keeping it faintly visible for context / Raise the focus item: scale it up, shift its colour to the accent or move the selection mark onto it
- **logo_resolve**: Shapes, icons or blurred type move, merge and sharpen until they settle into the brand logo, often with the mark arriving first and the wordmark joining it to complete the lockup. Steps: Clear or cut away the previous content so the frame is calm / Start from pieces related to the brand: scattered parts of the mark, product icons, a soft shape, or blurred type / Optionally add a small anticipatory squeeze or contraction before the main move / Move, merge or morph the pieces into the mark on one shared ease, sharpening any blur as they land

## 8. Rules learned so far (each must hold)
1. Every handover carries one persistent element (a card, a row, a chip) that changes shape into the next scene's layout. No hard cut, no fade to blank, no crossfade ghosting. _(demo15 and demo25 comparisons (2026-10-17))_
2. Nothing covers live text mid-transition; retire or move text out of the carrier's path first. _(demo15 round 1 (the growing card covered the headline))_
3. On-screen headlines never overlap the logo or the product UI; give each its own zone. _(demo25 blind review (C at 8.4 s))_
4. No empty container on screen for 0.8 s or more; content arrives as (or before) its card settles. _(handoff v1 section 6; lens dead holds)_
5. Something new happens at least every shot median, and the frame never idles past the shot high. _(exports/pacing.json; demo25 (all builds idle in the first 6 s))_
6. Every reveal lands on the word that names it; cue to the word clock, never guess times. _(CLAUDE.md; handoff v1 section 5.3)_
7. Fill the frame at video scale; text at the brand's video sizes and never under the frame's minimum text size. _(DESIGN.md sections 3-4; demo15 and demo25 (text read small))_
8. Brand rules beat taste; no gradients, glows, glass or underline accents; one accent moment per frame (the orange logo counts as half). _(DESIGN.md sections 2 and 6; demo15 and demo25 (freehand builds broke them))_
9. SFX are tied to reveals at the measured offsets, a handful per scene, never one per tween. _(handoff v1 section 5.9; exports/sound-spec.json)_
10. Ids start with a letter; no opacity dims on text (contrast risk). _(handoff v1 sections 5.6-5.7)_
11. Numbers on screen settle on their final value as their word is spoken, and every example number carries the brand's example-data label. _(demo15 and demo25 (37% shown for 38%))_
12. The logo appears whole, in a zone of its own, or not at all until the close; never a clipped sliver at a frame edge or under a headline. _(demo25 acceptance review (2026-10-17))_
13. The main card of a scene spans at least half the frame width; an empty frame around a small card reads as unfinished. _(demo15, demo25 and the demo25 acceptance review)_
14. Hold the final frame (logo and url) still for at least the final hold. _(brief)_
