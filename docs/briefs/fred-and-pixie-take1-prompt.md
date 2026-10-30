# Prompt: Robert's Fred & Pixie video (take 1)

Paste everything below the line into a new Claude Code chat on this repository, and attach the fish photo
(the common carp picture) to that message.

---

Build my Fred & Pixie video from the take I filmed. Work on the branch `claude/ai-tiktok-video-concept-507k4d`
of VijaRobert/explainer-video-creator. It holds everything a previous chat built and learned, so read these
first and follow them:
- `CLAUDE.md`;
- skills `character-animation`, `pixel-art`, `draft-reel-plan` and `review-reel`;
- `docs/decisions/0027…`, `0028…` and `0029-animation-lab-and-real-3d.md`;
- `docs/learnings/animation-lab.md` (20 test reels and an audit; its rules are hard-won, so don't relearn
  them);
- `docs/filming-fred-and-pixie.md`;
- `docs/lab/v20.yaml`, the plan of the demo I liked best: its structure, written in words.

## The footage
- **File:** `https://drive.google.com/file/d/1dybeU9P_N7m7qO8_5dZ0FdIOM-ubaCTQ/view`, a 640 MB DJI clip.
  Download it with `curl -L "https://drive.usercontent.google.com/download?id=1dybeU9P_N7m7qO8_5dZ0FdIOM-ubaCTQ&export=download&confirm=t"`.
- **Format:** 3840×2160, **30 fps** (not 60), 7:12, SDR bt709. It is media, so keep it in data/ and never
  commit it.
- **Shot:** one wide, static shot. I sit in a yellow armchair in the middle of the frame: a wooden slat wall
  behind me on the left, a floor lamp and a white bookshelf on the right, grey carpet.
- **Vertical:** a 9:16 crop around the chair is 1215 px wide at 4K, so the TikTok version stays sharp
  (F5 reframe).
- **Transcript:** a previous chat transcribed it with ElevenLabs Scribe, but the transcript isn't in the
  repo. Run the normal footage pipeline (`create ingest` → `transcribe` → `cuts`, using the keyterms
  Fred, Pixie, Claude, ElevenLabs, Acme, Cloudflare). I improvised, so the transcript is the truth,
  not the old script.

## Cuts (times on the original clip)
- **Start:** cut everything before **31.4 s** (chair and mesh notes to Claude, "Three, two, one, let's go").
  The video starts on "This video is entirely edited by AI".
- **End:** "Pixie, no!" is at 426.3 s. At 426.5 I lean and reach out toward screen **left**, at
  427.5 I jump up and run out of frame on screen **left**, the chair is empty from 428.5, and I walk back
  in at about 431. **Cut at about 430.5**, on the empty chair.
- **Black holes:** at 385.4–401.0 I sit silently for 15.6 s, waiting for "a random explainer about how black
  holes work". **Keep that span**: it is filled (see below). Remove the other dead air, ums and repeats
  with the cut rules; send me the cuts to approve.

## Two versions
1. **TikTok, about 75–90 s, 1080×1920.** The cold open, the hook, the real fish and Fred's transformations,
   the arm-and-a-leg gag, 4–5 of the best process lines (pick the ones with the best Fred gags), the
   black-hole mini explainer (shortened to 6–8 s), and the Pixie payoff with the RIP card.
2. **Full version, about 6.5 min.** Everything, tightened, with Fred's gags spread through it. Make it
   1080×1920 too, unless you think 16:9 serves the long one better (say why).

## The beats (timestamps on the original clip)
- **Cold open (first ~1 s of both versions).** A flash-forward of the payoff: Pixie snatching Fred and me
  diving off the chair (~426–428 s). Then a record-scratch, a freeze frame and a quick rewind whoosh into
  "This video is entirely edited by AI" (33 s).
- **The hook needs extra energy** on the first line:
  - zoom punches on "entirely" and "zoom in, the zoom out" (36.7 s): do the zooms as I say them;
  - a glitch;
  - Fred peeking into frame for half a second.

  Something must happen every 1–2 s in the first 5 s.
- **"Hi, my name is Robert" (43.6):** a name sticker. Keep the intro short in the TikTok version.
- **"without losing maybe an arm and a leg in costs" (67.9 "arm", 68.3 "leg"): the Fullmetal Alchemist
  homage on me.**
  - My arm and leg turn to steel automail (a metallic overlay on my right arm and leg), with a
    transmutation circle under the chair, sparks and a flash.
  - It doesn't need to be perfect; a rough overlay is fine.
  - Use a local pose or matte model to place it: no paid APIs.
- **"So take a look at this fish" (88.4).** Through the whole fish beat (88–104 s) my hands frame an
  invisible fish in front of my chest: one hand up near my face, the other palm-up at my belly. **Put the
  fish between my hands.**
  - First the **real fish photo** (attached: the common carp from our first family fishing trip), with a
    small hand-drawn arrow and the label **"Our first catch 🎣"**, and under it, smaller, "first family
    fishing trip".
  - "Let's make it 3D" (90.9): the 3D turntable.
  - "pixel art" (95.0): pixel style, and I go blocky for that beat (hearts and a hotbar), as in the lab
    demo.
  - "call it Fred" (98.1): the name tag and a wave.
  - "a mustache and maybe a top hat" (101.1 and 103.0): they land on him.
