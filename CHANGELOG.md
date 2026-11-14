# Changelog

## v2.1 — accepted version, November 2026

The article was accepted by IEEE Access on 13 November 2026 as manuscript
Access-2026-47170. This release aligns the repository with the accepted text.
No published number changes; `scripts/verify_paper_numbers.py` still reports
80/80 and the test suite still reports 42 passed.

**The safety layer is now described as it is implemented.** `README.md`,
`docs/SIMULATION_SPEC.md` and `docs/MAPPING_PAPER_TO_CODE.md` state that
`ros2_bridge.CoordinationBridge.scale_velocity` sits outside the reproduction
path by the module's own design, that nothing in the package calls it, and that
the velocity constants in `config.py` record the policy rather than drive a
campaign. The accepted article makes the matching statement: the separations of
the learned policy are reported as separation behaviour, and admissibility under
the protective separation distance would require a velocity schedule tied to
that distance, which this study did not implement and the campaigns did not
measure.

**Stored constants are labelled as such.** `SEPARATION_FIXED_M` and
`SEPARATION_LEARNED_CBF_M` are archived campaign outputs consumed only by
`coordination.conservatism_reduction_pct`. `docs/MAPPING_PAPER_TO_CODE.md` and
`docs/DATA_DICTIONARY.md` now say so, so that no reader mistakes the Figure 1
series for a computed result.

**Deposit contents stated precisely.** The deposit records the minimum observed
separation and the violation count, not a full separation distribution. The
accepted article was corrected to match, as was `MANIFEST.md`.

**Figure generator reconciled.** `src/industry50/figures.py` predated the
revision and disagreed with the published figures in two places: it labelled the
0.15 m line "ISO min" rather than "Design floor" and omitted the protective
separation distance line in Figure 1, and it labelled the Figure 4 reference
series "Projected" rather than "Nominal simulation". Both were terminology the
revision corrected, so the module reproduced pre-revision figures. It now
carries the same code as `scripts/p3_figures_v7.py`, which generated the
published figures, and the Figure 4 method is renamed
`fig4_disruption_comparison` to match. Nothing in the package called the old
names. `docs/MAPPING_PAPER_TO_CODE.md` records the change.

**Figure script corrected (v8).** Four defects were fixed in the generator, now
identical in `scripts/p3_figures_v7.py` and `src/industry50/figures.py`.
(i) In Figure 1 the legend hid the "1.20 m" bar label, because matplotlib's
'best' placement avoids bars and lines but not `ax.text()` annotations; the
y-limit was raised to 1.95 m and the legend fixed at the upper right.
(ii) The Figure 1 legend read "Traditional" where the article says
"fixed-separation baseline"; it now reads "Fixed separation".
(iii) Figure 4 plotted a disrupted uptime of 95.9 % while Table 9, which its
caption cites, and the running text both give 95.8 %, so the figure showed a
deviation of -2.6 % against the -2.7 percentage points stated in the text. The
value now follows Table 9.
(iv) In Figure 4 the 100 % reference line struck through the value labels of
bars that land just below nominal; those labels now carry a white background.
The header, the run banner and the unrounded coefficients of Eq. 3 were brought
up to date, the blanket warning filter was narrowed to the font-fallback notice
so that real errors surface, `figure.autolayout` was disabled where
`tight_layout()` is called explicitly, and the output directory is created with
`parents=True`. No plotted series changed except the uptime value named above.

**Scene wording aligned.** `README.md` and `MANIFEST.md` now use the same
formulation as the Figshare description and the article: the scene files are not
available and are not part of the deposit, so the *N* = 1–5 series are an input
to the analysis rather than a reproducible output of it.

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
