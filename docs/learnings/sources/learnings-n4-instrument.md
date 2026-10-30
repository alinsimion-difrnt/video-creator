<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/six/n4-instrument/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# Learnings — n4 "The Instrument"

1. **Put HTML onto a 3D surface with a homography.** Project the 4 corners of the 3D screen, solve the
   square-to-quad map in closed form, and write it as `matrix3d` with `transform-origin:0 0`. The result is pixel-locked
   to the moving 3D device, crisp at any scale, and seek-safe. It is far better than a CanvasTexture at a 0.5–0.667 render
   scale. **Catch:** the overlay always draws on top. If anything in 3D sits between the camera and the screen (keys,
   when the camera is low), it shows through wrongly. Keep the camera pitch above about 25° when looking across the keys.
2. **Strong perspective reads as italic type.** At fov 28 from close up, the converging verticals made upright text
   look slanted. A longer lens (fov 22) from further back reads as "macro product film" and keeps the type upright.
3. **Line length sets the camera distance.** A question line is about 12 device units wide. Any framing tighter than
   that cuts the first word, and "…ich CRM should" fails the read. Frame the whole line, then push only where
   the text is short.
4. **Give focus its own track.** Sharing keyframes with the camera made every rack land halfway, so both "Your brand?"
   and the key were soft. A separate focus track with hold → fast rack fixed it.
5. **Compute the overlay DOF at the screen point nearest the focus point**, not at the screen centre. A large tilted
   screen otherwise blurs while the 3D around it is sharp.
6. **Load fonts before drawing font-dependent canvas textures.** The drum digits and the "DAY" label rendered in
   a serif fallback until I redrew them once `document.fonts.check()` passed.
7. **Odometer math.** The drum angle is `(v+0.5)*36°-90°`. The tens drum carries `max(0, ones-9)`. The digit glyphs
   are rotated +90° in the strip texture, because u runs around the axis.
8. **A dot-matrix mask works on light screens** (destination-in with a 6 px dot pattern, r≈0.5 pitch). Unlit
   dots stay faintly visible, so the screen reads as hardware even on white. If r is too small, navy turns grey.
9. **Contention:** with 4 builders the load was ~15–17. A 30 s draft (0.5 scale, no MSAA) took 20–24 min, and the
   final took much longer. Do stills-first iteration (`shotcam.sh` with a debug camera override) and render the full
   film only after the stills are right.
