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

The CoppeliaSim scene files from which the one-to-five-robot throughput,
occupancy, latency, bandwidth and separation series were originally obtained
were lost and are not recoverable. No copy is held here or by the author. Those
series are archived in full and are the input to the analysis, but the model
that generated them cannot be re-run. The specification needed to rebuild an
equivalent twin is included, and so is the complete verification protocol,
3,970 runs across nine blocks, that a rebuilt twin would permit; that protocol
has not been executed.

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
