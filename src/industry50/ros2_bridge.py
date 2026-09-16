"""
Optional ROS 2 Humble bridge between the coordination layer and the digital twin.

This module is NOT required to reproduce any number in the manuscript: every
result in the paper is produced by `campaign.py`, which has no ROS dependency.
The bridge is provided because the coordination layer described in Section IV
runs over ROS 2 middleware, and a reader replicating the architecture on
hardware will need the interface rather than the offline analysis.

Requires a sourced ROS 2 Humble environment (`rclpy`).  If `rclpy` is absent the
module imports cleanly and `available()` returns False, so the rest of the
package remains usable in a plain Python environment.

Topics
------
  /industry50/robot_<i>/state      geometry_msgs/PoseStamped   at 20 Hz
  /industry50/robot_<i>/command    trajectory_msgs/JointTrajectory
  /industry50/operator/state       std_msgs/Float32MultiArray  (REBA, TLX)
  /industry50/cell/separation      std_msgs/Float32            minimum distance
  /industry50/cell/consensus       std_msgs/Bool               ADMM converged
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config as C

try:                                            # pragma: no cover
    import rclpy
    from rclpy.node import Node
    _HAVE_ROS = True
except Exception:                               # pragma: no cover
    rclpy = None
    Node = object
    _HAVE_ROS = False


def available() -> bool:
    """True when a ROS 2 environment is sourced and rclpy imports."""
    return _HAVE_ROS


@dataclass(frozen=True)
class TopicMap:
    state = "/industry50/robot_{i}/state"
    command = "/industry50/robot_{i}/command"
    operator = "/industry50/operator/state"
    separation = "/industry50/cell/separation"
    consensus = "/industry50/cell/consensus"


class CoordinationBridge(Node):                 # pragma: no cover
    """Publishes cell state and subscribes to per-robot trajectories.

    The consensus loop runs at the slow reallocation rate of Section IV
    (10-15 Hz); the separation check runs on the 50 Hz servo loop and is what
    the 20 ms budget constrains.
    """

    def __init__(self, n_robots: int = 2,
                 state_rate_hz: int = C.STATE_BROADCAST_HZ):
        if not _HAVE_ROS:
            raise RuntimeError(
                "ROS 2 is not available. Source a ROS 2 Humble environment, or "
                "use industry50.campaign for the offline analysis, which needs "
                "no ROS dependency.")
        super().__init__("industry50_coordination_bridge")
        self.n_robots = n_robots
        self.state_rate_hz = state_rate_hz
        self.separation_floor_m = C.SEPARATION_FLOOR_M
        self.separation_margin_m = C.SEPARATION_MARGIN_M
        self.get_logger().info(
            f"coordination bridge up: N={n_robots}, "
            f"state {state_rate_hz} Hz, servo {C.CONTROL_RATE_HZ} Hz, "
            f"budget {C.CONTROL_BUDGET_MS} ms")

    def scale_velocity(self, separation_m: float) -> float:
        """ISO/TS 15066 speed and separation monitoring, Section IV."""
        if separation_m <= self.separation_floor_m:
            return 0.0
        if separation_m >= self.separation_margin_m:
            return C.VELOCITY_NOMINAL_MS
        span = self.separation_margin_m - self.separation_floor_m
        frac = (separation_m - self.separation_floor_m) / span
        return C.VELOCITY_FLOOR_MS + frac * (
            C.VELOCITY_NOMINAL_MS - C.VELOCITY_FLOOR_MS)
