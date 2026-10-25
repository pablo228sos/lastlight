# Forecast-to-physics foundation: explicit research contract

`research/energydna/profile_contract.py` defines
`lastlight-forecast-allocation-research-1`; its generated JSON schema is
[forecast-allocation.schema.json](forecast-allocation.schema.json).
It is separate from the official `SimulationRequest` and is not an accepted
physical-load schema or an automatic adapter into the live simulator.

The required fields identify source building, source references/checksum, model,
timezone-aware forecast origin, IANA source zone, interval/horizon, finite
nonnegative whole-building average kW, missing-data policy and explicit allocation
evidence/reviewer. A naive source clock is rejected: the BDG2 demonstration's
unresolved local/DST basis cannot silently become a reviewed UTC physical trace.

Each 60-minute average kW value represents `kW × 1 h` kWh. All forecast intervals
must be present. A 12-hour profile has exactly twelve values. Missing predictions
are rejected, not forward-filled into an engineering load. This contract accepts
1–24 hourly intervals and refuses other intervals/units until a versioned design
specifies their treatment.

An explicit critical fraction allocates each hourly value into critical and
noncritical parts; tests verify their sum and integrated energy. **A typed
reviewer string does not verify a real review.** Circuit allocation still needs
actual independent circuit evidence; whole-building demand does not establish
critical demand. The result always states `engineering_clearance:false` and
`official_v1_dynamic_load_compatible:false`.

Optional lower/upper bounds must cover the full horizon and contain every point
forecast. They indicate supplied uncertainty only; neither trained EnergyDNA
artifact currently provides calibrated intervals. The application states that
limitation. Realized future weather is not part of either model's inputs.

`to_official_v1()` deliberately raises an explicit compatibility error. Official
v1 has constant critical/noncritical load fields. The allocation proposal does
not average, reinterpret, or inject unsupported dynamic profiles into it.

A future owner-reviewed extension must version both load semantics and physical
equations, specify whether timestamps mark interval starts/ends, and align
forecast intervals to physical sampling using energy-conserving interval
intersections, including partial steps. It needs independent energy-balance,
reserve, power-limit and exclusive-horizon regressions before activation.
No such extension or owner approval is assumed in this PR.
