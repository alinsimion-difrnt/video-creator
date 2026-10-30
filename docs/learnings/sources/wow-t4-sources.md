<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/wow/t4-sources/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# t4-sources: Source explosion

Idea: an AI answer (Perplexity card with a small Sources row) shatters, and its few citations burst into a deep 3D cloud of
about 340 sources in three depth layers. A ringed cluster of ten Google results looks tiny inside it. The camera then flies cluster to cluster (Reddit, Facebook, forums) and pulls back to mark the opportunities in orange.

## Beats (s, clip time), round 2 (after judge feedback)
- 0.00 the 640px answer card is already rising (expo.out). 0.32 "sources": the Sources row lifts and the rest of the card dims.
- 0.64-0.84 anticipation. 0.84 "go": the card breaks into 12 jittered shards, staggered outward from the Sources row.
  Within about 0.1 s, favicons pour out of the four source chips: the ten Google results first, landing about 160px wide just below the card,
  then the mid and far layers.
- 1.12-1.74 "far beyond": a single 0.62 s pull-back (power3.inOut, z 1700 -> 0). Near tokens stream in past the lens and the Google cluster
  shrinks to about 60-80px. 1.84 "search results": a dashed ring plus a label around it, with the cloud dimmed.
- 2.98-3.58 one dolly and pan to Reddit; 3.36 the pill "r/smallbusiness" opens; 3.70 a thread card on "threads".
- 4.16-4.76 dolly and pan (z hop 260) to Facebook; 4.52 the pill "Parents of toddlers group"; post cards fan out of the pill on
  "sell" 6.22, "children's" 6.50 and "products" 7.02.
- 7.56-8.16 to the forum; 7.92 the pill "Student forum"; posts on "a" 9.06 and "college" 9.38.
- 10.08-10.70 pull back to the wide shot. Everything else dims to 35%. From 10.62, 4px #00AA90 rings appear on the three named places only
  (0.08 s stagger, power3.out), and those tokens grow 1.55x (about 64-80px). Settled hold to 12.98.

## Build
src/index.tpl + src/build.py -> comp/index.html. One clock tween calls render(t), a pure function of time. render(t):
- runs the camera legs;
- projects every world token (scale = 1000/depth), so parallax is real;
- applies blur to the far layer only (at most 2.5px) and sets it to 40% opacity;
- fades out tokens that pass close to the lens before they get large;
- dims tokens outside the focused cluster;
- drives the pills, post cards and rings.

There is no velocity blur. The layout comes from a seeded mulberry32 PRNG.
Layers in the wide shot:
- near: 44 tokens at 55-85px, framing the edges;
- mid: 130 tokens at about 22-32px;
- far: 170 tokens at about 9-14px, with grey icons at 40%.

Reddit and StackOverflow icons outside their cluster are grey, and Substack and G2 were removed from the mix, so orange stays the accent.

## Iterations
1. v1-v4 (round 1): the cloud system, density, z-hop flights, label clearance, and a shatter rebuilt with drop-shadowed shards.
   The judge scored it 5-6: the flights read as blur crossfades between flat scatters, with dead holds.
2. v5: rebuilt to the judge's notes:
   - one continuous space with real parallax and no velocity blur;
   - three explicit layers, 340+ tokens;
   - an opening camera 1700 deep so the Google cluster shrinks in front of the viewer during the "far beyond" pull-back;
   - a 640px card in motion at frame 0;
   - 12 staggered shards, with the chips left out of the shards so the favicons come from the row;
   - post cards on the words at Facebook and forum (and one thread card at Reddit);
   - Space Grotesk 700 pills (about 40px on screen, 34 px of padding on the right);
   - rings on the three named places only.
3. v6: lens-pass tokens now fade before they get big (removes ghost blobs), and non-focus dimming is raised to 60%.

## Known weaknesses
- The shards are plain white card pieces, with skeleton lines only where the card had text. They read as paper more than glass.
- Pre-placed near tokens fade in around the frame edges at 0.84-1.1 rather than coming out of the row (most are still off-frame then).
- The Google cluster sits in view during the Facebook and forum shots (dimmed). It is fixed world content, not removed.
- The final wide frame has light contrast by design (others at 35%).
