#!/bin/bash
# Copied 2026-10-09 from the Acme v2 session scratchpad: $S/film/assemble.sh. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md.
# assemble.sh: concat segment videos (frame-exact, video only) + master audio -> film.mp4 ; report per-segment frame counts
F=$(dirname "$0"); cd "$F"
declare -A N=([A]=590 [B]=337 [C]=452 [D]=264 [E]=942 [F]=321 [G]=248)
rm -f list.txt
for s in A B C D E F G; do
  v=$s/render.mp4; [ -f $v ] || { echo "missing $v"; exit 1; }
  n=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $v)
  echo "$s frames $n (want ${N[$s]})"
  ffmpeg -v error -y -i $v -an -vf "fps=30,scale=1920:1080,setsar=1,trim=end_frame=${N[$s]},setpts=PTS-STARTPTS" -c:v libx264 -crf 16 -pix_fmt yuv420p -r 30 seg-$s.mp4
  echo "file 'seg-$s.mp4'" >> list.txt
done
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy video.mp4
ffmpeg -v error -y -i video.mp4 -i master-audio.m4a -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest film.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 film.mp4
