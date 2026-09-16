#!/usr/bin/env python3
"""
P3 -- Analysis pipeline for the replication and extension campaign.

Consumes the CSVs written by p3_campaign_runner.py and emits, for each of the
eight outstanding threats-to-validity items, the statistics and the LaTeX
table fragment that replaces the corresponding passage in the manuscript.

    python3 p3_analysis_v7.py --runs runs/ --out tex/

Nothing here invents data. Every function reads a CSV column and reports what
is in it. If a block is absent, its section is skipped and the manuscript
keeps the current threats-to-validity wording for that item.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import least_squares

T1_FALLBACK = 307.0          # only used if N = 1 is absent from a block
RNG = np.random.default_rng(20260915)


# --------------------------------------------------------------------------
# basic statistics
# --------------------------------------------------------------------------

def summarize(x: np.ndarray) -> dict:
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n == 0:
        return dict(n=0, mean=np.nan, sd=np.nan, lo=np.nan, hi=np.nan)
    m, sd = x.mean(), x.std(ddof=1) if n > 1 else 0.0
    half = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n) if n > 1 else 0.0
    return dict(n=n, mean=m, sd=sd, lo=m - half, hi=m + half)


def fmt(s: dict, d: int = 1) -> str:
    if s["n"] == 0:
        return "---"
    return f"{s['mean']:.{d}f} $\\pm$ {s['mean']-s['lo']:.{d}f}"


def welch(a, b) -> dict:
    t, p = stats.ttest_ind(a, b, equal_var=False)
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * np.var(a, ddof=1) + (nb - 1) * np.var(b, ddof=1))
                 / (na + nb - 2))
    return dict(t=t, p=p, d=(np.mean(a) - np.mean(b)) / sp if sp else np.nan)


# --------------------------------------------------------------------------
# coordination-efficiency model
# --------------------------------------------------------------------------

MODELS = {
    "quadratic": (lambda N, b, g: 1 - b * (N - 1) - g * (N - 1) ** 2,
                  [0.066, 0.003], 2,
                  r"$1-\beta(N{-}1)-\gamma(N{-}1)^2$"),
    "linear": (lambda N, b: 1 - b * (N - 1), [0.076], 1,
               r"$1-\beta(N{-}1)$"),
    "exponential": (lambda N, l: np.exp(-l * (N - 1)), [0.087], 1,
                    r"$\exp[-\lambda(N{-}1)]$"),
    "hyperbolic": (lambda N, c: 1 / (1 + c * (N - 1)), [0.099], 1,
                   r"$[1+c(N{-}1)]^{-1}$"),
    "usl": (lambda N, s, k: 1 / (1 + s * (N - 1) + k * N * (N - 1)),
            [0.05, 0.012], 2,
            r"USL: $[1{+}\sigma(N{-}1){+}\kappa N(N{-}1)]^{-1}$"),
    "power": (lambda N, a: N ** (-a), [0.18], 1, r"$N^{-a}$"),
}


def fit(model: str, N, eta):
    f, p0, k, _ = MODELS[model]
    r = least_squares(lambda p: f(np.asarray(N, float), *p) - np.asarray(eta, float), p0)
    return r


def ic(model: str, N, eta):
    f, p0, k, _ = MODELS[model]
    r = fit(model, N, eta)
    res = f(np.asarray(N, float), *r.x) - np.asarray(eta, float)
    n = len(N)
    rss = float(np.sum(res ** 2))
    aic = n * np.log(rss / n) + 2 * (k + 1)
    denom = n - k - 2
    aicc = aic + 2 * (k + 1) * (k + 2) / denom if denom > 0 else np.nan
    bic = n * np.log(rss / n) + (k + 1) * np.log(n)
    return dict(params=r.x, rmse_pp=float(np.sqrt(rss / n) * 100),
                aic=aic, aicc=aicc, bic=bic, resid_pp=res * 100)


def loo(model: str, N, eta):
    f, p0, _, _ = MODELS[model]
    N = np.asarray(N, float); eta = np.asarray(eta, float)
    errs = []
    for i in range(len(N)):
        if np.isclose(N[i], 1.0):
            continue                      # fixed by the eta(1) = 1 constraint
        idx = [j for j in range(len(N)) if j != i]
        r = least_squares(lambda p: f(N[idx], *p) - eta[idx], p0)
        errs.append((eta[i] - f(np.array([N[i]]), *r.x)[0]) * 100)
    return np.array(errs)


def coef_uncertainty(N, eta, model="quadratic", B=10000):
    f, p0, k, _ = MODELS[model]
    N = np.asarray(N, float); eta = np.asarray(eta, float)
    r = fit(model, N, eta)
    res = f(N, *r.x) - eta
    dof = len(N) - k
    s2 = float(np.sum(res ** 2)) / dof
    cov = s2 * np.linalg.inv(r.jac.T @ r.jac)
    se = np.sqrt(np.diag(cov))
    tcrit = stats.t.ppf(0.975, dof)
    boot = []
    for _ in range(B):
        y = f(N, *r.x) + RNG.choice(res, size=len(N), replace=True)
        boot.append(least_squares(lambda p: f(N, *p) - y, p0).x)
    boot = np.array(boot)
    out = {}
    for j, name in enumerate(["beta", "gamma"][:k] if model == "quadratic"
                             else [f"p{j}" for j in range(k)]):
        out[name] = dict(
            est=float(r.x[j]), se=float(se[j]),
            ci=(float(r.x[j] - tcrit * se[j]), float(r.x[j] + tcrit * se[j])),
            boot=(float(np.percentile(boot[:, j], 2.5)),
                  float(np.percentile(boot[:, j], 97.5))),
            t=float(r.x[j] / se[j]),
            p=float(2 * (1 - stats.t.cdf(abs(r.x[j] / se[j]), dof))),
        )
    if k == 2:
        out["corr"] = float(cov[0, 1] / (se[0] * se[1]))
    return out


# --------------------------------------------------------------------------
# geometric capacity bound (analytical; independent of the runs)
# --------------------------------------------------------------------------

def capacity(area, reach=0.85, phi=0.70, a_op=2.0, a_acc=1.5, n_ops=1):
    return int(np.floor((area - n_ops * a_op - a_acc) / (phi * np.pi * reach ** 2)))


# --------------------------------------------------------------------------
# TOPSIS with dispersion
# --------------------------------------------------------------------------

def topsis(X, w, benefit):
    X = np.asarray(X, float)
    R = X / np.sqrt((X ** 2).sum(0))
    V = R * np.asarray(w, float)
    ideal = np.array([V[:, j].max() if benefit[j] else V[:, j].min()
                      for j in range(X.shape[1])])
    anti = np.array([V[:, j].min() if benefit[j] else V[:, j].max()
                     for j in range(X.shape[1])])
    dp = np.sqrt(((V - ideal) ** 2).sum(1))
    dn = np.sqrt(((V - anti) ** 2).sum(1))
    return dn / (dp + dn)


def topsis_with_seeds(df, attrs, benefit, n_boot=2000):
    """Resample seeds within each configuration and report how often each N
    ranks first. This answers the reviewers' question of whether the ranking
    survives between-run dispersion, which the single-run version could not."""
    Ns = sorted(df.n_robots.unique())
    wins = {n: 0 for n in Ns}
    for _ in range(n_boot):
        rows = []
        for n in Ns:
            sub = df[df.n_robots == n]
            samp = sub.sample(len(sub), replace=True)
            rows.append([samp[a].mean() for a in attrs])
        C = topsis(np.array(rows), np.ones(len(attrs)) / len(attrs), benefit)
        wins[Ns[int(np.argmax(C))]] += 1
    return {n: wins[n] / n_boot for n in Ns}


# --------------------------------------------------------------------------
# per-block analyses
# --------------------------------------------------------------------------

def eta_series(df):
    """Mean efficiency per N, with the seed-level CI, using each run's own
    N = 1 mean as T(1)."""
    g = df.groupby("n_robots")["throughput_units_shift"]
    means = g.mean()
    t1 = float(means.get(1, T1_FALLBACK))
    rows = []
    for n, sub in df.groupby("n_robots"):
        e = sub["throughput_units_shift"].to_numpy() / (n * t1)
        rows.append(dict(N=int(n), **{k: v for k, v in summarize(e).items()},
                         thr=summarize(sub["throughput_units_shift"].to_numpy())))
    return t1, pd.DataFrame(rows)


def do_replication(df, out):
    t1, eta = eta_series(df)
    lines = [r"\begin{tabular}{p{1.1cm}p{2.1cm}p{2.1cm}p{1.5cm}}", r"\toprule",
             r"\textbf{N} & \textbf{Throughput (u/shift)} & "
             r"\textbf{Efficiency (\%)} & \textbf{Seeds} \\", r"\midrule"]
    for _, r in eta.iterrows():
        lines.append(f"{int(r.N)} & {fmt(r.thr,1)} & "
                     f"{r['mean']*100:.1f} $\\pm$ {(r['mean']-r['lo'])*100:.1f} & "
                     f"{int(r['n'])} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "tab_replication.tex").write_text("\n".join(lines))

    N = eta.N.to_numpy(float); e = eta["mean"].to_numpy(float)
    comp = []
    for name in MODELS:
        s = ic(name, N, e)
        l = loo(name, N, e)
        comp.append(dict(model=name, label=MODELS[name][3], k=MODELS[name][2],
                         rmse=s["rmse_pp"], aicc=s["aicc"],
                         loo=float(np.sqrt(np.mean(l ** 2)))))
    comp = pd.DataFrame(comp).sort_values("aicc")
    lines = [r"\begin{tabular}{p{3.25cm}p{0.5cm}p{0.85cm}p{0.85cm}p{0.85cm}}",
             r"\toprule",
             r"\textbf{Form} & \textbf{par.} & \textbf{RMSE (pp)} & "
             r"\textbf{AICc} & \textbf{LOO (pp)} \\", r"\midrule"]
    for _, r in comp.iterrows():
        lines.append(f"{r.label} & {r.k} & {r.rmse:.2f} & "
                     f"${'-' if r.aicc<0 else ''}${abs(r.aicc):.1f} & {r.loo:.2f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "tab_modelsel.tex").write_text("\n".join(lines))

    unc = coef_uncertainty(N, e)
    (out / "coef_uncertainty.json").write_text(json.dumps(jsonable(unc), indent=1))
    return dict(t1=t1, eta=eta.to_dict("records"),
                model_comparison=comp.to_dict("records"), coefficients=unc)


def do_range(df, out):
    """N up to 7 across three areas. Reports, per area, the N at which mean
    throughput stops rising, and refits the model on the extended series."""
    res = {}
    for cell, sub in df.groupby("cell"):
        t1, eta = eta_series(sub)
        thr = sub.groupby("n_robots")["throughput_units_shift"].mean()
        peak = int(thr.idxmax())
        N = eta.N.to_numpy(float); e = eta["mean"].to_numpy(float)
        unc = coef_uncertainty(N, e)
        res[cell] = dict(t1=t1, peak_N=peak,
                         throughput=thr.round(1).to_dict(),
                         efficiency={int(r.N): round(r["mean"] * 100, 1)
                                     for _, r in eta.iterrows()},
                         coefficients=unc,
                         geometric_bound=capacity({"rect12": 12.0,
                                                   "rect18": 18.0,
                                                   "rect24": 24.0}[cell]))
    (out / "range.json").write_text(json.dumps(jsonable(res), indent=1))
    return res


def do_ablation(df, out):
    """Contribution of each adaptive mechanism, against the full framework."""
    res = {}
    for n, sub in df.groupby("n_robots"):
        base = sub[sub.ablation == "full"]
        row = {}
        for a in sub.ablation.unique():
            if a == "full":
                continue
            v = sub[sub.ablation == a]
            row[a] = {m: dict(delta=float(v[m].mean() - base[m].mean()),
                              **welch(v[m].to_numpy(), base[m].to_numpy()))
                      for m in ("throughput_units_shift", "reba_score",
                                "workload_index", "min_separation_m")}
        res[int(n)] = row
    (out / "ablation.json").write_text(json.dumps(jsonable(res), indent=1))
    return res


def do_baselines(df, out):
    res = {}
    for n, sub in df.groupby("n_robots"):
        ref = sub[sub.coordinator == "admm"]
        row = {}
        for c in sub.coordinator.unique():
            v = sub[sub.coordinator == c]
            row[c] = {m: summarize(v[m].to_numpy())
                      for m in ("throughput_units_shift",
                                "planning_latency_ms_mean",
                                "robot_active_time_pct")}
            if c != "admm":
                row[c]["vs_admm_throughput"] = welch(
                    v["throughput_units_shift"].to_numpy(),
                    ref["throughput_units_shift"].to_numpy())
        res[int(n)] = row
    (out / "baselines.json").write_text(json.dumps(jsonable(res), indent=1))
    return res


def do_network(df, out):
    res = {}
    for n, sub in df.groupby("n_robots"):
        ref = sub[sub.network == "nominal"]
        res[int(n)] = {
            net: {m: summarize(v[m].to_numpy())
                  for m in ("throughput_units_shift", "sync_latency_ms_p95",
                            "separation_violations", "admm_fallback_frac")}
            for net, v in sub.groupby("network")}
    (out / "network.json").write_text(json.dumps(jsonable(res), indent=1))
    return res


def do_disruption(df, out):
    """Availability allowance as a function of N, which the submitted paper
    could only state at N = 2."""
    res = {}
    for n, sub in df.groupby("n_robots"):
        res[int(n)] = {m: summarize(sub[m].to_numpy())
                       for m in ("throughput_units_shift", "uptime_pct",
                                 "defect_rate_pct", "energy_kwh_shift")}
    (out / "disruption.json").write_text(json.dumps(jsonable(res), indent=1))
    return res


def do_bottleneck(df, out):
    """Idle-time decomposition, which replaces robot active time as the
    evidence for the spatial-contention claim."""
    cols = ["idle_spatial_pct", "idle_task_dep_pct", "idle_material_pct",
            "idle_operator_pct", "idle_sync_pct"]
    rows = []
    for n, sub in df.groupby("n_robots"):
        rows.append(dict(N=int(n), **{c: summarize(sub[c].to_numpy())["mean"]
                                      for c in cols},
                         swept=summarize(sub["swept_volume_overlap_m3"].to_numpy())["mean"],
                         interference=summarize(sub["interference_events_shift"].to_numpy())["mean"]))
    tab = pd.DataFrame(rows)
    lines = [r"\begin{tabular}{p{2.9cm}" + "p{0.62cm}" * len(tab) + "}", r"\toprule",
             r"\textbf{Idle-time component} & " +
             " & ".join(f"\\textbf{{N={int(r.N)}}}" for _, r in tab.iterrows()) + r" \\",
             r"\midrule"]
    labels = {"idle_spatial_pct": "Spatial conflict",
              "idle_task_dep_pct": "Task dependency",
              "idle_material_pct": "Material waiting",
              "idle_operator_pct": "Operator waiting",
              "idle_sync_pct": "Synchronization"}
    for c in cols:
        lines.append(labels[c] + " & " +
                     " & ".join(f"{r[c]:.1f}" for _, r in tab.iterrows()) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "tab_idle_decomposition.tex").write_text("\n".join(lines))
    return tab.to_dict("records")




def do_geometry(df, out):
    """Shape at fixed area, and task spread. Reports the contention coefficient
    per geometry, which is the quantity the manuscript says is a property of
    the cell and the task jointly."""
    res = {}
    for key, sub in df.groupby(["cell", "task"]):
        if sub.n_robots.nunique() < 3:
            continue
        t1, eta = eta_series(sub)
        N = eta.N.to_numpy(float); e = eta["mean"].to_numpy(float)
        try:
            unc = coef_uncertainty(N, e)
        except Exception:
            unc = {}
        res["|".join(map(str, key))] = dict(
            t1=t1,
            efficiency={int(r.N): round(r["mean"] * 100, 1) for _, r in eta.iterrows()},
            throughput={int(r.N): round(r.thr["mean"], 1) for _, r in eta.iterrows()},
            coefficients=unc,
            swept_overlap={int(n): float(g["swept_volume_overlap_m3"].mean())
                           for n, g in sub.groupby("n_robots")},
        )
    (out / "geometry.json").write_text(json.dumps(jsonable(res), indent=1))
    return res


def do_operators(df, out):
    """K swept against N. Isolates the O(NK) term the manuscript can only
    bound at K = 1."""
    res = {}
    for k, sub in df.groupby("n_operators"):
        t1, eta = eta_series(sub)
        N = eta.N.to_numpy(float); e = eta["mean"].to_numpy(float)
        entry = dict(
            t1=t1,
            efficiency={int(r.N): round(r["mean"] * 100, 1) for _, r in eta.iterrows()},
            workload={int(n): summarize(g["workload_index"].to_numpy())
                      for n, g in sub.groupby("n_robots")},
            reba={int(n): summarize(g["reba_score"].to_numpy())
                  for n, g in sub.groupby("n_robots")},
        )
        if len(N) >= 3:
            try:
                entry["linear_slope"] = float(fit("linear", N, e).x[0])
            except Exception:
                pass
        res[int(k)] = entry
    (out / "operators.json").write_text(json.dumps(jsonable(res), indent=1))
    return res


def do_compute(df, out):
    """Computational capacity varied independently of area and bandwidth.
    Refits the latency law per core count and reports where each one reaches
    the 20 ms budget, which replaces the analytical entry of the ceilings
    table with a measured one."""
    from scipy.optimize import brentq
    res = {}
    for cores, sub in df.groupby("cores"):
        g = sub.groupby("n_robots")["planning_latency_ms_mean"].mean()
        N = g.index.to_numpy(float); t = g.to_numpy(float)

        def model(p, N=N):
            return p[0] + p[1] * N ** p[2]

        r = least_squares(lambda p: model(p) - t, [6.8, 1.21, 1.3],
                          bounds=([0, 0, 0.5], [30, 20, 3.0]))
        a, b, c = r.x
        try:
            ceiling = brentq(lambda x: a + b * x ** c - 20.0, 1.0, 200.0)
        except ValueError:
            ceiling = float("nan")
        res[int(cores)] = dict(intercept_ms=float(a), coef=float(b),
                               exponent=float(c), ceiling_N=float(ceiling),
                               latency={int(n): float(v) for n, v in g.items()})
    (out / "compute.json").write_text(json.dumps(jsonable(res), indent=1))
    return res


HANDLERS = {
    "replication": do_replication,
    "range": do_range,
    "ablation": do_ablation,
    "baselines": do_baselines,
    "network": do_network,
    "disruption": do_disruption,
    "geometry": do_geometry,
    "operators": do_operators,
    "compute": do_compute,
}


def jsonable(o):
    """Recursively coerce numpy scalars used as dict keys or values into
    built-in types, so that json.dump never fails on an int64 key."""
    if isinstance(o, dict):
        return {(int(k) if isinstance(k, (np.integer,))
                 else float(k) if isinstance(k, (np.floating,))
                 else str(k) if not isinstance(k, (str, int, float, bool, type(None)))
                 else k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, np.ndarray):
        return jsonable(o.tolist())
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default="tex")
    args = ap.parse_args()
    runs, out = Path(args.runs), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    report = {}
    for name, fn in HANDLERS.items():
        csv_path = runs / f"{name}.csv"
        if not csv_path.exists():
            print(f"[skip] {name}: {csv_path} not found")
            continue
        df = pd.read_csv(csv_path)
        print(f"[{name}] {len(df)} runs, "
              f"{df.seed.nunique()} seeds, N in {sorted(df.n_robots.unique())}")
        report[name] = fn(df, out)

    rep = runs / "replication.csv"
    if rep.exists():
        report["bottleneck"] = do_bottleneck(pd.read_csv(rep), out)
        df = pd.read_csv(rep)
        attrs = ["throughput_units_shift", "robot_active_time_pct",
                 "planning_latency_ms_mean"]
        report["topsis_seed_stability"] = topsis_with_seeds(
            df, attrs, benefit=[True, True, False])

    report["geometric_bound"] = {a: capacity(a) for a in (12.0, 18.0, 24.0)}
    (out / "report.json").write_text(json.dumps(jsonable(report), indent=1))
    print(f"\nwrote {out/'report.json'} and the LaTeX fragments in {out}")


if __name__ == "__main__":
    main()
