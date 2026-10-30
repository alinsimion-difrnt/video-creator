# Chip Pops Onto Element

`chip_append`

A small tag, chip, badge or attachment pill pops onto an existing input, field, list or headline, and the things around it shift aside to make room, showing that something was just added or selected.

## When to use
- Showing a selection, mention or file attachment landing in an input after a click or drop
- Labelling items in a list or column with a status, category or icon
- Dropping a feature name or shortcut hint onto a scene without cutting away
- Inserting a brand icon into a headline so it becomes part of the sentence

## Avoid when
- Many chips would arrive at once in different places, splitting attention
- The chip's meaning is not clear without reading it closely

## Build
1. Show the cause first: a click, a drag and drop, or the narrated line that introduces the item
2. Close any menu or dropdown at the same moment the chip appears
3. Pop the chip in from slightly smaller with a quick fade, or slide it up into place if it lands over footage
4. Shift neighbouring words, labels or form rows aside or down so the layout reflows around the chip
5. If several chips gain the same element, add them together or with a tiny stagger so they read as one state change
6. Move the cursor or focus straight on to the next control

- GSAP / HyperFrames: Use gsap.fromTo on the chip (scale and autoAlpha to rest) with a back-style overshoot ease for a pop, or ease-out for a calm insert, alongside ease-in-out or ease-out tweens that move neighbours aside; use gsap.set for instant UI swaps like closing the menu. Add a small stagger when several chips appear.
- Remotion: Drive chip scale and opacity with a spring, a slightly bouncy config for a pop or a damped one for a quiet insert; move neighbours with interpolate or a damped spring from the same start frame. Switch menu and field states on the click frame without interpolation.

## Measured in premium explainers
- Duration: 134-686 ms (typical 281), 3 videos
- Easing: ease out 26%, ease in out 26%, spring overshoot 23%, ease in 13%
- Changes: fade 25%, slide down 19%, pop 17%, slide right 15%
- Sound offset to the landing: -393-162 ms (typical -115), 1 videos

## Sound
No typical sound; moments sit under music or an unclear bed.

## Why it reads as premium
Each chip makes a cause and its effect visible together: a click, drop or spoken phrase instantly becomes attached context, a status or a named feature. Premium versions keep it tight, closing the menu and landing the chip in the same instant, while the surrounding words or rows shift aside so the chip feels like part of the layout rather than a sticker on top. When several chips change at once they move as one coordinated update, and the cursor moves straight on, so the demo never stalls.

## Caveats
- Timing comes from few measured elements and the confidence interval is wide
- Several members are screen recordings where the chip appears in a single frame, so measured motion mostly reflects surrounding reflow
- No easing family dominates, and sound evidence comes from a single video
