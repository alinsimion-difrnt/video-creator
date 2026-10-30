# 0027 — Team access: teammates make videos, Robert owns the rules

- **Status:** proposed (Robert, 2026-10-12)
- **Date:** 2026-10-12

## Context
Robert wants teammates to chat with Claude, ask for videos, upload references, give feedback and get the
final file, on their own Claude Team seats (their own usage). Rules, clients (brands), training (corpus,
taxonomy, exports) and code stay his. Teammates should be able to save approved projects so they can reopen
them later. Slack (Claude Tag) and a ClickUp routine were considered: the first needs a paid Slack, the second
runs everything on Robert's seat and turns chat into task comments.

## Decision
- Teammates use Claude Code on the web with this repo, as GitHub collaborators, in an org-shared cloud
  environment.
- Everything they keep comes back as a PR from the `save-project` skill: `projects/<p>/**` text files and
  `projects/<p>/learnings.md`. Brand, rule or default changes are written as proposals in that file; Robert
  promotes them.
- `main` is locked by GitHub: `.github/CODEOWNERS` names Robert, and a branch rule requires a PR and code-owner
  review. The "Team mode" section in CLAUDE.md is a courtesy layer only.
- Large incoming files (footage, references) come as Google Drive links shared "Anyone with the link"; sessions
  download them directly (worked for ~200 MB files before). Finished videos go back in the chat. A Drive
  service account for uploads is only worth building if chat delivery fails for large renders.
- Setup steps: `docs/team-setup.md`.

## Consequences
- Teammates can read the code (GitHub has no "use but not read"). Accepted.
- On Team plans anyone using the shared environment can read its secrets: use a separate, capped ElevenLabs key.
- "Anyone with the link" makes a client file reachable by anyone who has the URL: turn sharing off after the
  session. If the Workspace blocks link sharing outside the domain, the download fails.
- An unmerged project lives only on its PR branch; prompt merges keep it reachable.
