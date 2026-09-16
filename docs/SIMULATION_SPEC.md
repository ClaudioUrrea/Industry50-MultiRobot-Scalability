# Simulation specification

Everything a reader needs to re-instantiate the digital twin. All values live in
`src/industry50/config.py`; this document is the human-readable version.

## Cell and hardware

| Item | Value |
|---|---|
| Cell footprint | 4 m × 3 m = 12 m² |
| Robots | Universal Robots UR5, 6 DOF, 850 mm reach, 5 kg payload |
| Effective floor claim per arm, incl. separation margin | 1.8–2.2 m² |
| Layout | robots on the perimeter, operator working centrally |
| Configurations | N = 1, 2, 3, 4, 5 |
| Operators | K = 1 per cell |

UR5 kinematic and dynamic parameters were derived from manufacturer technical
documentation. The parameters are not redistributed here.

## Control and coordination

| Item | Value |
|---|---|
| Servo loop | 50 Hz, 20 ms budget |
| Reallocation / replanning loop | 10–15 Hz, invoked on task-set or workspace change |
| Coordination scheme | ADMM, 3–5 iterations, 60–100 ms to consensus |
| State broadcast | 20 Hz per robot |
| Network | switched Ethernet, 100 Mbps |
| Middleware | ROS 2 Humble |
| Coordination server | Intel Xeon E5-2690, 32 cores, 128 GB RAM |

The 20 ms budget constrains the fast loop only. The per-cycle latencies of
Table 3 (8.3 ms at N = 1 to 16.8 ms at N = 5) belong to that loop.

## Sensing

| Item | Value |
|---|---|
| Depth cameras | Intel RealSense D435i, 30 Hz update |
| Tracking | continuous 3D, predictive trajectory verification |

## Safety layer (ISO/TS 15066)

| Item | Value |
|---|---|
| Design separation floor | 0.15 m |
| Velocity-scaling margin | 0.25 m |
| Nominal velocity | 1.2 m/s |
| Velocity floor under scaling | 0.3 m/s |
| Collaboration velocity band | 0.5–1.2 m/s |

Two policies were instrumented in parallel: the conservative fixed-separation SSM
baseline, which governed the campaign, and a learned control-barrier-function
variant evaluated offline against the same simulated sensor streams. The
velocity-scaling law is implemented in `ros2_bridge.CoordinationBridge.scale_velocity`.

## Digital twin

| Item | Value |
|---|---|
| Physics | CoppeliaSim 4.10 EDU |
| Visualisation | Unity 2022.3 LTS |
| Synchronisation budget | 100 ms |
| Measured mean sync latency | 37 ms (N = 1) to 54 ms (N = 5), 4.25 ms per robot |
| 95th percentile | 52–82 ms, inside budget throughout |
| Maximum | crosses 100 ms from N = 3 onward (103, 115, 127 ms) |

## Task model

Automotive component assembly: electrical connector installation (4 variants,
12–18 parts per assembly), torque-controlled bolt fastening (8–12 fasteners per
unit), automated optical inspection. Parts spread over roughly 4 m²; tolerances
around ±1 mm.

## Campaign 1 — scalability, Section V

| Item | Value |
|---|---|
| Configurations | 5 (N = 1..5) |
| Duration per configuration | 11 shifts × 8 h = 88 h |
| Total cell operation | 440 h |
| Robot-hours | 1 320 |
| Operator-hours | 440 |
| Separation violations | 0 |

## Campaign 2 — extended, under stochastic disruption, Section VI

| Item | Value |
|---|---|
| Configuration | N = 2 |
| Duration | 60 shifts × 8 h = 480 h, twelve weeks single-shift |
| Stations | 3, one simulated operator each |
| Operator-hours | 1 440 |
| Phases | shifts 1–10 at 70 % of target; 11–20 transition; 21–60 full rate |
| Separation violations | 0 |

### Disruption model

| Family | Arrival | Recovery | Steady-state unavailability |
|---|---|---|---|
| Equipment faults (gripper, pneumatic, end effector) | Poisson, cell-level MTBF 60 h → 8 expected events | lognormal, median 24.3 min, σ = 0.60, mean 29.0 min | 0.800 % |
| Network interruptions (switch, link) | Poisson, MTBF 96 h → 5 expected events | mean 70.0 min, physical replacement dominating | 1.200 % |
| Operator absence | Bernoulli, 0.05 per operator-shift → 9 expected events over 180 operator-shifts | 67 min station idle, averaged over 3 stations | 0.698 % |
| **Total** | | | **2.70 %** |

Steady-state unavailability follows `U = E[R] / (MTBF + E[R])`; for the lognormal,
`E[R] = median · exp(σ²/2)`.

Functional forms are standard reliability practice for industrial robotic
systems, and rates are of the order of magnitude reported in the published
literature (Tsarouhas & Fourlas, *Int. J. Performability Eng.* 11(5), 2015).
**They are not fitted to the maintenance record of any facility**, and the
resulting three-point availability allowance should be re-estimated from site
data before it is relied upon.

### Operator proficiency

`p(s) = 1 − 0.52 · exp(−(s−1)/12)`, applied to task execution time. The deficit
and time constant are those that reproduce the ramp-up trajectory of Section VI-B.

### Defect model

`d(s) = 0.6 % + 1.082 % · exp(−(s−1)/17)`. The fault term is stationary; the
excess is proficiency-linked. Reported campaign value is the mean over shifts
11–60. Decomposition at steady state: connector insertion misalignment 0.3 %,
torque verification failure 0.2 %, optical inspection false positives 0.2 %,
uncharacterised 0.1 %.

## Human-factors instrumentation

REBA is computed from simulated postures at each control cycle using the standard
tables (`reba.py`). NASA-TLX is **estimated**, not measured, from simulated task
structure through a regression calibrated on published HRC studies. Satisfaction,
sick days, injury rate and turnover are **projected** from published empirical
relationships applied to the simulated REBA and modelled workload trajectories.

**No human participant took part at any stage.** No survey, interview,
questionnaire, physiological recording or observational measurement involving a
person was conducted, and no data of human origin were collected, processed or
stored. Institutional ethics review and informed consent were accordingly not
applicable.
