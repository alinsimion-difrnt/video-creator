---
name: save-project
description: Save a teammate's approved video project and what was learned on it as a pull request to Robert. Use when a teammate says "save learnings", "save the project" or approves a finished video. Commits only projects/<p>/ text files plus projects/<p>/learnings.md; never rules, brands, corpus or code.
---

# save-project

Team mode (CLAUDE.md, ADR 0027): teammates make videos; Robert owns the rules. This skill is how a teammate's
work comes back to the repo, so they can reopen the project in a later session and Robert can promote what
was learned.

## When
The teammate approved the video (or asked to save work in progress). Ask once if unclear: "Save
`<project>` and its learnings as a PR to Robert?"

## Steps
1. **Learnings.** Write or update `projects/<p>/learnings.md` from this session only:
   - `## Approved` — date, who approved (their name as they gave it), destination, length, which render.
   - `## What worked` and `## What they changed` — their feedback in plain words, each with the scene or word
     index it was about. No timestamps you did not get from code.
   - `## Proposed for Robert` — anything that would change a brand, a rule, a skill or a default. Proposals
     only: never apply them.
   - No client secrets, no personal data beyond the teammate's first name, no verbatim third-party copy.
2. **Scope check.** Only these may change: `projects/<p>/**` text files (yaml, json, md). Run
   `git status --porcelain` and stop if anything else is modified; leave it out of the commit and tell the
   teammate. Never stage media or images (`.gitignore` covers most; check anyway): uploads and renders stay in
   the session and in `data/` (never committed).
3. **Validate.** `uv run lens validate --all` and `uv run lens dag --check` must pass.
4. **Branch and PR.** Branch `team/<p>-<yyyymmdd>` from `origin/main`, commit with a message naming the project
   and the teammate, push, open a PR to `main`:
   - Title: `Project <p>: <one line>` (`Project acme-v2: approved LinkedIn cut`).
   - Body: what the video is, who approved it, the learnings summary, the `Proposed for Robert` list, and the
     changed files.
   - Never merge, approve or enable auto-merge. Robert reviews (CODEOWNERS).
5. **Hand back.** Give the teammate the PR link and say: once Robert merges it, any new session can reopen
   `<p>`; until then, it lives only on the PR branch (a new session can start from that branch).

## Reopening a project later
A teammate starting a new session on a saved project: read `projects/<p>/learnings.md` first, then the
project's brief and plan. Media (voice audio, renders) is not in the repo: rebuild it with the `create`
commands; `uv run create status <p>` shows what is missing. Ask before anything that spends ElevenLabs
credits (`create voice`).
