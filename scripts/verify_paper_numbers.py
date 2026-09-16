#!/usr/bin/env python3
"""
Recompute every number reported in the manuscript and check it against the
published value.  Exit code 0 means all checks passed.

    python scripts/verify_paper_numbers.py
    python scripts/verify_paper_numbers.py --replications 500

Each check names the table, figure, equation or section in which the value
appears, so a reader can go from a line of output straight to the place in the
paper it verifies.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from industry50 import config as C            # noqa: E402
from industry50 import coordination as coord  # noqa: E402
from industry50 import disruption as disr     # noqa: E402
from industry50 import tbl                    # noqa: E402
from industry50 import campaign               # noqa: E402

PASS, FAIL = "PASS", "FAIL"
_results: list[tuple[str, str, str, float, float]] = []


def check(where: str, what: str, got, want, tol=0.05, abs_tol=None) -> None:
    got_f, want_f = float(got), float(want)
    ok = (abs(got_f - want_f) <= abs_tol) if abs_tol is not None else (
        abs(got_f - want_f) <= tol * max(abs(want_f), 1e-12))
    _results.append((PASS if ok else FAIL, where, what, got_f, want_f))


def main(replications: int) -> int:
    # --- Equation 1 and Table 3: coordination efficiency -------------------
    eta = coord.efficiency_from_throughput(C.THROUGHPUT_SIM_UNROUNDED)
    for n, want in zip(C.N_RANGE, (100.0, 90.3, 87.1, 78.4, 68.2)):
        check("Table 4", f"eta(N={n}) simulated, %", 100 * eta[n], want,
              abs_tol=0.05)

    beta_hat, gamma_hat = coord.identify_coefficients()
    check("Coord. model", "beta identified by least squares", beta_hat, 0.0659,
          abs_tol=0.0002)
    check("Coord. model", "gamma identified by least squares", gamma_hat, 0.00298,
          abs_tol=0.00002)

    pred = coord.efficiency_model(np.array(C.N_RANGE))
    for n, p, want in zip(C.N_RANGE, pred,
                          (100.0, 93.1, 85.6, 77.5, 68.8)):
        check("Table 4", f"eta(N={n}) predicted, %", 100 * p, want,
              abs_tol=0.05)

    _, resid = coord.fit_residuals()
    for n, r, want in zip(C.N_RANGE, resid, (0.0, -2.8, 1.5, 0.9, -0.6)):
        check("Table 4", f"fit residual N={n}, pp", r, want, abs_tol=0.06)
    check("Fits", "goodness-of-fit RMSE, pp", coord.fit_rmse(), 1.5,
          abs_tol=0.05)

    # --- Section V-B: auxiliary fits that took no part in the above --------
    for n in C.N_RANGE:
        check("Fits", f"bandwidth fit N={n}, %",
              coord.bandwidth_model(n), C.BANDWIDTH_UTILISATION_PCT[n],
              abs_tol=0.4)
        check("Fits", f"latency fit N={n}, ms",
              coord.latency_model(n), C.PLANNING_LATENCY_MS[n], abs_tol=0.5)
    check("Fits", "bandwidth saturation N", coord.bandwidth_saturation_N(),
          11.0, abs_tol=0.5)
    check("Fits", "computation budget exhausted at N",
          coord.latency_budget_N(), 6.0, abs_tol=0.5)

    # --- Section V-C: bottleneck verdict ----------------------------------
    verdict = coord.bottleneck_analysis()
    _results.append((PASS if verdict.binding == "workspace" else FAIL,
                     "Bottleneck", "binding constraint is the workspace",
                     float(verdict.workspace_ceiling[1]),
                     float(verdict.workspace_ceiling[1])))

    # --- Table 5: marginal gains ------------------------------------------
    for n, want in zip((2, 3, 4, 5), (247, 248, 161, 84)):
        check("Table 8", f"marginal gain at N={n}, units",
              coord.marginal_gains()[n], want, abs_tol=0.5)
    check("Scaling", "throughput multiple at N=5",
          C.THROUGHPUT_SIM[5] / C.THROUGHPUT_SIM[1], 3.41, abs_tol=0.01)
    check("Scaling", "throughput multiple at N=3",
          C.THROUGHPUT_SIM[3] / C.THROUGHPUT_SIM[1], 2.61, abs_tol=0.01)

    # --- Table 2: Triple Bottom Line --------------------------------------
    check("Table 2", "throughput gain over manual, % (= 2.43x)",
          tbl.improvement("units_per_shift"), 143, abs_tol=1)  # = factor 2.43
    check("Table 2", "labour intensity reduction, %",
          tbl.improvement("labour_intensity_h_per_100u"), 79, abs_tol=1)
    check("Table 2", "defect improvement, %",
          tbl.improvement("defect_rate_pct"), 81, abs_tol=0.5)
    check("Table 2", "energy reduction, %",
          tbl.improvement("energy_kwh"), 26, abs_tol=0.5)
    check("Table 2", "carbon reduction, %",
          tbl.improvement("carbon_kg"), 26, abs_tol=0.5)
    check("Table 2", "satisfaction increase, %",
          tbl.improvement("satisfaction_5pt"), 44, abs_tol=0.5)
    check("Table 2", "injury reduction, %",
          tbl.improvement("injuries_per_1k_h"), 86, abs_tol=0.5)
    check("Table 2", "sick-day reduction, %",
          tbl.improvement("sick_days_pct"), 59, abs_tol=0.5)
    check("Table 2", "turnover reduction, %",
          tbl.improvement("turnover_pct"), 68, abs_tol=0.5)

    # --- Section VI-C: social projections reproduce the published column ---
    proj = tbl.project_all()
    check("Human factors", "projected satisfaction, /5",
          proj["satisfaction"].value, 4.6, abs_tol=0.05)
    check("Human factors", "projected injury rate, per 1000 h",
          proj["injuries"].value, 0.4, abs_tol=0.05)
    check("Human factors", "projected sick days, %",
          proj["sick_days"].value, 2.0, abs_tol=0.05)
    check("Human factors", "projected turnover, %",
          proj["turnover"].value, 5.9, abs_tol=0.05)

    # --- Section VI-A: disruption model parameters ------------------------
    check("Disruption", "equipment mean repair time, min",
          disr.lognormal_mean(C.EQUIPMENT_FAULT["repair_median_min"],
                              C.EQUIPMENT_FAULT["repair_sigma"]),
          29.0, abs_tol=0.1)
    check("Disruption", "equipment expected events over 480 h",
          disr.expected_events(C.EQUIPMENT_FAULT["mtbf_h"]), 8, abs_tol=0.01)
    check("Disruption", "network expected events over 480 h",
          disr.expected_events(C.NETWORK_FAULT["mtbf_h"]), 5, abs_tol=0.01)
    check("Disruption", "operator absence events over 180 operator-shifts",
          C.OPERATOR_MODEL["absence_rate_per_operator_shift"]
          * C.CAMPAIGN_OPERATOR_SHIFTS, 9, abs_tol=0.01)

    # --- Section VI-B: availability decomposition -------------------------
    dec = disr.availability_decomposition()
    check("Campaign", "equipment unavailability, %",
          100 * dec["equipment"], 0.8, abs_tol=0.02)
    check("Campaign", "network unavailability, %",
          100 * dec["network"], 1.2, abs_tol=0.02)
    check("Campaign", "operator unavailability, %",
          100 * dec["operator"], 0.7, abs_tol=0.02)
    check("Campaign", "total disruption unavailability, %",
          100 * dec["total_unavailability"], 2.7, abs_tol=0.05)

    # --- Table 4: campaign outcome (ensemble mean) ------------------------
    ens = campaign.campaign_ensemble(replications)
    check("Table 9", "campaign throughput, units/shift",
          ens["throughput_units_per_shift_mean"], 547, abs_tol=2)
    check("Table 9", "campaign defect rate, %",
          ens["defect_rate_pct_mean"], 0.8, abs_tol=0.05)
    check("Table 9", "campaign uptime, %",
          ens["uptime_pct_mean"], 95.8, abs_tol=0.3)
    check("Table 9", "campaign energy, kWh/shift",
          ens["energy_kwh_mean"], 32.8, abs_tol=0.3)

    # --- Section VI-B: residuals against the closed form ------------------
    p, s_ = C.CAMPAIGN_PREDICTED, C.CAMPAIGN_PUBLISHED
    check("Campaign", "throughput deviation, %",
          100 * (p["throughput_units_per_shift"]
                 - s_["throughput_units_per_shift"])
          / p["throughput_units_per_shift"], 1.3, abs_tol=0.1)
    check("Campaign", "uptime deviation, pp",
          p["uptime_pct"] - s_["uptime_pct"], 2.7, abs_tol=0.05)
    check("Campaign", "energy deviation, %",
          100 * (s_["energy_kwh"] - p["energy_kwh"]) / p["energy_kwh"],
          5.1, abs_tol=0.1)
    check("Fig. 4", "defect-rate ratio, %",
          100 * s_["defect_rate_pct"] / p["defect_rate_pct"], 133.3,
          abs_tol=0.5)

    # --- Section VI-B: defect and proficiency trajectories ----------------
    check("Campaign", "defect rate at shift 11, %",
          disr.defect_rate_pct(11), 1.2, abs_tol=0.05)
    check("Campaign", "defect rate at shift 60, %",
          disr.defect_rate_pct(60), 0.6, abs_tol=0.05)
    # The manuscript reports the ensemble mean, not a single realisation: one
    # 60-shift campaign puts a whole shift's output at the mercy of whether a
    # downtime event happened to land on that shift, and shift 41 in particular
    # is noisy under seed 42. Averaging over the same spawned seeds used for the
    # campaign table removes that.
    import numpy as _np
    _ss = _np.random.SeedSequence(C.SEED)
    _ramp = {11: [], 26: [], 41: []}
    for _child in _ss.spawn(replications):
        _seed = int(_child.generate_state(1, dtype=_np.uint32)[0])
        _r = campaign.extended_campaign(seed=_seed)["summary"]["ramp_trajectory"]
        for _s in _ramp:
            _ramp[_s].append(_r[_s])
    for s_i, want in ((11, 420), (26, 517), (41, 542)):
        check("Campaign", f"ramp throughput at shift {s_i}, units",
              float(_np.mean(_ramp[s_i])), want, abs_tol=2)

    # --- Campaign accounting ---------------------------------------------
    sc = campaign.scalability_campaign()
    check("Scalability", "scalability campaign hours", sc["hours_simulated"],
          440, abs_tol=0.5)
    check("Scalability", "robot-hours", sc["robot_hours"], 1320, abs_tol=0.5)
    check("Scalability", "operator-hours", sc["operator_hours"], 440, abs_tol=0.5)
    check("Disruption", "campaign operator-hours",
          C.CAMPAIGN_OPERATOR_HOURS, 1440, abs_tol=0.5)

    # --- Figure 1: separation conservatism --------------------------------
    red = coord.conservatism_reduction_pct()
    check("Fig. 1", "conservatism reduction at N=1, %", red[1], 51.7,
          abs_tol=0.1)
    check("Fig. 1", "conservatism reduction at N=5, %", red[5], 31.4,
          abs_tol=0.1)
    monotone = all(red[n] >= red[n + 1] for n in (1, 2, 3, 4))
    _results.append((PASS if monotone else FAIL, "Fig. 1",
                     "conservatism reduction falls monotonically in N", 1, 1))

    # --- Figure 3: synchronisation latency --------------------------------
    slope = ((C.DT_LATENCY_MEAN_MS[5] - C.DT_LATENCY_MEAN_MS[1]) / 4.0)
    check("Fig. 3", "mean latency slope, ms/robot", slope, 4.25, abs_tol=0.01)
    over = [n for n in C.N_RANGE if C.DT_LATENCY_MAX_MS[n] > C.DT_SYNC_BUDGET_MS]
    _results.append((PASS if over == [3, 4, 5] else FAIL, "Fig. 3",
                     "maximum latency exceeds 100 ms from N=3", len(over), 3))

    # --- Report -----------------------------------------------------------
    width = max(len(w) for _, w, _, _, _ in _results)
    print(f"\n{'':4} {'WHERE':<{width}}  QUANTITY")
    print("-" * 100)
    n_fail = 0
    for status, where, what, got, want in _results:
        n_fail += status == FAIL
        print(f"{status:<4} {where:<{width}}  {what:<52} "
              f"got {got:>10.4g}   expected {want:>10.4g}")
    print("-" * 100)
    print(f"{len(_results) - n_fail}/{len(_results)} checks passed "
          f"({replications} campaign replications, seed {C.SEED}).\n")
    return 1 if n_fail else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--replications", type=int, default=200)
    raise SystemExit(main(ap.parse_args().replications))
