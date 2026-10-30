#!/usr/bin/env bash
# Fetch a video that cloud runners cannot (YouTube, X, LinkedIn) and upload it to r2://inbox/.
# Run on your own machine (cloud IPs get bot-blocked; ToS considerations are in ADR 0006).
#
#   scripts/local_fetch.sh <url> <source-id>
#
# Then set `url: r2://inbox/<source-id>.mp4` for that entry in sources/sources.yaml.
# If yt-dlp cannot fetch a LinkedIn video, open the post, find the <video> element's `src` in devtools
# (usually a direct progressive MP4 on LinkedIn's CDN) and pass that URL instead. If only screenshots are
# possible, mark the source `media: frames_only`.
set -euo pipefail

url="${1:?usage: local_fetch.sh <url> <source-id>}"
id="${2:?usage: local_fetch.sh <url> <source-id>}"
if [[ ! "$id" =~ ^[a-z0-9]+([-_][a-z0-9]+)*$ ]]; then
  echo "source id must be a lowercase slug: $id" >&2
  exit 2
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
out="$tmp/$id.mp4"

if [[ "$url" == *.mp4* ]]; then
  curl -fL --retry 3 -o "$out" "$url"
else
  command -v yt-dlp >/dev/null || { echo "install yt-dlp first (pipx install yt-dlp)" >&2; exit 2; }
  yt-dlp -f "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b" --merge-output-format mp4 -o "$out" "$url"
fi

ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,avg_frame_rate -of compact "$out"
uv run lens storage put-inbox "$out"
