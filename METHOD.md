# CAMS Method

## Purpose

CAMS is specifically for managing collaborative autonomy: commander intent, objectives, team engagements, OPMs, shared resources, and probability-of-success estimation and monitoring.  CAMS does not care about any given vehicle/threat model or any individual autonomous behavior.

The denied-environment scenario is an example of a specific domain (`denied`) that extends the core CAMS vocabulary with domain-specifics.

## Description patterns

<!-- NBPM: Project Deliverable 4: minimum 4 patterns -- we did it! -->

| Pattern | Viewpoint | Focal types | Editor |
|---------|-----------|-------------|--------|
| Authority | Who / why | MissionCommander, Intent, Constraint, Condition | table |
| Mission | What | MissionPlan, Objective | table |
| Engagement | How | EngagementPlan, OPM, Role | tree |
| Platform | With what | Team, Asset, Capability, Behavior, Imaging/Radar sensors | table |
| Coverage | Fit | Objective x OPM; OPM x Asset (allocated vs able) | matrix |

World-state, estimators, and assessments stay in the shared description as context.

### Notes

- "spawn"/activation gates are only meaningful with specific intents and constraints on those gates.
- OPMs satisfy objectives; engagements realize a mission for a team.
- OPMs contain Roles -- hierarchy matches a "play" breakdown for planning/execution.
- allocation and capability coverage are checked against teams/assets already named by their respective engagements.

## Business rules (SHACL)

Rules are enforced in pattern shapes, e.g.:

1. An OPM must contain at least one Role.
2. A Role must be allocated to exactly one Asset.
3. That Asset must belong to the Team executing the EngagementPlan that contains the Role's OPM.
4. That Asset must provide every Capability required by the Role's Behavior.

Structural checks (e.g., Intent/Objective `isGatedBy`, Constraint has Conditions) are implemented as property shapes.

## Layout

```
src/method/md/example.com/cams/     # compose templates = notebook + SHACL
src/model/md/CAMS Denied/           # pages that invoke templates
src/model/oml/.../denied/project/
  description.oml                   # ABox module
  bundle.oml
```

I decided to put everything in same descriptipon as cross-links (i.e., Intent --> Objective --> OPM --> Asset --> Team) tend to be dense and splitting into multiple description IRIs adds `uses` cycles without improving usability very much, AFAICT.  Viewpoint separation is achieved via the compose patterns/pages.
