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
| `cams:Behavior` | Requires capabilities/resources |
| `cams:ResourceTypeToken` | Class-level needs in Requires Resource (e.g. ImagingSensorResource) |
| `cams:ResourceRequirement` | Reified Behavior-->Resource need (+ denied scalars) |
| `cams:ImagingSensorResource` | EO/IR; pixel/FOV |
| `cams:RadarSensorResource` | Radar; range/frequency |

## Rules

- Team should list members used in engagements.
- Asset should provide at least one Capability when used in Roles.

### Teams

Collaborative groups: member assets and shared SA.

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

### Assets

Platforms that provide capabilities, own resources, and may execute an OPM.

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

### Capabilities

Catalog of abilities assets can provide.

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

### Behaviors

Plays that Roles realize. "Requires Resource" accepts a specific pod (e.g. SensorEOIR) or a type token named like the class (e.g. ImagingSensorResource, SensorResource). Use "Resource requirements" for denied standoff/GSD/jam sizing.

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
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path cams:requiresResource ;
        sh:name "Requires Resource" ;
        sh:class cams:Resource ;
        sh:order 3 ;
    ] ;
    .
```

### Imaging sensors

EO/IR pods: name plus horizontal pixels and FOV.

```table-editor
---
columns: { this: { label: "Imaging sensor" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .
@prefix denied: <https://example.com/cams/denied/vocabulary#> .

cams:ImagingSensorResourceShape
    a sh:NodeShape ;
    sh:targetClass cams:ImagingSensorResource ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Imaging sensor should have a name (e.g. EO/IR pod)." ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path denied:horizontalPixelCount ;
        sh:name "Horizontal pixels" ;
        sh:datatype xsd:integer ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Imaging sensor needs horizontalPixelCount for GSD checks." ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path denied:horizontalFOVDegrees ;
        sh:name "Horizontal FOV (deg)" ;
        sh:datatype xsd:decimal ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Imaging sensor needs horizontalFOVDegrees for GSD checks." ;
        sh:order 3 ;
    ] ;
    .
```

### Radar sensors

Radars: name, max detection range, and operating frequency.

```table-editor
---
columns: { this: { label: "Radar sensor" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix cams: <https://example.com/cams/vocabulary#> .
@prefix denied: <https://example.com/cams/denied/vocabulary#> .

cams:RadarSensorResourceShape
    a sh:NodeShape ;
    sh:targetClass cams:RadarSensorResource ;
    sh:property [
        sh:path cams:name ;
        sh:name "Name" ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Radar sensor should have a name." ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path denied:maxDetectionRangeMeters ;
        sh:name "Max detection range (m)" ;
        sh:datatype xsd:decimal ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "Radar sensor should assert maxDetectionRangeMeters." ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path denied:operatingFrequencyHz ;
        sh:name "Operating frequency (Hz)" ;
        sh:datatype xsd:decimal ;
        sh:maxCount 1 ;
        sh:order 3 ;
    ] ;
    .
```

### Resource requirements

Reified Behavior-->Resource links with denied standoff / GSD / jam sizing. These also appear under Behavior "Requires Resource" via the path union.

```table-editor
---
columns: { this: { label: "Resource requirement" } }
---
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix dash: <http://datashapes.org/dash#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix oml: <http://opencaesar.io/oml#> .
@prefix cams: <https://example.com/cams/vocabulary#> .
@prefix denied: <https://example.com/cams/denied/vocabulary#> .

cams:ResourceRequirementShape
    a sh:NodeShape ;
    sh:targetClass cams:ResourceRequirement ;
    sh:property [
        sh:path oml:hasSource ;
        sh:name "Behavior" ;
        sh:class cams:Behavior ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "ResourceRequirement must link from a Behavior." ;
        sh:order 1 ;
    ] ;
    sh:property [
        sh:path oml:hasTarget ;
        sh:name "Resource" ;
        sh:class cams:Resource ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:message "ResourceRequirement must link to a Resource." ;
        sh:order 2 ;
    ] ;
    sh:property [
        sh:path denied:expectedStandoffMeters ;
        sh:name "Expected standoff (m)" ;
        sh:datatype xsd:decimal ;
        sh:maxCount 1 ;
        sh:order 3 ;
    ] ;
    sh:property [
        sh:path denied:maxGroundSampleDistanceMeters ;
        sh:name "Max GSD (m/pixel)" ;
        sh:datatype xsd:decimal ;
        sh:maxCount 1 ;
        sh:order 4 ;
    ] ;
    sh:property [
        sh:path denied:minTransmitPowerWatts ;
        sh:name "Min transmit power (W)" ;
        sh:datatype xsd:decimal ;
        sh:maxCount 1 ;
        sh:order 5 ;
    ] ;
    sh:property [
        sh:path denied:countersThreat ;
        sh:name "Counters Threat" ;
        sh:class cams:Threat ;
        sh:maxCount 1 ;
        sh:order 6 ;
    ] ;
    .
```
