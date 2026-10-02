# CAMS Analysis

Question --> evidence --> finding for methodology questions.

> [!NOTE]
> Scenario Context: While the CAMS methodology vocabulary and analysis queries are domain- and scenario-neutral, the specific findings, evidence traces, and diagnosed gaps documented below are tailored to the `CAMS Denied` operational scenario (MissionDeny1, TeamAlpha, TeamBravo) as specific evidence for the course project submission.

---

## Q1. Does a set of ordered behaviors satisfy an Intent?

Evidence: `src/method/sparql/q1_intent_opm_roles.sparql`; Dashboard Q1 table; OPM `precedes` graph in analysis-bundle.

Finding: Yes for Active Intents on MissionDeny1's assigned TeamAlpha.  Active Objectives Search --> Strike --> BDA are satisfied by OPMs with Roles allocated to assets in Alpha; order is visible via `OPM_Search precedes OPM_JamAndStrike precedes OPM_BDA`.  Alternate OPMs (e.g., wide search, radar search, strike solo, recon-strike) also satisfy Active Objectives when contained by EngagementAlpha.

---

## Q2. Is the set of available behaviors, based on team composition, sufficient to synthesize a mission plan that realizes/satisfies all commander Intents?

Evidence: `src/method/sparql/q2_team_intent_coverage.sparql`; Dashboard Q2 table.

Finding: TeamAlpha has Roles and sufficient capabilities for all Active Objectives.  TeamBravo's engagement plan covers Search only; Strike and BDA report missing coverage, as expected.

Bravo team cannot synthesize full MissionDeny1 Active objective set.  Note we have intentionally constructed the scenario like for the project submission to show this sort of finding through the SPARQL query mechanic.  We can fix this, e.g., by adding Bravo strike/BDA assets+OPMs or even perhaps not assigning Bravo to that mission.

---

## Q3. Do all behaviors have mappings for platforms and Intents?

Evidence: `src/method/sparql/q3_behavior_mapping_gaps.sparql`; Dashboard Q3; Engagement orphan table (shows unused Behaviors).

Finding: Behaviors used on Roles (i.e., Search, Strike, Jam, BDA, RadarSearch, Bravo search) map through Role --> Asset and OPM --> Objective --> Intent/Mission.  `BehLoiter` has no Role -- expected unused entry while ObjInactiveLoiter stays Inactive.

Behavior data ICDs / message contracts are currently a consideration outside of the model. This is a limitation of the CAMS ontology -- not a bad or fatal, just recognizing it as such (and that
s okay!). Rules of Engagement are also outside of the model's concern by design.  We could add these later as additional ontology content.

---

## Q4. Is a mission plan feasible in terms of resource requirements of allocated behaviors and platform resource constraints?

Evidence: `src/method/sparql/q4_resource_feasibility.sparql`; Dashboard Q4; scripted PoS cards; GSD/jam checks in `scripts/evaluate_queries.py`.

Finding: Allocated Roles resolve resource needs via owns/shares (including taking into account type tokens such as `SensorResource` / `RadarSensorResource`).  EngagementAlpha Active-objective PoS composes above thresholds in the scripted analysis (~0.757 estimated probability of success).  Imaging GSD and jam RF feasibility are demonstrated as met.

---

## Q5. Can concurrent execution lead to resource contention?

Evidence: `src/method/sparql/q5_resource_contention.sparql`; Dashboard Q5 table; occupancy checks in `scripts/evaluate_queries.py`.

Finding: No contention under nominal execution (only `OPM_Search` executing on `RQ23_Recon`).  Resource reservation is modeled: SWRL `ResourceOccupied*` rules derive `isOccupiedBy` and `availabilityStatus = Busy` when an asset is executing an OPM whose Role requires that resource.  The `check_resource_occupancy` function in `evaluate_queries.py` validates that executing Role resources are correctly marked occupied.

Diagnosed gap (Outside the model): Runtime time-slot scheduling, priority preemption, and real-time resource arbitration are platform-runtime concerns.  The CAMS model checks static allocation feasibility and instantaneous occupancy, but does not model temporal overlap or queueing.

---

## Q6. How does mission assessment monitor probability of success and trigger contingency responses?

