---
template:
  id: https://example.com/cams/platform
  name: "Platform (Team, Asset, Capability)"
  rank: 40
  expose:
    - kind: compose
  params:
    - id: ontology
      type: iri
      defaultValue: ${context.ontology}
      required: true
---

# Platform

Teams, assets, and capabilities that fill engagement Roles. Domain-specific resource physics (imaging/RF) are found in `denied`, as they are in-general not portable across autonomy implementations.

## Focal types

| Type | Role |
|------|------|
| `cams:Team` | Members and SA |
| `cams:Asset` | Capabilities, owned resources |
| `cams:Capability` | Catalog of abilities |
| `cams:Behavior` | Requires capabilities/resources (context) |

## Rules

- Team should list members used in engagements.
- Asset should provide at least one Capability when used in Roles.

```table-editor
---
columns: { this: { label: "Team" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .

cams:TeamShape
    a sh:NodeShape ;
    sh:targetClass cams:Team ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path cams:includesMember ;
        sh:name "Member Asset" ;
        sh:class cams:Asset ;
        sh:minCount 1 ;
        sh:message "Team should include at least one Asset member." ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path cams:maintainsSA ;
        sh:name "Situational Awareness" ;
        sh:class cams:SituationalAwareness ;
        sh:order 3 ;
    ] ;
    .
```

```table-editor
---
columns: { this: { label: "Asset" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .
@prefix denied: <https://example.com/cams/denied/vocabulary#> .

cams:AssetShape
    a sh:NodeShape ;
    sh:targetClass cams:Asset ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path denied:assetKind ;
        sh:name "Asset kind (domain)" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path cams:providesCapability ;
        sh:name "Provides Capability" ;
        sh:class cams:Capability ;
        sh:minCount 1 ;
        sh:message "Asset should provide at least one Capability for Role allocation." ;
        sh:order 3 ;
    ] ;
    sh:property [
        sh:path cams:ownsResource ;
        sh:name "Owns Resource" ;
        sh:class cams:Resource ;
        sh:order 4 ;
    ] ;
    sh:property [
        sh:path cams:isExecuting ;
        sh:name "Executing OPM" ;
        sh:class cams:OPM ;
        sh:maxCount 1 ;
        sh:order 5 ;
    ] ;
    .
```

```table-editor
---
columns: { this: { label: "Capability" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .

cams:CapabilityShape
    a sh:NodeShape ;
    sh:targetClass cams:Capability ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    .
```

```table-editor
---
columns: { this: { label: "Behavior" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .

cams:BehaviorShape
    a sh:NodeShape ;
    sh:targetClass cams:Behavior ;
    dash:readOnly true ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path cams:requiresCapability ;
        sh:name "Requires Capability" ;
        sh:class cams:Capability ;
        dash:readOnly true ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path cams:requiresResource ;
        sh:name "Requires Resource" ;
        sh:class cams:Resource ;
        dash:readOnly true ;
        sh:order 3 ;
    ] ;
    .
```
