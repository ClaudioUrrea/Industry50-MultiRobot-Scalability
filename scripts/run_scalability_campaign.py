#!/usr/bin/env python3
"""
Reproduce the N = 1..5 scalability analysis of Section V and write the processed
series to data/processed/.

    python scripts/run_scalability_campaign.py [--out data/processed]

The digital-twin traces from which the throughput series is aggregated are
archived at https://doi.org/10.6084/m9.figshare.33090107
(Scalability_Simulation_N1-N5.zip).  This script operates on the aggregated
series and recomputes every derived quantity reported in the paper.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from industry50 import config as C            # noqa: E402
from industry50 import coordination as coord  # noqa: E402
from industry50 import campaign               # noqa: E402


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    res = campaign.scalability_campaign()

    rows = []
    eta = coord.efficiency_from_throughput(C.THROUGHPUT_SIM_UNROUNDED)
    pred = coord.efficiency_model(list(C.N_RANGE))
    _, resid = coord.fit_residuals()
    for i, n in enumerate(C.N_RANGE):
        rows.append({
            "N": n,
            "throughput_simulated_units_per_shift": C.THROUGHPUT_SIM[n],
            "throughput_ideal_units_per_shift": C.THROUGHPUT_SIM[1] * n,
            "efficiency_simulated_pct": round(100 * eta[n], 1),
            "efficiency_predicted_pct": round(100 * float(pred[i]), 1),
            "fit_residual_pp": round(float(resid[i]), 1),
            "workspace_utilisation_pct": C.WORKSPACE_UTILISATION_PCT[n],
            "bandwidth_utilisation_pct": C.BANDWIDTH_UTILISATION_PCT[n],
            "planning_latency_ms": C.PLANNING_LATENCY_MS[n],
            "dt_sync_mean_ms": C.DT_LATENCY_MEAN_MS[n],
            "dt_sync_p95_ms": C.DT_LATENCY_P95_MS[n],
            "dt_sync_max_ms": C.DT_LATENCY_MAX_MS[n],
            "separation_fixed_m": C.SEPARATION_FIXED_M[n],
            "separation_learned_cbf_m": C.SEPARATION_LEARNED_CBF_M[n],
            "separation_violations": 0,
        })

    csv_path = out_dir / "scaling_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    (out_dir / "scaling_summary.json").write_text(
        json.dumps(res, indent=2, default=str), encoding="utf-8")

    print(f"wrote {csv_path}")
    print(f"wrote {out_dir / 'scaling_summary.json'}")
    print(f"identified beta = {res['beta_identified']}, "
          f"gamma = {res['gamma_identified']}, RMSE = {res['rmse_pp']} pp")
    print(f"binding constraint: {res['bottleneck']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/processed"))
    main(ap.parse_args().out)
