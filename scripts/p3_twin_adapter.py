#!/usr/bin/env python3
"""
P3 -- CoppeliaSim adapter.

This is the only file that touches the local installation. p3_campaign_runner
imports CoppeliaSimAdapter from here automatically if the file is present.

It assumes the twin is driven through the ZMQ remote API shipped with
CoppeliaSim 4.6+ (package `coppeliasim-zmqremoteapi-client`), and that the
scene exposes the run parameters as named string/float signals and writes its
per-shift telemetry to a CSV that the adapter reads back.

Two things must match the local scene, and both are collected at the top of
the file so that nothing else needs editing:

    SIGNALS      the signal name used for each run parameter
    TELEMETRY    the column name used for each metric in the scene's CSV

If a signal or a column does not exist yet, add it to the scene's Lua script
rather than changing the analysis pipeline, because the manuscript tables are
generated from the metric names in p3_campaign_runner.METRICS.

Quick check before launching a campaign:

    python3 p3_twin_adapter.py --selftest --scenes scenes/
"""

from __future__ import annotations

import csv
import os
import time
from pathlib import Path

from p3_campaign_runner import METRICS, Run, TwinAdapter

# --------------------------------------------------------------------------
# Local mapping: run parameter -> scene signal name
# --------------------------------------------------------------------------

SIGNALS = {
    "seed":            ("int",    "p3_seed"),
    "n_robots":        ("int",    "p3_n_robots"),
    "n_operators":     ("int",    "p3_n_operators"),
    "task":            ("string", "p3_task_profile"),
    "ablation":        ("string", "p3_ablation"),
    "coordinator":     ("string", "p3_coordinator"),
    "avoidance":       ("string", "p3_avoidance"),
    "disruption":      ("int",    "p3_disruption_enabled"),
    "cores":           ("int",    "p3_solver_threads"),
    # network parameters are expanded from the Network record
    "net_bw_mbps":     ("float",  "p3_net_bw_mbps"),
    "net_loss":        ("float",  "p3_net_loss"),
    "net_jitter_ms":   ("float",  "p3_net_jitter_ms"),
    # the scene writes its telemetry here
    "telemetry_path":  ("string", "p3_telemetry_path"),
    # the scene sets this to 1 when the requested shifts have completed
    "done":            ("int",    "p3_run_complete"),
    "shifts":          ("int",    "p3_target_shifts"),
}

# Local mapping: metric name used in the manuscript -> column in the scene CSV.
# Identity by default; override only the ones that differ.
TELEMETRY = {m: m for m in METRICS}
TELEMETRY.update({
    # e.g. "throughput_units_shift": "units_per_shift",
})

SCENE_FOR_CELL = {
    "rect12": "p3_cell_rect_12m2.ttt",
    "rect18": "p3_cell_rect_18m2.ttt",
    "rect24": "p3_cell_rect_24m2.ttt",
    "L18":    "p3_cell_L_18m2.ttt",
    "circ18": "p3_cell_circ_18m2.ttt",
}

# Shifts counted as steady state. Disruption runs discard the ramp-up, matching
# the manuscript, which reports shifts 41-60. Non-disruption runs use all.
STEADY_STATE = {"disruption": lambda n: list(range(41, n + 1))}

POLL_S = 2.0
TIMEOUT_S = 6 * 3600


