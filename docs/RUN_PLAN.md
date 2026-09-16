# P3 verification campaign — run plan

Everything here drives your own CoppeliaSim twin. No number in the output is
produced by the scripts themselves; they set parameters, wait, and read back
the telemetry the scene already writes.

## Files

| File | Role | Edit? |
|---|---|---|
| `p3_campaign_runner.py` | Experiment matrix and driver. Nine blocks, 3,970 runs. | No |
| `p3_twin_adapter.py` | Connects to CoppeliaSim, sets signals, reads telemetry. | **Yes — this one only** |
| `p3_analysis_v7.py` | Statistics and LaTeX fragments. | No |
| `requirements.txt` | Python dependencies. | No |

## 0. Setup

```bash
pip install -r requirements.txt
```

Then open `p3_twin_adapter.py` and reconcile two dictionaries with the scene:

- `SIGNALS` — the signal name the scene reads for each run parameter. Add any
  that do not exist yet to the scene's Lua script. The scene must set
  `p3_run_complete` to 1 when it has finished the requested number of shifts,
  and must write its per-shift telemetry to the path given in
  `p3_telemetry_path`.
- `TELEMETRY` — the column name in that CSV for each of the 32 metrics. It is
  identity by default; override only the ones that differ.
- `SCENE_FOR_CELL` — the `.ttt` file for each geometry.

Five metrics are new and have to be emitted by the scene, because they are the
direct contention measurements that replace robot active time as evidence:

```
idle_spatial_pct  idle_task_dep_pct  idle_material_pct
idle_operator_pct  idle_sync_pct
```

together with `swept_volume_overlap_m3` and `interference_events_shift`. The
five idle components should partition the robot's non-executing time and sum to
100 minus the active percentage.

Check the wiring before committing to a long campaign:

```bash
python3 p3_twin_adapter.py --selftest --scenes scenes/
python3 p3_campaign_runner.py --block replication --seeds 2 --out runs_smoke/
python3 p3_analysis_v7.py --runs runs_smoke/ --out tex_smoke/
```

If `tex_smoke/tab_replication.tex` contains plausible numbers with intervals,
the chain works.

## 1. Sizing the campaign

Time one run, then plan:

```bash
python3 p3_campaign_runner.py --block all --dry-run --minutes-per-run 12
```

At 12 minutes per run the full matrix is about 33 days of single-machine
wall-clock. Blocks are independent, so they parallelise across machines or
CoppeliaSim instances simply by running different `--block` values into the
same `--out` directory. Every block resumes where it stopped; re-running a
finished block is a no-op.

## 2. Execution order

Run in this order. The first two do most of the work.

```bash
python3 p3_campaign_runner.py --block replication --out runs/   #  150 runs
python3 p3_campaign_runner.py --block range       --out runs/   #  630 runs
python3 p3_campaign_runner.py --block ablation    --out runs/   #  450 runs
python3 p3_campaign_runner.py --block disruption  --out runs/   #  150 runs
python3 p3_campaign_runner.py --block network     --out runs/   #  720 runs
python3 p3_campaign_runner.py --block baselines   --out runs/   #  840 runs
python3 p3_campaign_runner.py --block geometry    --out runs/   #  600 runs
python3 p3_campaign_runner.py --block operators   --out runs/   #  270 runs
python3 p3_campaign_runner.py --block compute     --out runs/   #  160 runs
```

Analyse after each block; the pipeline skips whatever is absent.

```bash
python3 p3_analysis_v7.py --runs runs/ --out tex/
```

## 3. What each block closes

| Block | Reviewer points | What changes in the paper |
|---|---|---|
| `replication` | R2-2, R3-19, R4-3 | Every tabulated quantity gains a mean over 30 seeds with a 95% interval. Error bars on all four figures. The TOPSIS ranking is recomputed under seed resampling, so the preference for N=3 becomes a probability instead of a point claim. |
| `range` | R2-4, R3-5, R4-5 | β and γ separate, or are shown not to. N=6 and N=7 are simulated in 18 and 24 m², with robot count and area crossed rather than confounded. The geometric bound is tested instead of asserted. |
| `ablation` | R3-15 | Individual contribution of fatigue reallocation, REBA allocation, velocity modulation and adaptive assistance, by Welch's test with effect size, at N=2, 3 and 5. |
| `disruption` | R2-5, R3-20 | The availability allowance stops being an N=2 result. Variance and intervals on throughput, uptime, defect rate and energy at every N. |
| `network` | R3-10 | Packet loss, jitter and degraded bandwidth replace bandwidth utilisation as the communication evidence. |
| `baselines` | R3-8, R3-24 | ADMM against centralized MILP, hierarchical zones and market-based allocation; SSM against reciprocal-velocity and prioritized planning. Paired on cell, task and seed list. |
| `geometry` | R1-3, R3-5, R3-28 | The contention coefficient per shape and per task spread, which is what the generalization argument currently asserts without evidence. |
| `operators` | R1-3, R3-5 | The O(NK) term measured rather than bounded. |
| `compute` | R3-9, R3-27 | The computational ceiling measured at four core counts, replacing the analytical entry in the resource-ceilings table. |

Running `replication` and `range` alone converts four of the eight
threats-to-validity items into results.

## 4. Outputs

`p3_analysis_v7.py` writes into `--out`:

- `tab_replication.tex` — throughput and efficiency per N with intervals.
- `tab_modelsel.tex` — six functional forms with RMSE, AICc and LOO on the
  extended series.
- `tab_idle_decomposition.tex` — the five idle-time components per N.
- `coef_uncertainty.json` — β and γ with standard errors, t-intervals,
  bootstrap percentile intervals, correlation and p-values.
- `range.json`, `geometry.json`, `operators.json`, `baselines.json`,
  `network.json`, `ablation.json`, `disruption.json`, `compute.json`.
- `report.json` — everything above in one file, including the seed-resampled
  TOPSIS stability and the geometric capacity bound.

## 5. Depositing

Add to the figshare record, alongside the existing material:

- `runs/*.csv` — the raw per-run output.
- `runs/manifest.json` — git hash, scene checksums, seed list, wall-clock.
- `tex/report.json` and the LaTeX fragments.
- These four scripts.

The manuscript states that every number regenerates from the deposited code.
Keeping the raw CSVs in the record is what makes that statement checkable, and
it is the first thing a sceptical reviewer will look for.
