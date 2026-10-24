# Engineering plan

The browser app uses React, TypeScript and Vite. A future service will own deterministic battery, solar and load calculations. The frontend will render a versioned simulation trace, without independently recomputing physics.

For each interval, stored battery energy changes by charged energy times charge efficiency, less discharged energy divided by discharge efficiency. Grid input is zero during an outage. Solar input in island mode requires suitable equipment. Battery energy, inverter output and served critical load must respect their limits. The energy balance residual must be recorded.

A simple reference case uses 1.5 kW critical load, a 24 kWh battery, 80% initial charge, 20% minimum charge, 95% discharge efficiency and no solar. Its continuous idealized autonomy is `(0.8 - 0.2) * 24 * 0.95 / 1.5 = 9.12 hours`. This is a test fixture, not a result produced by the current browser app. The legacy simulator in `reference/legacy-physics` is retained for equation review and is not wired into the product.

Planned outputs include served critical energy, first failure time, battery state of charge, unserved demand and provenance. They require validation before publication as engineering results.
