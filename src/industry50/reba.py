"""
Rapid Entire Body Assessment (REBA) scorer.

REBA scores reported in the manuscript are DIRECTLY SIMULATED: they are computed
from the simulated operator postures produced by the digital twin at each control
cycle, using the standard scoring procedure (Hignett & McAtamney, 2000).  They
are not measurements on a human participant.

The implementation follows the published tables.  Inputs are joint angles in
degrees taken from the biomechanical model of the simulated operator; outputs are
the group A score (trunk, neck, legs), the group B score (upper arm, lower arm,
wrist), and the final REBA score after the activity adjustment.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Table A: [trunk][neck][legs] -> score, 1-indexed inputs collapsed to 0-indexed
_TABLE_A = np.array([
    [[1, 2, 3, 4], [1, 2, 3, 4], [3, 3, 5, 6]],
    [[2, 3, 4, 5], [3, 4, 5, 6], [4, 5, 6, 7]],
    [[2, 4, 5, 6], [4, 5, 6, 7], [5, 6, 7, 8]],
    [[3, 5, 6, 7], [5, 6, 7, 8], [6, 7, 8, 9]],
    [[4, 6, 7, 8], [6, 7, 8, 9], [7, 8, 9, 9]],
])
# Table B: [upper arm][lower arm][wrist]
_TABLE_B = np.array([
    [[1, 2, 2], [1, 2, 3]],
    [[1, 2, 3], [2, 3, 4]],
    [[3, 4, 5], [4, 5, 5]],
    [[4, 5, 5], [5, 6, 7]],
    [[6, 7, 8], [7, 8, 8]],
    [[7, 8, 8], [8, 9, 9]],
])
# Table C: [score A][score B]
_TABLE_C = np.array([
    [1, 1, 1, 2, 3, 3, 4, 5, 6, 7, 7, 7],
    [1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 7, 8],
    [2, 3, 3, 3, 4, 5, 6, 7, 7, 8, 8, 8],
    [3, 4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9],
    [4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9, 9],
    [6, 6, 6, 7, 8, 8, 9, 9, 10, 10, 10, 10],
    [7, 7, 7, 8, 9, 9, 9, 10, 10, 11, 11, 11],
    [8, 8, 8, 9, 10, 10, 10, 10, 10, 11, 11, 11],
    [9, 9, 9, 10, 10, 10, 11, 11, 11, 12, 12, 12],
    [10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 12],
    [11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12],
    [12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12],
])

RISK_BANDS = ((1, 1, "negligible"), (2, 3, "low"), (4, 7, "medium"),
              (8, 10, "high"), (11, 15, "very high"))


def _trunk_score(flexion_deg: float, twisted: bool = False,
                 side_bent: bool = False) -> int:
    a = abs(flexion_deg)
    s = 1 if a <= 5 else 2 if (a <= 20 or flexion_deg < -5) else 3 if a <= 60 else 4
    return min(5, s + int(twisted) + int(side_bent))


def _neck_score(flexion_deg: float, twisted: bool = False,
                side_bent: bool = False) -> int:
    s = 1 if 0 <= flexion_deg <= 20 else 2
    return min(3, s + int(twisted) + int(side_bent))


def _leg_score(bilateral: bool = True, knee_flexion_deg: float = 0.0) -> int:
    s = 1 if bilateral else 2
    if 30 < knee_flexion_deg <= 60:
        s += 1
    elif knee_flexion_deg > 60:
        s += 2
    return min(4, s)


def _upper_arm_score(flexion_deg: float, abducted: bool = False,
                     shoulder_raised: bool = False,
                     arm_supported: bool = False) -> int:
    a = abs(flexion_deg)
    s = 1 if a <= 20 else 2 if (a <= 45 or flexion_deg < -20) else 3 if a <= 90 else 4
    s += int(abducted) + int(shoulder_raised) - int(arm_supported)
    return int(min(6, max(1, s)))


def _lower_arm_score(flexion_deg: float) -> int:
    return 1 if 60 <= flexion_deg <= 100 else 2


def _wrist_score(flexion_deg: float, twisted: bool = False) -> int:
    return min(3, (1 if abs(flexion_deg) <= 15 else 2) + int(twisted))


@dataclass(frozen=True)
class Posture:
    """One simulated posture sample, angles in degrees."""
    trunk_flexion: float
    neck_flexion: float
    upper_arm_flexion: float
    lower_arm_flexion: float
    wrist_flexion: float
    knee_flexion: float = 0.0
    trunk_twisted: bool = False
    neck_twisted: bool = False
    arm_abducted: bool = False
    arm_supported: bool = False
    load_kg: float = 0.0
    shock_or_rapid_buildup: bool = False
    coupling: int = 0            # 0 good, 1 fair, 2 poor, 3 unacceptable
    static_hold_over_1min: bool = False
    repeated_small_range: bool = False   # > 4 times per minute
    rapid_large_change: bool = False


def _load_score(load_kg: float, shock: bool) -> int:
    s = 0 if load_kg < 5 else 1 if load_kg <= 10 else 2
    return s + int(shock)


def _activity_score(p: Posture) -> int:
    return (int(p.static_hold_over_1min) + int(p.repeated_small_range)
            + int(p.rapid_large_change))


def score_posture(p: Posture) -> dict:
    """Full REBA score for a single simulated posture sample."""
    trunk = _trunk_score(p.trunk_flexion, p.trunk_twisted)
    neck = _neck_score(p.neck_flexion, p.neck_twisted)
    legs = _leg_score(True, p.knee_flexion)
    a = int(_TABLE_A[trunk - 1, neck - 1, legs - 1]) + _load_score(
        p.load_kg, p.shock_or_rapid_buildup)

    ua = _upper_arm_score(p.upper_arm_flexion, p.arm_abducted,
                          False, p.arm_supported)
    la = _lower_arm_score(p.lower_arm_flexion)
    wr = _wrist_score(p.wrist_flexion)
    b = int(_TABLE_B[ua - 1, la - 1, wr - 1]) + p.coupling

    a_i = int(np.clip(a, 1, 12)) - 1
    b_i = int(np.clip(b, 1, 12)) - 1
    c = int(_TABLE_C[a_i, b_i])
    final = c + _activity_score(p)
    return {"score_a": a, "score_b": b, "score_c": c,
            "reba": float(final), "risk": risk_band(final)}


def risk_band(score: float) -> str:
    for lo, hi, label in RISK_BANDS:
        if lo <= score <= hi:
            return label
    return "very high"


def score_trace(postures) -> dict:
    """Aggregate a trace of simulated postures into the reported REBA index."""
    scores = np.array([score_posture(p)["reba"] for p in postures], dtype=float)
    return {
        "n_samples": int(scores.size),
        "mean": float(scores.mean()),
        "p95": float(np.percentile(scores, 95)),
        "fraction_high_risk": float((scores >= 8).mean()),
        "risk": risk_band(float(scores.mean())),
    }
