<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/wow/t1-tunnel/NOTES.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# t1-tunnel — The Answer Tunnel (9.30 s)

**Idea:** the question goes into ChatGPT and the camera flies through it into the answer itself. Answer
fragments rush past in 3D depth, then the camera slows and lands on a short list: four names and an empty fifth slot.
**Signature move (round 5):** one continuous camera path toward the list, which is the deepest plane of the tunnel from 2.9 s. The four answer names ride the nearest layer, park around the card when the camera lands, and drop into rows 1-4 on "Four". Earlier version: (v4) the dive runs 2.90 to 5.30 s on one CSS-3D camera: power3.in for 1.10 s, then expo.out for 1.30 s at the same speed at the joint, with a small 4° roll. It
passes through the question bubble. Answer fragments with speed-scaled blur and fog rush past, and brand chips
flare navy as they pass the lens. The camera then slows onto the list card, which was waiting at the end of the tunnel.

## Round 5 (third judge round): beats (s)
- 0.00 typing starts at frame 0 in a 1344px (70%) composer bar, 44px text; complete at 2.45
- 2.66-2.98 send press on "CRM?"; the composer fades out by 3.10 and the dive starts at once (no bubble, no composer drop)
- 2.88 the list card is visible as the deepest plane, centred at about 0.12x (LZ = 7300, perspective 1000, vanishing point = card centre)
- Camera, single z path, speeds matched at both joints: 2.90-3.30 power3.in, 3.30-4.00 linear cruise (~7.7k px/s),
  4.00-4.70 expo.out, landing at 1.0x. No card fade-in late, no blank frames
- Layers: NEAR = 96px Space Grotesk names at 80% navy, sharp (Attio, Monday, Close, Freshsales, Copper, Insightly),
  each passing the lens during the cruise and leaving through the frame edge; the 4 answer names (HubSpot, Pipedrive,
  Salesforce, Zoho) ride a near plane that stops 350px in front of the card and park clear of it.
  MID = 32px phrases at 75%, opacity fog, blur <= 2px in the distance only. FAR = bars, opacity fog only
- 5.30-5.95 "Four" (5.48): names drop into rows 1-4 (power3.out 0.35, 0.1 stagger), then hand over to the card's own chips
- 6.32 "five": numeral 5 (orange) and the orange border arrive together; caret blinks until 8.6
- 7.60 "Is yours one of them?": rows 1-4 dim to 55%; 1.12x push (power2.inOut 0.6) anchored on the slot-5 row;
  final frame card at y 194-886, x 346-1574 (>= 72px margins); still from 8.6

## Round 5 notes and weaknesses
- No skeleton bars; rows 1-4 are numerals only until the names arrive.
- Slot 5 sits at about y 810 in the final frame. Centring it while keeping >= 72px margins for the whole card is not
  geometrically possible, so the push is anchored on the slot row and the card stays balanced in the frame.
- The near names cross the lens in about 0.2 s each at cruise speed; the parked four carry the readable hold.
- The fly-in moves each name in world x/y/z at once, so the drop path curves slightly (it reads as a natural fall into depth).
