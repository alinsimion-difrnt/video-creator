# create (Phase 2)

Turns a brief into a premium SaaS explainer, reusing what `lens` measured (`exports/`). Plan:
`docs/phase2-plan.md`. Stages C1-C13 are registered in `lens/stages.py` with the exact paths they write,
so `lens dag --check` and the write guard cover them like every Phase 1 stage.

    uv run create init <project>     # projects/<project>/ and data/create/<project>/
    uv run create status <project>   # each stage: done, ready, waiting, invalid or optional

A project keeps small text artifacts in `projects/<project>/` (brief.yaml, script.yaml, voice.json,
timeline.json, ...; validated by `uv run lens validate`) and media in `data/create/<project>/` (never
committed). The brand hand-off in `brands/<brand>/` (named by the brief, ADR 0022) is an input no stage writes.

Build routes (ADR 0032): a tts brief builds the **motion** way by default. `create direction <p>` writes
`projects/<p>/direction.md` (word clock, brand CSS and DESIGN.md rules verbatim, measured motion, pacing and
sound ranges, the recipe menu and the learned rules from config `create.motion`); the `motion-builder` agent
builds one composition in `projects/<p>/motion/` (index.html, sfx.json) with its own taste inside it;
`create grade <p>` renders and checks it (layout, contrast, brand colours and decoration, move lengths, text
size, accent moments, overlaps, lens pacing, SFX, length) into `motion/grade.json` plus review sheets;
`create music <p>` makes the bed built for the video (cached by plan, dropout check) and `create mix <p>` the
final file. The skill `.claude/skills/build-motion` has the whole flow. `build: templates` keeps the
storyboard + template route below.

Frames (ADR 0023): the brief's destination picks a frame from config `create.design.frames` (landscape
1920x1080, vertical 1080x1920 with the TikTok/Reels/Shorts safe area). `uv run create audit
<project>` checks every built scene's text and logos against that frame's safe area and caption band.

Captions (ADR 0024): `uv run create captions <project>` groups the timeline's words by the frame's rules;
`uv run create burn <project> --plate film.mp4` burns them on with the brand's caption style
(`create/kit/captions.html`) and checks the output is frame-exact.

Presenter footage (ADR 0025, `voice: presenter` in the brief): `create ingest | transcribe | cuts | edl |
reframe | timing | edit`, then `captions` and `burn`; `create pip --background <video>` sets the presenter's
layout per scene (`layout.yaml`: full, corner bubble, off). Robert approves cuts in `projects/<p>/cuts-approved.yaml`. How to
film: `docs/filming-guide.md`.

Presenter reels (ADR 0026): after `edit`, `reframe` and `captions`, `create reel <p>` renders the whole video in one
pass from `projects/<p>/reel.yaml`: layouts from a word on (full, split, pip, off), animated widgets from
`create/kit/motion.js` on the presenter's words (entrance styles per widget, code-drawn pixel art), captions above the head or above the seam (never on the face or
chest), a push-in per shot, punch-ins on key words and a light grade. `create reel <p> --preview 2,5.5,9` writes a
contact sheet without rendering; `create reel <p> --draft` renders half size in ~4 min for review rounds (full size ~6 min); `create reel <p> --check` checks the plan and where every widget lands (no
render); `create qa <p> --video <file>` checks the result; `create review <p> --video <file>` writes a contact
sheet, motion strips and a brief for a fresh-eyes review (`.claude/skills/review-reel`). `create prep <p>` runs edl,
reframe, timing, edit and captions after the cut approvals. `create cuts <p> --page` writes a phone page for the cut decisions; `create cover` and the write-post skill
package a finished TikTok; the process-take skill runs the whole flow from a full video Robert sends to the
finished versions. `create words <p>` prints
the take's words with their indexes; `.claude/skills/draft-reel-plan` drafts a plan from them.
