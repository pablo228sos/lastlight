# Unified intelligence: compatibility audit and execution plan

## Audited sources (2026-10-25, Asia/Bishkek)

| Source | Head | Integration decision |
|---|---|---|
| PR13 release candidate | 479e8d1 | Official dispatch/schema 1.0.0 and existing React/Three scene |
| PR19 official ML | b3b4c4b | New branch starts here; both genuine checkpoints retained |
| PR18 design search | a986245 | Same merge base 479e8d1; separate additive API, owner branch preserved |
| PR7 legacy ML | 7147b3f | Incompatible 1.1 physics/requests/checkpoint; no code transplant |
| PR14 jury UX | e788cb0 | Readable verdicts/labels/checked-case markers as reference only |

Both PR19 and PR18 merge bases with the release candidate are 479e8d1.
PR7/PR14 merge bases with the release candidate are `776caa4`; PR14's merge
base with PR7 is `7147b3f`, confirming its incompatible research ancestry.
The work branch is `feat/unified-ml-intelligence`, with PR19 as the stacked
review base. PR18 remains a separate contributor PR; no competing design-search
implementation or owner-branch rewrite is introduced.

Read before shared changes: official engine/schema/frontier/API, frontend
App/usePhysicsRun/instrument/frontier/client, bridge contracts/runtime/features/
loader/adapter/candidates, actual registered model manifests/evaluations, and
EnergyDNA source/checkpoint. Both actual checkpoints loaded successfully.
Official source SHA remains
`d776af652f8bba19b666ff9acf6cea1f801c0d57f6af033de230eb1581cc4a7a`.

Important findings:

- The default school request is 12 hours. A 16-hour reference must be an actual
  user-selected request; its result must not be fabricated in labels.
- The current Frontier client silently always requests the 12-hour baseline,
  even after an upgrade. It must receive the active official input.
- The physical API has no integrated ML routes; the bridge is a separate app.
- The standalone physics installer copies only the simulation package and
  compares its exact OpenAPI to the frozen official document. Optional ML must
  not break this independent installation or its contract.
- The current source fingerprint covers engine/schema/package, not API mounting;
  route integration can preserve the already verified model identity.
- Existing FragilityNet test has 20 false negatives (logistic 18); existing
  EnergyDNA loses to persistence on MAE. Neither is silently marketed as better.
- UI reference PR14 uses incompatible legacy envelopes. Only presentation ideas
  are reusable; physical traces and scene/camera/geometry remain official.

## Execution order and acceptance

1. **Backend (P0):** mount strict typed assessment/candidate routes on the
   official application with lazy optional ML imports. Preserve the frozen
   physical OpenAPI; expose a separately generated additive intelligence schema
   for discovery/client types. HTTP tests compare complete official results,
   exact 9.12-hour boundaries and missing/corrupt-runtime fallback.
2. **Application (P0):** use the actual active scenario for physics, AI and map.
   Add accessible analysis and checked-candidate controls, readable physical/AI
   verdicts, provenance/OOD/uncertainty, cancellation/timeouts and stale-result
   rejection. Existing scene/lighting/cameras are not edited. Browser evidence
   at 1366x768, 1440x900 and 1920x1080 must use genuine unified HTTP responses.
3. **Forecast preview:** package attributed historical inputs, compute actual
   GRU and preferred persistence predictions at request time, show observed past
   and recorded target separately. Keep it explicitly research-only. Missing
   neural packages must not prevent physics or the simple research baseline.
4. **Classification reliability:** replay every actual old false negative,
   inspect traces, pre-register a fresh holdout before new comparisons, and
   compare input-only timing features/thresholds using train/validation only.
   Do not register an inferior checkpoint as an upgrade.
5. **Forecast evidence:** audit degenerate/sparse/abnormal cohorts without
   deleting difficult outcomes; report identical-target and per-building
   baseline comparisons. Investigate a separately evaluated direct 12-hour
   model while preserving the working one-hour artifact.
6. **Compatibility foundation:** typed forecast-to-demand proposal with explicit
   source/time/units/gaps/uncertainty/allocation. Official v1 accepts constant
   loads; no unsupported profile injection or silent critical-load conversion.
7. **Verification/delivery:** real backend + browser/fallback tests, unchanged
   physical fixtures, actual latency measurements (warm/cold), judge overview,
   two-minute script, screenshots and Draft PR. Merge/production approval stays
   with the team; no main push.

Alternatives rejected: transplant legacy engine (incompatible), keep a separate
prototype (misses the user flow), or replace the working physical map with ML
ranking (no demonstrated speed advantage). The selected integration reuses
verified components and makes their different evidentiary roles visible.
