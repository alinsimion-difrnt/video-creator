#!/usr/bin/env bash
# SessionStart hook: in Claude Code cloud sessions, install deps so tests, the CLI and the reel tools work.
# Local sessions are left alone (run `make setup` yourself). Idempotent; each step is skipped when done.
set -euo pipefail
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
cd "${CLAUDE_PROJECT_DIR:-.}"
command -v uv >/dev/null 2>&1 || exit 0
# the cloud image sets UV_NATIVE_TLS, which uv now warns about on every run (a line in every command's output);
# UV_SYSTEM_CERTS is the same setting (the proxy's CA bundle) without the warning
if [ -n "${UV_NATIVE_TLS:-}" ]; then
  unset UV_NATIVE_TLS
  export UV_SYSTEM_CERTS=true
  [ -n "${CLAUDE_ENV_FILE:-}" ] && printf 'unset UV_NATIVE_TLS\nexport UV_SYSTEM_CERTS=true\n' >> "$CLAUDE_ENV_FILE"
fi
# Python deps, including the dev group (pytest-xdist, playwright)
uv sync --quiet >/dev/null 2>&1 || echo "session_start: uv sync failed; run 'make setup'" >&2
# media tools the tests and the footage pipeline need (in the cloud image already; install only if missing)
missing=""
for t in ffmpeg ffprobe espeak-ng; do command -v "$t" >/dev/null 2>&1 || missing="$missing $t"; done
if [ -n "$missing" ] && command -v apt-get >/dev/null 2>&1; then
  (apt-get update -qq && apt-get install -y -qq ffmpeg espeak-ng) >/dev/null 2>&1 \
    || echo "session_start: could not install$missing" >&2
fi
# the cloud image's Chromium, for create reel --check/--preview, create audit and the browser tests
if [ -x /opt/pw-browsers/chromium ] && [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export CHROMIUM=/opt/pw-browsers/chromium' >> "$CLAUDE_ENV_FILE"
fi
# GSAP for the HyperFrames kits (data/ is not committed): fetched once, then cached
uv run --quiet python -c "from pathlib import Path; from create.bundle import gsap; gsap(Path('data/create/_cache'))" \
  >/dev/null 2>&1 || echo "session_start: GSAP cache not warmed (no network?)" >&2
