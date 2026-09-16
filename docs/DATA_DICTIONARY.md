# Data dictionary

Every file written to `data/processed/` by the scripts in `scripts/`.

## `scaling_results.csv` — one row per configuration, N = 1..5

| Column | Unit | Provenance | Source in article |
|---|---|---|---|
| `N` | robots | design | Section V |
| `throughput_simulated_units_per_shift` | units per 8 h shift | simulated | Table 3 |
| `throughput_ideal_units_per_shift` | units per shift | derived, `N · T(1)` | Table 3 |
| `efficiency_simulated_pct` | % | derived, Eq. 1 | Table 3 |
| `efficiency_predicted_pct` | % | derived, Eq. 3 | Table 3 |
| `fit_residual_pp` | percentage points | derived, simulated − predicted | Table 3 |
| `workspace_utilisation_pct` | % of shift time executing | simulated | Table 3 |
| `bandwidth_utilisation_pct` | % of 100 Mbps link | simulated | Table 3 |
| `planning_latency_ms` | ms per 50 Hz cycle | simulated | Table 3 |
| `dt_sync_mean_ms`, `dt_sync_p95_ms`, `dt_sync_max_ms` | ms | simulated | Figure 3 |
| `separation_fixed_m` | m | simulated | Figure 1 |
| `separation_learned_cbf_m` | m | simulated | Figure 1 |
| `separation_violations` | count | simulated | Section V-B |

`fit_residual_pp` is a **goodness-of-fit residual, not a prediction error**: β
and γ were identified from this same efficiency series.

## `campaign_shifts.csv` — one row per shift, 60 shifts

| Column | Unit | Meaning |
|---|---|---|
| `shift` | index 1..60 | shift number |
| `downtime_min` | min | cell-equivalent downtime sampled from the three disruption families |
| `availability` | fraction | nominal 0.985 less the sampled downtime fraction |
| `proficiency` | fraction | learning curve `p(s) = 1 − 0.52 exp(−(s−1)/12)` |
| `target_units` | units | production target under the three-phase ramp |
| `units` | units | realised throughput |
| `defect_rate_pct` | % | stationary fault term plus decaying proficiency excess |
| `energy_kwh` | kWh | nominal plus idle-standby plus rework energy |

## `campaign_summary.json`

Four blocks: `single_realisation` (seed 42), `ensemble` (means and standard
deviations over the replications requested), `published_table4`, and
`closed_form_prediction`. The `availability_decomposition` sub-block carries the
three unavailability terms of Section VI-B in per cent.

## `table2_triple_bottom_line.csv`

Long format: `configuration, pillar, indicator, value, unit, provenance`. The
**provenance column is the point of this file**. Rows carrying `projected` are
obtained by applying published empirical relationships to the simulated REBA and
modelled workload trajectories; they are not measurements and not findings of
this work. Rows carrying `simulated` are digital-twin outputs.

## `table5_configuration_selection.csv`

Performance–complexity trade-off across N = 1..5, matching Table 5.

## `scaling_summary.json`

Identified coefficients, RMSE, campaign accounting (440 h, 1 320 robot-hours,
440 operator-hours), the bottleneck verdict, and the two projected ceilings
(bandwidth saturation near N ≈ 11, computation budget exhausted near N ≈ 6).
