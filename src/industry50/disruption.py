"""
Stochastic disruption model of the extended campaign (Section VI-A).

Three independent families are superimposed on the nominal model:

  1. equipment faults      Poisson arrivals, lognormal repair time
  2. network interruptions Poisson arrivals, exponential recovery time
  3. operator variation    learning curve plus an absence process

Functional forms are standard reliability practice for industrial robotic
systems; rates and recovery times are of the order of magnitude reported in the
published literature (Tsarouhas & Fourlas, Int. J. Performability Eng., 2015)
but are NOT fitted to the maintenance record of any facility.  Each family
reproduces by construction the steady-state unavailability decomposition of
Section VI-B: 0.8 % + 1.2 % + 0.7 % = 2.7 %.

All draws come from a seeded generator (config.SEED = 42).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import config as C


# ---------------------------------------------------------------------------
# Closed-form steady-state quantities (no sampling)
# ---------------------------------------------------------------------------
def steady_state_unavailability(mtbf_h: float, mean_repair_min: float) -> float:
    """U = E[R] / (MTBF + E[R]), both terms in the same units."""
    r = mean_repair_min / 60.0
    return r / (mtbf_h + r)


def lognormal_mean(median_min: float, sigma: float) -> float:
    """E[R] = median * exp(sigma^2 / 2)."""
    return median_min * float(np.exp(sigma ** 2 / 2.0))


def expected_events(mtbf_h: float, horizon_h: float = C.CAMPAIGN_HOURS) -> float:
    return horizon_h / mtbf_h


def equipment_unavailability() -> float:
    p = C.EQUIPMENT_FAULT
    return steady_state_unavailability(
        p["mtbf_h"], lognormal_mean(p["repair_median_min"], p["repair_sigma"]))


def network_unavailability() -> float:
    p = C.NETWORK_FAULT
    return steady_state_unavailability(p["mtbf_h"], p["recovery_mean_min"])


def operator_unavailability() -> float:
    """Station idle time from the absence process, averaged over stations."""
    p = C.OPERATOR_MODEL
    events = p["absence_rate_per_operator_shift"] * C.CAMPAIGN_OPERATOR_SHIFTS
    idle_min = events * p["absence_idle_min"] / C.CAMPAIGN_STATIONS
    return idle_min / (C.CAMPAIGN_HOURS * 60.0)


def availability_decomposition() -> dict[str, float]:
    eq, nw, op = (equipment_unavailability(), network_unavailability(),
                  operator_unavailability())
    return {"equipment": eq, "network": nw, "operator": op,
            "total_unavailability": eq + nw + op,
            "availability": 1.0 - (eq + nw + op)}


# ---------------------------------------------------------------------------
# Operator proficiency
# ---------------------------------------------------------------------------
def proficiency(shift: int | np.ndarray) -> np.ndarray:
    """p(s) = 1 - d exp(-(s-1)/tau), the learning curve of Section VI-A."""
    p = C.OPERATOR_MODEL
    s = np.asarray(shift, dtype=float)
    return 1.0 - p["proficiency_deficit"] * np.exp(
        -(s - 1.0) / p["time_constant_shifts"])


def ramp_target(shift: int | np.ndarray,
                nominal: float = C.CAMPAIGN_PREDICTED[
                    "throughput_units_per_shift"]) -> np.ndarray:
    """Production target during the three-phase ramp-up of Section VI-A.

    Shifts 1-10 run at 70 % of nominal while the proficiency model is below
    asymptote; shifts 11-20 ramp linearly to full rate; shifts 21-60 run at
    full rate.
    """
    s = np.asarray(shift, dtype=float)
    ramp_hi = C.RAMP_PHASES["ramp"][1]                 # 10
    trans_lo, trans_hi = C.RAMP_PHASES["transition"]   # 11, 20
    a = C.RAMP_TRANSITION_START_FRACTION
    span = np.clip((s - trans_lo) / (trans_hi - trans_lo), 0.0, 1.0)
    frac = np.where(s <= ramp_hi, C.RAMP_TARGET_FRACTION,
                    np.where(s <= trans_hi, a + (1.0 - a) * span, 1.0))
    return nominal * frac


def defect_rate_pct(shift: int | np.ndarray) -> np.ndarray:
    """Stationary fault term plus a proficiency-linked excess that decays."""
    s = np.asarray(shift, dtype=float)
    return (C.DEFECT_ASYMPTOTE_PCT + C.DEFECT_PROFICIENCY_EXCESS_PCT
            * np.exp(-(s - 1.0) / C.DEFECT_TIME_CONSTANT_SHIFTS))


# ---------------------------------------------------------------------------
# Event sampling
# ---------------------------------------------------------------------------
@dataclass
class DowntimeTrace:
    equipment_events: np.ndarray      # shift index of each event
    equipment_minutes: np.ndarray
    network_events: np.ndarray
    network_minutes: np.ndarray
    absence_events: np.ndarray
    absence_minutes: np.ndarray

    def minutes_per_shift(self, n_shifts: int = C.CAMPAIGN_SHIFTS) -> np.ndarray:
        """Cell-equivalent downtime per shift, in minutes.

        Equipment and network faults are cell level.  An absence idles one of
        the three stations, so its contribution is divided by the station count
        before it is aggregated to the cell, consistently with the availability
        decomposition of Section VI-B.
        """
        out = np.zeros(n_shifts)
        for ev, mn, scale in (
                (self.equipment_events, self.equipment_minutes, 1.0),
                (self.network_events, self.network_minutes, 1.0),
                (self.absence_events, self.absence_minutes,
                 1.0 / C.CAMPAIGN_STATIONS)):
            for s, m in zip(ev, mn):
                out[int(s) - 1] += m * scale
        return out

    @property
    def total_minutes(self) -> float:
        return float(self.equipment_minutes.sum() + self.network_minutes.sum()
                     + self.absence_minutes.sum() / C.CAMPAIGN_STATIONS)


def sample_downtime(rng: np.random.Generator,
                    n_shifts: int = C.CAMPAIGN_SHIFTS) -> DowntimeTrace:
    """Draw one campaign realisation of the three disruption families."""
    horizon_h = n_shifts * C.SHIFT_HOURS

    # 1. Equipment faults: Poisson arrivals, lognormal repair
    eq = C.EQUIPMENT_FAULT
    n_eq = rng.poisson(horizon_h / eq["mtbf_h"])
    eq_shifts = rng.integers(1, n_shifts + 1, size=n_eq)
    mu = np.log(eq["repair_median_min"])
    eq_minutes = rng.lognormal(mean=mu, sigma=eq["repair_sigma"], size=n_eq)

    # 2. Network interruptions: Poisson arrivals, exponential recovery
    nw = C.NETWORK_FAULT
    n_nw = rng.poisson(horizon_h / nw["mtbf_h"])
    nw_shifts = rng.integers(1, n_shifts + 1, size=n_nw)
    nw_minutes = rng.exponential(scale=nw["recovery_mean_min"], size=n_nw)

    # 3. Operator absences: Bernoulli per operator-shift, fixed idle interval
    op = C.OPERATOR_MODEL
    draws = rng.random((n_shifts, C.CAMPAIGN_STATIONS))
    idx = np.argwhere(draws < op["absence_rate_per_operator_shift"])
    ab_shifts = idx[:, 0] + 1
    ab_minutes = np.full(len(idx), op["absence_idle_min"], dtype=float)

    return DowntimeTrace(eq_shifts, eq_minutes, nw_shifts, nw_minutes,
                         ab_shifts, ab_minutes)
