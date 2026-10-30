---
name: process-take
description: Robert's whole presenter-video flow from his phone — a full TikTok video he sends becomes a cut-approval page he taps through, then, after he sends the approval back, a TikTok video with a bespoke animated panel, cover and post text, checked and reviewed. Use when Robert sends a video to edit.
---

# process-take

Robert is usually on his phone: everything he has to do is tap a link, read, and send a message back. Keep
him to two touches at most: the cuts (often decided in the message that brings the take), then the video. Read what he wants and what the last videos
taught, not the whole playbook: `sed -n '/^## 0\./,/^## b\./p' docs/learnings/presenter-reels.md`.

## Claude usage
CLAUDE.md "Claude usage" holds (x-ads, facebook-algorithm and acme-reel cost $3.5, $7.8 and $25 of Opus, almost
all in the main session). Here that means: one video per session; images, plans and reviews are the
`lab-reviewer`, `reel-planner` and `reel-reviewer` agents' work (the panel page is yours, from the starter);
renders run in the background; the commands below are complete (no `--help`, no other projects as templates).

## 0. Get the video
- Robert films on his own and sends the full TikTok video in the chat (an upload or a link he pastes). Use
  that file; don't go looking for takes in Drive or elsewhere. `<p>`: a short slug for the topic, e.g.
  `reviews-context`.
- His message may already decide the cuts: "cuts: all" (every proposed cut), "cuts: all, keep 0:41" (all but
  the ones near those times on his take). The cut approval is his gate: only his words decide it, never a guess.
- If you name the session, `set_session_title` needs this session's id: `get_session` first.

## 1. Project and transcript (no input from Robert): one command
- Colour or sound to fix first (he asks for DaVinci/Resolve, or the take is a flat-looking or quiet DJI Mimo
  file): skill `resolve-fix-take`, then feed its render to `create take`.
- `uv run create take <p> --video <file> [--term "X Lift"]...` (a `--term` per name he may say that the
  speech-to-text could miss; `--brand <b>` for another brand than acme). It writes a provisional brief,
  links the take into `data/create/<p>/footage/raw/` (never committed), ingests, transcribes with ElevenLabs
  (approved for his own footage; the language is detected), proposes cuts, writes the phone page and prints the
  cuts and what he says as text.
- **He decided the cuts in his message:** add `--approve [--keep 0:41,1:05]` and chain the rest:
  `uv run create take <p> --video <file> --approve --keep 0:41 && uv run create prep <p> && uv run create words
  <p> --times`. No cut page, no waiting: edit the brief (next line) and go on to step 2's build. Tell him in the
  video's message which cuts were kept in, and any `--keep` time that had no cut near it.
- Read the brief and replace its TODO lines from that text (one Edit): the topic in `one_liner`, `audience`, `tone`,
  `message`, another brand's product, and one `facts` entry per claim he makes about a product or a number,
  with the source you checked.
- Otherwise publish `data/create/<p>/cuts.html` with the Artifact tool and send Robert the link, with one line:
  how long the take is, how long it will be, anything odd (a retake, the count-in), and that next time "cuts:
  all" (or "all, keep 0:41") in the message with the take skips this page.

## 2. After the cuts are decided
- From the page: he sends back `create cuts <p> --approve all --reject ...`; run it chained: `uv run create cuts <p> --approve ... && uv run create prep <p> && uv run create words <p>
  --times`.
- **Default: the bespoke panel (ADR 0034, skill `build-panel`).** `create panel --init` (it writes the split base
  plan), start the base render in the background, write the beat sheet and the page, a `lab-reviewer` on the
  stills, then render, QA, review and cover as the skill says. One version, done well, beats two template
  versions.
- **Kit widgets only when Robert asks for them** (or for a quick draft): two plans, in parallel, as
  `reel-planner` agents (`layout` → `projects/<p>/reel-layout.yaml`, `overlay` → `projects/<p>/reel-overlay.yaml`),
  each looping on `--check` to 0 errors, rendered one after the other (they share one work folder:
  `create reel --check/--preview` on another plan during a render overwrites it).
- `uv run create qa <p> --video <file>`: fix every FAIL before anything else.
- `uv run create review <p> --video <file>` (a panel video adds `--at <settled times>`) and one `reel-reviewer`
  agent on its brief. Fix what it finds, and stop when reviewers start to contradict each other
  (docs/learnings/presenter-reels.md §d).

## 3. Package and send
- `write-post` skill → `projects/<p>/post.md`; the cover is `uv run create cover <p> --split ... --onto <render>`
  (title above the seam, never on his face; it writes `<render stem>-cover.mp4` with the cover as frame 0; a kit
  layout version also passes `--video <render> --plan <its plan>`; an overlay version has no seam: the same
  command with the layout render and plan, `--onto <overlay render>`).
- Compress that `-cover.mp4` for the phone (`ffmpeg -crf 26 -preset slow -c:a copy` into `data/share/`, under
  ~25 MB) and send it, the cover and the post text (inline, so he can copy it) with SendUserFile.
- One short message: what is in the video, the QA result, anything he must decide or check (`[?]` items,
  made-up example numbers).
- With it, the edit page, so he can correct it himself:
  `uv run create edits <p> --page --plan projects/<p>/reel-base.yaml --video <render>` (a kit version: its
  `reel-<type>.yaml`) → publish
  `data/create/<p>/edit.html` with the Artifact tool (it holds his footage: private, never committed).

## 4. When he sends an edit-page answer (a JSON object with `"edits": "<p>"`)
- Save it to a scratch file and run `uv run create edits <p> --apply <file>`. It writes
  `projects/<p>/edits.yaml`. Values, not wishes: don't reinterpret his crops or zooms, and don't "improve" them.
- Shot crops: `create reframe <p>`, `create edit <p>`, then the reel. Zoom changes only: just `create reel`
  with the same `--plan` (it applies them). Then `create qa` as in step 2.
- Notes: act on each one at its time (a panel note is a targeted Edit of the page; a plan, kit or cut note
  likewise). Mark it `done: true` in edits.yaml once handled. Say in one line per note what you changed. If a note
  can't be done, say why, rather than re-rendering the same thing.
- On the panel route a re-rendered base is not the video yet: `create panel <p> --base <new base>` (background),
  `create qa`, `create cover <p> --split ... --onto <new panel render>`, then send the new `-cover.mp4`.
- Send the new render and a fresh edit page (it starts from his last values).
- An answer that comes hours later to a long session: the cache has expired and the next request rewrites the
  whole context (one such request cost $1.21 on google-ai-links). Suggest a fresh session for it; the project
  files carry everything (section 5).

## 5. Resuming in a fresh session
- `uv run create status <p>`, `ls data/create/<p>/render/`, then only what the note needs: `projects/<p>/post.md`,
  `projects/<p>/panel/beats.md`, `edits.yaml`. For a panel note, grep the page for the beat at that time and
  read that range only.

## Rules
- Never commit media; plans, briefs, post text and notes are fine to commit on the working branch.
- Don't spend credits beyond speech-to-text without asking (music, sound effects, dubbing).
- TikTok only: build no other format (16:9, 1:1, LinkedIn, YouTube) unless Robert asks for it.
- If a step fails, say exactly which and why in one line; don't silently skip it.
