#!/usr/bin/env python3
"""
Emit Tables 2-5 of the manuscript as CSV, with a provenance column on every
human-factors row.

    python scripts/make_tables.py --out data/processed
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from industry50 import config as C            # noqa: E402
from industry50 import coordination as coord  # noqa: E402
from industry50 import tbl                    # noqa: E402


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Table 2 -- Triple Bottom Line, with provenance
    rows = []
    for cfg in ("manual", "i50_hrc", "automated"):
        rows.extend(tbl.build(cfg).as_rows())
    with (out_dir / "table2_triple_bottom_line.csv").open(
            "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["configuration", "pillar", "indicator", "value", "unit",
                    "provenance"])
        w.writerows(rows)

    # Table 5 -- configuration selection
    with (out_dir / "table5_configuration_selection.csv").open(
            "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["N", "throughput_units_per_shift", "efficiency_pct",
                    "marginal_gain_units", "workspace_utilisation_pct",
                    "computation_ms", "complexity"])
        eta = coord.efficiency_from_throughput(C.THROUGHPUT_SIM_UNROUNDED)
        gains = coord.marginal_gains()
        complexity = {1: "Low", 2: "Low", 3: "Medium", 4: "High", 5: "High"}
        for n in C.N_RANGE:
            w.writerow([n, C.THROUGHPUT_SIM[n], round(100 * eta[n], 1),
                        gains.get(n, ""), C.WORKSPACE_UTILISATION_PCT[n],
                        C.PLANNING_LATENCY_MS[n], complexity[n]])

    print(f"wrote {out_dir / 'table2_triple_bottom_line.csv'}")
    print(f"wrote {out_dir / 'table5_configuration_selection.csv'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/processed"))
    main(ap.parse_args().out)
