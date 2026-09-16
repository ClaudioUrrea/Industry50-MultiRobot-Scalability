#!/usr/bin/env python3
"""
Run the 60-shift extended campaign under stochastic disruption (Section VI).

    python scripts/run_extended_campaign.py
    python scripts/run_extended_campaign.py --replications 500 --seed 42

A single 60-shift campaign carries appreciable sampling variance -- five network
interruptions are expected over the whole campaign -- so the ensemble mean over
independent replications is what should be compared with Table 4.  Both are
written out.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from industry50 import config as C   # noqa: E402
from industry50 import campaign      # noqa: E402


def main(seed: int, replications: int, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    run = campaign.extended_campaign(seed=seed)
    ens = campaign.campaign_ensemble(replications, seed=seed)

    csv_path = out_dir / "campaign_shifts.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(run["records"][0]))
        w.writeheader()
        w.writerows(run["records"])

    payload = {"single_realisation": run["summary"], "ensemble": ens,
               "published_table4": C.CAMPAIGN_PUBLISHED,
               "closed_form_prediction": C.CAMPAIGN_PREDICTED}
    (out_dir / "campaign_summary.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8")

    s = run["summary"]
    print(f"wrote {csv_path}")
    print(f"wrote {out_dir / 'campaign_summary.json'}")
    print(f"\nsingle realisation (seed {seed}): "
          f"{s['throughput_units_per_shift']} units/shift, "
          f"{s['defect_rate_pct']} % defects, {s['uptime_pct']} % uptime, "
          f"{s['energy_kwh']} kWh/shift")
    print(f"ensemble of {replications}: "
          f"{ens['throughput_units_per_shift_mean']:.1f} units/shift "
          f"(sd {ens['throughput_units_per_shift_sd']:.1f}), "
          f"{ens['uptime_pct_mean']:.1f} % uptime "
          f"(sd {ens['uptime_pct_sd']:.1f})")
    print(f"published Table 4: 547 units/shift, 0.8 % defects, "
          f"95.8 % uptime, 32.7 kWh/shift")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=C.SEED)
    ap.add_argument("--replications", type=int, default=200)
    ap.add_argument("--out", type=Path, default=Path("data/processed"))
    a = ap.parse_args()
    main(a.seed, a.replications, a.out)
