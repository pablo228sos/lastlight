# Engineering plan

The browser app uses React, TypeScript and Vite. The independent Python service
in `services/simulation` owns deterministic battery, solar and load calculations.
The frontend renders a versioned simulation trace through a dedicated scene
adapter without independently recomputing physics. Python schemas generate
OpenAPI and TypeScript wire types; contract drift is checked in CI.

For each interval, stored battery energy changes by charged energy times charge efficiency, less discharged energy divided by discharge efficiency. Grid input is zero during an outage. Solar input in island mode requires suitable equipment. Battery energy, inverter output and served critical load must respect their limits. The energy balance residual must be recorded.

A reference case uses 1.5 kW critical load, a 24 kWh battery, 80% initial charge,
20% minimum charge, 95% discharge efficiency and no solar. Its continuous
idealized autonomy is `(0.8 - 0.2) * 24 * 0.95 / 1.5 = 9.12 hours`. The engine
now reproduces that event inside the sampling interval and the school UI shows
it. The legacy simulator remains archived; its equations/tests informed the
reviewed team engine, not a second running backend.

Implemented outputs include served/unserved energy, observed first failure, SOC,
curtailment, losses, residuals and provenance. Default input resolution is 15
minutes; event intervals split exactly at SOC limits. Variable critical,
noncritical, PV and grid profiles are supported. See [MODEL](physics/MODEL.md),
[wire contract](physics/CONTRACT.md) and [ML architecture](ML_ARCHITECTURE.md).

These are calculations under declared simplified assumptions. They are not
field validation, certified electrical design or evidence about a real school.
