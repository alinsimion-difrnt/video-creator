# acme-explainer-v1 against its answer key

## Transitions

14/14 found within 200 ms.

| into | true start | detected | error ms | kind |
|---|---|---|---|---|
| 02-handful | 9.40 | 9.50 | +100 | crossfade |
| 03-what-it-does | 16.20 | 16.30 | +100 | crossfade |
| 04-research | 24.50 | 24.50 | +0 | push |
| 05-how-it-works | 29.00 | 29.03 | +33 | zoom_through |
| 06-questions | 32.60 | 32.67 | +67 | push |
| 07-personas | 41.40 | 41.47 | +67 | crossfade |
| 08-real-browser | 56.30 | 56.37 | +67 | push |
| 09-why-not-api | 61.10 | 61.17 | +67 | crossfade |
| 10-three-engines | 74.90 | 74.97 | +67 | crossfade |
| 11-reading | 83.30 | 83.33 | +33 | push |
| 12-what-you-get | 96.20 | 96.23 | +33 | push |
| 13-what-else | 112.60 | 112.63 | +33 | zoom_through |
| 14-pitch-reports | 123.00 | 123.07 | +67 | crossfade |
| 15-close | 133.50 | 133.60 | +100 | crossfade |

## SFX

Recall 6/14; 1 detected candidate(s) match no clip (x007 music @ 143.98).

| true clip | start | detected | onset - start ms |
|---|---|---|---|
| whoosh-short.mp3 | 0.00 | x001 swoosh_reverse | +142 |
| click-soft.mp3 | 9.40 | missed | |
| pop.mp3 | 24.50 | missed | |
| chime.mp3 | 29.00 | x002 glitch | +413 |
| click-soft.mp3 | 32.60 | missed | |
| pop.mp3 | 41.40 | missed | |
| typing.mp3 | 56.30 | missed | |
| whoosh-short.mp3 | 61.10 | x003 whoosh | +140 |
| ping.mp3 | 74.90 | x004 chime | +320 |
| click-soft.mp3 | 83.30 | missed | |
| pop.mp3 | 96.20 | x005 click | +115 |
| click-soft.mp3 | 112.60 | missed | |
| pop.mp3 | 123.00 | missed | |
| impact-bass-2.mp3 | 133.50 | x006 music | +21 |

## Tweens (S7 on true end boxes)

62/80 measured; 26 draw the same motion as the truth (within 1 px of travel or 5 pp of opacity). Nearest GSAP ease exact 12, same family 33, same direction 51. Median |start error| 19 ms, median |duration error| 58 ms (1 frame = 33 ms). Isolated tweens (no other animation overlapping in time and on screen): 12/23 draw the same motion.

