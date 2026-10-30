<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/dirs/d3-answer-city/DIRECTION.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Direction 3: Answer City

**Pitch:** AI answers are a city seen from a drone. Every brand is a building, and its height is its share of AI
answers. Questions rise from the streets as light, fly to the three engine towers, and the answers that come back
light up the buildings that get named. Acme is the map of that city.

## World rules
- **Palette:** dusk navy sky #0A2036, roads #0D2843, block plinths #16395B, parks #1B4468 with tree dots #24567F.
  Architecture is white-and-navy: tops #F2F5F8/#FFFFFF, faces #BAC7D5 (south), #8798AD (east), #C9D3DF, #A7B6C7.
  Questions and answers are white. Orange #00AA90 appears only on Acme CRM: its building, its trail, its chip.
  People and cars are #5F84A8 and #C9D6E3 dots.
- **Materials:** flat matte boxes like an architectural model. Long dusk shadows and contact occlusion are one
  soft blurred pass. There is no glow, no gradient and no texture.
- **Type:** Space Grotesk 700 for titles and numbers; Inter 500 for chat bubbles and chips. Chips are white cards
  that face the camera and stay 24 px or larger.
- **Logos:** the real ChatGPT, Gemini and Perplexity marks sit on white plaques on top of the towers. Real Reddit,
  Facebook and YouTube marks are on the highway signs. Every brand is fictional.
  An "Example data" tag shows whenever numbers do.
- **Camera language:** one continuous drone. It descends, dives from sky to street, follows a light trail, rides
  a question, and orbits the skyline. Moves use a monotone-cubic camera path (no overshoot, no idle drift).
  Depth of field goes on during the dives.
- **Cuts:** mostly none, because the drone carries us. Chapter changes are a dive into a street (Z forward) or a
  climb-out to altitude (Z back = arrival). The current is "north", toward the towers.
- **Build:** one 2D canvas, drawn every frame from the camera with painter's order and near-plane clipping.
  Bubbles, chips, logos and trails are HTML/SVG billboards projected with the same matrix. It is deterministic and
  seek-safe, and renders 9.4 s in about 40 s. A CSS-3D version had over 1,000 layers and timed out the renderer.

## Beat map
1. **Hook** (built, 0–9.4 s; kf-1). Overhead city at dusk. Waves of bubbles rise on "People / AI / everything /
   now" and leave as trails to the horizon. On "running shoes" the drone dives to one street bubble, and the
   question types word by word. That bubble rides its own thick trail north, and the drone hands off to "eat
   tonight". "Which CRM should a small agency use?" (the client's wording) lifts off with an orange trail and
   arrives on the Gemini plaque at 9.28 s. Only then does the trail fork to the ChatGPT and Perplexity plaques,
   which are framed large.
2. **"Short list, four maybe five names / is yours one of them"**: the answer trails come back down and five
   buildings light one by one (Northwind, Contoso, Fabrikam, Tailspin). The fifth lot is an empty orange-outlined
   plot: slot 5 as a vacant site. "Is yours" pushes in on the empty plot.
3. **Acme reveal + engines vs competitors** (kf-2). The plot grows into Acme's orange building, and the logo
   resolves over the city. Orbit the skyline: heights are shares, and each tower's trails show who it names.
   Switching engines swaps which trails are lit.
4. **Personas:** the drone pans across three neighbourhoods (Greg CEO / Nadia marketer / Liam student). The same
   brands have different heights in each, so Acme is tall in one and small in another.
5. **Phones / real answers:** dive to street level; a person holds a phone and the answer card fills the frame
   (match cut into the existing phone shots).
6. **Sentiment X-ray:** the camera goes top-down. The street grid becomes a heat map around Acme's block (green
   streets for praise, red for complaints) with topic labels on the avenues.
7. **Sources** (kf-3): climb out to see highways feeding the towers: Reddit, the Toddler Parents Club
   (Facebook group), YouTube and forums. Traffic is the content each source carries. The one highway with no
   Acme traffic is the gap.
8. **Agencies, "only pay if they sign":** the drone drops to street level outside Litware Travel. The report
   link travels as a trail into the building, and a "Signed" chip lands on the door. Then fly up.
9. **Logo close:** climb to altitude until the city's grid becomes the Acme mark's G, at dusk.

## Files
- `sketch.mp4`: 0–9.4 s, 30 fps, audio-A trimmed. Source is in `src/` (`city.tpl` engine, `sketch.js`, `kf.js`,
  `build.py`) and `sketch/comp/`. `check.json` is the final check.
- `kf-1.png` (hook, 3.3 s), `kf-2.png` (skyline = share of answers), `kf-3.png` (sources are highways), `sheet.png`.
- Review: `review-r*.png`, `sketch/strip-r1-*`, `sketch/strip-r2-*`, `strip-final-dive.png`, `strip-final-ride.png`.
