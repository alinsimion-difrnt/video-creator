---
name: review-reel
description: Fresh-eyes review of a finished presenter video from the files `create review` wrote (contact sheet, motion strips, brief). Give it to a subagent with no other context; it scores the video on the brief's rubric and lists the remaining problems by frame. Use after `create qa` passes, before sending a video to Robert.
disable-model-invocation: true
---

# review-reel

You judge a finished vertical video as a senior short-form editor would, from frames only. You were not part of
making it: that is the point. Do not open the plan, the code or earlier reviews.

## Inputs
- `data/create/<p>/review/<video>/brief.md` — read it first; it names the only files you may open
  (`sheet.png`, `motion.png`), the platform's UI zones and the client's notes.

The brief says what kind of edit it is (layout or overlay, with or without cutaways) and the house rules:
captions never on the face or chest; widgets never on the face, but on the chest by design in an overlay edit.

"Brand consistency" means the brand's fixed parts: captions, logo, end card, brand text and type. A acme
video (ADR 0031) may use any colours and style in its animations when they fit the topic; judge whether they
fit and hold together across the video, not whether they are on-palette.

## How to look
- **Sheet**: rows of frames, one every few seconds. Read it left to right. For each frame ask: does the
  graphic show what the caption says? Is anything on the face or chest? Is anything in a UI zone? Is the
  frame empty or the same as the last one?
- **Motion strips**: 8 frames 0.1 s apart. Does the widget build (types, counts, lights up, springs) or only
  fade? A half-transparent grey card in the middle frames reads as a muddy ghost.
- **Flow** (ADR 0033): where one product card follows another, is there a frame with nothing, a hard swap, or
  does a surface carry over (one card becomes the next, slides into its place, or lands on it)? Does the step
  label stay put while the cards change under it? Across the sheet, does the video move in one style (its
  entrances, hand-overs and background agree), and does the top half react to the cuts below it?
- **Crops**: each widget at full resolution once built. Judge text size and finish here, not on the sheet.
- Each sheet frame is stamped with its time; motion strip rows are named in the brief. Give positions as
  time (and row/column), and estimated pixels when it matters (1080x1920 frame).

## Report (in your final message, under 500 words)
Scores 1–10 for each rubric line in the brief and overall; the remaining problems, most important first, each
with where you saw it; whether you would post it as is. Be specific enough that a fix can be written from it.

## Notes for the person running the review
- Run it as the `reel-reviewer` agent (`.claude/agents/reel-reviewer.md`: Read only, a smaller model). A review
  on the most capable model cost about 70k tokens; most of that is not needed to judge frames.
- Reviews are advice. Fix problems in the plan or the kit, run `create reel --check` and `create qa`, and
  render again. Five rounds on the first take moved the scores from 5.5–6.5 to 6–7; after that, reviewers
  start contradicting each other (cards off the chest vs readable cards). Hand those trade-offs to Robert.
