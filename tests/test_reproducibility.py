"""
Regression tests over the published quantities.

    pytest -q tests/

These duplicate a subset of scripts/verify_paper_numbers.py in a form CI can
run quickly; the script remains the exhaustive check.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from industry50 import config as C            # noqa: E402
from industry50 import coordination as coord  # noqa: E402
from industry50 import disruption as disr     # noqa: E402
from industry50 import reba                   # noqa: E402
from industry50 import tbl                    # noqa: E402
from industry50 import campaign               # noqa: E402


# --- coordination-efficiency model ----------------------------------------
@pytest.mark.parametrize("n,want", [(1, 100.0), (2, 90.3), (3, 87.1),
                                    (4, 78.4), (5, 68.2)])
def test_simulated_efficiency(n, want):
    eta = coord.efficiency_from_throughput(C.THROUGHPUT_SIM_UNROUNDED)
    assert 100 * eta[n] == pytest.approx(want, abs=0.05)


@pytest.mark.parametrize("n,want", [(1, 100.0), (2, 93.1), (3, 85.6),
                                    (4, 77.5), (5, 68.8)])
def test_predicted_efficiency(n, want):
    assert 100 * coord.efficiency_model(n) == pytest.approx(want, abs=0.05)


def test_identified_coefficients():
    beta, gamma = coord.identify_coefficients()
    assert beta == pytest.approx(0.0659, abs=2e-4)
    assert gamma == pytest.approx(0.00298, abs=2e-5)


def test_fit_rmse_is_one_point_five_points():
    assert coord.fit_rmse() == pytest.approx(1.5, abs=0.05)


def test_residuals_do_not_trend_with_N():
    """Section V-B: residuals scatter, changing sign twice."""
    _, resid = coord.fit_residuals()
    signs = np.sign(resid[1:])
    assert int(np.sum(signs[:-1] != signs[1:])) == 2


def test_eta_of_one_is_eta_zero_by_construction():
    assert coord.efficiency_model(1) == pytest.approx(C.ETA0)


# --- bottleneck analysis ---------------------------------------------------
def test_workspace_is_the_binding_constraint():
    assert coord.bottleneck_analysis().binding == "workspace"


def test_bandwidth_and_computation_ceilings():
    assert coord.bandwidth_saturation_N() == pytest.approx(11.0, abs=0.5)
    assert coord.latency_budget_N() == pytest.approx(6.0, abs=0.5)


@pytest.mark.parametrize("n", C.N_RANGE)
def test_auxiliary_fits_within_stated_bounds(n):
    assert coord.bandwidth_model(n) == pytest.approx(
        C.BANDWIDTH_UTILISATION_PCT[n], abs=0.4)
    assert coord.latency_model(n) == pytest.approx(
        C.PLANNING_LATENCY_MS[n], abs=0.5)


def test_marginal_gains():
    assert coord.marginal_gains() == {2: 247, 3: 248, 4: 161, 5: 84}


def test_conservatism_reduction_is_monotone():
    red = coord.conservatism_reduction_pct()
    assert red[1] == pytest.approx(51.7, abs=0.1)
    assert red[5] == pytest.approx(31.4, abs=0.1)
    assert all(red[n] >= red[n + 1] for n in (1, 2, 3, 4))


# --- disruption model ------------------------------------------------------
def test_availability_decomposition_sums_to_two_point_seven():
    d = disr.availability_decomposition()
    assert 100 * d["equipment"] == pytest.approx(0.8, abs=0.02)
    assert 100 * d["network"] == pytest.approx(1.2, abs=0.02)
    assert 100 * d["operator"] == pytest.approx(0.7, abs=0.02)
    assert 100 * d["total_unavailability"] == pytest.approx(2.7, abs=0.05)


def test_expected_event_counts():
    assert disr.expected_events(C.EQUIPMENT_FAULT["mtbf_h"]) == 8
    assert disr.expected_events(C.NETWORK_FAULT["mtbf_h"]) == 5


def test_defect_trajectory_endpoints():
    assert disr.defect_rate_pct(11) == pytest.approx(1.2, abs=0.05)
    assert disr.defect_rate_pct(60) == pytest.approx(0.6, abs=0.05)


def test_proficiency_saturates():
    assert disr.proficiency(1) == pytest.approx(0.48, abs=0.01)
    assert disr.proficiency(60) > 0.99


# --- campaign --------------------------------------------------------------
def test_campaign_ensemble_matches_table4():
    ens = campaign.campaign_ensemble(n_replications=60)
    assert ens["throughput_units_per_shift_mean"] == pytest.approx(547, abs=3)
    assert ens["defect_rate_pct_mean"] == pytest.approx(0.8, abs=0.05)
    assert ens["uptime_pct_mean"] == pytest.approx(95.8, abs=0.5)
    assert ens["energy_kwh_mean"] == pytest.approx(32.7, abs=0.4)


def test_campaign_is_deterministic_under_the_documented_seed():
    a = campaign.extended_campaign(seed=C.SEED)["summary"]
    b = campaign.extended_campaign(seed=C.SEED)["summary"]
    assert a == b


def test_campaign_accounting():
    sc = campaign.scalability_campaign()
    assert sc["hours_simulated"] == 440
    assert sc["robot_hours"] == 1320
    assert sc["operator_hours"] == 440
    assert C.CAMPAIGN_OPERATOR_HOURS == 1440
    assert sc["separation_violations"] == 0


# --- Triple Bottom Line and provenance -------------------------------------
@pytest.mark.parametrize("metric,want", [
    ("units_per_shift", 143), ("labour_intensity_h_per_100u", 79),
    ("defect_rate_pct", 81), ("energy_kwh", 26), ("carbon_kg", 26),
    ("satisfaction_5pt", 44), ("injuries_per_1k_h", 86),
    ("sick_days_pct", 59), ("turnover_pct", 68)])
def test_tbl_improvements(metric, want):
    assert tbl.improvement(metric) == pytest.approx(want, abs=1)


def test_social_projections_reproduce_table2():
    p = tbl.project_all()
    assert p["satisfaction"].value == pytest.approx(4.6, abs=0.05)
    assert p["injuries"].value == pytest.approx(0.4, abs=0.05)
    assert p["sick_days"].value == pytest.approx(2.0, abs=0.05)
    assert p["turnover"].value == pytest.approx(5.9, abs=0.05)


def test_social_indices_are_labelled_as_projections():
    """The provenance label is a substantive claim, not decoration."""
    t = tbl.build("i50_hrc")
    assert all(i.provenance == "projected" for i in t.social.values())
    assert all(i.provenance == "simulated" for i in t.economic.values())
    assert all(i.provenance == "simulated" for i in t.environmental.values())


# --- REBA ------------------------------------------------------------------
def test_reba_scorer_bands():
    neutral = reba.Posture(trunk_flexion=0, neck_flexion=5,
                           upper_arm_flexion=10, lower_arm_flexion=80,
                           wrist_flexion=0)
    strained = reba.Posture(trunk_flexion=65, neck_flexion=25,
                            upper_arm_flexion=100, lower_arm_flexion=30,
                            wrist_flexion=20, load_kg=7,
                            trunk_twisted=True, arm_abducted=True,
                            static_hold_over_1min=True,
                            repeated_small_range=True)
    assert reba.score_posture(neutral)["reba"] < reba.score_posture(
        strained)["reba"]
    assert reba.score_posture(strained)["reba"] >= C.REBA_HIGH_RISK_THRESHOLD
    assert reba.risk_band(4.3) == "medium"
    assert reba.risk_band(8.2) == "high"
