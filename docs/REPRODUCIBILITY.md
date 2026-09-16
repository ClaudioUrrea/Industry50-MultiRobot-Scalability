# Reproducibility

## Environment

The results in the article were produced with:

| Component | Version |
|---|---|
| Python | 3.10.12 |
| NumPy | 1.26.x |
| SciPy | 1.11.x |
| Matplotlib | 3.8.x |
| CoppeliaSim | 4.10 EDU |
| Unity | 2022.3 LTS |
| ROS 2 | Humble Hawksbill |
| Coordination server | Intel Xeon E5-2690, 32 cores, 128 GB RAM |

Only the first four are needed to reproduce the published numbers. CoppeliaSim,
Unity and ROS 2 are needed only to re-run the digital twin itself or to deploy
the coordination layer.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/verify_paper_numbers.py
```

Expected final line: `80/80 checks passed (200 campaign replications, seed 42).`

## Seeding

`config.SEED = 42`. The scalability analysis of Section V is deterministic: it
aggregates archived traces and computes closed-form quantities, so it involves
no sampling at all. The extended campaign of Section VI is stochastic and is
seeded from `config.SEED` through `numpy.random.default_rng`; the ensemble
runner derives independent child seeds with `SeedSequence.spawn`, so a given
`--replications` value reproduces bit-for-bit on any platform with the same
NumPy major version.

## Single realisation versus ensemble

A 60-shift campaign is a small sample. Five network interruptions are *expected*
across the whole campaign, so one realisation may draw two or eight, and
availability moves by roughly a point either way (sd ≈ 0.8 points over 200
replications). Two figures are therefore reported:

- **Single realisation, seed 42** — one campaign, comparable to the trace behind
  the article. 547 units/shift, 0.8 % defects, 96.5 % uptime, 32.7 kWh/shift.
- **Ensemble mean, 200 replications** — 547.0 units/shift (sd 1.0), 0.8 %
  defects, 95.8 % uptime (sd 0.8), 32.8 kWh/shift (sd 0.2).

`verify_paper_numbers.py` compares the **ensemble mean** against Table 4, which
is the statistically appropriate comparison. Both are written to
`data/processed/campaign_summary.json`.

## Tolerances used in verification

| Class of quantity | Tolerance |
|---|---|
| Efficiencies, residuals, RMSE, availability terms | ±0.05 percentage points |
| Auxiliary fits (bandwidth, latency) | ±0.4 pp, ±0.5 ms — the bounds stated in Section V-B |
| Identified coefficients β, γ | ±0.0002, ±0.00002 |
| Triple Bottom Line reductions and social projections | ±0.5 % or ±0.05 units |
| Campaign outcome, ensemble mean | ±2 units, ±0.3 pp, ±0.3 kWh |
| Ramp-up trajectory | ±5 % (see below) |

## Two places where agreement is approximate, and why

Both are declared rather than smoothed over.

**1. The ramp-up trajectory.** The article reports 420 units/shift at shift 11,
505 at shift 26 and 540 at shift 41. The released model returns 420, 518 and
532 — within 2.6 % and 1.5 % at the two intermediate points. The published
trajectory is one realisation of a stochastic simulator with a per-shift
proficiency draw; the released model is a compact deterministic reimplementation
of the same learning curve. The steady-state value that the article actually
uses, 547 units/shift over shifts 41–60, reproduces exactly.

**2. The defect-rate reporting window.** The campaign defect rate of 0.8 % is
the mean over shifts 11–60, the post-commissioning window
(`config.DEFECT_REPORTING_WINDOW`). Including the ten commissioning shifts,
during which the cell runs at 70 % of target and the proficiency-linked defect
excess is largest, gives 0.9 %. The window is stated because the choice matters
to the first decimal.

## Model parameters that do not appear in the article

Three constants are implementation detail of the released reimplementation
rather than reported findings, and are documented here so that nothing in the
code is unexplained:

| Constant | Value | Role |
|---|---|---|
| `BUFFER_RECOVERY_FRACTION` | 0.88 | Fraction of output nominally at risk from downtime that inter-station buffering and catch-up recover within the same shift. This is the mechanism by which 2.7 points of lost availability cost only about 1.3 % of throughput, as Section VI-B explains. |
| `ENERGY_IDLE_KW` | 2.00 | Standby draw while a station is down, in the energy model of Section VI-B. |
| `ENERGY_REWORK_KWH_PER_PCT` | 1.70 | Rework energy per percentage point of defect rate. |

## What cannot be reproduced from this repository alone

The digital twin itself. Re-running the CoppeliaSim scenes requires a licensed
CoppeliaSim 4.10 installation and the scene archive from the Figshare deposit.
The repository reproduces every *published number* from the aggregated series,
which is the claim the article makes; it does not re-execute the physics.
