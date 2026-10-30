# CLAUDE.md — explainer-video-creator

## Mission
Research, understand and (Phase 2) create premium SaaS explainers. Phase 1 = `lens`: measure what makes
premium explainers premium; export reusable specs; grade our own videos.
Truth: BUILD_PLAN.md (v2.2). Audit: docs/plan-audit.md. Lessons: docs/handoff-v1.md.
Progress: PROGRESS.md. Decisions: docs/decisions/. Verified facts: docs/external-facts.md.

## Hard rules
- No pay-per-use APIs (no Gemini/OpenAI/Anthropic API keys). Visual annotation = Claude Code skills/subagents.
  Audio analysis = local tools/models only. Only exception: ElevenLabs subscription for Phase 2 voice
  (REST with-timestamps in the pipeline; the ElevenLabs MCP for interactive voice work only).
- One milestone per branch/PR; acceptance evidence in the PR. Stop at HUMAN GATES (issue `needs-robert`).
- Never commit media or images (except tiny synthetic fixtures and a project's own SVG logos under
  `projects/*/brand/logo/`, ADR 0019). Never commit secrets.
- Code measures, Claude names. Numbers about timing/easing/colour/audio come from code; Claude estimates
  only as flagged fallback (source="model_estimate").
- Annotators only use IDs given in packets (shots, words, events, box ids, SFX candidates). Never invent
  timestamps. Prefer candidate box ids; manual_box only with a reason.
- Every annotation file must pass `uv run lens validate <file>` before the task is done.
- Writes are enforced by `.claude/hooks/guard_paths.py`: when `LENS_STAGE` is set, Write/Edit is allowed
  only on the paths those stages declare in `lens/stages.py`. Bash for annotation subagents: only
  `uv run lens validate*` and `uv run lens status*`; builder agents (motion-builder, reel-planner) only the
  commands their agent file lists. Path permission rules use `Edit(...)`, never
  `Write(...)`.
- Respect annotate batch limits in config/lens.yaml. Never exceed images-per-task budgets.
- MCP servers are optional; the Phase 1 pipeline must pass without any.
- Verify external facts in official docs before relying on them; log them in docs/external-facts.md.
- Measurement code is test-first against synthetic fixtures.
- Every stage declares inputs and the exact paths it writes in `lens/stages.py`; `lens dag --check` must
  pass. No stage rewrites another stage's output. Completion = validated artifacts on disk.
- `lens/stages.py` and `.claude/hooks/guard_paths.py` stay standard-library only (the hook imports stages).
- Motion outputs are renderer-agnostic: GSAP ease + cubic-bezier (primary, HyperFrames) and a Remotion
  spring config. The spring model is first-principles physics; do not copy Remotion source (ADR 0004).
- Lowercase slug file names only (case-insensitive filesystems).
- Every output JSON has provenance (schema_version, tool_version, stage, skill_id@hash, annotator,
  input_hash, created_at). Stages are idempotent and cached.
- Exports and the skill pack contain no third-party media and no verbatim third-party copy.
- Thresholds and targets live in config/lens.yaml, never as literals in code.

