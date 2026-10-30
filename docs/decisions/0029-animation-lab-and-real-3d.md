# 0029 — The animation lab, motion rules and a real 3D Fred

- **Status:** accepted (Robert, 2026-10-11: "improve the animations, they still are strange and clunky …
  work on 20 such videos … the purpose of this chat is for you to learn a new skill")
- **Date:** 2026-10-12
- **Milestone:** Phase 2, presenter reels (follows ADRs 0027 and 0028)

## Context
The first Fred and Pixie demo ran on a synthetic take. It had:
- a test-tone hum;
- a drawn stand-in for Robert;
- motion that read as stickers: no anticipation, no grounding, fixed durations whatever the distance;
- a `toon3d` style that was only a lighting filter;
- a Pixie whose face was small square eyes at the edge of a profile head.

Robert asked for a skill, not a video: make about twenty test reels with varied animations, directions and
quirks; review, document and improve; deliver one final demo; audit; and leave everything usable in a later
chat when his own footage exists.

## Decision
- **`create lab <spec> --photo <file>` (create/lab.py).** It makes a stand-in reel without Robert:
  - a still photo becomes a plate (a slow breathing zoom, optionally a jump cut with a punch-in);
  - an ElevenLabs voice (the subscription allowed by CLAUDE.md, cached) gives real word times;
  - the plan is written in words of the script ("fish", "fish#2");
  - it writes a lab project, renders the reel through the normal `create reel` path, and adds
    motion-study strips (frames 0.1 s apart around every beat) and a scan for green edge rows.

  Settings live in `create.lab`. Media stays in data/.
- **Motion and timing rules in code**, each from a lab finding (docs/learnings/animation-lab.md). Python
  decides *when*, the kit decides *how it looks*:
  - **Distance and travel:**
    - gaited moves take their time from distance (`props.speeds`, in body widths a second);
    - walks escalate to runs when late;
    - walkers jump between heights (`jump_rise`);
    - a move waits for any move still running.
  - **Carries:**
    - a carrier stops beside its prey and on its surface (`stop_short`, `approach`);
    - the grab waits for arrival plus the pounce;
    - the prey stays until it is snatched;
    - a carried prop is at most `carry_max` of the carrier and lies crosswise.
  - **Exits and endings:**
    - exits wait for the last beat; an exit with no time left is dropped and flagged (`min_exit_s`,
      `prop-exit-cut`);
    - fade to black follows the last prop;
    - hits on a carry's word land on the grab.
  - **Kit (props.js, fred.js):**
    - contact shadows; props graded like the plate;
    - squash/stretch transformations under a short poof;
    - arcs for hops and jumps; a stretched fall with a landing squash;
    - layered secondary motion;
    - eyes on the camera that look up only with purpose;
    - items at 1.45x;
    - landings for accessories added in frame styles.
  - **Behind the presenter:** props are raised until `peek_share` of them shows outside the matte
    (`matte.alpha_at`, `props.peek_y`, measured in frame pixels via the room).
  - **Recolour:** a code edit recolours the brand accent (`caption_font {accent}`), never the presenter's
    skin.
- **A real 3D Fred (create/render3d).**
  - **Renderer:** sdf.py is a small numpy ray marcher over smooth-unioned signed-distance primitives. It
    uses wrap lighting with toon steps, fill, rim, ambient occlusion, soft shadows, 2x supersampling, a
    bounding sphere and active-ray compaction, all in float32.
  - **Model:** fred3d.py models Fred (forked tail, hinged fins, top hat, handlebar moustache, automail).
    A pose is a few numbers.
  - **In reels:** `toon3d` is now frames like pixel. He does a turntable the first time he becomes 3D (the
    proof he is a volume), then idle, hop and wave.
  - **Speed and caching:**
    - frames render in parallel (spawned workers, one BLAS thread each);
    - written atomically, they are cached under `fred3d.VERSION`, a hash of the code as loaded;
    - a new accessory set (34 frames, all four animations) renders in 54 s on 4 cores, after that zero.
  - **In the boat:** frame styles fall back to the rig, whose clay filter is tuned to match the frames.
- **Characters (skill pixel-art):**
  - Pixie:
    - a three-quarter face with big dark eyes, a shine on top and the light-blue iris below;
    - a happy-arc blink;
    - softer fur (`_soft` ramp), the head lit nearly flat;
    - new `pounce` and `jump` cycles.
  - Pixel Fred:
    - fins on his silhouette's edges, below the mouth, with no ray stripes;
    - he waves with the far fin; the clap is a cheer.
- **Skill `.claude/skills/character-animation`** holds the loop, the review order (sprite sheets, then
  strips, then full frames, then data), the motion and timing rules, and the lab pitfalls.

## Evidence
- 20 lab reels (v01 to v20) on a CC BY 2.0 stock photo ("man sitting on brown armchair while taking photo
  of a cup", John Beans, via Openverse; kept out of the repository) with the ElevenLabs voice "Chris".
- Each reel was reviewed as strips, a contact sheet and its data, and logged with what was seen, the
  cause, the fix and the lesson.
- Picked findings:
  - a green edge in every video, caused by the plate zoom dipping below 1;
  - the "beak" fin;
  - the cotton-ball poof;
  - the pounce that skated;
  - "behind" that read as "missing";
  - a recolour that turned skin green.
- A fresh-eyes audit simulated the timing code and confirmed six bugs no render had shown yet, including
  matte placement in the wrong coordinate space, which would have broken on 4K masters. All are fixed,
  with regression tests.
- The final demo is `docs/lab/v20.yaml`:
  - the hook is the fish on the first sentence (`create.qa.first_visual_max_s` is 3 s; v12's open took
    5.7 s);
  - the presenter goes blocky as Fred goes pixel;
  - the cat build-up, the peek from behind, and the pounce, grab and fade.

## Consequences
- Lab reels can test any gag before Robert films. The lab plan format is the reel plan written in words,
  so a lab plan becomes Robert's plan by swapping words for his transcript's.
- **3D cost:** the first 3D render of a new accessory set costs about a minute (54 s on 4 cores), and the
  cache is per model version. Editing fred3d.py or sdf.py re-renders everything.
- **Known limits:**
  - explainer cards are small in the split layout (widget fitting, a separate topic);
  - captions sit over the face when the shot has no headroom; Robert's framing should leave some;
  - shoulder spots are face-relative estimates (`anchors`); behind props are measured, front props are not.
- **Follow-up:** the payoff (pounce, grab, run-off, fade) needs about 2 s after the last word (the lab's
  `tail_s` is 2.4, v20). `create.qa.max_tail_s` (1.5 s, against dead air) would flag Robert's cut. The QA
  rule should count animated props as activity, not silence. That decision is Robert's; it is not changed
  here.
- 8 tests in tests/test_evidence_packets.py crash in this container's numba build. They fail identically on
  the base commit and are not this round's.

## CLAUDE.md lines (Robert applies; an agent may not edit CLAUDE.md)
In "Commands", add:
```
uv run create lab docs/lab/<v>.yaml --photo <photo> [--draft] [--preview s,s] [--matte] [--force] (ADR 0029; skill character-animation) |
```
