---
name: tiktok-edit
description: Plan or check a TikTok reel for Robert (talking head on AI, marketing, Claude, GEO, SEO, with widgets and a pixel mascot) against what 194 measured TikToks in that niche do (studies/tiktok/findings.md). Use when drafting a reel plan, choosing a hook, deciding how many graphics, captions, CTA and length, or reviewing a cut before rendering.
---

# tiktok-edit

These rules come from the TikTok study (`studies/tiktok/findings.md`, section 10): 194 videos, measured by code
and named by Claude. Numbers are medians from `studies/tiktok/stats.json`, unless they name the notes. Read
the findings for the evidence; read `studies/tiktok/studied.md` for examples to watch.

Any script or line he will say is written in his voice: read `brands/acme/VOICE.md` first (a blunt claim,
a concrete test, a hard last line, no hedging).

## The rules
1. **Length.** 30-75 s, aiming for about 50 s, with one idea per reel. The top quarter by plays runs 49 s, the
   rest 60 s.
2. **Hook at 0.0 s.** No intro and no credentials first. By 2 s, show the result, the object or a one-line
   reversal. Patterns that work:
   - the result in frame one;
   - a physical move;
   - the mascot acting out the hook verb;
   - a number promise with fingers or a title pill;
   - a callout naming one viewer;
   - claim, then the answer within 2 s.

   Curiosity gaps and pattern interrupts are overrepresented in the top quarter.
3. **Voice.** 3.0-3.8 words/s, silence ≤ 15 %.
4. **Face.** On screen 60-90 % of the time (the top quarter is at 0.76), 0.19-0.35 of the frame tall, centred
   around 0.45. Hand the frame to proof only for its beat.
5. **Graphics.**
   - 3-7 graphic events a minute: one per idea, on the word that names it, one new element at a time.
   - Stay under about 10 graphic changes a minute, caption pops included. "Heavy" (about 25 a minute) belongs to
     faceless formats.
   - Clutter is layers competing: text over text, cards too fast to read.
6. **Still, never static.** The picture changes at least every 10-15 s. "Too static" is the most common weakness
   (87 of 194 notes).
7. **Zooms.** 0-1.5 punches a minute, saved for the key line. The median video has none.
8. **Captions.**
   - Word-by-word or 2-3-word chunks, at least 0.045 of frame height (about 86 px at 1920).
   - One fixed band that never jumps. Nothing overlaps it.
   - All text inside the safe core: x 120-780, y 288-1248.
   - One persistent title label (topic, plus "Part N" for a series), pinned top or middle.
9. **Proof.** Show every claim within about 3 s of saying it (screenshot, number, AI answer), big enough to read.
   GEO reels in the sample almost never show proof, which is the gap to fill.
10. **Mascot (Fred).** 2-4 appearances of 1-3 s each, each with a job: act out the hook verb, point at or tap
    the proof, hold the number or keyword, doubt or react. He exits between appearances and returns for the CTA.
    Never a static badge, and never on screen the whole time. 14 of 22 characters in the sample come back; 3 of
    the 4 pixel mascots did not, and the notes flag it.
11. **Lists.** Show an on-screen counter: fingers, "2/4", or Fred holding the number.
12. **CTA.** One ask, best comment-a-keyword, placed 2-7 s before the end (median 0.92 of the length). Never
    two stacked.
13. **Ending.** Cut right after the payoff, or end on the line that leads back to the start (a loop).
14. **Sound.** About -16 to -21 LUFS, with a quiet music bed in the gaps (about -27 dBFS in the top quarter).
    Sound effects are rare; give them to Fred's actions.

## By topic (findings section 9)
- **AI:** trend hooks, curiosity gaps, comment-keyword asks.
- **Claude:** split screen with UI cards; "N codes / N plugins" lists.
- **GEO:** talking heads with almost no visuals, so proof visuals stand out.
- **Marketing:** faster cuts, skits, follow asks.
- **SEO:** long tutorials and "Part N" series.

## Checking a cut
Measure the render with the study's code and compare it with the rules above:
`uv run python -c "from study.tiktok.measure import measure; ..."`, or copy the render to
`data/study/tiktok/<id>.mp4` with a `<id>.json` holding `{"duration_s": N}`, then run
`uv run python -m study.tiktok measure <id>`.

Compare: length, words/s, face share, events per minute, punches per minute, caption height,
outside_safe_share, first cut.

For pixel-art acting and the look of Fred and Pixie, use the pixel-art skill and
`studies/pixel-art/findings.md`. The two studies are kept separate; `studies/combining.md` says how they meet.
