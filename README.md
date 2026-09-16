# Industry 5.0 multi-robot scalability — code and data

Companion repository for

> C. Urrea, "Simulation-Based Scalability Assessment of Multi-Robot Industry 5.0
> Human-Centric Cells: Coordination-Efficiency Modeling, Bottleneck
> Identification, and Triple-Bottom-Line Screening in a Physics-Based Digital
> Twin," *IEEE Access*, 2026 (under review).

Data deposit: <https://doi.org/10.6084/m9.figshare.33090107>

---

## What this repository reproduces, and what it does not

Two levels of reproducibility exist here and they are not the same thing. The
distinction is stated in the paper and is repeated at the top of this file
because it is the first thing a reader should know.

**Every derived quantity in the paper recomputes from the archived series.**
`scripts/verify_paper_numbers.py` performs 80 such checks and all 80 pass.
`tests/` holds 42 unit tests over the same code. Coordination efficiency, the
fitted coefficients with their intervals, the model comparison, the geometric
capacity bound, the resource ceilings, the configuration ranking, the Triple
Bottom Line screening and the uncertainty propagation are all computed here,
from the constants and series in `src/industry50/config.py` and
`data/processed/`.

**The stochastic disruption model is executable.** It is not a stored result.
`scripts/p3_disruption_ensemble.py` runs it 500 times under independent seeds
and produces the intervals and the sensitivity analysis reported in the paper.

**The physics cannot be re-executed.** The CoppeliaSim scene files behind the
*N* = 1–5 throughput, occupancy, latency, bandwidth and separation series are
not available and are not part of the deposit. Those series are archived in
`data/processed/` and are the input to everything above, but they are an input
to the analysis rather than a reproducible output of it. `docs/SIMULATION_SPEC.md` gives the full specification needed
to rebuild an equivalent twin, and `scripts/p3_campaign_runner.py` is written
against that specification rather than against a particular scene.

The paper states this in its Data Availability Statement, quantifies what it
costs in Section XI-C, and bounds the exposure in Section XI-D by reporting how
large an error in the series would have to be before each conclusion changed.

---

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/verify_paper_numbers.py     # expect: 80/80 checks passed
python -m pytest -q tests/                 # expect: 42 passed
```

On Windows use `py` instead of `python`. If the imports fail, set
`PYTHONPATH=src` (`$env:PYTHONPATH="src"` in PowerShell).

## Reproducing the paper

| Paper artefact | Command |
|---|---|
| All 80 numerical checks | `python scripts/verify_paper_numbers.py` |
| Table 4 (scaling series) | `python scripts/run_scalability_campaign.py --out data/processed` |
| Table 9 (extended campaign) | `python scripts/run_extended_campaign.py --out data/processed` |
| Tables 11–12 (ensemble, sensitivity) | `python scripts/p3_disruption_ensemble.py --repo . --reps 500 --sens-reps 200 --out data/ensemble` |
| Tables 2, 8 (TBL, configuration) | `python scripts/make_tables.py --out data/processed` |
| Figures 1–4 | `python scripts/p3_figures_v7.py --output figures` |

The ensemble run takes a few minutes. Everything else is seconds.

## Layout

```
src/industry50/     the model and the analysis
  config.py         every published constant, annotated with its table
  coordination.py   efficiency model, fits, bottleneck analysis
  disruption.py     stochastic disruption model (executable, seeded)
  campaign.py       campaign drivers and the replication ensemble
  reba.py           REBA scorer
  tbl.py            Triple Bottom Line accounting with provenance labels
  figures.py        figure data helpers
  ros2_bridge.py    ROS 2 interface used by the coordination layer
scripts/            entry points, verification, drivers
data/processed/     archived series and generated tables
data/ensemble/      ensemble and sensitivity output
docs/               specification, reproducibility notes, mapping, dictionary
figures/            the four figures of the paper, PDF and PNG
tests/              42 unit tests
```

## Verification campaign that an instantiated twin would permit

`scripts/p3_campaign_runner.py` implements the 3,970-run matrix specified in
Table 10 of the paper: replication, range extension to *N* = 7, geometry and
task variation, multiple operators, algorithmic baselines, network degradation,
ablation, disruption at every configuration, and computational scaling.
`scripts/p3_twin_adapter.py` is the only file that would need editing to point
it at a rebuilt twin. `scripts/p3_analysis_v7.py` consumes the output and emits
the corresponding tables. `docs/RUN_PLAN.md` explains the order and what each
block closes.

None of it has been executed. It is deposited so that the protocol can be
judged and, if anyone instantiates an equivalent cell, executed.

## Human subjects

No human participants were involved at any stage. The operators in the
simulation are model agents. No survey, interview, physiological recording or
observational measurement involving a person was conducted, and no data of
human origin were collected. Satisfaction, injury, absence and turnover figures
are projections obtained by applying published exposure–response relationships
to simulated trajectories; they are labelled `projected` in `tbl.py` and are
not findings of this work.

## Licence

Code: MIT (`LICENSE-CODE`). Data, documentation and figures: CC BY 4.0
(`LICENSE`). CoppeliaSim and Unity are not redistributed and are not required
by anything in this repository.

## Citation

See `CITATION.cff`. Correspondence: claudio.urrea@usach.cl
