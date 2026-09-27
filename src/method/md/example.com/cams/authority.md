---
template:
  id: https://example.com/cams/authority
  name: "Authority (Intent & Gates)"
  rank: 10
  expose:
    - kind: compose
  params:
    - id: ontology
      type: iri
      defaultValue: ${context.ontology}
      required: true
---

# Authority

Commander intents and constraints.

## Focal types

| Type | Role |
|------|------|
| `cams:MissionCommander` | Expresses intents (read-only) |
| `cams:Intent` | Priority, constraints, spawned objectives |
| `cams:Constraint` | Conjunction of Conditions |
| `cams:Condition` | Atomic predicate vs evaluation context |

## Rules

- Intent must have exactly one Constraint.
- Constraint must comprise at least one Condition.
- Condition should carry a satisfaction status for monitoring.

```table-editor
---
columns: { this: { label: "Commander" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .

cams:MissionCommanderShape
    a sh:NodeShape ;
    sh:targetClass cams:MissionCommander ;
    dash:readOnly true ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path cams:expresses ;
        sh:name "Expresses Intent" ;
        sh:class cams:Intent ;
        dash:readOnly true ;
        sh:order 2 ;
    ] ;
    .
```

```table-editor
---
columns: { this: { label: "Intent" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .

cams:IntentShape
    a sh:NodeShape ;
    sh:targetClass cams:Intent ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path cams:priority ;
        sh:name "Priority" ;
        sh:datatype xsd:string ;
        sh:in ( "Low" "Medium" "High" ) ;
        sh:maxCount 1 ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path cams:isGatedBy ;
        sh:name "Spawn gate (Constraint)" ;
        sh:class cams:Constraint ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Intent must have exactly one Constraint." ;
        sh:order 3 ;
    ] ;
    sh:property [
        sh:path cams:spawns ;
        sh:name "Spawns Objective" ;
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

```table-editor
---
columns: { this: { label: "Constraint" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .

cams:ConstraintShape
    a sh:NodeShape ;
    sh:targetClass cams:Constraint ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path cams:comprisesCondition ;
        sh:name "Condition" ;
        sh:class cams:Condition ;
        sh:minCount 1 ;
        sh:message "Constraint must include at least one Condition." ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path cams:satisfactionStatus ;
        sh:name "Satisfaction" ;
        sh:datatype xsd:string ;
        sh:in ( "Satisfied" "Unsatisfied" ) ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Constraint must assert Satisfied or Unsatisfied." ;
        sh:order 3 ;
    ] ;
    .
```

```table-editor
---
columns: { this: { label: "Condition" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .

cams:ConditionShape
    a sh:NodeShape ;
    sh:targetClass cams:Condition ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path cams:satisfactionStatus ;
        sh:name "Satisfaction" ;
        sh:datatype xsd:string ;
        sh:in ( "Satisfied" "Unsatisfied" ) ;
        sh:maxCount 1 ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path cams:isEvaluatedAgainst ;
        sh:name "Evaluated against" ;
        sh:class cams:EvaluationContext ;
        sh:order 3 ;
    ] ;
    .
```