- **"I will just leave Fred here" (104.8–105.8).** I lean to my left and set him on the **floor to the
  right of the chair** (screen right, by the bookshelf). From here to the end, that floor spot is Fred's
  stage.
- **Fred's gags while I explain (112–384 s).** He does random stuff, each gag with a sound (ElevenLabs
  sound effects through the subscription; no other paid APIs). Time them to my words:
  - "100 explainer videos on YouTube" (154.9 / 156.6): he watches a tiny screen with popcorn (crunch);
  - "screenshots every zero point three seconds" (171.1): he takes photos (camera **flash and shutter**
    sound);
  - "feedback" (187.4): he holds up a thumbs-up and thumbs-down card (ding / buzz);
  - "GitHub repo… memory" (200.9 / 219.3): he scribbles in a notebook (pencil scribble);
  - "R2 bucket on Cloudflare… free plan" (240.2 / 246.3): he drops things into a bucket (clunk) and
    shows a "FREE" sign;
  - "Claude, don't show the API key here, please" (260.2): a fake API key appears, a black CENSORED
    bar slams over it (bleep), and Fred covers his eyes;
  - "a swoosh or maybe even a piano" (279.2 / 282.2): an actual swoosh, then Fred plays a tiny piano
    (piano notes);
  - "change the fonts… the colors" (314.3 / 316.6): his look changes (the accent recolour);
  - "change a dog with a bird" (320.6 / 321.5): poof, he becomes a dog (woof), poof, a bird (tweet),
    poof, back to Fred;
  - "multiple variants" (334.7): three Freds side by side, then two vanish;
  - "voiceover… the rhythm of the voice" (359.3): he conducts with a baton;
  - somewhere in a quieter stretch: he **rows his boat** through the air around me (paddle and water
    splash sounds), and reads a book.
  - Keep him in the safe area, above TikTok's bottom UI.
- **Black holes (384.5 "black holes", 385.4–401.0 silence).**
  - A real mini explainer about how black holes work, as a cutaway. Narrate it with an ElevenLabs voice
    and write the script yourself: accurate, simple, under 15 s full and 6–8 s short.
  - As a gag, Fred gets pulled toward the black hole and spirals in. He pops back out onto the floor
    when we return to me on "Yeah, I think that's enough" (401.7).
- **Pixie (417–430 s).**
  - "And I think that's… Wait." (417.0): I look down. Pixie walks in from screen right (meow sound) to
    Fred's floor spot, next to him.
  - "Okay, that's a cute cat" (420.3): she looks at the camera.
  - "I think I'll call it Pixie" (423.1): the name tag.
  - "Pixie, no!" (426.3): she pounces, grabs Fred crosswise in her mouth, and runs out of frame on
    screen **left**. I dive after her (that's real; time her run so I'm chasing her). A shake on the
    grab, cat and chase sounds.
- **End card.** On the empty chair, a fade into **"RIP Fred 🐟"** with a happy, satisfied Pixie (licking
  her paw, a tiny crown or a halo-fish above her), then a small credit line: **"Character Pixie credited to Pet
  Foolery by Ben Hed"**, with the Webtoons link
  `https://www.webtoons.com/en/canvas/pixie-and-brutus/list?title_no=452175` in the description I post. Pixie
  is our own original drawing in the comic's spirit, not a copy; keep it that way.

## Fred's design: please redesign him first
I didn't love the old Fred (the orange cartoon goldfish). Base the new Fred on **our real fish**, a common
carp:
- an olive-gold body with a darker back and a golden belly, a visible scale pattern;
- **orange fins and an orange forked tail**;
- small barbels at the mouth;
- a round eye.

Keep him upright on his tail with fins as arms, as before. He has to match across all his styles:
illustrated rig, 3D (create/render3d), pixel (create/pixel).

Show me a design sheet of the three styles side by side, and a short motion test, before animating the
whole video. Ask me what I think before going further.

## Sound
- A sound for every gag, at the right moment, mixed under my voice.
- Light background music only if it doesn't fight my voice.
- Normalize to TikTok loudness (existing `create` audio rules).

## Process (follow the repo's)
1. Ingest, transcribe, cuts. I approve the cuts.
2. Run `create prep`, then the matte for the props behind or around me.
3. Redesign Fred and show me.
4. Draft the reel plan (skill draft-reel-plan) for the TikTok version first.
5. Run `create reel --check`, `--preview` and a draft render. Review it with the motion strips and a
   fresh-eyes reviewer agent (review-reel). Fix and log the lessons in `docs/learnings/`.
6. Show me the TikTok draft. After my feedback, make the full version.
7. Commit code, plans, skills and learnings as you go, but **never commit media**: no footage, no fish
   photo, no renders, no voices.

Ask me anything you need before you start.
