---
name: write-post
description: Write the TikTok post text for a finished presenter video — a caption, hashtags and a first comment, in the video's language, from its transcript — plus the cover title for `create cover`. Use when a video is ready to post.
---

# write-post

The post text is what people read before they tap and what search reads after; the cover is what they see in
a grid. Write from what Robert actually says in the video (the transcript), in his voice: read
`brands/acme/VOICE.md` first.

## Inputs
- `uv run create words <p>` (what he says, in order) and `projects/<p>/brief.yaml` (brand, language,
  destination).
- Anything Robert says about the goal of the post (followers, trial sign-ups, a client).

## Write `projects/<p>/post.md`
```markdown
# Cover
title: Get your restaurant **cited by ChatGPT**      (≤ 6 words; **one** accent phrase; for create cover)
tag: 3 steps                                         (≤ 3 words; the kicker pill above the title)
sub: Three fixes, ten minutes.                       (optional, one short line under the title)
at: 5.6                                              (seconds: a frame where he looks at the camera)

# TikTok
<caption: the hook as a line (not the same words as the cover), then one line of value, then the CTA>
#hashtag #hashtag #hashtag

# First comment
<the link or the one resource (links in TikTok captions do not work)>
```

## Rules
1. **The first line is the hook**, written for reading, not a copy of the spoken hook or the cover.
2. **Concrete over clever**: the names, places and numbers from the video (ChatGPT, Google Maps, Budapest).
   Never add a claim, number or result the video does not make.
3. **One CTA**, the same as the video's (e.g. the free trial at acme.example).
4. **Hashtags**: 3-5, specific to the topic and audience (#restaurantmarketing, #chatgpt), not generic
   (#fyp, #viral).
5. **Language**: the video's. A Romanian video gets a Romanian post; add an English line only if Robert asks.
6. Mark anything that needs checking (a client's name, a number) with `[?]` and list it for Robert.

The format above is complete: don't open other projects' post.md for an example.

## Then
- The cover: `uv run create cover <p> --split --title "<title>" --tag "<tag>" --sub "<sub>" --at <at>
  --onto <render>` for a presenter video on a split base (the panel route; the title stays off his face and the
  cover becomes the video's first frame; `--icon <svg>` puts a logo in the pill; a kit layout version adds
  `--video <render> --plan <its plan>`; an overlay version has no seam: the same command with the layout render
  and plan, `--onto <overlay render>`). Without `--split` (title over the full frame) only for videos with no
  face in the frame.
- Send Robert the post text (inline, so he can copy it on the phone), the cover and the videos.
- TikTok only. Write for another platform (Instagram, YouTube, LinkedIn) only when Robert asks.
