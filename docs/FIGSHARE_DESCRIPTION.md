# Figshare item description

Paste the body below into the Figshare description field. Keep the title,
authors, licence and keyword fields as given.

---

**Title**

Industry 5.0 multi-robot scalability: code, archived series and verification
protocol

**Authors**

Claudio Urrea, University of Santiago of Chile (ORCID 0000-0001-7197-8928)

**Categories**

Robotics and mechatronics engineering; Manufacturing engineering; Simulation
and modelling

**Keywords**

collaborative robots; Industry 5.0; multi-robot coordination; digital twin;
scalability; human-robot collaboration; ergonomics; reproducibility; simulation

**Licence**

CC BY 4.0 for data, documentation and figures. MIT for source code, as stated
in the code bundle.

**Description**

Code, archived series and figures supporting the article "Simulation-Based
Scalability Assessment of Multi-Robot Industry 5.0 Human-Centric Cells:
Coordination-Efficiency Modeling, Bottleneck Identification, and
Triple-Bottom-Line Screening in a Physics-Based Digital Twin" (IEEE Access,
2026).

The study characterises how coordination efficiency degrades as collaborative
robots are added to a 12 m2 human-centric assembly cell, across one to five
robots, and reports a second campaign of sixty simulated shifts under
stochastic disruption. No physical cell was built and no human participant took
part; every quantity is a model output.

What this deposit permits, and what it does not, is stated here rather than
left to inference.

Every derived quantity in the paper recomputes from the archived series. A
verification script performs eighty such checks and all eighty pass, and a
suite of forty-two unit tests covers the same code. The stochastic disruption
model is executable and seeded: the replication ensemble of five hundred
realisations and the parameter sensitivity analysis reported in the paper are
produced by running it, not read from a stored result.

Re-execution of the physics is not among them. The CoppeliaSim scene files
behind the one-to-five-robot throughput, occupancy, latency, bandwidth and
separation series are not available and are not part of this deposit, so those
series are an input to the analysis rather than a reproducible output of it.
What that costs is quantified in the article, which reports how large an error
in the archived series would have to be before each conclusion changed. The
specification needed to instantiate an equivalent twin is included, together
with the verification protocol of 3,970 runs across nine blocks that such a
twin would permit; that protocol has not been executed.

**Files**

- `Industry50-MultiRobot-Scalability-code.zip` — the complete repository
- `data_processed.zip` — archived series and generated tables
- `data_ensemble.zip` — 500-replication ensemble and sensitivity output
- `figures.zip` — the four figures, PDF and PNG
- `CHECKSUMS.txt` — SHA-256 of each file above

**Related identifiers**

Software repository: https://github.com/ClaudioUrrea/Industry50-MultiRobot-Scalability

**Funding**

This research received no external funding.
