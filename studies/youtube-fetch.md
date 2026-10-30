# YouTube fetch: instructions for the laptop session

YouTube blocks the cloud container. This job runs in a Claude session on Robert's laptop and only does this
one thing. Analysis happens in the cloud session, which reads the videos from R2.

**Do not change code, plans or other studies.** Only these files get added:
- `studies/pixel-art/youtube.yaml`
- `studies/tiktok/youtube.yaml`

## Before you start (Robert)
1. In the repo folder: `git fetch origin claude/affectionate-keller-nt54v1 && git checkout claude/affectionate-keller-nt54v1 && git pull`.
2. `yt-dlp` and `ffmpeg` installed (`brew install yt-dlp ffmpeg`). Update yt-dlp (`yt-dlp -U` or `brew upgrade yt-dlp`): YouTube breaks old versions.
3. The `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` and `R2_BUCKET` variables exported in the
   shell, as for `scripts/fetch_batch.py` (docs/operating-guide.md). Never paste them into a chat.
4. `uv sync`, then start the session: `claude remote-control` (or the Desktop app) in the repo folder, and say
   "follow studies/youtube-fetch.md".

## Steps (the laptop session)
1. **List.** Run `uv run python scripts/study_youtube_fetch.py list`.
   - This resolves `studies/youtube-fetch.yaml` (creators, Robert's links, game trailers, Shorts searches) into
     `studies/pixel-art/youtube.yaml` and `studies/tiktok/youtube.yaml`.
   - Check that each subject got videos. When a channel handle is wrong, find the right one (`yt-dlp
     --flat-playlist -J "https://www.youtube.com/@<handle>/videos"`), fix only that `url` in
     `studies/youtube-fetch.yaml`, and list again.
   - Keep game trailers that are official (the publisher's or developer's channel). When a search picked a
     fan video, replace it with a better search phrase.
2. **Commit the lists.** `git add studies/youtube-fetch.yaml studies/*/youtube.yaml`, commit
   ("YouTube lists for the studies"), `git pull --no-rebase`, `git push`.
3. **Fetch.** Run `uv run python scripts/study_youtube_fetch.py fetch`.
   - It downloads each video (up to 1080p) and uploads it to `r2://study/<track>/youtube/<id>.mp4`, then
     deletes the local copy.
   - Re-run it until nothing is left. Report the ones that keep failing (age-gated, region-locked).
4. **Report.** In the chat, give the number of videos per track and per subject, the failures, and anything
   you changed in `studies/youtube-fetch.yaml`. Then stop. The cloud session takes it from there.

## Rules
- No videos in git. Media is ignored by `.gitignore`; check `git status` before committing anyway.
- The two tracks stay separate: pixel-art videos never go into the tiktok list or folder, and the other way
  round.
