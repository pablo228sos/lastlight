# Measured execution latency

Local Windows CPU, Python 3.12. Three new-process measurements per cold workload;
20 serial warm repetitions after one warmup. These measurements exclude browser
rendering and HTTP/JSON overhead. OS filesystem cache was not flushed. Raw
samples/definitions are in [performance.json](performance.json).

| Workload | Warm median ms | Warm p95 ms | Cold import + first result median ms |
|---|---:|---:|---:|
| One official 16 h simulation | 1.765 | 1.862 | 392 |
| Verified timing neural analysis | 7.566 | 8.158 | 3,888 |
| Combined physics + neural assessment | 14.918 | 15.246 | 3,800 |
| Physical Frontier, 13 traces / 273 cells | 24.277 | 26.074 | 410 |
| Score 273 points + independently check 12 candidates | 101.488 | 110.695 | 3,988 |
| Actual one-hour EnergyDNA preview | 3.972 | 4.067 | 5,074 |

The candidate cold setup also constructs a physical map to obtain its input
points. These workloads return different outputs. They are not a scientific
comparison of two algorithms producing the same exact Frontier. **No AI search
acceleration is demonstrated or claimed.** The physical map is already fast.

Feature extraction + calibrated score alone, 100 serial warm CPU repetitions:
frozen logistic .210 ms; original MLP .494 ms; timing logistic .587 ms; timing
MLP .814 ms. Those exclude catalog/disk/source verification and physics; raw
p95 values are in `research/reliability/artifacts/latency.json`.

Cold package imports dominate first neural requests. The UI gives a loading
state and a 30-second deadline, aborts obsolete requests, and retains physical
results on failures. Backend endpoints run synchronous compute in FastAPI's
worker pool; they do not compute inside the browser's animation loop. Small
PyTorch classifiers use one CPU thread to avoid thread fanout for tiny layers.
These are local reproducible workload measurements, not a hardware-independent
latency guarantee or a network performance claim.

Reproduce: `python -m ml_bridge.benchmark` and
`python -m research.reliability.benchmark`.
