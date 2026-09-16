"""
Triple Bottom Line accounting (Section III-D, Table 2) and the projection of the
social indices (Section VI-C).

PROVENANCE IS NOT UNIFORM ACROSS THIS MODULE AND THE CODE SAYS SO AT EVERY
RETURN VALUE:

  * directly simulated  -- throughput, defect rate, uptime, energy, carbon,
                           material waste, REBA.  Digital-twin outputs.
  * model estimated     -- NASA-TLX.  A regression calibrated on published
                           human-robot collaboration studies, applied to
                           simulated task structure.
  * projected           -- satisfaction, injury rate, sick days, turnover.
                           Published empirical relationships applied to the
                           simulated REBA and workload trajectories.  These are
                           PROJECTIONS, they carry the uncertainty of the source
                           studies, and they are not findings of this work.

No survey, interview or physiological measurement on a human participant was
conducted at any point.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import config as C


@dataclass(frozen=True)
class Indicator:
    name: str
    value: float
    unit: str
    provenance: str          # "simulated" | "model_estimated" | "projected"
    note: str = ""

    def __str__(self) -> str:  # pragma: no cover - presentation only
        return f"{self.name}: {self.value:g} {self.unit} [{self.provenance}]"


@dataclass
class TripleBottomLine:
    configuration: str
    economic: dict = field(default_factory=dict)
    environmental: dict = field(default_factory=dict)
    social: dict = field(default_factory=dict)

    def as_rows(self):
        for pillar in ("economic", "environmental", "social"):
            for ind in getattr(self, pillar).values():
                yield (self.configuration, pillar, ind.name, ind.value,
                       ind.unit, ind.provenance)


def _sim(name, value, unit, note=""):
    return Indicator(name, value, unit, "simulated", note)


def _proj(name, value, unit, note=""):
    return Indicator(name, value, unit, "projected", note)


def build(configuration: str) -> TripleBottomLine:
    """Assemble Table 2 for one configuration, with provenance attached."""
    d = C.TBL[configuration]
    return TripleBottomLine(
        configuration=configuration,
        economic={
            "units": _sim("Units per shift", d["units_per_shift"], "units"),
            "direct_labour": _sim("Direct labour", d["direct_labour_h"], "operator-h/shift"),
            "labour_intensity": _sim("Labour intensity", d["labour_intensity_h_per_100u"], "operator-h/100 units"),
            "defects": _sim("Defect rate", d["defect_rate_pct"], "%"),
            "uptime": _sim("Uptime", d["uptime_pct"], "%"),
        },
        environmental={
            "energy": _sim("Energy", d["energy_kwh"], "kWh/shift"),
            "carbon": _sim("Carbon", d["carbon_kg"], "kg CO2/shift"),
            "waste": _sim("Material waste", d["material_waste_pct"], "%"),
        },
        social={
            "satisfaction": _proj("Satisfaction", d["satisfaction_5pt"],
                                  "/5.0", "projected from published relations"),
            "injuries": _proj("Injuries", d["injuries_per_1k_h"],
                              "per 1000 h", "annualised projection from REBA"),
            "sick_days": _proj("Sick days", d["sick_days_pct"], "%"),
            "turnover": _proj("Turnover", d["turnover_pct"], "%"),
        },
    )


def relative_change(metric: str, base: str = "manual",
                    other: str = "i50_hrc") -> float:
    """Signed relative change from `base` to `other`, in per cent."""
    b, o = C.TBL[base][metric], C.TBL[other][metric]
    return 100.0 * (o - b) / b


def improvement(metric: str, base: str = "manual",
                other: str = "i50_hrc") -> float:
    """Magnitude of improvement, in per cent, sign-corrected per metric."""
    lower_is_better = {"direct_labour_h", "labour_intensity_h_per_100u",
                       "defect_rate_pct", "energy_kwh",
                       "carbon_kg", "material_waste_pct", "injuries_per_1k_h",
                       "sick_days_pct", "turnover_pct"}
    change = relative_change(metric, base, other)
    return -change if metric in lower_is_better else change


# ---------------------------------------------------------------------------
# Social projection (Section VI-C).  PROJECTIONS, NOT MEASUREMENTS.
# ---------------------------------------------------------------------------
def project_satisfaction(reba_before: float, reba_after: float,
                         tlx_before: float, tlx_after: float,
                         satisfaction_before: float) -> Indicator:
    k = C.SOCIAL_PROJECTION["satisfaction"]
    delta = (k["per_reba_point"] * (reba_before - reba_after)
             + k["per_tlx_point"] * (tlx_before - tlx_after))
    value = min(5.0, satisfaction_before + delta)
    return _proj("Satisfaction", round(value, 1), "/5.0",
                 "applied published exposure-satisfaction relationships to the "
                 "simulated REBA and modelled NASA-TLX trajectories")


def project_injury_rate(reba_before: float, reba_after: float,
                        injury_rate_before: float) -> Indicator:
    k = C.SOCIAL_PROJECTION["injury_rate"]["exposure_response_exponent"]
    value = injury_rate_before * (reba_after / reba_before) ** k
    return _proj("Injuries", round(value, 1), "per 1000 h",
                 "annualised projection from the simulated REBA distribution "
                 "via published exposure-response relationships; not an "
                 "incident count")


def project_sick_days(injury_before: float, injury_after: float,
                      sick_days_before: float) -> Indicator:
    e = C.SOCIAL_PROJECTION["sick_days"]["elasticity_to_injury"]
    value = sick_days_before * (injury_after / injury_before) ** e
    return _proj("Sick days", round(value, 1), "%")


def project_turnover(sat_before: float, sat_after: float,
                     turnover_before: float) -> Indicator:
    e = C.SOCIAL_PROJECTION["turnover"]["elasticity_to_satisfaction"]
    value = turnover_before * (sat_after / sat_before) ** e
    return _proj("Turnover", round(value, 1), "%")


def project_all() -> dict[str, Indicator]:
    """Reproduce the social column of Table 2 for the I5.0 HRC configuration."""
    m = C.TBL["manual"]
    sat = project_satisfaction(C.REBA_BASELINE, C.REBA_CAMPAIGN,
                               C.NASA_TLX_BASELINE, C.NASA_TLX_CAMPAIGN,
                               m["satisfaction_5pt"])
    inj = project_injury_rate(C.REBA_BASELINE, C.REBA_NOMINAL,
                              m["injuries_per_1k_h"])
    sick = project_sick_days(m["injuries_per_1k_h"], inj.value,
                             m["sick_days_pct"])
    turn = project_turnover(m["satisfaction_5pt"], sat.value,
                            m["turnover_pct"])
    return {"satisfaction": sat, "injuries": inj,
            "sick_days": sick, "turnover": turn}
