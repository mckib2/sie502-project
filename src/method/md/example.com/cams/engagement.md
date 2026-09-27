---
template:
  id: https://example.com/cams/engagement
  name: "Engagement, OPMs, and Roles"
  rank: 30
  expose:
    - kind: compose
  params:
    - id: ontology
      type: iri
      defaultValue: ${context.ontology}
      required: true
---

# Engagement, OPMs & Roles

How a team realizes a mission: EngagementPlan contains OPMs; each OPM contains Roles (Behavior bound to Asset).  This is the "how" to the "what".

## Focal types

| Type | Role |
|------|------|
| `cams:EngagementPlan` | Realizes mission; executed by team |
| `cams:OPM` | Satisfies objective; contains roles; estimators |
| `cams:Role` | Exactly one Behavior and one Asset |

## Rules

- Engagement realizes exactly one Mission and is executed by exactly one Team.
- OPM must contain at least one Role and satisfy an Objective.
- Role must realize one Behavior and allocate to one Asset.
- Allocated Asset must be a member of the Engagement's executing Team.
- Asset must provide every Capability the Behavior requires.

```tree-editor
---
columns: { this: { label: "Plan element" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .

cams:EngagementPlanShape
    a sh:NodeShape ;
    sh:targetClass cams:EngagementPlan ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path cams:realizes ;
        sh:name "Realizes Mission" ;
        sh:class cams:MissionPlan ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "EngagementPlan must realize exactly one MissionPlan." ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path cams:isExecutedBy ;
        sh:name "Executed by Team" ;
        sh:class cams:Team ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "EngagementPlan must be executed by exactly one Team." ;
        sh:order 3 ;
    ] ;
    sh:property [
        sh:path cams:contains ;
        sh:name "Contains OPM" ;
        sh:class cams:OPM ;
        sh:minCount 1 ;
        sh:message "EngagementPlan should contain at least one OPM." ;
        sh:order 4 ;
    ] ;
    .

cams:OPMShape
    a sh:NodeShape ;
    sh:targetClass cams:OPM ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path cams:contains ;
        sh:name "Contains Role" ;
        sh:class cams:Role ;
        sh:minCount 1 ;
        sh:message "OPM must contain at least one Role (bind a Behavior to an Asset)." ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path cams:satisfies ;
        sh:name "Satisfies Objective" ;
        sh:class cams:Objective ;
        sh:minCount 1 ;
        sh:message "OPM must satisfy at least one Objective." ;
        sh:order 3 ;
    ] ;
    sh:property [
        sh:path cams:usesEstimator ;
        sh:name "Uses Estimator" ;
        sh:class cams:SuccessProbabilityEstimator ;
        sh:minCount 1 ;
        sh:message "OPM should use at least one success-probability estimator." ;
        sh:order 4 ;
    ] ;
    sh:property [
        sh:path cams:precedes ;
        sh:name "Precedes OPM" ;
        sh:class cams:OPM ;
        sh:order 5 ;
    ] ;
    .

cams:RoleShape
    a sh:NodeShape ;
    sh:targetClass cams:Role ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path cams:realizesBehavior ;
        sh:name "Behavior" ;
        sh:class cams:Behavior ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Role must realize exactly one Behavior." ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path cams:allocatedTo ;
        sh:name "Allocated Asset" ;
        sh:class cams:Asset ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Role must be allocated to exactly one Asset." ;
        sh:order 3 ;
    ] ;
    sh:property [
        sh:path cams:isContainedBy ;
        sh:name "Owning OPM" ;
        sh:class cams:OPM ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Role must belong to exactly one OPM (do not reuse a Role across OPMs)." ;
        sh:order 4 ;
    ] ;

    sh:sparql [
        sh:message "Allocated Asset is not a member of the Team executing this Role's EngagementPlan." ;
        sh:select """
            PREFIX cams: <https://example.com/cams/vocabulary#>
            SELECT $this WHERE {
                $this cams:allocatedTo ?asset .
                ?opm cams:contains $this .
                ?ep a cams:EngagementPlan ;
                    cams:contains ?opm ;
                    cams:isExecutedBy ?team .
                FILTER NOT EXISTS { ?team cams:includesMember ?asset }
            }
        """ ;
    ] ;

    sh:sparql [
        sh:message "Allocated Asset does not provide a Capability required by this Role's Behavior." ;
        sh:select """
            PREFIX cams: <https://example.com/cams/vocabulary#>
            SELECT $this WHERE {
                $this cams:allocatedTo ?asset ;
                      cams:realizesBehavior ?beh .
                ?beh cams:requiresCapability ?cap .
                FILTER NOT EXISTS { ?asset cams:providesCapability ?cap }
            }
        """ ;
    ] ;
    .
```
