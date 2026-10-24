# PV-01 — Architectural Solar Roof / Production Direction

**Status:** Implemented as real-time React Three Fiber candidate in this branch; screen-capture acceptance still required.

This is the **first high-detail geometry-locked visual improvement** after the school's initial facades. Do not design an unrelated school or replace the synthetic neighborhood.

## Immutable objects, from the running project
- Scene source: `apps/web/src/scene/DistrictWorld.tsx`
- School group world origin: `[13,0,7]`
- Existing solar module centers (school local): x = `-12 + col * 4.5`, `col=0..5`; z = `2.3 + row * 3.4`, `row=0..1`.
- Module group Y = `8.75`, rotation X = `-0.12` radians, original case dimensions = `[3.7,0.12,2.6]`.
- **Module count = 12 = two rows of six**. Interior drawn crystalline-looking cells are NOT extra solar modules.
- Original roof, windows, fence, sports/courtyard surface, streets, city buildings and cameras must remain untouched.

## Target aesthetic
Premium climate/energy scientific visualization shot through restrained cinematic architectural rendering. Slate-black anti-reflective solar glass, dark blue micro-texture, faint silver busbar lines, powder-coated metal perimeter, glints under sodium-vapor-like surrounding streetlights. Not bright cyan sci-fi tiles, not a glowing hologram, not mirror-finish chrome.

## What can go into the actual app
The authored `SchoolSolarArray.tsx` uses a deterministic reusable `CanvasTexture` and real `meshPhysicalMaterial`; all twelve fixed module positions and footprints are preserved. Faint frame bars and mount rails stay inside existing panel footprints. The one shared texture is created once, reused across modules, and disposed on unmount.

Validation:
- `npm run build`, `npm run lint`, `npm run test:smoke`
- `Issue 04 — WebGL visual captures` CI artifact
- Real screenshots from `SHOTS.facility` and `SHOTS.equipment`.
- Check roof panel count, panel readability at close camera, glass doesn't glow after blackout, no strange overbright lines.

## Google AI Pro / Nano Banana — OPTIONAL concept look-dev, not geometry

Google's current Gemini image editor accepts image uploads and reference-guided edits; subscribers can redo a generation with Nano Banana Pro. See [official help](https://support.google.com/gemini/answer/14286560).

**Upload actual image** `evidence/phase-00.5/keyframe-facility.png` or a same-camera current WebGL capture from GitHub Actions.

Suggested edit prompt in English (keep original reference uploaded):

> Edit the provided actual WebGL screenshot of LASTLIGHT. This is a strict image-to-image **surface and lighting look-development pass**, not an architectural redesign. Preserve the camera, crop, silhouettes, road grid, fence, main two-level school body, right annex, window pattern, courtyard, neighboring buildings, and rooftop solar installation at their precise pixel positions. There are exactly TWELVE individual solar panel modules, in two rows of six. Do not alter module count, size, spacing, direction or location. Improve only physically plausible solar glass detail (subtle internal cells and busbars), thin metal framing, modest metallic roughness, soft nighttime reflections, realistic exposure and restrained urban atmosphere. Neutral mineral wall materials, mild amber street lighting, no neon. It must look like a real-time architectural energy-resilience observatory at night, not a new city. No extra HVAC, no new windows, no new buildings, no new streets, no cars, no people, no text, no UI, no solar array expansion. If unsure, preserve the source pixels.

**Critical:** A generated photo can silently replace the school or change 12 modules to dozens. That image is then *REJECTED as a geometry reference* and may serve only as an atmosphere/color reference. Manually compare against the original real WebGL screenshot. Do **not** use it as an in-game frame or pretend it is an editable 3D model.

## Higgsfield — optional marketing cinematic AFTER in-app geometry lock
Cinema Studio can produce camera-directed video from reference frames ([official guide](https://higgsfield.ai/creator-hub/help-center/tools/how-do-i-use-cinema-studio)). An AI-generated moving camera may invent facades, change buildings or warp PV arrays even with references. It should only be an **external, separately labeled concept/marketing film**, never used as proof of a 3D camera transition. For the hackathon's actual interactive journey, use the R3F camera trajectory defined in `useMissionState.ts`.

## Approval label conventions
- `IMPLEMENTED_WEBGL`: Verified code changes in a PR; **not necessarily artist-approved**.
- `CONCEPT_ONLY`: AI output; no editable 3D geometry or continuity guarantee.
- `RUNTIME_CAPTURE`: Browser screenshot of actual WebGL from precise commit/state; no AI morph.
- `APPROVED`: Needs Abai's explicit visual review after testing low-power & blackout states.

### Next iteration, not part of this one
Refine the school's overly mottled concrete using controlled texture amplitude and compare with same-camera captures. Do not change it in the PV-01 iteration.