| tween | true ease / ms | measured channel | nearest GSAP / ms | start err ms | dur err ms | class | max curve gap |
|---|---|---|---|---|---|---|---|
| 01-questions#01 | expo.out / 480 | y | expo.out / 488 | +3 | +8 | linear | 0.1 px |
| 01-questions#04 | expo.out / 480 | y | expo.out / 536 | +6 | +56 | ambiguous | 1.1 px (overlapped) |
| 01-questions#10 | back.out(1.4) / 380 | scale | back.out(1.4) / 374 | +5 | -6 | ease_out | 0.9 px (overlapped) |
| 01-questions#19 | back.out(1.4) / 380 | scale | back.out(1.2) / 364 | +1 | -16 | ease_out | 0.7 px (overlapped) |
| 02-handful#00 | expo.out / 450 | x | circ.inOut / 309 | +219 | -141 | linear | 4.0 px (overlapped) |
| 02-handful#03 | expo.out / 420 | y | circ.out / 211 | +12 | -209 | linear | 0.4 px (overlapped) |
| 02-handful#09 | expo.out / 420 | y | circ.out / 202 | -135 | -218 | linear | 17.1 px (overlapped) |
| 02-handful#16 | back.out(1.4) / 300 | scale | back.out(1.7) / 261 | +23 | -39 | ease_out | 6.6 px (overlapped) |
| 02-handful#20 | power2.out / 500 | none | | | | |
| 03-what-it-does#00 | expo.out / 500 | y | sine.in / 255 | +40 | -245 | linear | 0.6 px |
| 03-what-it-does#03 | expo.out / 500 | y | expo.out / 515 | +1 | +15 | linear | 0.6 px |
| 03-what-it-does#09 | power2.out / 240 | none | | | | |
| 03-what-it-does#12 | back.out(1.4) / 400 | y | back.out(1.4) / 395 | +1 | -5 | ease_out | 0.3 px |
| 04-research#02 | power3.out / 1150 | none | | | | |
| 04-research#06 | expo.out / 450 | none | | | | |
| 05-how-it-works#02 | back.out(1.4) / 450 | y | back.out(1.7) / 465 | -0 | +15 | ease_out | 0.4 px |
| 05-how-it-works#05 | back.out(1.4) / 450 | scale | back.out(1.4) / 443 | +3 | -7 | ease_in_out | 0.3 px |
| 06-questions#04 | back.out(1.4) / 400 | scale | back.out(1.7) / 374 | +27 | -26 | ease_out | 4.2 px |
| 06-questions#07 | expo.out / 400 | none | | | | |
| 06-questions#10 | expo.out / 400 | none | | | | |
| 06-questions#13 | power3.out / 1050 | scale | circ.out / 819 | +167 | -231 | ease_out | 3.2 px (overlapped) |
| 06-questions#17 | expo.out / 400 | none | | | | |
| 07-personas#00 | expo.out / 450 | none | | | | |
| 07-personas#03 | expo.out / 350 | none | | | | |
| 07-personas#07 | expo.out / 350 | x | power1.out / 198 | -4 | -152 | ease_out | 0.7 px (overlapped) |
| 07-personas#10 | power3.out / 300 | y | power1.out / 251 | -2 | -49 | ease_out | 0.4 px (overlapped) |
| 07-personas#14 | expo.out / 350 | x | power4.out / 330 | +8 | -20 | ease_out | 0.4 px (overlapped) |
| 07-personas#17 | power3.out / 300 | y | circ.out / 261 | +33 | -39 | linear | 0.4 px (overlapped) |
| 07-personas#21 | expo.out / 350 | x | expo.out / 365 | +11 | +15 | ease_out | 0.6 px (overlapped) |
| 07-personas#24 | power3.out / 300 | y | circ.out / 261 | +33 | -39 | linear | 0.4 px (overlapped) |
| 07-personas#29 | expo.out / 320 | scale | expo.out / 472 | -175 | +152 | ease_out | 22.0 px (overlapped) |
| 07-personas#34 | expo.out / 320 | x | power4.out / 286 | -2 | -34 | ease_out | 0.1 px (overlapped) |
| 07-personas#39 | back.out(1.4) / 400 | scale | back.out(2) / 396 | +29 | -4 | ease_in_out | 11.9 px |
| 07-personas#45 | back.out(1.4) / 400 | x | none / 407 | -204 | +7 | linear | 3.3 px (overlapped) |
| 07-personas#49 | back.out(1.4) / 400 | scale | back.out(2) / 387 | +32 | -13 | ease_out | 6.2 px |
| 07-personas#54 | power2.out / 300 | none | | | | |
| 08-real-browser#01 | expo.out / 450 | x | power2.in / 85 | +353 | -365 | spring | 16.0 px |
| 08-real-browser#09 | back.out(1.2) / 320 | scale | circ.out / 795 | +52 | +475 | linear | 9.7 px (overlapped) |
| 08-real-browser#14 | back.out(1.6) / 300 | opacity | circ.out / 357 | -213 | +57 | ease_out | 99.9 pp (overlapped) |
| 08-real-browser#20 | power2.out / 200 | scale | circ.out / 178 | +367 | -22 | ease_in | 23.3 px (overlapped) |
| 09-why-not-api#03 | power3.out / 500 | x | circ.inOut / 494 | -9 | -6 | linear | 6.7 px (overlapped) |
| 09-why-not-api#06 | back.out(1.4) / 320 | scale | back.out(1.2) / 303 | +2 | -17 | ease_out | 0.7 px (overlapped) |
| 09-why-not-api#10 | back.out(1.4) / 400 | scale | back.out(1.7) / 373 | +29 | -27 | ease_out | 4.5 px (overlapped) |
| 09-why-not-api#14 | power2.out / 240 | x | elastic.out(1,0.4) / 113 | +12 | -127 | spring | 35.5 px (overlapped) |
| 09-why-not-api#17 | power2.out / 240 | y | elastic.out(1,0.3) / 231 | +4 | -9 | ease_out | 3.6 px (overlapped) |
| 09-why-not-api#20 | power2.out / 240 | y | sine.out / 175 | -4 | -65 | linear | 0.4 px (overlapped) |
| 09-why-not-api#23 | power2.out / 240 | y | circ.in / 303 | -278 | +63 | ease_in_out | 19.1 px (overlapped) |
| 09-why-not-api#26 | back.out(1.4) / 400 | x | sine.inOut / 117 | +16 | -283 | spring | 2.3 px (overlapped) |
| 09-why-not-api#37 | power3.out / 500 | x | power3.out / 312 | +228 | -188 | ease_out | 1.5 px (overlapped) |
| 09-why-not-api#129 | back.out(1.4) / 380 | opacity | back.inOut(2.5) / 508 | -161 | +128 | ease_in_out | 35.2 pp |
| 09-why-not-api#133 | power2.out / 450 | opacity | power4.out / 612 | -3 | +162 | ease_out | 100.0 pp |
| 10-three-engines#01 | expo.out / 400 | none | | | | |
| 10-three-engines#70 | power3.out / 300 | y | power2.out / 266 | -4 | -34 | ease_out | 0.3 px |
| 11-reading#03 | power4.out / 400 | x | none / 59 | +332 | -341 | spring | 16.0 px |
| 11-reading#06 | power3.out / 300 | y | power2.out / 198 | +25 | -102 | linear | 0.5 px (overlapped) |
| 11-reading#31 | back.out(1.4) / 400 | x | back.out(1.4) / 392 | +10 | -8 | ease_in_out | 14.5 px (overlapped) |
| 11-reading#58 | power3.out / 450 | x | circ.out / 319 | -9 | -131 | ease_in_out | 16.4 px |
| 11-reading#65 | power3.in / 250 | scale | circ.out / 250 | +330 | +0 | linear | 7.1 px (overlapped) |
| 11-reading#70 | power3.out / 450 | none | | | | |
| 11-reading#73 | power3.out / 450 | none | | | | |
| 12-what-you-get#13 | power3.out / 300 | none | | | | |
| 12-what-you-get#21 | none / 200 | y | none / 700 | -247 | +500 | linear | 63.8 px |
| 12-what-you-get#29 | power2.inOut / 900 | x | power1.inOut / 638 | +138 | -262 | ease_in_out | 98.0 px (overlapped) |
| 12-what-you-get#32 | power2.inOut / 800 | x | power1.inOut / 530 | +129 | -270 | ease_in_out | 104.0 px (overlapped) |
| 12-what-you-get#36 | expo.out / 400 | y | power2.in / 86 | +253 | -314 | spring | 5.0 px (overlapped) |
| 13-what-else#00 | expo.out / 400 | none | | | | |
| 13-what-else#03 | power3.out / 350 | none | | | | |
| 13-what-else#06 | power3.out / 350 | y | power4.out / 380 | +21 | +30 | linear | 3.5 px (overlapped) |
| 13-what-else#12 | power3.out / 300 | x | power2.out / 233 | +0 | -67 | ease_out | 0.2 px (overlapped) |
| 13-what-else#15 | back.out(1.4) / 380 | scale | back.out(1.7) / 361 | +24 | -19 | ease_out | 5.9 px |
| 13-what-else#18 | power3.out / 350 | y | power2.out / 270 | +15 | -80 | ease_in_out | 4.6 px (overlapped) |
| 13-what-else#25 | back.out(1.4) / 300 | none | | | | |
| 13-what-else#28 | power3.out / 350 | y | power2.out / 271 | +18 | -79 | linear | 4.3 px (overlapped) |
| 14-pitch-reports#03 | back.out(1.4) / 300 | none | | | | |
| 14-pitch-reports#06 | expo.out / 420 | y | circ.out / 247 | +15 | -173 | ease_out | 0.5 px |
| 14-pitch-reports#09 | expo.out / 420 | y | circ.out / 194 | +44 | -226 | linear | 0.6 px |
| 14-pitch-reports#12 | expo.out / 420 | y | circ.out / 283 | -58 | -137 | linear | 0.5 px |
| 14-pitch-reports#15 | power3.out / 320 | x | power3.out / 324 | -0 | +4 | linear | 0.3 px |
| 14-pitch-reports#18 | power3.out / 320 | x | power2.out / 261 | -1 | -59 | linear | 0.1 px |
| 14-pitch-reports#21 | power3.out / 320 | x | power2.out / 259 | -2 | -61 | ease_out | 1.2 px |

