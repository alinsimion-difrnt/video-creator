<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/keyframes/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Acme v2: key frames (style frames), rev 2

Rev 2 follows the client rule: idea lines are expressive (kf05, kf07, kf08 hybrid); product-promise lines show the real product zoomed to one component (kf04, kf09). kf01–03, kf06 and kf10 are unchanged. The rev 1 sources are kept in `src-v1/`.

Ten settled 1920x1080 frames, one per beat. Each is a static HyperFrames composition (`kfNN/comp/index.html`,
duration 1 s, paused GSAP timeline) so it can be animated later. PNGs are in `png/`; the contact sheet is `png/sheet.png`.

**Build:** sources are in `src/`. `kfNN.html` holds the CSS, body and JS for each frame. `tokens.css` holds the shared
system. `build.py kfNN…` inlines the real SVGs (Lobe Icons, simple-icons, Acme logo) and copies the assets.
`shot.sh kfNN…` runs `hyperframes snapshot --at 0.5 --describe false`. `checkall.sh kfNN…` runs lint and check.

**Checks:** every frame passes `lint` (0 errors, 0 warnings) and `check` (ok: true; layout 0 errors, 0 warnings;
contrast 0 errors). Results are in `kfNN/check.json`. Deliberate layering is declared with `data-layout-allow-*`.

**Shared system:**
- Canvas #F5F7FA with a dot grid that fades toward the edges.
- White cards with a 1px #E5E7EB border, 28px radius and one shadow token.
- Space Grotesk for titles (44px) and numbers, Inter for UI text (24–40px).
- Elements behind the focus are dimmed toward the canvas or blurred 2–3px.
- One orange focus per frame. Status green and red appear only for sentiment and Signed.
- Every frame with data carries an "Example data" tag.
- Fictional universe: Acme CRM (you); competitors Northwind, Contoso, Fabrikam and Tailspin; personas Greg, Nadia and Liam.
- Real logos are used only for the AI engines and sources.

| kf | Beat / shot | Shows | Follows real screen | Fictional data | Weaknesses |
|---|---|---|---|---|---|
| 01 | s01 / 3 | Large centred prompt bar, the question typed, caret, orange send button | none (neutral chat bar) | none | Still a quiet frame; its premium feel relies on scale and the shadow. Accent is the send button |
| 02 | s02 / 6 | ChatGPT answer card: user bubble, list 1–4 dimmed, slot 5 empty with orange outline and caret | ChatGPT answer layout (08-single-answer-drawer-chatgpt for structure) | Northwind, Contoso, Fabrikam, Tailspin | Answer prose is skeleton bars, by design (no narration text) |
| 03 | s03 / 9 | Shared-report hero: ChatGPT, Gemini and Perplexity lines flow into a navy Acme CRM card with 41% | 11-shared-report-00-top-overview-hero | 41%, 1,284 answers, 01–07 Oct 2026 | The navy brand card is a dark fill (true to the app). The Acme mark is an invented "A" monogram |
| 04 | s03 / 11 (product promise) | Camera crop of Competitor breakdown: 4 rows (Acme CRM, Northwind, Contoso, Fabrikam), engine icons as column headers, 54–60px names and numbers; card runs off the frame edges | 03-engines-tab-competitor-breakdown-per-engine-table | Acme 41.8/36.4/47.9 (#2/#3/#1); Northwind 52.3/44.1/39.6; Contoso 33.7/38.2/28.4; Fabrikam 21.5/19.8/24.0 | Rank labels are small next to the numbers. No visible card edge on the left (a deliberate crop) |
| 05 | s04 / 15–16 (idea line) | Three people side by side (Greg CEO, Nadia Marketer, Liam Student), each with an avatar and the same question, each with a different answer list: Acme CRM #1 for Greg, #3 for Nadia, a "Not mentioned" slot for Liam; a big #1 / #3 / – verdict in each footer | none (expressive) | Greg: Acme, Northwind, Contoso; Nadia: Northwind, Contoso, Acme; Liam: Contoso, Tailspin, Fabrikam | Orange appears twice (both Acme CRM chips): one idea, two marks. The footer verdict repeats the list (intended, for a reading at a glance) |
| 06 | s05 / 18 | Three phones in CSS 3D. ChatGPT and Gemini show "Not mentioned"; Perplexity, in front, names Acme CRM at #2 | t2-phones build; answers from 08-* drawers | Lists per app; sources Reddit, G2, YouTube | Side phones are washed at 42%, so their small text is soft at phone size, which is intended |
| 07 | s06 / 22–23 (idea line) | X-ray scorecard: huge "Burger +3" verdict in an orange-ringed card with two green marks and an empty third slot, which the torn phrase "the best burger in town" is landing in; smaller "Waiting time −1" and "Price +1" rows; blurred ChatGPT answer with holes at the left | none (expressive; sentiment colour only on signs and marks) | Patty Lane: Burger +3, Waiting time −1, Price +1 | The ghost answer card at the left is soft filler |
| 08 | s07 / 28 (hybrid) | Big stack of three orange-ringed places (r/smallagency Reddit community, Parents in Business Facebook group, Campus Hub student forum, each "TO WIN"), an orange Next arrow into the real "Where competitors are cited and you aren't" card at the lower right with empty dock slots; soft source cloud | 10-sources-gap-sites-where-competitors-are-cited (destination) | 3 sites to win; progress bar in slate, no orange | The stack sits left of centre so the card header stays readable. The dock is a corner touch rather than a deep overlap |
| 09 | s08 / 30–31 (product promise) | Camera crop of the Pitch reports table: Litware Travel "Signed" + orange "Billing starts on sign"; Wingtip Toys Sent / No charge; Woodgrove Dental Not sent. The link chip (acme.example/share/k7q2…) is mid-flight from its empty table cell to a large phone showing the received shared-report hero (Litware Travel 38%) | 12-pitch-reports-viewport, 11-shared-report-00 | Litware Travel, Wingtip Toys, Woodgrove Dental; 38% | The real table has Billing as a separate column; here it is stacked under Status to fit the zoom |
| 10 | s09 / 32 | End card: orange logo 770px (40%), Free plan · No card needed, acme.example with orange underline | t5-close | none | The logo and underline are both orange (brand close) |

Notes:
- Space Grotesk's flagged "1" and ink-trap "N" are the font's real glyphs, not rendering errors.
- kf04, kf05 and kf09 are faithful to app components but use navy and grey where the app uses extra hues (cyan type
  chips, orange "Leads" chip kept). The orange "you" convention is kept everywhere.
