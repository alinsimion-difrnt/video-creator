<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/dirs/d1-one-take/DIRECTION.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# D1 — One Take

**Pitch:** the whole film is one unbroken camera flight through the AI's mind: a deep navy space of glass answers
and light, where every question is a light stream, and being named in an answer is the only way your brand gets warm.

## World rules
- Palette: space #06182B to #0B2540 (radial, darker corners + vignette); light is cool ice #EAF3FF / #9FBBDD with
  blue bloom rgba(90,170,255); the ONLY warm light is Acme CRM, orange #00AA90 (core #FFE6D2, bloom #00AA90).
  Sentiment later borrows green #16A34A / red #DC2626 as tinted light, never as fills.
- Type: Inter 500 for typed prompts (44px), Space Grotesk 700 for numbers, engine names, captions. Ice text with a soft glow.
- Materials: frosted glass (gradient fill 13% to 2%, 1px ice hairline, top-edge highlight), light lines drawn
  additively, dust with motion streaks, grain overlay (13%, moves every frame), depth of field = per-plane blur
  tied to the focus distance plus speed blur on fast moves.
- Engines are constellations: real logo as a glowing core, an orbit ring, brands as light points on spokes.
  Competitors (Northwind, Contoso, Fabrikam, Tailspin) are cool-white points. Acme starts as a dim ember.
- Camera: one CSS-3D camera, one depth path (Hermite curve, speeds matched at every key). There are NO cuts.
  Shots change only by flying: dive into a panel, through it, along its light stream, out the other side.
  Lateral drift is always rightward, so content flows LEFT (the house current). It banks up to 2 degrees on turns.
- "Example data" glass tag bottom-right whenever names or numbers are on screen.

## Beat map (one take, 105 s)
1. Hook (0-9.4): a flare at frame 1 unfolds into a lit prompt by 0.3 s while the camera already moves; from 0.5 s dozens of prompts bloom across the
   depth and fire streams toward one far core. The camera dives through "running shoes", rides its stream, passes
   "eat tonight", and slows on "Which CRM...", the only bright line. A dim orange ember waits deep behind it. (Built.)
2. ChatGPT / short list / "Is yours one of them?": the CRM stream fires and we follow it into the ChatGPT
   constellation. Its answer forms as a glass panel: four cool points snap into rows 1-4. Slot 5 is an empty glass
   socket, and the Acme ember sits outside it, unlit. Push into the socket.
3. Acme reveal and engines vs competitors: the socket's rim traces the Acme mark in light. Pull back (the
   only backward move, ARRIVAL) to reveal three constellations: ChatGPT, Gemini, Perplexity. Acme glows orange where
   it is named and stays an ember where it isn't. A glass HUD reads the share per engine (kf-2).
4. Personas: the camera orbits one constellation. Greg, Nadia and Liam are three coloured "observer" lenses, and
   each lens re-sorts the points. The same field gives a different answer per person.
5. Phones / real answers: three glass phone slabs float in the field; dive through the Perplexity screen into its
   answer card (kf-3 world: "1 Acme CRM" chip turns warm and the whole space warms).
6. Sentiment X-ray: fly behind the answer panel. Its back is a topic map, and each topic beam is tinted green or
   red by how the AI talks about Acme.
7. Sources: the answer's light runs backwards down thin beams to the sources it was built from. Real Reddit,
   YouTube, Facebook-group, forum logos float as distant source stars, and "Toddler Parents Club" is one of them.
8. Agencies "only pay if they sign": a single glass link card (Litware Travel) is sent as a light stream to a
   prospect node. When the node turns warm it locks as "Signed", and only then does the meter tick.
9. Logo close: every warm point in the field converges into the Acme mark at the core. The camera arrives
   and stops for the first time in the film.

## Files
- kf-1.png (hook, 4.95 s of the sketch), kf-2.png (engines as constellations + HUD), kf-3.png (named = warm), sheet.png
- sketch.mp4 (9.4 s, 30 fps, audio-A trimmed), comp/ (sketch source), kf/comp/ (key-frame source, built from
  src/kf.tpl by src/build_kf.py, which inlines the real Lobe icons), check.json, strip-final.png (3.6-6.0 s dive)
