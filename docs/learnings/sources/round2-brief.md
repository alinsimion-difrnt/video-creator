<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/six/BRIEF.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Six new futuristic directions — 30 s each (shared brief, round 2)

$S = /tmp/claude-0/-home-user-explainer-video-creator/d8546e8e-2ef6-5546-bc1d-4c1a0ec27017/scratchpad
Work ONLY in your folder $S/six/<id>/. Never touch the git repo. No paid APIs (never `--describe`, always
`env -u GEMINI_API_KEY` for snapshot, never `capture`). 4 CPU cores are shared by up to 4 builders: draft at reduced
quality, ONE render at a time, WebGL renders with `-w 1`.

## Clean slate
Do NOT look at earlier builds in $S/ten, $S/dirs or $S/film — we want fresh eyes, not their looks. **No city, no
buildings, no skyline, no map** anywhere. Chat bubbles are optional (he liked them; don't carpet the screen with them).

## The client's taste (Robert, Acme founder)
Futuristic and tech. WHITE + ORANGE: cool white world (#FFFFFF–#EEF1F5, value steps and real shadows for depth, never a
grey-blue tint), navy #3E0863 only for text, orange #00AA90 = the one accent and always means "your brand". He loved a
one-take camera feel. Rejected: navy/dark worlds, paper/hand-made, report-UI slides, any frame still >1.5 s
(something new every 1.0–1.5 s; verify `ffmpeg -i x.mp4 -vf freezedetect=n=0.002:d=1.2 -map 0:v -f null - 2>&1 | grep freeze_`).

## Read first
1. $S/research2/web/WEB.md (trends; your concept's seed is there), $S/research2/films/FILMS.md (what the GEO
   competitors do — avoid their look; what none of them do), $S/research2/tech/TECH.md (what renders here and at what
   cost — follow its "premium-on-white recipe"; code in $S/research2/tech/lib and tests/).
2. $S/wow/BRIEF.md (HyperFrames composition contract, seek-safe GSAP rules, commands, real logo assets) and
   $S/research/hf-skills/_repo-dev-skills/motion-doctrine/SKILL.md.

## The 30 s (exact)
Audio $S/six/audio-30.m4a (voice+music, 30.9 s); words with times $S/six/words-30.txt; data-duration 30.9, 30 fps,
1920x1080. Shown questions read exactly "Where to buy running shoes?", "Where to eat tonight?", "Which CRM should a
small agency use?" typed in sync (the voice says "Which CRM a small agency should use": type "should" at ~7.6–8.0 s,
finish by 9.3 s). Beats on their words: the questions; "ChatGPT" (real logo, with real answer text appearing at once);
"short list"; "Four, maybe five"; "Is yours one of them?" (the empty 5th place, orange, labelled "Your brand?");
"Ack-me" (Acme logo complete ON the word, 20.24 s; real logo SVG in $S/keyframes/src or $S/film/B/comp);
"tracks which brands AI recommends" (21.8–24.4 s: must show AI answers being read and brands detected — never empty);
"ChatGPT, Gemini and Perplexity" (real logos, each on its word); "Every day" (a 1.5–2 s readable time-lapse);
"competitors you pick" (Northwind, Contoso, Fabrikam, Tailspin vs Acme CRM in orange; do NOT show Acme as #1).
Fictional brands; "Example data" tag when names/numbers show.

## Hard-won rules (from an independent review of ten earlier tests)
- No empty or placeholder state on any line (no blank card on "ChatGPT", no waiting machine): every line has its image.
- Striking at 0.3 s; camera moving from frame 1. Hero object fills ≥40% of frame; no frame >30% empty for >0.5 s.
- Questions ≥44 px, meaningful labels ≥32 px at 1080p. Max three moving labels at once; nothing flies across text.
- Motion blur on fast moves, depth of field to separate layers (TECH.md recipes).
- Seek-safe: everything a pure function of t; precompute sims into tables. HTML for all text over the canvas.

## Process
1. Research your concept specifically (WebSearch/WebFetch: 4–6 references; write RESEARCH.md incl. at least one technique
   new to you and how you'll do it seek-safely).
2. Key frames as stills first (kf-1 hook, kf-2 the "Is yours one of them?" frame, kf-3 your choice); look; fix.
3. Build the 30 s; ≥3 render rounds; each round review 10 fps strips across every move + full-res stills of each beat.
4. lint 0 errors; `check` (declare deliberate layering on the text element itself); freezedetect clean.
5. Deliver: sketch.mp4 (with audio), kf-1/2/3.png, poster.jpg, RESEARCH.md, CRITIQUE.md (3 good + 3 bad with timestamps,
   honest), LEARNINGS.md. Delete your intermediate renders/strips when done (keep the deliverables + src/comp).
6. Final reply ≤10 lines.
