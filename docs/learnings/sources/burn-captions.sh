#!/usr/bin/env bash
# Copied 2026-10-09 from the Acme v2 session scratchpad: $S/final/captions/burn.sh. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md.
# Burn the designed captions onto the Acme film and mux the final audio.
# Usage: burn.sh [film.mp4] [audio-source.mp4] [captions.json] [out.mp4]
set -euo pipefail
S=/tmp/claude-0/-home-user-explainer-video-creator/d8546e8e-2ef6-5546-bc1d-4c1a0ec27017/scratchpad
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILM="${1:-$S/film/film.mp4}"
AUDIO="${2:-$S/film/sfx/film-sfx-cut3.mp4}"
CAPS="${3:-$S/final/captions.json}"
OUT="${4:-$S/final/acme-v2-captioned.mp4}"
COMP="$HERE/comp"
TMP="$HERE/last-render.mp4"   # video-only render, kept for review

echo "== plate: $FILM"
cp -f "$FILM" "$COMP/plate.mp4"
FRAMES=$(python3 "$HERE/src/build.py" "$CAPS" | tail -1)

cd "$COMP"
npx --yes hyperframes@0.8.137 telemetry disable >/dev/null 2>&1 || true
npx --yes hyperframes@0.8.137 lint .
T0=$(date +%s)
npx --yes hyperframes@0.8.137 render . -o "$TMP" --quiet --video-frame-format png --resolution 1080p
echo "== render took $(( $(date +%s) - T0 )) s"

ffmpeg -y -v error -i "$TMP" -i "$AUDIO" -map 0:v -map 1:a -c:v copy -c:a copy -movflags +faststart "$OUT"
GOT=$(ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 "$OUT")
if [ "$GOT" != "$FRAMES" ]; then
  echo "FRAME COUNT MISMATCH: output $GOT, plate $FRAMES" >&2
  exit 1
fi

echo "== OK: $OUT ($GOT frames)"
