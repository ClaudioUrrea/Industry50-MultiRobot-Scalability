# Changelog

## v2.0 — resubmission to IEEE Access, September 2026

Aligned with the revised manuscript. The substantive changes:

**Provenance stated accurately.** The CoppeliaSim scene files were lost and are
not recoverable. `MANIFEST.md` and `README.md` now say so, and the earlier
listing of two archives that were never deposited has been removed. The
distinction between recomputing derived quantities, which this repository does
in full, and re-executing the physics, which is no longer possible, is stated
at the top of the README.

**Monetary labour cost removed.** `config.TBL` reported `labour_cost_usd` while
the simulation contains no wage model. It is replaced by `direct_labour_h` and
`labour_intensity_h_per_100u`, which are derived from simulated staffing and
output. `tbl.py`, the verifier and the tests follow.

**Carbon recomputed from a stated emission factor.** A single grid factor of
0.44 kg CO2e/kWh is now applied explicitly, so carbon is a declared linear
rescaling of energy: 18.6, 13.7 and 17.0 kg per shift. The previous values were
not consistent with any single factor and implied a 28 % reduction where the
energy reduction is 26 %.

**Extended campaign reported as an ensemble.** Table 9 of the paper now reports
the mean over 500 independent realisations rather than a single seeded run, and
`CAMPAIGN_PUBLISHED["energy_kwh"]` moves from 32.7 to 32.8 accordingly.
`scripts/p3_disruption_ensemble.py` produces the intervals and the sensitivity
analysis.

**Ramp trajectory corrected.** The expected values at shifts 26 and 41 were 505
and 540, which the model no longer produces. The ensemble means are 517 and
542, and the verifier and the manuscript now use those.

**New drivers deposited.** `p3_disruption_ensemble.py` (replication and
sensitivity, executable today), `p3_campaign_runner.py` and `p3_twin_adapter.py`
(the 3,970-run verification protocol of Table 10, executable only against a
rebuilt twin), `p3_analysis_v7.py` (the analysis pipeline for that protocol),
and `p3_figures_v7.py` (figures regenerated with corrected labels).

**Verifier labels resynchronised.** The check labelled "labour cost reduction"
measured labour intensity; the campaign energy expectation still read 32.7; the
ramp trajectory was read from a single seeded realisation while the manuscript
reports the ensemble mean, which put shift 41 ten units apart; and the table and
section references pointed at the numbering of the previous manuscript. All
four corrected: the ramp check now averages over the same spawned seeds as the
campaign table, and section references were replaced by descriptive labels so
that they survive renumbering at proof stage.

Verification after the changes: 80/80 checks passed, 42 tests passed.

## v1.0 — original submission, July 2026

First public release accompanying the submitted manuscript.
