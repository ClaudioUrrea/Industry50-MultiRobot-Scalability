"""
Industry 5.0 multi-robot scalability framework.

Companion code for

    C. Urrea, "Scalable Multi-Robot Architecture for Industry 5.0 Human-Centric
    Manufacturing: Coordination Efficiency, Sustainability Integration, and
    Digital-Twin Validation", IEEE Access, 2026.

Archived deposit: https://doi.org/10.6084/m9.figshare.33090107
Source repository: https://github.com/ClaudioUrrea/Industry50-MultiRobot-Scalability

Every quantity produced by this package is a simulation parameter or a
simulation output.  No physical multi-robot cell was built and no human
participant took part in any measurement.  The provenance of each human-factors
index -- directly simulated, model estimated, or projected from published
empirical relationships -- is recorded in `config.PROVENANCE` and repeated at
the point of use in `tbl.py`.
"""

from . import config, coordination, disruption, reba, tbl, campaign  # noqa: F401

__version__ = "1.0.0"
__author__ = "Claudio Urrea"
__license__ = "CC-BY-4.0"
__all__ = ["config", "coordination", "disruption", "reba", "tbl", "campaign"]
