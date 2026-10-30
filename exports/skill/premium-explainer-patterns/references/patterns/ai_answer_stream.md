# AI Answer Streams In

`ai_answer_stream`

An assistant's reply appears piece by piece, line by line or word by word, while the surrounding chat or page shifts up to make room, so the viewer watches the answer being generated live.

## When to use
- Showing an AI assistant or agent answering a question in the product
- Proving automation is working by letting real output or progress lines arrive
- Following a typed prompt, as the payoff beat of a prompt-and-answer demo

## Avoid when
- The answer is long and the viewer needs to read it all; show the finished result instead
- The scene has no input or question that the answer clearly responds to

## Build
1. Lay out the finished answer first, split into lines, bullets or words, and hide every piece
2. Optionally grow the reply container from a small typing-indicator pill or show a short status line with a spinner
3. Reveal the pieces in order with a short fade and small upward rise, at a steady cadence
4. As each piece lands, push the thread or page up so the newest content stays in view
5. If there is narration, key each word or line to the moment it is spoken
6. Finish with a clear end state, such as follow-up cards, an action menu or the assistant icon settling

- GSAP / HyperFrames: Use a timeline with gsap.fromTo on the answer pieces (autoAlpha and a small y offset) and a stagger between them; mostly ease-in, ease-in-out or linear eases, with ease-out on settles and an occasional back-style overshoot for avatars or icons. Run a parallel gsap.to on the thread or panel y to scroll it up. For a terminal feel, use stepped (steps) eases so lines snap in.
- Remotion: Give each piece a start frame and drive opacity and translateY with interpolate, or a damped spring with no overshoot for softer rises; for a stepped generation feel, show a piece only once frame passes its start. Move the thread container with interpolate or a heavily damped spring, and grow the reply bubble's width and height with a livelier spring from pill size.

## Measured in premium explainers
- Duration: 55-840 ms (typical 238), 5 videos
- Easing: ease in 31%, ease in out 25%, linear 23%, ease out 11%
- Changes: fade 40%, slide up 28%, morph 7%, scale up 5%
- Sound offset to the landing: 50-83 ms (typical 67), 1 videos

## Sound
No typical sound; the corpus examples sit under music only, so let the score carry it and key text to the voice if there is narration.

## Why it reads as premium
The answer earns trust because it arrives the way real generation does: discrete lines or words at a steady rhythm, with the surrounding page reflowing to make room, rather than a block that simply appears or a generic spinner. Premium versions add small signs of live work, like a reply bubble born from a typing pill, a shimmering status line or a thinking mascot, and they lock the text to the narration so speech and screen agree. The end of the stream is used as a hand-off, landing follow-up cards or an action menu so the next beat starts without a cut.

## Caveats
- Measured element durations vary widely, from snap-in terminal redraws to slow rises, so the confidence interval is broad
- The easing mix is split with no dominant family; pick per piece rather than one ease for everything
- Sound was only labelled as music, in a single video, so there is no evidence for a dedicated effect
