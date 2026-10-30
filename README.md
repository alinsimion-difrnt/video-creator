# explainer-video-creator

Research, understand and create premium SaaS explainer videos.

- **Phase 1 — `lens`** (in progress): builds a corpus of reference explainers, measures motion, sound,
  voice and rhythm with code, has Claude Code name the patterns, and grades our own videos
  (`lens compare`). Exports motion tokens, sound/voice/pacing specs and scene archetypes.
- **Phase 2 — `create`** (after gate G5): generates explainers from those exports, voiced with ElevenLabs.

Start here: [BUILD_PLAN.md](BUILD_PLAN.md) (v2.2) · [PROGRESS.md](PROGRESS.md) ·
[docs/plan-audit.md](docs/plan-audit.md) · [docs/operating-guide.md](docs/operating-guide.md)

```bash
make setup && make check
uv run lens --help
```

The `CLAUDE_CODE_OAUTH_TOKEN` Actions secret lasts about a year. Renew it with `claude setup-token`
before it expires.