## Commands
make setup | make check | make test | make fixtures | uv run lens validate --all | uv run lens dag [--check] |
uv run lens schemas export [--check] | uv run lens ingest|frames|signals|evidence|packets [--video id] [--force] |
uv run lens status [--pending] | uv run lens preview --video id [--embed] |
uv run lens measure --video id [--event eid --box b01] | uv run lens reconcile [--video id] |
uv run lens queue [--json] | uv run lens compare --video id [--targets-only] [--destination linkedin] (corpus placement by default) |
uv run lens status --fixes <video> (A4 compare-fixes brief) | uv run lens report --video id (md + html, with fixes.json) |
uv run lens gold seed|page --out f.html|import reviews.json (G2 gold set; the page is never committed) |
uv run lens storage push|pull-state|put-inbox|mark-failed|lifecycle |
uv run python scripts/fetch_batch.py (local machine: YouTube etc. → r2 inbox) |
scripts/hyperframes_answer_key.py + scripts/eval_answer_key.py (our renders' ground truth) |
scripts/golden_curves.mjs (GSAP/Remotion goldens)
uv run lens eval [--run id] [--sample] (S13: answer key, blind re-annotation agreement, measured share) |
uv run lens synth [--force] [--no-proposals] (S9: corpus/stats/*.json, taxonomy/proposals.yaml) |
uv run lens cards [--pending] [--g4-page f.html] (A3 cards -> .md; briefs: lens status --card <pid>) |
uv run lens scenes [--pending] (S9 scene stats) | uv run lens export (S10: exports/*.json + skill pack) |
uv run create init|status <project> (Phase 2: projects/<project>/, stages C1-C13 in lens/stages.py) |
uv run create init <p>-tiktok --from <p> --destination tiktok (vertical sibling: same script + voice) |
uv run create voice <project> [--dry-run] [--force] | uv run create timing <project> (P1: C4, C5) |
uv run create tokens <project> (P2: C3; needs brand/video.yaml) |
uv run create edits <project> --page|--apply f (Robert's crops, zooms, notes -> edits.yaml) |
uv run create panel <project> --init|--stills t1,t2|--base f (default presenter route, ADR 0034, skill build-panel) |
uv run create take <project> --video f [--brand b] [--approve [--keep 0:41]] (presenter start; cut page) |
uv run create words <project> [--times] | uv run create cover <project> --split --title .. [--onto f] |
uv run create panel <project> --assets | uv run create review <project> --video f [--at t1,t2] |
uv run create build <project> (P3: C8 scenes + render bundle) | uv run create sketches <project> (C7, needs npx) |
uv run create direction|grade|music|mix <project> (motion route, ADR 0032: direction.md -> motion-builder agent ->
grade [--lint-only|--snapshot t1,t2] -> music [--dry-run] -> mix; skill build-motion; default for tts briefs) |
Iterating: `make test-quick T=tests/test_x.py` (first failure, one line); `make check` once before pushing.
Tests: fixtures are generated (frame-exact video, synthetic soundtrack, espeak-ng narration); never commit media.

## Claude usage
Cost = main-session requests × context: every request re-reads it all (~85k before any work, measured).
- Every image and every long tool output stays in context for the rest of the session: keep both out of
  the main session. Image review goes to subagents (`lab-reviewer`, `reel-reviewer`, annotators), within the
  budgets in config/lens.yaml (`annotate.max_images_per_task`, `create.lab.review_images`,
  `create.footage.panel.review_sheets`).
- Use the custom agents: they start at ~7k context (general-purpose: ~59k). A panel page stays in the main
  session: a Sonnet builder spent ~135k output tokens on one, Opus ~25k (ADR 0035).
- Subagents run on Sonnet (`model:` in `.claude/agents/*.md`); keep it pinned on new agents.
- Fewer requests: chain dependent commands in one Bash call, send independent calls together, run renders in
  the background and wait for the notification (never sleep, poll or tail). Skills give exact commands: no
  `--help`. Read ranges (`grep -n`, `sed -n a,bp`), never another project as a template.
- One task per session (one video, one lab round, one batch run); code fixes, ADRs and PRs found on the way go
  to a fresh session with a short handoff, not on top of a long one.

## Style
Python 3.12, type hints, ruff (line length 110), mypy strict in lens/schemas, lens/stages.py and
lens/measure. Small pure functions. Tests in tests/, fixtures in tests/fixtures/.

## Owner
This copy is yours: you are the admin. Where skills, ADRs and learnings say "Robert", read "the owner" (you, the
presenter in your own takes). START-HERE.md has the setup and how to add your brand (`add-brand` skill).
- `brands/acme/` is a made-up demo brand that the tests and the example projects use. Leave it in place; add
  your own brand next to it and point your projects at it (`brand: <your-brand>` in brief.yaml).
- `uv run create take` defaults to `--brand acme`: pass `--brand <your-brand>`, or change the default in
  `create/cli.py` and `create/footage/take.py` once your brand passes `create tokens`.
- Ask before spending ElevenLabs credits.
