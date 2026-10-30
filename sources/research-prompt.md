# Research prompt: reference explainer videos

Paste into a research-capable assistant (Claude with web search / Research mode). Paste the YAML it returns
into `sources/sources.yaml`; `uv run lens validate sources/sources.yaml` checks it.

---

You are curating a reference corpus of premium product explainer and launch videos. A video-analysis tool
will measure their motion design (easing, springs, stagger, transitions), sound design (SFX placement,
music, ducking, loudness), voiceover (pace, pauses, expressiveness) and pacing, and learn reusable patterns
for our own SaaS explainers. Our product is Acme.ai, an AI-visibility platform for SEO agencies; our
house style is a calm, narrated, light-UI explainer with bold typography and simple data visuals.

## What to find

About 60 candidates, so that ~50 survive review, in this mix:

| Bucket | Count | Examples of where to look |
|---|---|---|
| Big tech product explainers and launches | ~12 | Apple, Google, Microsoft, Meta, Amazon/AWS, Adobe |
| AI companies and AI startups | ~15 | Anthropic, OpenAI, Perplexity, Runway, ElevenLabs, Notion AI, Cursor, Vercel, Replit |
| Design-led SaaS | ~15 | Linear, Stripe, Figma, Framer, Raycast, Arc, Loom, Superhuman, Pitch, Attio |
| Corporate / enterprise explainers | ~8 | Salesforce, HubSpot, Atlassian, Shopify, Intercom, Datadog |
| "Average" (competent, not premium) | ~10 | typical B2B SaaS explainers, template-agency work, SEO/marketing tool explainers |
| Competitors and adjacent tools | 3–5 | SEO, AI-visibility and GEO tools' own explainers |

Format quota: **at least 20 must be narrated explainers** (voiceover explains how the product works),
not only music-driven launch reels. Include some 16:9 and a few 9:16 or 1:1 social cuts.

## What makes a video "premium" (what to select for)

- Purposeful motion: spring or eased entrances with overshoot, staggered reveals, camera pushes into UI,
  match cuts. Not linear slides or template transitions.
- UI shown as a designed object (recreated or stylised UI), not a raw screen recording.
- Sound design tied to the picture: whooshes and clicks landing on reveals, music that builds and drops,
  voice clearly on top.
- A human-sounding voiceover (if narrated): varied pace, real pauses, plain concrete language, no slogans.
- Shaped pacing: fast and slow sections, not uniform; no dead holds on empty frames.
- Clear story in 30 s to 3 min.

## Rules

- Only include videos you actually found. **Never invent a URL, title, date or brand.** If you are unsure a
  video exists, leave it out.
- Prefer, in order: a direct `.mp4` URL; the official brand YouTube channel; the brand's own site or blog;
  Vimeo; X or LinkedIn. Give the canonical page URL.
- Duration 20 s to 5 min. Prefer videos released 2023 or later.
- Official brand uploads only (no re-uploads, reaction videos or compilations).
- One video per product launch; at most 3 per brand.
- For "average" picks, choose competent but plain videos, not bad ones.
- Open every URL before listing it and confirm it plays and matches the title and brand.
- Tag your 5 strongest picks for a pilot with `pilot`: 3 premium narrated explainers in or near our
  style, 1 premium launch reel, and 1 "average" narrated explainer.

## Output

Return one YAML list, nothing else, with one entry per video in exactly this shape:

```yaml
- id: linear-initiatives-2025          # lowercase slug: brand-topic-year
  url: https://www.youtube.com/watch?v=...
  brand: Linear
  title: "Initiatives"                  # the video's own title
  format: feature_reel                  # feature_reel | narrated_explainer | teaser | founder_talk | tutorial | other
  tier: reference                       # reference | average | competitor
  why: "dark UI hero, minimal VO, great stagger"   # one line: what specifically to learn from it
  tags: [dark-ui, no-vo]                # 2-5 lowercase tags: light-ui/dark-ui, vo/no-vo, 3d, kinetic-type, data-viz, 9x16 ...
  media: full
  refetchable: true                     # false if it might be taken down (e.g. LinkedIn-only)
  status: draft                         # always draft: Robert reviews before ready
  # duration_s: 94                      # add as a YAML comment
  # released: 2025-03                   # add as a YAML comment
```

After the YAML, add a short note listing any buckets where you could not find enough good candidates.
