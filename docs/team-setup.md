# Team setup (ADR 0027)

Teammates chat with Claude on their own seats; Robert keeps every change to `main`.

## Robert, once
1. **Branch rule on `main`** (GitHub → repo Settings → Rules → Rulesets, or Branches): require a pull request,
   require review from Code Owners (`.github/CODEOWNERS` = you), block force pushes and deletion. Leave
   yourself on the bypass list. Private repos on a personal account need GitHub Pro for this; or move the repo
   to a GitHub organisation, which also gives a real read-only role.
2. **Collaborators:** repo Settings → Collaborators → add each teammate's GitHub account.
3. **Shared environment:** in Claude Code on the web, open your environment's settings and share it with the
   organisation ("Who can use it"), or create an org environment in claude.ai admin settings. Put a separate,
   capped ElevenLabs key in it: on Team plans, anyone using the environment can read its variables.
4. **Seats:** each teammate needs a Team seat that includes Claude Code.

## Each teammate, once
1. Sign in at claude.ai/code (or the Claude app → Code) with their work account.
2. Connect GitHub when asked and choose this repository; pick the shared environment.

## Day to day
- New video: "Make a <destination> video for <brand> about …". Attach images in the chat.
- Files: attach images in the chat. For footage or anything large, paste a Google Drive link set to "Anyone
  with the link" (turn it off afterwards).
- Feedback: reply in the same session. The finished video is sent back in the chat.
- Done: "save learnings" → a PR to Robert (`save-project` skill). After he merges, a new session can reopen it.
- New client, rule change, new concept: ask Robert.

## Verify before rollout
- A teammate's Drive link downloads (Workspace link-sharing settings can block it).
- A finished render (tens of MB) arrives in the teammate's chat. If not, add a Drive upload step.
- A teammate session can open a PR, and cannot merge it.
