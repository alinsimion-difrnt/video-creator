<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/dirs/d2-paper/DIRECTION.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Direction 2: Paper Studio

**Pitch:** the whole film happens on one warm desk, shot from above. Every question, answer and report is a real
object made by hand: typed, printed, cut, pinned and stamped. AI visibility becomes something you can touch.

## World rules
- **Palette:** desk oat-kraft #E2CFAE (grain plus soft mottle); paper bond #FFFDF8 / #FBF8F1; sticky notes butter
  #F2E2A0, powder #DCE4EA and white; typewriter lacquer navy #0E2A44; ink #18222F; headings navy #3E0863.
  **Orange #00AA90 is a material:** orange paper, orange tape, orange stamp ink. It only ever means "your brand".
  Green #16A34A and red #DC2626 appear only as highlighter (sentiment).
- **Type:** Courier Prime 700 for typed strips and receipts (the voice of the machines); Caveat for handwriting on
  sticky notes (questions only, never data); Space Grotesk 700 for headings, numbers and the stamp; Inter is kept
  for real UI only (the phones act).
- **Materials:** paper grain (SVG noise multiply), soft top-left key light, shadows fall down-right. Lifted objects
  get larger, softer shadows and scale 1.06; landed objects get tight contact shadows. Torn and cut edges come
  from seeded polygons. Real engine and source logos are printed on the objects (printer faces, receipt headers,
  pins on the corkboard).
- **Camera:** smooth top-down slides and pushes (power3.inOut), with a 9px whip blur on fast slides. The current
  runs LEFT: typed paper travels left out of the carriage, so the camera follows it left. Macro shots blur the
  rest of the desk (depth of field).
- **Objects move in stop-motion:** power3.out sampled at 12 fps (stepped ease) for anything put down by a "hand".
  Typing jumps the carriage one character per keystroke, and the matching key goes down. The camera never steps.
- **Cuts:** no dissolves. A whip slide across the desk, a push into an object (into a printer slot, a receipt or a
  phone), or a match on paper (a receipt edge becomes the next bar).

## Beat map
| Act | In this world |
|---|---|
| Hook (0–9.4) | A burst of big sticky notes and typed strips piles up in the middle of the frame, faster and faster (0–3.3 s, 24 questions). The camera sweeps left off the pile and pushes into a typewriter as it types "Where to buy running shoes?". It whips left to a sticky note being written "Where to eat tonight?", then left again to a second typewriter. That tape feeds "Which CRM should a small agency use?" into a little printer with the ChatGPT logo. (Built: sketch.mp4.) |
| ChatGPT answers | The printer chatters and pushes out a thermal receipt: 1 Northwind, 2 Contoso, 3 Fabrikam, 4 Tailspin. |
| "Four, maybe five. Is yours one of them?" | Four receipts are torn off and pinned in a row (stepped). Slot 5 is a torn-out empty space in the corkboard, outlined in orange tape. The camera pushes into it, which becomes the A→B match cut. |
| Acme reveal | The orange tape outline peels and folds into the Acme mark, stamped onto a bond card. |
| Engines vs competitors | Three printers (ChatGPT, Gemini, Perplexity) print side by side. Their receipts are cut into a cut-paper bar chart: rivals in kraft, Acme CRM in orange paper with a "YOU" tag (kf-2). Switching engine means pinning a different receipt stub. |
| Personas | Paper cut-out people (Greg the CEO, Nadia the marketer, Liam the student) slide in on stands. Each holds a different printed answer, and Acme moves rank between them. |
| Phones / real answers | Real phones lie on the desk. The camera pushes into the Perplexity screen; this is the only act with live UI. |
| Sentiment X-ray | A highlighter drags across a printed answer: green on praise, red on complaints. Scissors cut the phrases out and pin them to a board in two columns. |
| Sources | A corkboard with source cards (Reddit, YouTube, Toddler Parents Club on Facebook, Quora) and pins. Red thread runs from each pin to the answer receipt, then turns orange where Acme is missing. |
| Agencies: pitch and "only pay if they sign" | A report for Litware Travel slides in on a clipboard. The rubber stamp comes down (stop-motion squash, ink texture) to stamp SIGNED in orange (kf-3). |
| Logo close | Every object is swept off the desk, leaving the stamp ink. The ink re-forms into the Acme logo on a bond card, with a pull back to the clean desk. |

## Why it is different
The other cuts are screens. This one is objects, so the film reads as "craft and evidence" rather than "dashboard".
The orange works harder here because it is the only coloured material on a neutral desk.
