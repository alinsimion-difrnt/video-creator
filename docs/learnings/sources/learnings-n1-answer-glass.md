<!-- Copied 2026-10-09 from the Acme v2 session scratchpad: $S/six/n1-answer-glass/LEARNINGS.md. $S paths are ephemeral (archived in R2 create/acme-v2/). See ../readme.md. -->

# n1 Answer Glass: learnings

1. **Pinning HTML text to 3D faces with a per-frame homography works well.** Project the face's 4 corners with the
   three.js camera, solve square-to-quad, and write `matrix3d` with `transform-origin:0 0`. Lay labels out at 400 px per
   world unit so they are scaled down, never up, and the text stays crisp at any camera angle. It satisfies "HTML for
   all text" and still looks like real type in 3D.
2. **HTML occlusion needs explicit work.** The canvas can never cover HTML. Clip each label with
   `clip-path: polygon(evenodd, frame, hull1, hull2…)` built from the convex hulls of nearer meshes, and z-sort the
   labels by depth. This is cheap: it is pure geometry with no extra renders.
3. **DOF on HTML:** `filter: blur()` acts before the transform, so divide the screen-space blur by the label's screen scale.
4. **Keep the world module free of three.js and the DOM.** Then node can sweep all 927 frames for camera-to-box
   clearance in about 1 s, which caught 3 fly-through collisions before any render.
5. **Monotone cubic (Fritsch-Carlson) camera keys** give a continuous one-take dolly with no overshoot and no
   backwards drift between holds. A Catmull-Rom would have overshot on the whip-to-hold keys.
6. **Glass on white:** heavy frosting (roughness 0.3 and up) reads as grey plastic. Use roughness ~0.12, thickness
   0.7, dispersion 3 and a neutral attenuation, with a white top-edge specular. It still mostly reads as frosted
   acrylic unless there is structure behind it.
7. **Neutral tone mapping greys a white world.** A #F4F6F9 background came out as #EFF0F3. Use background #FFFFFF
   and exposure 1.2 to land around #F4F6F8.
8. **Carrier objects must follow the camera's own progress.** An eased tween for the "sent" question bar raced
   ahead and left an empty frame. Driving its progress from `camAt(t).z` kept it big for the whole flight.
9. **Orange glass carries a meaning.** When a "your brand" tile passes close to the lens, it becomes a big orange
   smear. Drop tiles out of the camera path before the whip.
10. **Cost on a shared 4-core box with load ~15:** a 0.5-scale draft took ~40-46 min for 927 frames. The final
    (0.667, MSAA, PCF, contact, AO, DOF, adaptive motion blur up to 6) took longer. Plan rounds around that, or bake
    plates.
11. **Strips at 250 px per cell mislead about framing.** Check a full-res frame before moving the camera.
