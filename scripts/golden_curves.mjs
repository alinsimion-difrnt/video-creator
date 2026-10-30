// Sample reference curves from GSAP and Remotion for the measurement golden tests (BUILD_PLAN 7.5).
//
//   npm install --prefix /tmp/golden gsap@3.14.2 remotion@4
//   NODE_PATH=/tmp/golden/node_modules node scripts/golden_curves.mjs tests/fixtures/golden-curves.json
//
// lens implements the eases and the damped spring from first principles (ADR 0004); these samples only
// check that the outputs agree. No library source is copied.
import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";

const require = createRequire(import.meta.url);
const { gsap } = require("gsap");
const { spring } = require("remotion");

const T = Array.from({ length: 51 }, (_, i) => i / 50);
const EASES = [
  "none",
  ...["power1", "power2", "power3", "power4", "sine", "expo", "circ"].flatMap((e) =>
    ["in", "out", "inOut"].map((d) => `${e}.${d}`)),
  "back.in(1.7)", "back.out(1.2)", "back.out(1.4)", "back.out(1.6)", "back.out(1.7)", "back.out(2.5)",
  "back.inOut(1.7)",
  "elastic.out(1,0.3)", "elastic.out(1.2,0.5)", "elastic.in(1,0.3)",
];
const eases = {};
for (const name of EASES) {
  const f = gsap.parseEase(name);
  eases[name] = T.map((t) => Number(f(t).toFixed(8)));
}

const CONFIGS = [
  { mass: 1, stiffness: 100, damping: 10 }, // Remotion's default
  { mass: 1, stiffness: 200, damping: 20 },
  { mass: 1, stiffness: 170, damping: 26 },
  { mass: 1, stiffness: 300, damping: 15 },
  { mass: 1, stiffness: 100, damping: 20 }, // critically damped
  { mass: 1, stiffness: 80, damping: 30 }, // overdamped
  { mass: 2, stiffness: 150, damping: 12 },
];
const springs = [];
for (const fps of [24, 30, 60]) {
  for (const config of CONFIGS) {
    const frames = Array.from({ length: Math.round(fps * 2.5) }, (_, i) => i);
    springs.push({
      fps, config,
      values: frames.map((frame) => Number(spring({ frame, fps, config: { ...config, overshootClamping: false } })
        .toFixed(8))),
    });
  }
}

const out = {
  source: `gsap ${gsap.version}, remotion ${require("remotion/package.json").version}`,
  t: T, eases, springs,
};
writeFileSync(process.argv[2], JSON.stringify(out) + "\n");
console.log(`${Object.keys(eases).length} eases, ${springs.length} springs -> ${process.argv[2]}`);
