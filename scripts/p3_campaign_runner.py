#!/usr/bin/env python3
"""
P3 -- Replication and extension campaign runner.

Drives the CoppeliaSim 4.10 digital twin over the full experiment matrix
required to convert the eight outstanding threats-to-validity items of the
IEEE Access manuscript into reported results.

WHAT THIS SCRIPT DOES NOT DO
----------------------------
It does not simulate anything itself. It is a driver: it opens the author's
own scenes, sets the seed and the configuration parameters, starts the run,
waits for it to finish, and reads the per-shift telemetry the twin already
writes. Every number produced downstream is an output of the twin.

ADAPTER
-------
Exactly one block below has to be adapted to the local scene naming: the
TwinAdapter class. Everything else is generic. The three methods to fill in
are configure(), run_shifts() and collect(). If the twin is driven through
the CoppeliaSim ZMQ remote API, the stubs show the calls; if it is driven
through a batch entry point, replace the body with a subprocess call.

USAGE
-----
    python3 p3_campaign_runner.py --block replication --out runs/
    python3 p3_campaign_runner.py --block all --out runs/ --dry-run

Output: one tidy CSV per block under --out, plus runs/manifest.json with the
git hash, scene checksums, wall-clock times and the seed list actually used.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path

# --------------------------------------------------------------------------
# Experiment matrix
# --------------------------------------------------------------------------

N_SEEDS = 30                      # replication depth; 30 is the minimum that
                                  # supports a t-interval without normality
                                  # assumptions doing heavy lifting
SEED_BASE = 20260915              # seeds are SEED_BASE + k, k = 0..N_SEEDS-1
SHIFTS_SCALABILITY = 11           # 88 h, as in the submitted campaign
SHIFTS_DISRUPTION = 60            # 480 h, as in the submitted campaign


@dataclass
class Cell:
    """A cell geometry. area_m2 is used by the geometric capacity bound."""
    name: str
    area_m2: float
    shape: str                    # 'rect' | 'L' | 'circular'
    dims: str                     # human-readable, for the manifest


CELLS = [
    Cell("rect12", 12.0, "rect", "4.0 x 3.0 m"),          # submitted baseline
    Cell("rect18", 18.0, "rect", "6.0 x 3.0 m"),
    Cell("rect24", 24.0, "rect", "6.0 x 4.0 m"),
    Cell("L18", 18.0, "L", "L-shaped, 18 m2"),
    Cell("circ18", 18.0, "circular", "r = 2.39 m"),
]


@dataclass
class Task:
    name: str
    spread_m2: float              # area over which targets are distributed
    parts: str


TASKS = [
    Task("auto_assembly", 4.0, "12-18 connectors + 8-12 fasteners"),  # baseline
    Task("concentrated", 1.0, "same parts, single assembly point"),
    Task("distributed", 9.0, "same parts, spread over the surface"),
]


@dataclass
class Network:
    name: str
    bandwidth_mbps: float
    loss: float                   # packet loss probability
    jitter_ms: float


NETWORKS = [
    Network("nominal", 100.0, 0.000, 0.0),        # submitted baseline
    Network("loss01", 100.0, 0.001, 0.0),
    Network("loss1", 100.0, 0.010, 0.0),
    Network("loss5", 100.0, 0.050, 0.0),
    Network("jitter10", 100.0, 0.000, 10.0),
    Network("jitter20", 100.0, 0.000, 20.0),
    Network("bw50", 50.0, 0.000, 0.0),
    Network("bw10", 10.0, 0.000, 0.0),
]

# Ablation switches. 'full' is the configuration reported in the manuscript.
ABLATIONS = [
    "full",
    "no_fatigue",          # fatigue-driven reallocation disabled
    "no_reba",             # REBA term removed from the allocator
    "no_velocity",         # pace-tracking velocity modulation disabled
    "no_assistance",       # adaptive level of assistance disabled
]

# Coordination schemes, for the algorithmic baseline comparison.
COORDINATORS = [
    "admm",                # the scheme reported in the manuscript
    "centralized_milp",
    "hierarchical_zones",
    "market_cbba",
]

# Collision-avoidance policies.
AVOIDANCE = [
    "ssm_fixed",           # the policy that governed both submitted campaigns
    "orca",
    "prioritized",
]


@dataclass
class Run:
    block: str
    seed: int
    n_robots: int
    n_operators: int
    cell: str
    task: str
    network: str
    ablation: str
    coordinator: str
    avoidance: str
    disruption: bool
    shifts: int
    cores: int = 32
    extra: dict = field(default_factory=dict)

    def uid(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()[:16]


def _base(**kw) -> dict:
    d = dict(
        n_operators=1, cell="rect12", task="auto_assembly", network="nominal",
        ablation="full", coordinator="admm", avoidance="ssm_fixed",
        disruption=False, shifts=SHIFTS_SCALABILITY, cores=32,
    )
    d.update(kw)
    return d


def seeds():
    return [SEED_BASE + k for k in range(N_SEEDS)]


def block_replication():
    """Threat 1: single-run results. N = 1..5, 30 seeds, baseline everything."""
    return [Run(block="replication", seed=s, n_robots=n, **_base())
            for n in range(1, 6) for s in seeds()]


def block_range():
    """Threat 2: range of the efficiency series. N = 6, 7 need a larger cell,
    so area is varied deliberately as a second factor rather than confounded:
    N = 1..7 is run in 12, 18 and 24 m2. The 12 m2 runs at N = 6, 7 will be
    infeasible or heavily degraded; that outcome is itself the result."""
    out = []
    for cell in ("rect12", "rect18", "rect24"):
        for n in range(1, 8):
            for s in seeds():
                out.append(Run(block="range", seed=s, n_robots=n,
                               **_base(cell=cell)))
    return out


def block_geometry():
    """Generalization boundary: shape at fixed area, and task spread."""
    out = []
    for cell in ("rect18", "L18", "circ18"):
        for n in (2, 3, 4, 5):
            for s in seeds():
                out.append(Run(block="geometry", seed=s, n_robots=n,
                               **_base(cell=cell)))
    for task in ("concentrated", "distributed"):
        for n in (2, 3, 4, 5):
            for s in seeds():
                out.append(Run(block="geometry", seed=s, n_robots=n,
                               **_base(task=task)))
    return out


def block_operators():
    """Threat: K = 1 only. Sweep K against N in the 18 m2 cell, which has the
    floor area to hold more than one operator without confounding."""
    return [Run(block="operators", seed=s, n_robots=n,
                **_base(cell="rect18", n_operators=k))
            for n in (2, 3, 4) for k in (1, 2, 3) for s in seeds()]


def block_baselines():
    """Threat: no algorithmic baseline. Identical cell, task and seeds across
    coordination schemes and avoidance policies."""
    out = []
    for coord in COORDINATORS:
        for n in (2, 3, 4, 5):
            for s in seeds():
                out.append(Run(block="baselines", seed=s, n_robots=n,
                               **_base(coordinator=coord)))
    for pol in AVOIDANCE:
        for n in (2, 3, 4, 5):
            for s in seeds():
                out.append(Run(block="baselines", seed=s, n_robots=n,
                               **_base(avoidance=pol)))
    return out


def block_network():
    """Threat: communication modeled only by utilization."""
    return [Run(block="network", seed=s, n_robots=n, **_base(network=net.name))
            for net in NETWORKS for n in (2, 3, 5) for s in seeds()]


def block_ablation():
    """Threat: no ablation of the adaptive mechanisms. Run at the preferred
    configuration and at the highest one, so the contribution is characterized
    where contention is light and where it is heavy."""
    return [Run(block="ablation", seed=s, n_robots=n, **_base(ablation=a))
            for a in ABLATIONS for n in (2, 3, 5) for s in seeds()]


def block_disruption():
    """Threat: disruption exercised at one configuration only."""
    return [Run(block="disruption", seed=s, n_robots=n,
                **_base(disruption=True, shifts=SHIFTS_DISRUPTION))
            for n in (1, 2, 3, 4, 5) for s in seeds()]


def block_compute():
    """Bottleneck: vary computational capacity independently of area and
    bandwidth, which the manuscript currently treats analytically."""
    return [Run(block="compute", seed=s, n_robots=n, **_base(cores=c))
            for c in (8, 16, 32, 64) for n in (2, 3, 4, 5)
            for s in seeds()[:10]]   # 10 seeds suffice for a latency mean


BLOCKS = {
    "replication": block_replication,
    "range": block_range,
    "geometry": block_geometry,
    "operators": block_operators,
    "baselines": block_baselines,
    "network": block_network,
    "ablation": block_ablation,
    "disruption": block_disruption,
    "compute": block_compute,
}

# --------------------------------------------------------------------------
# Adapter -- THE ONLY PART THAT NEEDS LOCAL EDITING
# --------------------------------------------------------------------------

METRICS = [
    # economic / operational
    "throughput_units_shift", "defect_rate_pct", "uptime_pct",
    # coordination
    "robot_active_time_pct", "concurrency_prob",
    "planning_latency_ms_mean", "planning_latency_ms_p95",
    "traj_opt_ms", "collision_check_ms", "msg_proc_ms",
    "bandwidth_util_pct", "sync_latency_ms_mean", "sync_latency_ms_p95",
    "sync_latency_ms_max", "sync_excursion_frac",
    "admm_iters_mean", "admm_fallback_frac",
    # contention, needed for the idle-time decomposition
    "idle_spatial_pct", "idle_task_dep_pct", "idle_material_pct",
    "idle_operator_pct", "idle_sync_pct",
    "interference_events_shift", "blocked_motion_s_shift",
    "swept_volume_overlap_m3", "min_separation_m", "separation_violations",
    # environmental
    "energy_kwh_shift", "material_waste_pct",
    # human factors (model outputs)
    "reba_score", "workload_index",
]


class TwinAdapter:
    """Thin wrapper over the CoppeliaSim twin.

    Replace the three method bodies with the local calls. Nothing else in
    this file needs to change.
    """

    def __init__(self, scene_dir: Path, headless: bool = True):
        self.scene_dir = scene_dir
        self.headless = headless
        self.client = None

    def open(self):
        # from coppeliasim_zmqremoteapi_client import RemoteAPIClient
        # self.client = RemoteAPIClient()
        # self.sim = self.client.require('sim')
        raise NotImplementedError(
            "TwinAdapter.open: connect to the running CoppeliaSim instance."
        )

    def configure(self, run: Run) -> None:
        """Load the scene for run.cell, then push the run parameters.

        Expected mapping onto the existing scene signals:
            seed            -> 'p3_seed'
            n_robots        -> 'p3_n_robots'   (enables/disables arm models)
            n_operators     -> 'p3_n_operators'
            task            -> 'p3_task_profile'
            network.*       -> 'p3_net_bw_mbps', 'p3_net_loss', 'p3_net_jitter_ms'
            ablation        -> 'p3_ablation'
            coordinator     -> 'p3_coordinator'
            avoidance       -> 'p3_avoidance'
            disruption      -> 'p3_disruption_enabled'
            cores           -> 'p3_solver_threads'
        """
        raise NotImplementedError

    def run_shifts(self, n_shifts: int) -> None:
        """Start the simulation and block until n_shifts have elapsed."""
        raise NotImplementedError

    def collect(self) -> dict:
        """Return one dict keyed by METRICS, averaged over the steady-state
        shifts of the run (shifts 41-60 for disruption runs, all shifts
        otherwise), exactly as the existing telemetry writer already does."""
        raise NotImplementedError

    def close(self):
        pass


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def git_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unversioned"


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def execute(runs, adapter: TwinAdapter, out_csv: Path, resume: bool = True):
    done = set()
    if resume and out_csv.exists():
        with open(out_csv, newline="") as fh:
            done = {row["uid"] for row in csv.DictReader(fh)}
        print(f"resuming: {len(done)} runs already present")

    fields = ["uid", "wall_s"] + [f.name for f in Run.__dataclass_fields__.values()
                                  if f.name != "extra"] + METRICS
    new = not out_csv.exists()
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        for i, run in enumerate(runs, 1):
            uid = run.uid()
            if uid in done:
                continue
            t0 = time.time()
            adapter.configure(run)
            adapter.run_shifts(run.shifts)
            metrics = adapter.collect()
            row = {"uid": uid, "wall_s": round(time.time() - t0, 1)}
            row.update({k: v for k, v in asdict(run).items() if k != "extra"})
            row.update(metrics)
            w.writerow(row)
            fh.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(runs)} runs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", default="replication",
                    help="block name, comma-separated list, or 'all'. "
                         "Available: " + ", ".join(BLOCKS))
    ap.add_argument("--seeds", type=int, default=None,
                    help="override the number of seeds (default 30)")
    ap.add_argument("--minutes-per-run", type=float, default=None,
                    help="wall-clock minutes per run, for the ETA")
    ap.add_argument("--out", default="runs")
    ap.add_argument("--scenes", default="scenes")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-resume", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    if args.block == "all":
        names = list(BLOCKS)
    else:
        names = [b.strip() for b in args.block.split(",") if b.strip()]
    unknown = [n for n in names if n not in BLOCKS]
    if unknown:
        sys.exit(f"unknown block(s): {unknown}; available: {list(BLOCKS)}")

    if args.seeds is not None:
        global N_SEEDS
        N_SEEDS = args.seeds

    plan = {n: BLOCKS[n]() for n in names}
    total = sum(len(v) for v in plan.values())
    print(f"planned runs: {total}")
    for n, v in plan.items():
        line = f"  {n:12s} {len(v):6d}"
        if args.minutes_per_run:
            h = len(v) * args.minutes_per_run / 60.0
            line += f"   ~{h:7.1f} h  ({h/24:5.1f} d)"
        print(line)
    if args.minutes_per_run:
        h = total * args.minutes_per_run / 60.0
        print(f"  {'TOTAL':12s} {total:6d}   ~{h:7.1f} h  ({h/24:5.1f} d)")

    if args.dry_run:
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "plan.json", "w") as fh:
            json.dump({n: [asdict(r) for r in v] for n, v in plan.items()},
                      fh, indent=1)
        print(f"plan written to {out/'plan.json'}; no simulation run")
        return

    try:
        from p3_twin_adapter import CoppeliaSimAdapter as _Adapter
        print("using CoppeliaSimAdapter from p3_twin_adapter.py")
    except ImportError:
        _Adapter = TwinAdapter
        print("p3_twin_adapter.py not found; falling back to the stub adapter")
    adapter = _Adapter(Path(args.scenes))
    adapter.open()
    manifest = {
        "git": git_hash(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "seed_base": SEED_BASE,
        "n_seeds": N_SEEDS,
        "seeds": seeds(),
        "scenes": {p.name: checksum(p)
                   for p in sorted(Path(args.scenes).glob("*.ttt"))},
        "blocks": {n: len(v) for n, v in plan.items()},
        "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    try:
        for n, v in plan.items():
            print(f"[{n}] {len(v)} runs")
            execute(v, adapter, out / f"{n}.csv", resume=not args.no_resume)
    finally:
        adapter.close()
        manifest["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        with open(out / "manifest.json", "w") as fh:
            json.dump(manifest, fh, indent=1)
        print(f"manifest written to {out/'manifest.json'}")


if __name__ == "__main__":
    main()
