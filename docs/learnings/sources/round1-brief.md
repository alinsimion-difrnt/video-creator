<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/ten/BRIEF.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Ten futuristic directions — 30 s each (shared brief)

$S = /tmp/claude-0/-home-user-explainer-video-creator/d8546e8e-2ef6-5546-bc1d-4c1a0ec27017/scratchpad
Work ONLY in your folder $S/ten/<id>/. Never touch the git repo. No paid APIs (never `--describe`, never `capture`).
The machine has 4 CPU cores shared by up to 4 builders: render drafts at reduced quality/fps first, avoid
needless full renders, and never run more than one render at a time yourself.

## The client's taste (Robert, Acme founder — verbatim where quoted)
- "One take is great, but I'd like white and orange, not navy blue." "I like the chat bubbles over city."
  "I don't like paper." "We are tech based, so it needs to be futuristic."
- Earlier: "I don't want static slides that sit more than 2-3 seconds"; questions at the start were "too slow";
  "nothing really happens" was his complaint about a calm middle; report-UI elements felt "too simple".
- So: WHITE + ORANGE world (white/near-white #FFFFFF–#EEF1F5, soft greys for depth, navy #3E0863 only for text,
  orange #00AA90 = the one accent and always means "your brand"). Futuristic, premium tech. Constant purposeful
  motion: something new every 1.0–1.5 s, no frame still >1.5 s (verify with
  `ffmpeg -i x.mp4 -vf freezedetect=n=0.002:d=1.2 -map 0:v -f null - 2>&1 | grep freeze_`).

## The 30 s you animate (exact)
Audio: $S/ten/audio-30.m4a (voice + music, 30.9 s). Words with times: $S/ten/words-30.txt. Composition
data-duration 30.9, 30 fps, 1920x1080. Script: "People ask AI about everything now. Where to buy running shoes.
Where to eat tonight. Which CRM should a small agency use. And when someone asks ChatGPT for the best CRM? They
get a short list. Four, maybe five names. Is yours one of them? That's what Ack-me is for. It tracks which brands
AI recommends, in ChatGPT, Gemini and Perplexity. Every day, against the competitors you pick."
Any typed/shown question must read exactly: "Where to buy running shoes?", "Where to eat tonight?",
"Which CRM should a small agency use?" (that wording, typed in sync with the voice). Beats to land on their words:
the three questions; "ChatGPT"; "short list"; "Four, maybe five"; "Is yours one of them?" (Acme absent → the empty
5th place, orange); "Ack-me" (the Acme logo reveal — use the real logo from $S/keyframes/src or the film's
G-curl in $S/film/B/comp); "ChatGPT, Gemini and Perplexity" (real logos, each on its word); "Every day";
"competitors you pick" (Northwind, Contoso, Fabrikam, Tailspin). Fictional brands only; "Example data" tag when
names/numbers show; real logos only for AI engines/sources (assets per $S/wow/BRIEF.md).

## Read first
$S/wow/BRIEF.md (composition contract, seek-safe GSAP rules, commands, logo assets) and
$S/research/hf-skills/_repo-dev-skills/motion-doctrine/SKILL.md (vector law, the current is LEFT, carriers,
no idle wobble). HyperFrames skills in $S/research/hf-skills/. Past builds to learn from (look at them):
$S/dirs/d1-one-take (the client's favourite; navy — redo the idea in white), $S/dirs/d3-answer-city (bubbles over
city; canvas engine), $S/film/A and $S/film/B (current film's same 30 s, light UI).

## Lessons already learned (do not repeat these mistakes)
- Quiet/dark/slow first 2 s loses him: something striking by 0.3 s, camera moving from frame 1.
- Text under ~28 px at 1080p is unreadable on a phone. Max 3 moving cards at once; no chips covering text.
- Heavy scenes: >1000 CSS-3D layers time out the renderer; use one <canvas> redrawn per frame from the timeline
  time (seek-safe: draw purely from t), or WebGL via a locally vendored three.js if you need real 3D/refraction.
- Previews that look fine as stills can be mush in motion: review 10 fps strips across every move, every round.
- Placeholder states (00.0%, a logo before its word, a fork before its trigger) read as bugs.

## Process (required)
1. RESEARCH (~15 min): find how top studios/designers do your concept (WebSearch/WebFetch: references, technique
   write-ups, shader/canvas techniques, e.g. Apple, Stripe, Linear, Vercel, Framer, Rauno, Active Theory, Buck,
   ManvsMachine). Write RESEARCH.md: 5–8 references (URL + what to take), and techniques new to you with how
   you'll do them in HTML/canvas/WebGL seek-safely. Pick at least one technique you have not used before.
2. Two key frames as stills first (kf-1, kf-2), look at them, fix, then animate.
3. Build the 30 s; ≥3 render rounds; every round review 10 fps strips + full-res stills of every beat; fix.
4. lint 0 errors; `check` run (declare deliberate layering); freezedetect clean.
5. Deliver in your folder: sketch.mp4 (with audio-30), kf-1.png, kf-2.png, kf-3.png, poster.jpg (most
   striking frame), RESEARCH.md, CRITIQUE.md (honest: 3 things it does well, 3 things it does badly, each with a
   timestamp, and what a full film in this direction would take), LEARNINGS.md (techniques that worked/failed,
   render times, gotchas — written for the next builder).
6. Final reply ≤10 lines.
