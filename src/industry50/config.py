"""
Central configuration for the Industry 5.0 multi-robot scalability study.

Every constant below appears in the manuscript

    C. Urrea, "Scalable Multi-Robot Architecture for Industry 5.0 Human-Centric
    Manufacturing: Coordination Efficiency, Sustainability Integration, and
    Digital-Twin Validation", IEEE Access, 2026.

and is annotated with the table, equation or section in which it is reported.
Nothing in this file is fitted at run time: the values are the published ones,
and scripts/verify_paper_numbers.py recomputes every derived quantity from them.

ALL VALUES ARE SIMULATION PARAMETERS OR SIMULATION OUTPUTS.
No physical cell was built and no human participant took part in any
measurement.  See the Statement on Human Subjects in the manuscript.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Global reproducibility
# ---------------------------------------------------------------------------
SEED = 42                       # Data Availability Statement

# ---------------------------------------------------------------------------
# Cell geometry and hardware (Section IV, "System Architecture Overview")
# ---------------------------------------------------------------------------
CELL_AREA_M2 = 12.0             # 4 m x 3 m manufacturing cell
CELL_DIMS_M = (4.0, 3.0)
ROBOT_MODEL = "Universal Robots UR5"
ROBOT_DOF = 6
ROBOT_REACH_MM = 850
ROBOT_PAYLOAD_KG = 5.0
ROBOT_FOOTPRINT_M2 = (1.8, 2.2)  # effective floor claim incl. separation margin

CONTROL_RATE_HZ = 50            # fast servo loop
CONTROL_BUDGET_MS = 20.0        # 1000 / CONTROL_RATE_HZ
REPLAN_RATE_HZ = (10, 15)       # slow reallocation / replanning loop
CONSENSUS_ITERATIONS = (3, 5)
CONSENSUS_TIME_MS = (60, 100)
STATE_BROADCAST_HZ = 20
NETWORK_CAPACITY_MBPS = 100     # switched Ethernet
DEPTH_CAMERA = "Intel RealSense D435i"
DEPTH_CAMERA_HZ = 30
COORDINATION_SERVER = "Intel Xeon E5-2690, 32 cores, 128 GB RAM"

# Safety layer, ISO/TS 15066 speed and separation monitoring
SEPARATION_FLOOR_M = 0.15       # system design limit
SEPARATION_MARGIN_M = 0.25      # velocity scaling begins here
VELOCITY_NOMINAL_MS = 1.2
VELOCITY_FLOOR_MS = 0.3
COLLAB_VELOCITY_BAND_MS = (0.5, 1.2)

# Digital twin
SIMULATOR = "CoppeliaSim 4.10 EDU"
VISUALIZER = "Unity 2022.3 LTS"
DT_SYNC_BUDGET_MS = 100

# ---------------------------------------------------------------------------
# Scalability campaign (Section V) -- digital-twin outputs
# ---------------------------------------------------------------------------
N_RANGE = (1, 2, 3, 4, 5)
SHIFT_HOURS = 8
SHIFTS_PER_CONFIG = 11
HOURS_PER_CONFIG = SHIFT_HOURS * SHIFTS_PER_CONFIG          # 88 h

# Table 3, "Throughput (units/shift), Simulated"
THROUGHPUT_SIM = {1: 307, 2: 554, 3: 802, 4: 963, 5: 1047}
# Coordination efficiency is computed from unrounded throughput; the unrounded
# series is retained so that eta(2) = 90.3 % reproduces exactly (see caption of
# Table 3: eta(2) = 90.3 % corresponds to 554.4 units/shift).
THROUGHPUT_SIM_UNROUNDED = {1: 307.0, 2: 554.4, 3: 802.1, 4: 962.9, 5: 1046.7}

# Table 3, "Workspace Utilization (%), Robot time"
WORKSPACE_UTILISATION_PCT = {1: 72, 2: 85, 3: 78, 4: 67, 5: 62}
# Table 3, "Communication (utilization %)"
BANDWIDTH_UTILISATION_PCT = {1: 3.8, 2: 6.2, 3: 10.1, 4: 15.8, 5: 22.3}
# Table 3, "Computation (ms)"
PLANNING_LATENCY_MS = {1: 8.3, 2: 9.7, 3: 11.4, 4: 14.2, 5: 16.8}
# Section V-C, simulated probability of conflict-free concurrent execution
CONCURRENCY_PROBABILITY = {3: 0.78, 5: 0.52}

# Figure 3, digital-twin synchronisation latency
DT_LATENCY_MEAN_MS = {1: 37, 2: 42, 3: 48, 4: 51, 5: 54}
DT_LATENCY_P95_MS = {1: 52, 2: 67, 3: 74, 4: 78, 5: 82}
DT_LATENCY_MAX_MS = {1: 68, 2: 89, 3: 103, 4: 115, 5: 127}
DT_LATENCY_SLOPE_MS_PER_ROBOT = 4.25

# Figure 1, separation policies
SEPARATION_FIXED_M = {1: 1.20, 2: 1.15, 3: 1.22, 4: 1.19, 5: 1.18}
SEPARATION_LEARNED_CBF_M = {1: 0.58, 2: 0.71, 3: 0.79, 4: 0.80, 5: 0.81}

# ---------------------------------------------------------------------------
# Coordination-efficiency model (Equation 3, Section V-A)
#   eta(N) = eta0 * (1 - beta (N-1) - gamma (N-1)^2)
# Coefficients identified by least squares from the five-configuration series
# above with eta0 held at 1.0.  Unrounded: beta = 0.0659, gamma = 0.00298.
# ---------------------------------------------------------------------------
ETA0 = 1.0
BETA = 0.066
GAMMA = 0.003

# Auxiliary fits reported in Section V-B (not used to identify BETA/GAMMA)
BANDWIDTH_FIT = {"b0_pct": 3.1, "kappa_pct": 0.77}          # b(N) = b0 + kappa N^2
LATENCY_FIT = {"t0_ms": 6.8, "c_ms": 1.21, "exponent": 1.3}  # t(N) = t0 + c N^p

# ---------------------------------------------------------------------------
# Triple Bottom Line (Table 2, Section III-D) -- N = 2, nominal conditions
# ---------------------------------------------------------------------------
# Grid emission factor applied to every configuration: carbon = GRID_EF * energy.
# A single factor means the carbon column is a linear rescaling of the energy
# column and carries no independent information (Section IV-D of the paper).
GRID_EMISSION_FACTOR_KG_PER_KWH = 0.44

# Labour is reported in operator-hours, not currency: the simulation contains no
# wage, capital or maintenance model, and the revised manuscript removed the
# monetary column accordingly (see docs/MAPPING_PAPER_TO_CODE.md).
TBL = {
    "manual": {
        "units_per_shift": 228, "operators": 2.0, "direct_labour_h": 16.0,
        "labour_intensity_h_per_100u": 7.02, "defect_rate_pct": 3.2,
        "uptime_pct": 87.7, "energy_kwh": 42.3, "carbon_kg": 18.6,
        "material_waste_pct": 4.7, "satisfaction_5pt": 3.2,
        "injuries_per_1k_h": 2.8, "sick_days_pct": 4.9, "turnover_pct": 18.6,
    },
    "i50_hrc": {
        "units_per_shift": 554, "operators": 1.0, "direct_labour_h": 8.0,
        "labour_intensity_h_per_100u": 1.44, "defect_rate_pct": 0.6,
        "uptime_pct": 98.5, "energy_kwh": 31.2, "carbon_kg": 13.7,
        "material_waste_pct": 2.0, "satisfaction_5pt": 4.6,
        "injuries_per_1k_h": 0.4, "sick_days_pct": 2.0, "turnover_pct": 5.9,
    },
    "automated": {
        "units_per_shift": 612, "operators": 0.5, "direct_labour_h": 4.0,
        "labour_intensity_h_per_100u": 0.65, "defect_rate_pct": 0.4,
        "uptime_pct": 94.2, "energy_kwh": 38.7, "carbon_kg": 17.0,
        "material_waste_pct": 1.8, "satisfaction_5pt": 2.8,
        "injuries_per_1k_h": 0.3, "sick_days_pct": 3.8, "turnover_pct": 22.4,
    },
}

# Human-factors indices (Section VI-C)
REBA_BASELINE = 8.2
REBA_NOMINAL = 4.1
REBA_CAMPAIGN = 4.3
REBA_HIGH_RISK_THRESHOLD = 8
NASA_TLX_BASELINE = 68
NASA_TLX_NOMINAL = 46
NASA_TLX_CAMPAIGN = 49
PACE_SYNC_FIXED_PCT = 78.3
PACE_SYNC_ADAPTIVE_PCT = 95.2

# ---------------------------------------------------------------------------
# Extended campaign under stochastic disruption (Section VI)
# ---------------------------------------------------------------------------
CAMPAIGN_N_ROBOTS = 2
CAMPAIGN_SHIFTS = 60
CAMPAIGN_DAYS_PER_WEEK = 5
CAMPAIGN_STATIONS = 3
CAMPAIGN_OPERATORS_PER_STATION = 1
CAMPAIGN_HOURS = CAMPAIGN_SHIFTS * SHIFT_HOURS               # 480 h
CAMPAIGN_OPERATOR_HOURS = (CAMPAIGN_HOURS * CAMPAIGN_STATIONS
                           * CAMPAIGN_OPERATORS_PER_STATION)  # 1440 h
CAMPAIGN_OPERATOR_SHIFTS = CAMPAIGN_SHIFTS * CAMPAIGN_STATIONS  # 180
RAMP_PHASES = {"ramp": (1, 10), "transition": (11, 20), "full": (21, 60)}
RAMP_TARGET_FRACTION = 0.70     # shifts 1-10 run at 70 % of nominal target

# Disruption model, Section VI-A.  Each family reproduces by construction the
# availability decomposition of Section VI-B: 0.8 % + 1.2 % + 0.7 % = 2.7 %.
EQUIPMENT_FAULT = {
    "mtbf_h": 60.0,             # cell-level, Poisson arrivals
    "repair_median_min": 24.3,  # lognormal
    "repair_sigma": 0.60,
    "target_unavailability": 0.008,
}
NETWORK_FAULT = {
    "mtbf_h": 96.0,
    "recovery_mean_min": 70.0,
    "target_unavailability": 0.012,
}
OPERATOR_MODEL = {
    "proficiency_deficit": 0.52,     # relative to asymptotic performance
    "time_constant_shifts": 12.0,
    "absence_rate_per_operator_shift": 0.05,
    "absence_idle_min": 67.0,
    "target_unavailability": 0.007,
}

# Inter-station buffering: fraction of the output lost to downtime that is
# recovered within the same shift by work in progress and catch-up at the
# unaffected stations.  This is why 2.7 points of lost availability cost only
# 1.3 % of throughput (Section VI-B, availability decomposition).
BUFFER_RECOVERY_FRACTION = 0.88

# Production target during the three-phase ramp-up, as a fraction of nominal.
# Shifts 1-10 run at 70 %; shifts 11-20 ramp linearly from 75.8 % to 100 %;
# shifts 21-60 run at full rate.
RAMP_TRANSITION_START_FRACTION = 0.758

# Defect model, Section VI-B
# The defect model carries its own time constant: the fault term is stationary
# while the proficiency-linked excess decays.  The reported campaign defect rate
# is the mean over the post-commissioning window, shifts 11-60.
DEFECT_ASYMPTOTE_PCT = 0.6
DEFECT_PROFICIENCY_EXCESS_PCT = 1.082
DEFECT_TIME_CONSTANT_SHIFTS = 17.0
DEFECT_REPORTING_WINDOW = (11, 60)
DEFECT_DECOMPOSITION_PCT = {
    "connector_insertion_misalignment": 0.3,
    "torque_verification_failure": 0.2,
    "optical_inspection_false_positive": 0.2,
    "uncharacterised": 0.1,
}

# Energy model, Section VI-B
ENERGY_NOMINAL_KWH = 31.2
ENERGY_IDLE_KW = 2.00           # standby draw while a station is down
ENERGY_REWORK_KWH_PER_PCT = 1.70  # rework energy per point of defect rate

# Published campaign outcome (Table 4) -- targets for verification
# Table 9 of the revised manuscript reports the mean over 500 independent
# realisations, not a single seeded run; scripts/p3_disruption_ensemble.py
# reproduces it together with the 95 % intervals of Table 11.
CAMPAIGN_PUBLISHED = {
    "throughput_units_per_shift": 547,
    "defect_rate_pct": 0.8,
    "uptime_pct": 95.8,
    "energy_kwh": 32.8,
    "nasa_tlx": 49,
    "reba": 4.3,
    "separation_violations": 0,
    "min_separation_m": 0.18,
}
CAMPAIGN_PREDICTED = {
    "throughput_units_per_shift": 554,
    "defect_rate_pct": 0.6,
    "uptime_pct": 98.5,
    "energy_kwh": 31.2,
    "nasa_tlx": 46,
    "reba": 4.1,
}
RAMP_TRAJECTORY_PUBLISHED = {11: 420, 26: 505, 41: 540, "41-60": 547}

# ---------------------------------------------------------------------------
# Social-index projection coefficients (Section VI-C)
# ---------------------------------------------------------------------------
# The social column of the Triple Bottom Line CANNOT be simulated.  The values
# in Table 2 are obtained by applying published empirical relationships between
# ergonomic exposure / workload and these outcomes to the simulated REBA and
# NASA-TLX trajectories.  They are projections, they carry the uncertainty of
# the source studies, and they are NOT findings of this work.
SOCIAL_PROJECTION = {
    "satisfaction": {
        "per_reba_point": 0.28,   # 5-point scale, decrease in REBA -> increase
        "per_tlx_point": 0.0165,
        "sources": ["Pollak et al. 2025", "Quenehen et al. 2023",
                    "Stecke & Mokhtarzadeh 2022"],
    },
    "injury_rate": {
        "exposure_response_exponent": 2.807,  # injuries scale with REBA^k
        "sources": ["Benazzouz et al. 2026", "Capponi et al. 2024"],
    },
    "sick_days": {"elasticity_to_injury": 0.460},
    "turnover": {"elasticity_to_satisfaction": -3.164},
}

PROVENANCE = {
    "directly_simulated": ["REBA", "throughput", "workspace_utilisation",
                           "bandwidth", "latency", "separation_distance",
                           "defect_rate", "energy"],
    "model_estimated": ["NASA-TLX"],
    "projected_from_literature": ["satisfaction", "injury_rate", "sick_days",
                                  "turnover"],
}
