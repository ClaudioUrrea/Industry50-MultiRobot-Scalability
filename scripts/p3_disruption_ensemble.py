#!/usr/bin/env python3
"""
P3 -- Ensemble replication and parameter sensitivity for the extended campaign.

This driver runs against the author's own `industry50` package. It does not
re-implement the disruption model: it calls `campaign.extended_campaign`, which
is a genuinely stochastic, seeded model, once per replication and aggregates the
results. Everything it reports is therefore an output of the published model.

It closes, with real numbers and without any hardware or CoppeliaSim scene:

    R3-19, R4-3   replication, dispersion and confidence intervals for the
                  extended campaign
    R2-5, R3-20   the campaign at configurations other than N = 2
    R1-4, R3-21,  sensitivity of the availability allowance to the fault,
    R3-26         repair, recovery, proficiency and absence parameters

Usage (Windows PowerShell, from the repository root):

    py p3_disruption_ensemble.py --repo . --reps 500 --out tex\
    py p3_disruption_ensemble.py --repo . --reps 500 --blocks ensemble,sensitivity,scaling

`--repo` is the directory that contains `src/industry50/`.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

KEYS = ("throughput_units_per_shift", "defect_rate_pct",
        "uptime_pct", "energy_kwh")


def _flat_package(files: dict, workdir: Path) -> Path:
    """The four modules use relative imports (`from . import config`), so a
    directory of loose .py files cannot be imported directly. Materialise a
    proper package next to them and return the directory to put on sys.path."""
    pkg_root = workdir / "_p3_pkg"
    pkg = pkg_root / "industry50"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("")
    for name, src in files.items():
        (pkg / f"{name}.py").write_text(src.read_text(encoding="utf-8"),
                                        encoding="utf-8")
    return pkg_root


NEEDED = ("config", "campaign", "coordination", "disruption")


def find_package(repo: Path) -> Path:
    """Return a directory to place on sys.path such that `import industry50`
    works. Accepts three layouts:

        repo/src/industry50/        the canonical one
        repo/industry50/            package at the top level
        repo/*.py                   loose modules, assembled on the fly
    """
    repo = repo.resolve()

    for cand in (repo / "src", repo):
        if (cand / "industry50" / "config.py").exists():
            return cand

    for cfg in repo.rglob("industry50/config.py"):
        if cfg.parent.name == "industry50":
            return cfg.parent.parent

    here = {n: repo / f"{n}.py" for n in NEEDED}
    if all(p.exists() for p in here.values()):
        extra = {n: repo / f"{n}.py" for n in ("reba", "tbl")
                 if (repo / f"{n}.py").exists()}
        print(f"loose modules found in {repo}; assembling a temporary package")
        return _flat_package({**here, **extra}, repo)

    for d in repo.rglob("*"):
        if not d.is_dir():
            continue
        cand = {n: d / f"{n}.py" for n in NEEDED}
        if all(p.exists() for p in cand.values()):
            extra = {n: d / f"{n}.py" for n in ("reba", "tbl")
                     if (d / f"{n}.py").exists()}
            print(f"loose modules found in {d}; assembling a temporary package")
            return _flat_package({**cand, **extra}, d)

    raise FileNotFoundError(repo)


def load(repo: Path):
    try:
        root = find_package(Path(repo))
    except FileNotFoundError as exc:
        searched = Path(exc.args[0])
        sys.exit(
            f"Could not locate the industry50 modules under {searched}.\n"
            f"Looked for, in order:\n"
            f"  {searched / 'src' / 'industry50'}\n"
            f"  {searched / 'industry50'}\n"
            f"  any industry50/ directory below it\n"
            f"  a directory holding config.py, campaign.py, coordination.py "
            f"and disruption.py\n\n"
            f"Pass --repo pointing at your repository root, for example:\n"
            f"  py p3_disruption_ensemble.py --repo \"C:\\\\Users\\\\Claudio\\\\P3\"\n"
            f"If you only have the loose .py files, point --repo at the folder "
            f"that contains them."
        )
    sys.path.insert(0, str(root))
    print(f"importing industry50 from {root}")
    from industry50 import campaign, config, disruption
    return campaign, config, disruption


def ci(x, conf=0.95):
    x = np.asarray(x, float)
    n = len(x)
    m = float(x.mean())
    sd = float(x.std(ddof=1)) if n > 1 else 0.0
    half = float(stats.t.ppf(0.5 + conf / 2, n - 1) * sd / np.sqrt(n)) if n > 1 else 0.0
    return dict(n=n, mean=m, sd=sd, lo=m - half, hi=m + half, half=half)


def run_ensemble(campaign, reps, base_seed=42):
    """One independent realisation per spawned seed, as the package's own
    ensemble helper does, but keeping the full per-replication vectors so that
    intervals and not only means can be reported."""
    ss = np.random.SeedSequence(base_seed)
    acc = {k: [] for k in KEYS}
    events = {"n_equipment_events": [], "n_network_events": [],
              "n_absence_events": []}
    for child in ss.spawn(reps):
        seed = int(child.generate_state(1, dtype=np.uint32)[0])
        s = campaign.extended_campaign(seed=seed)["summary"]
        for k in KEYS:
            acc[k].append(float(s[k]))
        for k in events:
            events[k].append(float(s[k]))
    return {k: ci(v) for k, v in acc.items()}, {k: ci(v) for k, v in events.items()}


# --------------------------------------------------------------------------
# sensitivity
# --------------------------------------------------------------------------

FACTORS = {
    "equipment_mtbf_h":     ("EQUIPMENT_FAULT", "mtbf_h"),
    "repair_median_min":    ("EQUIPMENT_FAULT", "repair_median_min"),
    "repair_sigma":         ("EQUIPMENT_FAULT", "repair_sigma"),
    "network_mtbf_h":       ("NETWORK_FAULT", "mtbf_h"),
    "network_recovery_min": ("NETWORK_FAULT", "recovery_mean_min"),
    "absence_rate":         ("OPERATOR_MODEL", "absence_rate_per_operator_shift"),
    "absence_idle_min":     ("OPERATOR_MODEL", "absence_idle_min"),
}

SCALAR_FACTORS = ["BUFFER_RECOVERY_FRACTION"]


def perturb(config, holder, key, factor):
    """Multiply one parameter by `factor`, returning a restore callable."""
    if holder is None:
        old = getattr(config, key)
        setattr(config, key, old * factor)
        return lambda: setattr(config, key, old)
    d = getattr(config, holder)
    old = copy.deepcopy(d)
    d[key] = old[key] * factor
    return lambda: setattr(config, holder, old)


def run_sensitivity(campaign, config, reps, levels=(0.5, 1.5)):
    out = {}
    for name, (holder, key) in FACTORS.items():
        row = {}
        for f in levels:
            restore = perturb(config, holder, key, f)
            try:
                res, _ = run_ensemble(campaign, reps)
                row[f"x{f}"] = {k: res[k]["mean"] for k in KEYS}
            finally:
                restore()
        out[name] = row
    for key in SCALAR_FACTORS:
        row = {}
        for f in levels:
            restore = perturb(config, None, key, f)
            try:
                res, _ = run_ensemble(campaign, reps)
                row[f"x{f}"] = {k: res[k]["mean"] for k in KEYS}
            finally:
                restore()
        out[key] = row
    return out


# --------------------------------------------------------------------------
# configurations other than N = 2
# --------------------------------------------------------------------------

def run_scaling(campaign, config, reps):
    """Run the same disruption model with the nominal throughput of each
    configuration substituted for the N = 2 value.

    The fault, network and absence processes are properties of the cell and the
    workforce, not of the robot count, so they are carried over unchanged; what
    changes is the nominal output on which the downtime acts. This is the
    published model evaluated at another operating point, and the caveat is
    recorded in the output so that it is reported as such.
    """
    out = {}
    base = copy.deepcopy(config.CAMPAIGN_PREDICTED)
    try:
        for n, nominal in sorted(config.THROUGHPUT_SIM.items()):
            cp = copy.deepcopy(base)
            cp["throughput_units_per_shift"] = nominal
            config.CAMPAIGN_PREDICTED = cp
            res, ev = run_ensemble(campaign, reps)
            out[int(n)] = {
                "nominal_units_per_shift": float(nominal),
                **{k: res[k] for k in KEYS},
                "throughput_loss_pct": 100.0 * (1 - res[
                    "throughput_units_per_shift"]["mean"] / nominal),
                "events": ev,
            }
    finally:
        config.CAMPAIGN_PREDICTED = base
    out["_caveat"] = ("Fault, network and absence processes are held at their "
                      "cell-level values; only the nominal throughput varies "
                      "with N.")
    return out


# --------------------------------------------------------------------------
# LaTeX emission
# --------------------------------------------------------------------------

def tex_ensemble(res, reps, path: Path):
    t = res["throughput_units_per_shift"]
    d = res["defect_rate_pct"]
    u = res["uptime_pct"]
    e = res["energy_kwh"]
    lines = [
        r"% Replaces the Disrupted column of the extended-campaign table.",
        r"\begin{tabular}{p{2.6cm}p{2.2cm}p{1.4cm}}",
        r"\toprule",
        r"\textbf{Metric} & \textbf{Disrupted (mean, 95\% CI)} & \textbf{SD} \\",
        r"\midrule",
        f"Throughput (u/shift) & {t['mean']:.1f} [{t['lo']:.1f}, {t['hi']:.1f}] & {t['sd']:.1f} \\\\",
        f"Defect rate (\\%) & {d['mean']:.2f} [{d['lo']:.2f}, {d['hi']:.2f}] & {d['sd']:.2f} \\\\",
        f"Uptime (\\%) & {u['mean']:.1f} [{u['lo']:.1f}, {u['hi']:.1f}] & {u['sd']:.1f} \\\\",
        f"Energy (kWh/shift) & {e['mean']:.1f} [{e['lo']:.1f}, {e['hi']:.1f}] & {e['sd']:.1f} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        f"% {reps} independent realisations of the 60-shift campaign.",
    ]
    path.write_text("\n".join(lines))


def tex_scaling(res, path: Path):
    lines = [r"\begin{tabular}{p{0.7cm}p{1.5cm}p{2.3cm}p{1.9cm}}", r"\toprule",
             r"\textbf{N} & \textbf{Nominal} & \textbf{Disrupted (95\% CI)} & "
             r"\textbf{Uptime (\%)} \\", r"\midrule"]
    for n in sorted(k for k in res if isinstance(k, int)):
        r = res[n]
        t, u = r["throughput_units_per_shift"], r["uptime_pct"]
        lines.append(f"{n} & {r['nominal_units_per_shift']:.0f} & "
                     f"{t['mean']:.1f} [{t['lo']:.1f}, {t['hi']:.1f}] & "
                     f"{u['mean']:.1f} $\\pm$ {u['half']:.1f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    path.write_text("\n".join(lines))


def tex_sensitivity(res, base, path: Path):
    b = base["uptime_pct"]["mean"]
    rows = []
    for name, row in res.items():
        lo = row.get("x0.5", {}).get("uptime_pct", np.nan)
        hi = row.get("x1.5", {}).get("uptime_pct", np.nan)
        rows.append((name, lo - b, hi - b, max(abs(lo - b), abs(hi - b))))
    rows.sort(key=lambda r: -r[3])
    lines = [r"\begin{tabular}{p{3.0cm}p{1.6cm}p{1.6cm}}", r"\toprule",
             r"\textbf{Parameter} & \textbf{$-$50\% (pp)} & "
             r"\textbf{$+$50\% (pp)} \\", r"\midrule"]
    pretty = {"equipment_mtbf_h": "Equipment MTBF",
              "repair_median_min": "Repair time (median)",
              "repair_sigma": "Repair time (shape)",
              "network_mtbf_h": "Network MTBF",
              "network_recovery_min": "Network recovery",
              "absence_rate": "Absence rate",
              "absence_idle_min": "Absence idle interval",
              "BUFFER_RECOVERY_FRACTION": "Inter-station buffering"}
    for name, dlo, dhi, _ in rows:
        lines.append(f"{pretty.get(name, name)} & {dlo:+.2f} & {dhi:+.2f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    path.write_text("\n".join(lines))


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--sens-reps", type=int, default=200)
    ap.add_argument("--out", default="tex")
    ap.add_argument("--blocks", default="ensemble,scaling,sensitivity")
    args = ap.parse_args()

    campaign, config, disruption = load(Path(args.repo))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    blocks = [b.strip() for b in args.blocks.split(",") if b.strip()]
    report = {"replications": args.reps, "blocks": blocks}

    base = None
    if "ensemble" in blocks or "sensitivity" in blocks:
        print(f"[ensemble] {args.reps} realisations ...")
        base, events = run_ensemble(campaign, args.reps)
        report["ensemble"] = base
        report["events"] = events
        tex_ensemble(base, args.reps, out / "tab_disruption_ci.tex")
        for k in KEYS:
            r = base[k]
            print(f"  {k:32s} {r['mean']:8.2f}  95% CI [{r['lo']:.2f}, "
                  f"{r['hi']:.2f}]  SD {r['sd']:.2f}")

    if "scaling" in blocks:
        print(f"[scaling] disruption model at every N ...")
        sc = run_scaling(campaign, config, max(100, args.reps // 4))
        report["scaling"] = sc
        tex_scaling(sc, out / "tab_disruption_by_N.tex")
        for n in sorted(k for k in sc if isinstance(k, int)):
            r = sc[n]
            print(f"  N={n}  nominal {r['nominal_units_per_shift']:6.0f}  "
                  f"disrupted {r['throughput_units_per_shift']['mean']:7.1f}  "
                  f"loss {r['throughput_loss_pct']:.2f}%  "
                  f"uptime {r['uptime_pct']['mean']:.2f}%")

    if "sensitivity" in blocks:
        print(f"[sensitivity] {len(FACTORS)+len(SCALAR_FACTORS)} factors "
              f"at -50% and +50%, {args.sens_reps} realisations each ...")
        sens = run_sensitivity(campaign, config, args.sens_reps)
        report["sensitivity"] = sens
        if base:
            tex_sensitivity(sens, base, out / "tab_sensitivity.tex")
        b = base["uptime_pct"]["mean"] if base else float("nan")
        for name, row in sens.items():
            lo = row["x0.5"]["uptime_pct"] - b
            hi = row["x1.5"]["uptime_pct"] - b
            print(f"  {name:28s} uptime {lo:+.2f} / {hi:+.2f} pp")

    (out / "disruption_report.json").write_text(json.dumps(report, indent=1,
                                                           default=float))
    print(f"\nwrote {out/'disruption_report.json'} and the LaTeX fragments")


if __name__ == "__main__":
    main()