class CoppeliaSimAdapter(TwinAdapter):

    def __init__(self, scene_dir: Path, headless: bool = True,
                 telemetry_dir: Path | None = None):
        super().__init__(scene_dir, headless)
        self.telemetry_dir = Path(telemetry_dir or "telemetry")
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        self.sim = None
        self._loaded = None
        self._tel = None
        self._run = None

    # -- lifecycle ---------------------------------------------------------

    def open(self):
        from coppeliasim_zmqremoteapi_client import RemoteAPIClient
        self.client = RemoteAPIClient()
        self.sim = self.client.require("sim")
        self.sim.setStepping(False)
        print("connected to CoppeliaSim:", self.sim.getStringParam(
            self.sim.stringparam_application_path))

    def close(self):
        try:
            if self.sim and self.sim.getSimulationState() != self.sim.simulation_stopped:
                self.sim.stopSimulation()
        except Exception:
            pass

    # -- helpers -----------------------------------------------------------

    def _set(self, key, value):
        kind, name = SIGNALS[key]
        if kind == "int":
            self.sim.setInt32Signal(name, int(value))
        elif kind == "float":
            self.sim.setFloatSignal(name, float(value))
        else:
            self.sim.setStringSignal(name, str(value))

    def _load(self, cell: str):
        scene = self.scene_dir / SCENE_FOR_CELL[cell]
        if not scene.exists():
            raise FileNotFoundError(scene)
        if self._loaded == cell:
            return
        if self.sim.getSimulationState() != self.sim.simulation_stopped:
            self.sim.stopSimulation()
            while self.sim.getSimulationState() != self.sim.simulation_stopped:
                time.sleep(0.1)
        self.sim.loadScene(str(scene.resolve()))
        self._loaded = cell

    @staticmethod
    def _network_params(name: str):
        from p3_campaign_runner import NETWORKS
        for n in NETWORKS:
            if n.name == name:
                return n
        raise KeyError(name)

    # -- the three methods the runner calls --------------------------------

    def configure(self, run: Run) -> None:
        self._run = run
        self._load(run.cell)
        self._tel = self.telemetry_dir / f"{run.uid()}.csv"
        if self._tel.exists():
            self._tel.unlink()

        net = self._network_params(run.network)
        self._set("seed", run.seed)
        self._set("n_robots", run.n_robots)
        self._set("n_operators", run.n_operators)
        self._set("task", run.task)
        self._set("ablation", run.ablation)
        self._set("coordinator", run.coordinator)
        self._set("avoidance", run.avoidance)
        self._set("disruption", 1 if run.disruption else 0)
        self._set("cores", run.cores)
        self._set("net_bw_mbps", net.bandwidth_mbps)
        self._set("net_loss", net.loss)
        self._set("net_jitter_ms", net.jitter_ms)
        self._set("shifts", run.shifts)
        self._set("telemetry_path", str(self._tel.resolve()))
        self._set("done", 0)
        # the solver thread count is also honoured by the host process
        os.environ["OMP_NUM_THREADS"] = str(run.cores)

    def run_shifts(self, n_shifts: int) -> None:
        _, done_sig = SIGNALS["done"]
        self.sim.startSimulation()
        t0 = time.time()
        while True:
            flag = self.sim.getInt32Signal(done_sig)
            if flag == 1:
                break
            if time.time() - t0 > TIMEOUT_S:
                self.sim.stopSimulation()
                raise TimeoutError(f"run {self._run.uid()} exceeded "
                                   f"{TIMEOUT_S/3600:.1f} h")
            time.sleep(POLL_S)
        self.sim.stopSimulation()
        while self.sim.getSimulationState() != self.sim.simulation_stopped:
            time.sleep(0.1)

    def collect(self) -> dict:
        if not self._tel.exists():
            raise FileNotFoundError(f"no telemetry written at {self._tel}")
        with open(self._tel, newline="") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            raise ValueError(f"empty telemetry at {self._tel}")

        keep = rows
        if self._run.disruption:
            wanted = set(STEADY_STATE["disruption"](self._run.shifts))
            keep = [r for r in rows if int(float(r.get("shift", 0))) in wanted] or rows

        out = {}
        for metric in METRICS:
            col = TELEMETRY.get(metric, metric)
            vals = []
            for r in keep:
                v = r.get(col)
                if v in (None, ""):
                    continue
                try:
                    vals.append(float(v))
                except ValueError:
                    pass
            if not vals:
                out[metric] = ""
                continue
            # counts accumulate over the run; everything else is averaged
            if metric in ("separation_violations", "interference_events_shift"):
                out[metric] = sum(vals) if metric == "separation_violations" \
                    else sum(vals) / len(vals)
            elif metric == "min_separation_m":
                out[metric] = min(vals)
            elif metric == "sync_latency_ms_max":
                out[metric] = max(vals)
            else:
                out[metric] = sum(vals) / len(vals)
        return out


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

def selftest(scene_dir: Path):
    missing = [c for c, f in SCENE_FOR_CELL.items()
               if not (scene_dir / f).exists()]
    print(f"scenes present : {len(SCENE_FOR_CELL)-len(missing)}/{len(SCENE_FOR_CELL)}")
    if missing:
        print(f"  MISSING      : {missing}")
    a = CoppeliaSimAdapter(scene_dir)
    a.open()
    try:
        for key, (kind, name) in SIGNALS.items():
            a._set(key, 0 if kind in ("int", "float") else "probe")
        print("all signals writable")
    finally:
        a.close()
    print("self-test complete. Run one short block next, for example:\n"
          "  python3 p3_campaign_runner.py --block replication --seeds 2 --out runs_smoke/")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--scenes", default="scenes")
    args = ap.parse_args()
    if args.selftest:
        selftest(Path(args.scenes))
    else:
        ap.print_help()
