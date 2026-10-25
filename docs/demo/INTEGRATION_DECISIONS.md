# Final demo integration decisions

Base: PR #13 at `479e8d1fdbb0c357f61468c8934a314f345a15ed`. Work proceeds on `integration/final-demo-hardening`; PR #13, `main` and teammate branches are untouched.

## Visual source: PR #15

Reviewed `creative/photoreal-district-v1` at `9f34e4827eea6c4fff449e8bea111080311e7ad3`.

- Adapted `CinematicStreets.tsx` and `RealNightLights.tsx` to the PR #13 world. The street axes, original school position and site parcels remain fixed. The new lamps use four existing pole sites and turn off with the grid.
- Corrected the inverter and storage displays and power-path glow in `DistrictWorld.tsx` so they follow the active official trace's critical-service state. The global school accent light now fades out after critical power loss.
- Did not copy PR #15's whole `DistrictWorld.tsx` because it would restore older building parcels over clinic, business and residential facilities. Did not add `SchoolHeroDetails.tsx` over the already detailed `SchoolDetails.tsx`: both define the same front and annex windows, entrance and equipment. Did not change cameras or the 12-module rooftop array.

## Analytical source: PR #14

Reviewed `feat/frontier-jury-ux` at `e788cb0`. Its readable verdict and physical map labeling informed the current UI. Its alternative 1.1.0 physics engine, ML chapter and checkpoint are not integrated. The app still validates official v1 results and preserves the 273-cell, 13-trace physical Frontier.

## Design review

12ui explored four variants of the official 1440×900 failure screenshot. Candidate B supplied the stronger hierarchy: one legible engineering finding beside the live school, then measured facts and an upgrade comparison. The implementation keeps the scene as interactive WebGL and binds every number to the validated physics response. Candidate artwork was not shipped because a rasterized school would freeze the camera, lighting and spatial interactions. Candidate B also pictured an upgrade before calculation; the running app reveals that verdict only after the user requests the comparison. The responsive export service failed after producing a fixed LayerDoc, so the generated HTML was not used as application code. The final browser screenshots, rather than the design proposal, are the visual acceptance evidence.

## Numerical source and limits

The official engine is `lastlight-dispatch-1.0.0`, schema `1.0.0`. The frontend does not recalculate first failure from a nominal step index; it reads the timestamped summary and validates trace intervals. Offline results are labeled archived, never new calculations. Other facilities remain visual-only. The JSON export contains the exact resolved inputs and response trace used in the session.

The bounded design search from [PR #17](https://github.com/pablo228sos/lastlight/pull/17) was integrated as merge commit `372ed10` after source and numerical review. Its exact source head is `390d1e7a2636b34e3aaa8d77453dbd1c4ee2758e`; [Physics API CI run 40115858905](https://github.com/pablo228sos/lastlight/actions/runs/40115858905), attempt 2, completed successfully on Ubuntu and Windows for that SHA. The first attempt had all substantive steps pass but was cancelled in Ubuntu post-run cleanup, so the successful repeat is the acceptance evidence. The branch remains a Draft PR; it was merged only into this review branch, not into `main`.

The addon has an additive `/api/v1/design-search` route and does not edit dispatch equations. It evaluates each supplied capacity through the unchanged `simulate()` function. The web adapter checks the exact official v1 model/schema, matching baseline input hash, sorted tested capacities, physical status and smallest-passing selection. It offers a live four-candidate interaction and includes the result in the JSON report. Offline mode retains the verified 24 versus 36 kWh comparison; it does not claim a new search without the API.
