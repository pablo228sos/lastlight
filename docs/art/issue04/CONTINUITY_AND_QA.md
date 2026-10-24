# LASTLIGHT art handoff: geometry and visual QA

## Scope
Work is for the **existing synthetic district**, not a new website or city. Main source: `apps/web/src/scene/DistrictWorld.tsx`, baseline SHA `91aaa7a33ad93e9dd1022821c4eaf7576d700486`. Direct WebGL captures: `evidence/phase-00.5/`.

## Immutable school anchors
| Object | Original local pose in School group |
|---|---|
| School group | World [13,0,7] |
| Campus | 60 × 50; local x -30..30, z -25..25 |
| Main school wall body | Local [0,4.1,6], box 30×8×14 |
| Right annex | Local [15.7,3.1,11], box 10×6×9 |
| Roof PV | 12 module meshes in 2×6 rows (not 24) |
| Inverter/battery-looking cabinets | Local centers [19.4,1.65,3.2] and [15.7,1.5,3.2]; confirm semantic mapping in app |
| South/front fence gate | At local z=25, gap x=-27..-9 |

Keep the roads, fence, solar PV, canopy and surrounding city **unchanged**. The earlier AI cinematic hero and before/after boards are concepts only; they were *not* pixel-registered edits of current WebGL captures.

## Continuous virtual camera
These are actual source poses (x,y,z), not inferred cuts:
- `district`: [81,63,83] → [6,1,2]
- `facility`: [65,39,58] → [13,3,7]
- `equipment`: [53,26,41] → [16,5,7]
- `orbit`: [47,37,-37] → [13,4,7]

Story sequence: overview → facility → rooftop equipment → power trace → blackout → restore → district. Do not splice separately invented neighborhoods. Existing state transitions can provide these beats; no physics claims.

## Material direction
Premium architectural nighttime observation software, warm-neutral mineral concrete, matte roof membrane, deep navy photovoltaic surfaces, brushed dark equipment metal, charcoal asphalt. Road lights amber; reserve teal for emergency and technical emphasis. Minimize neon and broad bloom.

Current PR image maps are deterministic **procedurally generated fallbacks**, *not exact binary copies* of the earlier ChatGPT Visual Kit PNGs and not scanned/physically measured PBR. Files live under `apps/web/public/assets/materials/facade02/` and are generated at 1024² indexed PNG with matching edge pixels. The original independent Visual Kit is retained as a ChatGPT ZIP; those original binaries were not transferable over this connector and must not be represented as committed.

## QA gate for Abai (not performed remotely)
1. `cd apps/web && npm ci && npm run build && npm run lint && npm run test:smoke`.
2. At `?capture=1`, 1920×1080, visit school and collect **same-camera** frames, before vs after.
3. Confirm 12 PV modules and unchanged positions of fence, courtyard, roofs and windows.
4. Confirm no normal-map inversion, stretched walls, tiling discontinuity, scene flicker.
5. Validate connected, blackout and reset visual states and laptop low-power mode.
6. Do not describe outage survival as physically simulated without verified trace.

This is a **draft visual integration for review**, not an approved performance pass.