Evidence: `src/method/sparql/q6_success_probability_monitor.sparql`; Dashboard Q6 table; `src/method/sparql/pos_inputs.sparql`; scripted PoS cards in Dashboard; `scripts/evaluate_queries.py` (`check_pos_product`).

Finding: `AssessmentAlphaFeasible` monitors `MissionDeny1` with baseline serial PoS ≈ 0.757 (Search 0.90 × Strike 0.99 × BDA 0.85).  All per-objective thresholds are met.  The assessment triggers `ReplanAfterSpawn`.  `AssessmentInfeasible` on EngagementBravo (PoS 0.70 for search-only) triggers `NoticeMissionImpossible`, which SWRL `KickbackAddressing` addresses to `Commander1`.

Including candidate/alternate OPMs (AlphaWideSearch, RadarSearch, StrikeSolo, ReconStrike) yields an ensemble PoS of ~0.849 -- this upper bound shows redundancy margin from alternate plays.

Diagnosed gap (Process / Tooling): Non-linear PoS arithmetic (parallel-then-serial composition) requires script-based computation.  The vocabulary supplies the inputs (per-OPM estimates, per-Objective thresholds), but the formula `P(Obj) = 1-∏(1-p)` and `P(Mission) = ∏ P(Obj)` lives in Python, not in SPARQL or SWRL.

---

## Q7. Does the mission plan maintain sequential world-state prediction continuity?

Evidence: `src/method/sparql/q7_sequential_world_state_prediction.sparql`; Dashboard Q7 table; `scripts/evaluate_queries.py` (`check_state_chain`).

Finding: Topological continuity is maintained: `OPM_Search` predicts successor `WS1`, `OPM_JamAndStrike` starts from `WS1` (chain-ok).  `OPM_JamAndStrike` predicts `WS2`, `OPM_BDA` starts from `WS2` (chain-ok).  The SWRL `StateChain` rule can derive `startsFrom` from `predictsSuccessor` + `precedes` when not manually asserted.

Diagnosed gap (Outside the model): Continuous physical state estimation (Kalman filtering, sensor fusion) and world-state delta semantics (what changed between `WS1` and `WS2`) are outside the scope of this management ontology.  `WorldState` and `PredictedWorldState` are opaque tokens representing planning context, not physical simulators.

---

## Q8. How do operational and environmental conditions gate Intent and Objective activation?

Evidence: `src/method/sparql/q8_constraint_condition_gating.sparql`; Dashboard Q8 table; `scripts/evaluate_queries.py` (`check_constraint_rollup`).

Finding: Conjunction gating is fully demonstrated.  Active: `IntentFindFix` has `IntentFindFixConstraint` (Satisfied, 1/1 conditions met) → spawns `ObjSearch`, `ObjBDA`.  `IntentNeutralize` has `IntentNeutralizeConstraint` (Satisfied, 2/2 conditions: `CondThreatPresent` + `CondThreatNear`) → spawns `ObjStrike`.  Inactive: `ObjInactiveLoiter` has `ObjLoiterConstraint` = Unsatisfied because `CondLoiterWeather` = Unsatisfied (1/2 conditions met → conjunction fails).

SWRL rules `ConstraintUnsatisfied`, `ObjectiveActive`, `ObjectiveInactive`, `IntentActive`, `IntentInactive` derive these statuses from condition satisfaction.

Diagnosed gap (Process): Temporal gate expiry (conditions becoming stale over time), condition re-evaluation triggers, and hysteresis are team process / runtime concerns.  The model captures a snapshot of condition satisfaction, not a continuous monitoring loop.

---

## Pattern gap detection (orphans)

One orphan / missing-relationship query per D4 pattern (`orphan_*.sparql`, composed in `analysis-bundle`):

| Pattern | Query | Typical finding in denied fixture |
|---------|-------|-----------------------------------|
| Authority | `orphan_authority.sparql` | Empty if gates complete |
| Mission | `orphan_mission.sparql` | Empty if Objectives on MissionDeny1 |
| Engagement | `orphan_engagement.sparql` | `BehLoiter` unused |
| Platform | `orphan_platform.sparql` | May flag unused CommStrike / Compute if never required |
| Coverage | `orphan_coverage.sparql` | Empty while Active Objectives have satisfying OPMs |

Empty orphan tables are a positive finding (i.e., there are no "holes" of that class).

