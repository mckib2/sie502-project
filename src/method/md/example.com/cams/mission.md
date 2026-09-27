---
template:
  id: https://example.com/cams/mission
  name: "Mission & Objectives"
  rank: 20
  expose:
    - kind: compose
  params:
    - id: ontology
      type: iri
      defaultValue: ${context.ontology}
      required: true
---

# Mission & Objectives

What the mission aims to achieve.  Note, this is "what", importantly not "how".

## Focal types

| Type | Role |
|------|------|
| `cams:MissionPlan` | Intents, objectives, assigned team |
| `cams:Objective` | Threshold, activation conditions, precedence |

## Rules

- Mission must include at least one Intent.
- Objective must have exactly one Constraint.
- Mission may assign at most one Team.

```table-editor
---
columns: { this: { label: "Mission" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .

cams:MissionPlanShape
    a sh:NodeShape ;
    sh:targetClass cams:MissionPlan ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path cams:includesIntent ;
        sh:name "Includes Intent" ;
        sh:class cams:Intent ;
        sh:minCount 1 ;
        sh:message "MissionPlan must include at least one Intent." ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path cams:includesObjective ;
        sh:name "Includes Objective" ;
        sh:class cams:Objective ;
        sh:order 3 ;
    ] ;
    sh:property [
        sh:path cams:assignedTo ;
        sh:name "Assigned Team" ;
        sh:class cams:Team ;
        sh:maxCount 1 ;
        sh:message "MissionPlan may be assigned to at most one Team." ;
        sh:order 4 ;
    ] ;
    .
```

```table-editor
---
columns: { this: { label: "Objective" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .

cams:ObjectiveShape
    a sh:NodeShape ;
    sh:targetClass cams:Objective ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path cams:successProbabilityThreshold ;
        sh:name "PoS threshold" ;
        sh:datatype xsd:decimal ;
        sh:maxCount 1 ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path cams:isGatedBy ;
        sh:name "Activation gate (Constraint)" ;
        sh:class cams:Constraint ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Objective must have exactly one Constraint." ;
        sh:order 3 ;
    ] ;
    sh:property [
        sh:path cams:precedes ;
        sh:name "Precedes" ;
        sh:class cams:Objective ;
        sh:order 4 ;
    ] ;
    sh:property [
        sh:path cams:activationStatus ;
        sh:name "Activation" ;
        sh:datatype xsd:string ;
        dash:readOnly true ;
        sh:maxCount 1 ;
        sh:order 5 ;
    ] ;
    .
```
