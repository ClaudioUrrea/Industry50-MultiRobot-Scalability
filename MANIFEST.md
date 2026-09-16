# Artefact manifest

This file records what exists, where it is, and what it permits. It replaces an
earlier version that listed two archives which were never deposited.

## In this repository

Everything needed to reproduce every number in the paper is here, in
`src/`, `scripts/`, `data/processed/` and `tests/`. Nothing has to be downloaded
to run `scripts/verify_paper_numbers.py` or the test suite.

## In the Figshare deposit

<https://doi.org/10.6084/m9.figshare.33090107>

| File | Contents |
|---|---|
| `Industry50-MultiRobot-Scalability-code.zip` | A snapshot of this repository at the version of record |
| `data_processed.zip` | The archived series of `data/processed/`, standalone |
| `data_ensemble.zip` | The 500-replication ensemble and sensitivity output |
| `figures.zip` | The four figures of the paper, PDF and PNG |
| `CHECKSUMS.txt` | SHA-256 of each file above |

Generate the checksum file before uploading:

```bash
python scripts/make_manifest.py dist/*.zip
```

## Not available

`DigitalTwin_Scenes.zip` — the CoppeliaSim 4.10 scenes, UR5 and sensor models,
Unity visualisation project and synchronisation layer.

These files were lost and are not recoverable. No copy is held by the author or
in the deposit. The consequence is stated plainly in the paper: the *N* = 1–5
series archived in `data/processed/scaling_results.csv` cannot be regenerated
by re-executing the physics, by the author or by anyone else. The series is the
input to the analysis rather than a reproducible output of it.

Two things mitigate that and neither repairs it. `docs/SIMULATION_SPEC.md`
carries the full specification of the cell, the robot parameters, the control
and coordination rates, the sensing chain and the safety layer, which is what a
third party would need to rebuild an equivalent twin. And Section XI-D of the
paper reports how large an error in the archived series would have to be before
each conclusion changed: 3 % dispersion leaves the preferred configuration
unchanged in 98 % of draws, 5 % dispersion leaves the model-selection verdict
unchanged in 99 % of draws, and the bottleneck ordering survives a 19 %
systematic error in the latency series.

`Scalability_Simulation_N1-N5.zip` — the raw per-cycle traces behind the
aggregated series. Not deposited. The aggregated series in `data/processed/`
are what the analysis consumes and are included in full.
