# Start here

A toolkit for making premium SaaS explainer videos with Claude Code: `lens` measures what makes good explainers
good (a corpus of measured videos, exported specs), `create` builds your own videos from a brief (script, voice,
timing, brand tokens, motion, music, mix) and grades them against that corpus.

It ships with no real brand. `brands/acme/` is a made-up demo brand used by the tests and the example
projects (`projects/acme-v2`, `projects/demo25`, `projects/acme-reel`). Add your own brand next to it.

## 1. Make it your repo
```bash
unzip explainer-starter-kit.zip && cd explainer-starter-kit
git init && git add -A && git commit -m "Start from the explainer starter kit"
```
Create an empty private repo on GitHub, then `git remote add origin <url>` and `git push -u origin main`.
To use it from claude.ai/code, connect that repo there.

## 2. Install and check
Needs Python 3.12, [uv](https://docs.astral.sh/uv/), ffmpeg, espeak-ng (tests) and Node 22 (renders).
```bash
make setup
make fixtures
make check
```
`make check` runs lint, types, tests and the validators; it should pass before you change anything.

## 3. Add your brand
Open Claude Code in the repo and say: **"add my brand"** (the `add-brand` skill). Have ready:
- your logo as SVG (one colour version for light backgrounds; optional on-dark and mono versions),
- your colours (hex) and what each is for, especially the one accent colour,
- your fonts (Google Fonts only, OFL licence),
- the product name, how it is pronounced, its URL and the video language.

The skill writes `brands/<your-brand>/` (tokens.json, video.yaml, DESIGN.md, FONTS.md, REVIEW.md, logo/) and
loops on `uv run create tokens <project>` until every contrast pair, type size, glyph and string passes.
`brands/README.md` documents every field if you prefer to do it by hand.

## 4. Make a video
```bash
uv run create init my-first-video --brand <your-brand>
```
Then ask Claude Code to "build the motion explainer for my-first-video" (skill `build-motion`). The main
commands are listed in CLAUDE.md; `create/README.md` explains the stages.

Voice uses an ElevenLabs subscription (`ELEVENLABS_API_KEY` in `.env`, never committed). Nothing else is a paid
API: visual review runs as Claude Code subagents.

## Good to know
- CLAUDE.md is the rulebook Claude follows here. Read its hard rules once; they keep media and secrets out of git.
- Skills and docs written for the original owner's presenter videos (process-take, build-panel, tiktok-edit,
  write-post, character-animation, pixel-art) work for anyone; read "Robert" as "you".
- The corpus under `videos/`, `corpus/` and `exports/` is measurement data (JSON), no third-party media.
