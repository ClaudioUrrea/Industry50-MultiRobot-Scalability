# Paper-to-code map

Where every reported quantity comes from. Run
`python scripts/verify_paper_numbers.py` to recompute all of it at once.

## Equations

| In the article | In the code |
|---|---|
| Eq. 1, `η(N) = T(N)/(N·T(1))` | `coordination.efficiency_from_throughput` |
| Eq. 2, `τ_c(N) ≈ α N²` | conceptual; its empirical counterpart is γ in Eq. 3 |
| Eq. 3, `η(N) = η₀(1 − β(N−1) − γ(N−1)²)` | `coordination.efficiency_model` |
| Least-squares identification of β, γ | `coordination.identify_coefficients` |
| RMSE of the fit | `coordination.fit_rmse` |
| `b(N) = b₀ + κN²` | `coordination.bandwidth_model` |
| `t(N) = t₀ + cN^1.3` | `coordination.latency_model` |
| `U = E[R]/(MTBF + E[R])` | `disruption.steady_state_unavailability` |
| `E[R] = median · exp(σ²/2)` | `disruption.lognormal_mean` |
| `p(s) = 1 − d exp(−(s−1)/τ)` | `disruption.proficiency` |

## Tables

| Table | Script | Output |
|---|---|---|
| Table 1, Industry 4.0 vs 5.0 | narrative only | — |
| Table 2, Triple Bottom Line | `scripts/make_tables.py` | `data/processed/table2_triple_bottom_line.csv` |
| Table 3, scaling fit vs digital twin | `scripts/run_scalability_campaign.py` | `data/processed/scaling_results.csv` |
| Table 4, extended campaign | `scripts/run_extended_campaign.py` | `data/processed/campaign_summary.json` |
| Table 5, configuration selection | `scripts/make_tables.py` | `data/processed/table5_configuration_selection.csv` |

## Figures

| Figure | Function |
|---|---|
| Fig. 1, safety performance | `figures.IEEEAccessFigures.fig1_safety_performance` |
| Fig. 2, throughput scaling | `figures.IEEEAccessFigures.fig2_throughput_scaling` |
| Fig. 3, latency scaling | `figures.IEEEAccessFigures.fig3_latency_scaling` |
| Fig. 4, campaign validation | `figures.IEEEAccessFigures.fig4_campaign_validation` |

## Selected claims in the text

| Claim | Where verified |
|---|---|
| RMSE 1.5 pp over N = 1–5 | `coordination.fit_rmse` |
| β = 0.0659, γ = 0.00298 | `coordination.identify_coefficients` |
| Binding constraint is the workspace | `coordination.bottleneck_analysis().binding` |
| Bandwidth saturates near N ≈ 11 | `coordination.bandwidth_saturation_N` |
| Computation budget exhausted near N ≈ 6 | `coordination.latency_budget_N` |
| Marginal gains +247, +248, +161, +84 | `coordination.marginal_gains` |
| 3.41× at N = 5, 2.61× at N = 3 | ratios of `config.THROUGHPUT_SIM` |
| Conservatism reduction 51.7 % → 31.4 %, monotone | `coordination.conservatism_reduction_pct` |
| 143 % throughput, 27 % labour, 26 % energy, 28 % carbon | `tbl.improvement` |
| 44 % satisfaction, 86 % injuries, 59 % sick days, 68 % turnover | `tbl.improvement` and `tbl.project_all` |
| Availability decomposition 0.8 + 1.2 + 0.7 = 2.7 % | `disruption.availability_decomposition` |
| 547 units/shift, 0.8 % defects, 95.8 % uptime, 32.7 kWh | `campaign.campaign_ensemble` |
| Deviations 1.3 %, 2.7 pp, 4.8 %, +0.2 pp | `verify_paper_numbers.py`, Sec. VI-B block |
| 1 440 operator-hours, zero separation violations | `config.CAMPAIGN_OPERATOR_HOURS`, campaign summary |
