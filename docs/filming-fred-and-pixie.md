# Filming notes: "This video is edited by AI" (Fred and Pixie)

What Robert does on camera so the edit (ADR 0027) can be built from his words alone. The general setup is in
`docs/filming-guide.md`.

## Setup
- **Camera:** phone on a tripod, portrait, 4K 30 fps, framed wide (head to knees), with empty couch beside him.
  Don't move the phone or the chair between takes.
- **Clean plate:** before sitting down, record 5 s of the empty couch.
- **Marks:** a piece of tape on the lap/cushion where Fred sits, and one on the floor or armrest where Pixie
  walks in. Look at the tape when talking to them.
- **Hands:** on the lap shots, rest the hands still, palms up, for 2-3 s. Still hands make Fred look held.
- **Light and sound:** soft light from the front; a lav mic if there is one.

## Cue words (say them roughly like this; the rest can be ad-libbed)
The edit keys every animation to a word. Saying these words lets the planner find the beats.

| Beat | Say | What happens |
|---|---|---|
| Hook | "my name is Robert" … "this video is **entirely edited by AI**" | punch-in, "edited by Claude" sticker |
| Fred | "even **this fish**? AI." (look at the tape) | Fred pops onto the lap |
| Styles | "it can be **3D** … **illustrated** … or **pixel art**" | Fred changes look on each word |
| Name | "I'll call him **Fred**" | name tag, Fred jumps |
| Hat | "Claude, give Fred a **moustache** and a **top hat**." (pause 1 s, look pleased) "much better" | moustache, then the hat drops in |
| Turn | "let's talk about **what we built**" | Fred hops off on his tail, or rows away in his boat |
| Shredder | "I gave Claude premium explainers … it **shredded** them … every **half second**" | videos into a shredder, frames grid |
| Tokens | "a process that wouldn't cost me an **arm and a leg** in tokens" … "I write the jokes, **Claude** does the alchemy" | Fred gets a steel fin and tail, claps, a transmutation circle lights up under him (a Fullmetal Alchemist homage) |
| Code | "everything is **code** … a different **colour** … a different **font**" | code card; the video recolours, captions change font |
| Storage | "it all lives in an **R2 bucket**" | bucket filling |
| Agents | "agents **make** videos, other agents **review** them, and **I** say what I like" | creator → reviewers → Robert, taste meter |
| Anime (optional) | "people turn themselves into **anime** …" (hold still 2 s) | anime filter, eyes, speed lines |
| Blocks (optional) | "… or **block** people" (hold still 2 s) | blocky Robert, hearts and hotbar |
| Ending | "Hey, my name is Robert, and that's—" (reach for the watch, stop) "… wait. What is **this cat**?" | Pixie walks in |
| Pixie | "Cute. I'll call him **Pixie**." | name tag; Pixie looks at Fred |
| Grab | freeze, turn to one side, shout "**Pixie, NO!**" | Pixie grabs Fred and runs that way, shake, fade to black |

- **Fred's side quests:** while you explain, Fred can read a book, write notes, text on a phone, hammer
  blocks, or row his boat around you through the air. Mention them or don't: the planner places them in the
  quieter stretches.
- **Pixie's colours:** tell Claude what she should look like (fur, stripes); she is drawn as an original
  kitten in the spirit of "Pixie and Brutus", not a copy.
- **Pauses:** leave 1 s after "moustache and a top hat" and after "what is this cat". The animation needs room.
- **The shout:** pick a side and turn to it. The cat runs out that way.
- **Re-takes:** shoot a couple of re-takes of the gag lines; the cut stage keeps the best.

## What the animation lab showed (ADR 0029; the final demo plan is docs/lab/v20.yaml)
- **Hook in the first second.** Open with the fish line ("This fish is AI."). Five seconds of introduction
  before anything happens was the weakest part of every lab reel.
- **Headroom.** Leave space above your head (about a head's height) for the captions. With your head near
  the top of the frame, captions sit on your face.
- **Lap and shoulders visible.** Fred stands on your lap and Pixie peeks over your shoulder: keep both in
  the frame. Don't hold a mug or a phone over your lap.
- **Hold still for the blocky and anime beats** (2-3 s). The effects follow your median face.
- **Give the cat time.** "What is this cat? … Cute. … I'll call her Pixie." Then the pause, then "Pixie,
  no!" The cat needs about 3 s to walk in and pounce.
- **Look over your shoulder on "wait"** if you can: Pixie peeks from behind you there.

## After filming
1. Upload the takes (`scripts/fetch_batch.py` or the R2 inbox) and the fish PNG: `projects/<p>/assets/fred.png`.
   A transparent PNG is best; a fish on a plain background also works (the background is removed in code).
2. Run `create ingest` → `transcribe` → `cuts`. Robert approves the cuts, then `create prep`.
3. Draft `reel.yaml` (skill draft-reel-plan) with props, fx and widgets.
4. Run `create matte` if Fred goes behind Robert or anime has its background. `create reel --check`, then
   `--preview`, then a draft render, then `create review`, then Robert.
