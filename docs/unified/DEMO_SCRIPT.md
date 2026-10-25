# Two-minute demonstration

**0:00–0:20 — The school and the question.**
Open LASTLIGHT, skip the introduction, select School and disconnect the grid.
“These are synthetic school assumptions. The official energy model calculates
the trace; the 3D lighting follows it.” Show 24 kWh, 80% starting charge and the
physical failure at 9.12 hours. Scrub before/after that point.

**0:20–0:45 — Inspect the boundary.**
Open Failure Frontier. “Charge and blackout duration determine whether critical
demand is served. Each color comes from deterministic physics.” Point to the
selected charge/window. Explain that a failure exactly at the excluded endpoint
is not an observed failure in that window.

**0:45–1:15 — What AI actually contributes.**
Show AI-suggested cases. “The trained model chooses cases near its estimated
boundary. Every outlined marker was independently simulated. Twelve checked
cases is a count, not accuracy, and this is not a speedup claim.” Close the map,
run AI resilience analysis and show the physical verdict beside the model's
actual score/version. “It predicts synthetic scenario labels, not city outage
probability. Physics wins if they disagree; range and uncertainty warnings stay
visible. Missing AI does not disable physics.”

**1:15–1:45 — A distinct forecasting capability.**
Open Demand Research and run the historical example. Show past observations,
the real GRU's next-hour forecast, preferred persistence and recorded actual.
“This is attributed overseas whole-building data, not a Kyrgyz school's critical
circuits. Persistence currently has lower validation MAE; we retain it.”

**1:45–2:00 — Evidence and limits.**
“Both neural networks have real weights and reproducible evaluations. The new
timing classifier missed 14 versus the original's 19 on a fresh 600-case test;
errors remain. Forecasts are separate research and do not enter emergency load
physics. A direct 12-hour experiment also retains its stronger simple baseline.
This is a tested hybrid demonstration, not field certification.”
