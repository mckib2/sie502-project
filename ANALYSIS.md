# CAMS Analysis

Question --> evidence --> finding for methodology questions.
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

