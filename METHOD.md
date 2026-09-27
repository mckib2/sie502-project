# CAMS Method

## Purpose

CAMS is a management method for collaborative autonomy: who decided what, what must be achieved, how a team plans to do it, with what platforms, and whether the plan still covers the objectives. It deliberately does not prescribe vehicle dynamics, threat physics, or the internals of any single autonomous behavior.

The `denied` scenario is one domain extension used to "dogfood" the method.

## Description patterns

<!-- NBPM: Project Deliverable 4: minimum 4 patterns -- we did it! -->

| Pattern | Viewpoint | Editor | Why this cut |
|---------|-----------|--------|----------------|
| Authority | Who / why | table | Commander intent and gates change slowly and are flat catalogs |
| Mission | What | table | Objectives are mission-owned outcomes, not plays |
| Engagement | How | tree | Engagement → OPM → Role is hierarchical; tree matches the play breakdown |
| Platform | With what | table | Teams, assets, capabilities, and resources are catalogs with cross-links |
| Coverage | Fit | matrix | Read-only fit check after authoring elsewhere; matrices beat scrolling SPARQL |

World-state, estimators, and assessments stay in the shared description as context. They support PoS and gating already authored under Authority / Engagement.

### Notes

- "spawn"/activation gates are only meaningful when Intents/Objectives point at Constraints that comprise Conditions.
- OPMs satisfy Objectives; EngagementPlans realize a Mission for a Team.
- Each Role belongs to exactly one OPM (a Role is a slot in one play, not a shared catalog entry).
- Allocation and capability checks are relative to the Team that executes the Engagement containing that Role's OPM.

## Rationale

Viewpoints follow the decision order a mission integrator will likely want: authority, then outcomes, then plays, then platforms, then "does this still cover?" Coverage is last (it'is diagnostic).

Engagement uses a tree because reusing a Role across OPMs is a easy-to-make mistake -- hierarchy makes this issue obvious.  Authority/Mission/Platform stay tables because their focal types are not nested the same way.

Business rules live in pattern SHACL (plus a few SPARQL shapes) so violations are visible in the editors.

## Alternatives considered

- Multiple description IRIs (e.g. authority.oml, platform.oml) vs one description. Split modules looked cleaner on paper; in practice Intent --> Objective --> OPM --> Asset --> Team cross-links forced `uses` cycles or duplicate individuals.  Viewpoint separation via compose pages seems like enough.
- Coverage as SPARQL queries only vs compose matrices.  Queries already answer Module 1 questions; matrices give the same story inside the notebooks directly.
- `requiresResourceType` string enum vs ResourceTypeToken individuals named like classes.  Strings needed a parallel column; tokens appear in the same Requires Resource picker as SensorEOIR.  True OWL class-punning (same IRI for class and individual) is not available cleanly in OML vocabularies.
- Domain physics in core CAMS vs `denied` vocabulary.  Pixel/FOV, jam RF, radar range are scenario-family specifics -- we want to keep them out of core to preserve reuse opportunity for other domains.

## Uncertainty

- Execution roll-up: SWRL marks an OPM Executing when any allocated Role's asset asserts `isExecuting` (existential). Universal "all roles checked in" is enforced in Python (`check_opm_role_checkin`), not in the reasoner.
- Editor vs reasoned graph: table editors bind asserted triples. Compact `requiresResource` and type tokens must be asserted to show in Platform; reified `ResourceRequirement` scalars alone do not fill that column until you also assert the forward need (or reasoner entailments are loaded -- which the compose editor does not assume).
- Coverage codes show satisfies / allocated / capability-able. They do not prove PoS thresholds, GSD/jam feasibility, or that candidate OPMs are in the `precedes` chain.

## Open issues

These are added for completeness for the assignment.  I think the ontology is very good, and I would hate for me pointing out very specific, in-the-weeds issues won't be counted against me.

- No World / PoS compose pattern; assessments and world facets are edited in raw OML or left as fixture data (this seems fine -- even sierra does this).
- Candidate OPMs on an Engagement are intentionally off the baseline `precedes` chain; method does not yet prescribe how planners promote a candidate into the serial plan. (again, this is fine; advanced mission planning concepts are what you build on top of this core ontology)
- ResourceTypeToken local names live in the description namespace (display names match class names); reviewers can confuse token vs class IRI. (see note above, mostly due to OML limitations; happy to brainstorm other options)
- Estimators were cloned per candidate OPM for clarity; whether sharing an estimator across OPMs should be forbidden is undecided. (this is a philosophical question about how success prediction works; reasonable minds may come up with different answers)

## Business rules (SHACL)

Enforced in pattern shapes (examples):

1. An OPM must contain at least one Role.
2. A Role must be allocated to exactly one Asset.
3. A Role belongs to exactly one OPM (`isContainedBy` exactly 1).
4. That Asset must be a member of the Team executing the EngagementPlan that contains the Role's OPM.
5. That Asset must provide every Capability required by the Role's Behavior.

Structural gates (Intent/Objective `isGatedBy`, Constraint has Conditions, etc.) are property shapes with `sh:message`s.

## Layout

```
src/method/md/example.com/cams/     # compose templates = notebook + SHACL
src/model/md/CAMS Denied/           # pages that invoke templates
src/model/oml/.../denied/project/
  description.oml                   # ABox module
  bundle.oml
```

I decided to put everything in same descriptipon as cross-links (i.e., Intent --> Objective --> OPM --> Asset --> Team) tend to be dense and splitting into multiple description IRIs adds `uses` cycles without improving usability very much, AFAICT.  Viewpoint separation is achieved via the compose patterns/pages.
