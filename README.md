# CAMS

Collaborative Autonomy Management System (CAMS) ontologies in OML.
CAMS manages commander intent, mission/engagement plans, multi-role OPMs, team assets, shared resources,
world/situational awareness, and probability-of-success monitoring.  It is specifically the management system,
not any single autonomous behavior or platform.

The initial OML concepts and relations were proceduring ported from an Open UDDL model I personally constructed
describing DARPA's Collaborative Operations in Denied Environment, based on openly available information.
I then iterated, trying to move everything from the ABox I could to the TBox, especially through rules.

## Layout

```
METHOD.md                     # method narrative
catalog.xml                   # IRI rewrites for OML Code
src/method/oml/example.com/cams/
  vocabulary.oml              # core CAMS TBox (domain-neutral)
  bundle.oml
  denied/                     # denied domain TBox
src/method/md/example.com/cams/
  authority.md mission.md engagement.md platform.md   # compose templates + SHACL
src/model/md/CAMS Denied/     # compose pages (viewpoint UI)
src/model/oml/example.com/cams/denied/project/
  description.oml             # scenario ABox
  bundle.oml
queries/                      # SPARQL regression + shapes.ttl (auto-updated from md)
scripts/evaluate_queries.py
scripts/sync_shapes_from_md.py
```

See [METHOD.md](METHOD.md) for patterns and business rules.
Refresh shapes after editing pattern md: `python scripts/sync_shapes_from_md.py`.

Start the OML server from the CLI (preferred when not using the VS Code extension):

```bash
oml start -w "$(pwd)"
```

Leave that process running, then lint/reason/export from another terminal.

I am not sure how to run arbitrary SPARQL and SHACL using the `oml` CLI tools, but I sure do know how to use
Python.  So that's why there is an `evaluate_queries.py`.  It also handles validation that either can't be done
using SPARQL, SHACL, or SWRL (or at least what I couldn't figure out how to do with those).

## Build

1. Open this folder in VS Code with the **OML Code** extension (or `oml start`).
2. `oml lint` — should be clean.
3. `oml reason` — consistency bar for the course.
4. `oml export -o build/owl --pretty` or `oml reason -o build/owl --pretty` for Turtle.

## Query evaluation

```bash
oml reason -o build/owl --pretty
python -m pip install rdflib pyshacl   # once
python scripts/evaluate_queries.py
```

You will likely need to install some Python packages to get the script running -- the error messages should guide you.

Current set of acceptance queries (expanded since initial project proposal):

| Query | Question |
|-------|----------|
| q1 | Active Intent + assigned-team OPM Roles (chronological via precedes) |
| q2 | Role/capability coverage; data-driven gaps for any engagement team |
| q3 | Behavior-catalog mapping gaps (Roles) |
| q4 | Role resource access: owns / shares / none |
| q5 | Runtime contention across distinct Roles (inter- or intra-OPM) |
| q6 | PoS estimates, assessments, replan / commander notice |
| q7 | Sequential predicted world-state chain |
| q8 | Constraint = conjunction of Conditions; spawn / active-inactive |

## High-level Concepts

Authority: MissionCommander, Intent, Constraint, Condition
Plans: Objective, MissionPlan, EngagementPlan, Behavior, OPM (Objective Plan Model) (contains Roles), Role
Platform: Asset, Team, Capability, Resource (+ Sensor/Compute/Comm)
World: WorldState, PredictedWorldState, facets (`AssetState` with `readinessStatus`), SituationalAwareness, WorldStateDelta
Probability of Success (PoS): SuccessProbabilityEstimator, OPMSuccessEstimate, MissionAssessment, ReplanAction, CommanderNotice

Roles: an OPM may contain multiple Roles; each Role `realizesBehavior` one Behavior and is `allocatedTo` one Asset.
Examples: `OPM_JamAndStrike` has `RoleStrike` + `RoleJam`. Assets `isExecuting` the OPM (many assets may execute one OPM).
OPM is an obtuse name inherited from DARPA CODE.  I apologize for their obtuseness.  It's a concept that bundles both
planning and execution facets associated to some Objective in order to satisfy or achieve the Objective's Intent.

Rules include same-team `ResourceSharing`, Role-based occupancy/capability, Intent/Objective activation, and execution roll-up via Roles. MissionExecuting only rolls up from an EngagementPlan executed by the mission's `assignedTo` team (alternate-team engagements do not mark the mission Executing).

PoS composition model:
1. Intra-objective (parallel roles/estimators): \(P(\mathrm{Obj}) = 1 - \prod_r (1 - p_r)\) over all `usesEstimator` estimates on OPMs that satisfy that objective (e.g. Strike, Jam \rightarrow 0.99).
2. Inter-objective (sequential phases): \(P(\mathrm{Mission}) = \prod_k P(\mathrm{Obj}_k)\) along the active objective chain (e.g., Search \times Strike \times BDA \rightarrow 0.757).

OPMExecuting (Horn convention for open-world): the rule sets `executionStatus` to Executing when *any* allocated Role's asset asserts `isExecuting` that OPM (existential). Requiring *all* roles to check in is checked procedurally in `scripts/evaluate_queries.py` (`check_opm_role_checkin`) because SWRL cannot express that universal quantification.

Other checks in `evaluate_queries.py`: imaging GSD / jam RF math over **denied** vocabulary properties (needs `tan` — not in SWRL), two-tier PoS product vs asserted assessments, constraint roll-up, state chain, occupancy, priority inheritance, KickbackAddressing `sentTo`, SHACL.
