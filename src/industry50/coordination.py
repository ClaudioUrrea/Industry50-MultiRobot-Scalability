"""
Coordination-efficiency model and bottleneck analysis (Section V).

    eta(N) = eta0 * (1 - beta (N-1) - gamma (N-1)^2)          [Eq. 3]

The two coefficients are identified by least squares from the same
five-configuration digital-twin series against which the expression is then
compared.  The residual reported in the paper (RMSE = 1.5 percentage points) is
therefore a goodness-of-fit statistic and NOT an out-of-sample prediction error.
The functions below make that distinction explicit in their names.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import config as C


# ---------------------------------------------------------------------------
# Efficiency model
# ---------------------------------------------------------------------------
def efficiency_model(N, eta0: float = C.ETA0,
                     beta: float = C.BETA, gamma: float = C.GAMMA):
    """Equation 3.  Valid for interpolation over N = 1..5 only."""
    N = np.asarray(N, dtype=float)
    return eta0 * (1.0 - beta * (N - 1.0) - gamma * (N - 1.0) ** 2)


def efficiency_from_throughput(throughput: dict[int, float]) -> dict[int, float]:
    """Equation 1: eta(N) = T(N) / (N * T(1))."""
    t1 = float(throughput[1])
    return {n: float(t) / (n * t1) for n, t in throughput.items()}


def identify_coefficients(throughput: dict[int, float] | None = None,
                          eta0: float = C.ETA0) -> tuple[float, float]:
    """Least-squares identification of (beta, gamma) with eta0 held fixed."""
    thr = throughput or C.THROUGHPUT_SIM_UNROUNDED
    eta = efficiency_from_throughput(thr)
    N = np.array(sorted(eta), dtype=float)
    y = np.array([eta[int(n)] for n in N]) - eta0
    X = np.column_stack([-eta0 * (N - 1.0), -eta0 * (N - 1.0) ** 2])
    (beta, gamma), *_ = np.linalg.lstsq(X, y, rcond=None)
    return float(beta), float(gamma)


def fit_residuals(beta: float = C.BETA, gamma: float = C.GAMMA):
    """Simulated minus predicted efficiency, in percentage points."""
    eta_sim = efficiency_from_throughput(C.THROUGHPUT_SIM_UNROUNDED)
    N = np.array(sorted(eta_sim), dtype=float)
    sim = np.array([eta_sim[int(n)] for n in N])
    pred = efficiency_model(N, C.ETA0, beta, gamma)
    return N.astype(int), (sim - pred) * 100.0


def fit_rmse(beta: float = C.BETA, gamma: float = C.GAMMA) -> float:
    """Goodness-of-fit RMSE in percentage points (NOT a prediction error)."""
    _, resid = fit_residuals(beta, gamma)
    return float(np.sqrt(np.mean(resid ** 2)))


# ---------------------------------------------------------------------------
# Bottleneck analysis (Section V-B and V-C)
# ---------------------------------------------------------------------------
def bandwidth_model(N, b0: float | None = None, kappa: float | None = None):
    """b(N) = b0 + kappa N^2, in per cent of the 100 Mbps link."""
    b0 = C.BANDWIDTH_FIT["b0_pct"] if b0 is None else b0
    kappa = C.BANDWIDTH_FIT["kappa_pct"] if kappa is None else kappa
    return b0 + kappa * np.asarray(N, dtype=float) ** 2


def latency_model(N, t0: float | None = None, c: float | None = None,
                  p: float | None = None):
    """t(N) = t0 + c N^p, per-cycle planning latency in ms."""
    t0 = C.LATENCY_FIT["t0_ms"] if t0 is None else t0
    c = C.LATENCY_FIT["c_ms"] if c is None else c
    p = C.LATENCY_FIT["exponent"] if p is None else p
    return t0 + c * np.asarray(N, dtype=float) ** p


def bandwidth_saturation_N(capacity_pct: float = 100.0) -> float:
    b0, k = C.BANDWIDTH_FIT["b0_pct"], C.BANDWIDTH_FIT["kappa_pct"]
    return float(np.sqrt((capacity_pct - b0) / k))


def latency_budget_N(budget_ms: float = C.CONTROL_BUDGET_MS) -> float:
    t0, c, p = (C.LATENCY_FIT["t0_ms"], C.LATENCY_FIT["c_ms"],
                C.LATENCY_FIT["exponent"])
    return float(((budget_ms - t0) / c) ** (1.0 / p))


def workspace_ceiling_N(area_m2: float = C.CELL_AREA_M2) -> tuple[int, int]:
    """Robots a cell can hold, from the effective floor claim per arm."""
    lo, hi = C.ROBOT_FOOTPRINT_M2
    return int(area_m2 // hi), int(area_m2 // lo)


@dataclass(frozen=True)
class BottleneckVerdict:
    workspace_ceiling: tuple[int, int]
    bandwidth_ceiling: float
    computation_ceiling: float

    @property
    def binding(self) -> str:
        return min(
            (("workspace", float(self.workspace_ceiling[1])),
             ("bandwidth", self.bandwidth_ceiling),
             ("computation", self.computation_ceiling)),
            key=lambda kv: kv[1],
        )[0]


def bottleneck_analysis() -> BottleneckVerdict:
    """Which of floor area, bandwidth or computation runs out first."""
    return BottleneckVerdict(
        workspace_ceiling=workspace_ceiling_N(),
        bandwidth_ceiling=bandwidth_saturation_N(),
        computation_ceiling=latency_budget_N(),
    )


def marginal_gains(throughput: dict[int, int] | None = None) -> dict[int, int]:
    thr = throughput or C.THROUGHPUT_SIM
    ns = sorted(thr)
    return {n: thr[n] - thr[prev] for prev, n in zip(ns, ns[1:])}


def conservatism_reduction_pct() -> dict[int, float]:
    """Figure 1, right panel: reduction in separation conservatism."""
    return {n: 100.0 * (C.SEPARATION_FIXED_M[n] - C.SEPARATION_LEARNED_CBF_M[n])
            / C.SEPARATION_FIXED_M[n] for n in C.N_RANGE}
