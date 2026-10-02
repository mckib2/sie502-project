---
template:
  id: https://example.com/cams/analysis-bundle
  name: "CAMS Analysis Bundle (orphans + OPM graph)"
  rank: 60
  expose:
    - kind: compose
  params:
    - id: ontology
      type: iri
      defaultValue: ${context.ontology}
      required: true
---

# Analysis bundle

Gap detection and baseline OPM sequence view.

## Orphan / missing relationships

### Authority

```table
---
stylesheet:
  - selector: cell[col === "impact"]
    style:
      color: "#c0392b"
      font-weight: bold
---
PREFIX cams: <https://example.com/cams/vocabulary#>

# Authority orphans: Intent without gate; Constraint without Conditions

SELECT ?element ?kind ?impact
WHERE {
  {
    ?element a cams:Intent .
    FILTER NOT EXISTS { ?element cams:isGatedBy ?c }
    BIND("Intent" AS ?kind)
    BIND("Intent has no spawn/activation Constraint" AS ?impact)
  }
  UNION
  {
    ?element a cams:Constraint .
    FILTER NOT EXISTS { ?element cams:comprisesCondition ?cond }
    BIND("Constraint" AS ?kind)
    BIND("Constraint has zero Conditions (empty conjunction)" AS ?impact)
  }
}
ORDER BY ?kind ?element
```

### Mission

```table
---
stylesheet:
  - selector: cell[col === "impact"]
    style:
      color: "#c0392b"
      font-weight: bold
---
PREFIX cams: <https://example.com/cams/vocabulary#>

# Mission orphans: Objective not on any MissionPlan; Active Objective with no spawn Intent

SELECT ?element ?kind ?impact
WHERE {
  {
    ?element a cams:Objective .
    FILTER NOT EXISTS { ?mission cams:includesObjective ?element }
    BIND("Objective" AS ?kind)
    BIND("Objective not included on any MissionPlan" AS ?impact)
  }
  UNION
  {
    ?element a cams:Objective ;
             cams:activationStatus "Active" .
    FILTER NOT EXISTS { ?intent cams:spawns ?element }
    BIND("Objective" AS ?kind)
    BIND("Active Objective has no spawning Intent" AS ?impact)
  }
}
ORDER BY ?kind ?element
```

### Engagement

```table
---
stylesheet:
  - selector: cell[col === "impact"]
    style:
      color: "#c0392b"
      font-weight: bold
---
PREFIX cams: <https://example.com/cams/vocabulary#>

# Engagement orphans: Role not in OPM; OPM not in Engagement; Behavior never realized

SELECT ?element ?kind ?impact
WHERE {
  {
    ?element a cams:Role .
    FILTER NOT EXISTS { ?opm a cams:OPM ; cams:contains ?element }
    BIND("Role" AS ?kind)
    BIND("Role not contained by any OPM" AS ?impact)
  }
  UNION
  {
    ?element a cams:OPM .
    FILTER NOT EXISTS { ?ep a cams:EngagementPlan ; cams:contains ?element }
    BIND("OPM" AS ?kind)
    BIND("OPM not contained by any EngagementPlan" AS ?impact)
  }
  UNION
  {
    ?element a cams:Behavior .
    FILTER NOT EXISTS { ?role cams:realizesBehavior ?element }
    BIND("Behavior" AS ?kind)
    BIND("No Role realizes this Behavior (unused catalog entry)" AS ?impact)
  }
}
ORDER BY ?kind ?element
```

### Platform

```table
---
stylesheet:
  - selector: cell[col === "impact"]
    style:
      color: "#c0392b"
      font-weight: bold
---
PREFIX cams: <https://example.com/cams/vocabulary#>

# Platform orphans: Capability never provided; non-token Resource never owned; Asset not on Team

SELECT ?element ?kind ?impact
WHERE {
  {
    ?element a cams:Capability .
    FILTER NOT EXISTS { ?asset cams:providesCapability ?element }
    BIND("Capability" AS ?kind)
    BIND("Capability never provided by any Asset" AS ?impact)
  }
  UNION
  {
    ?element a cams:Resource .
    FILTER NOT EXISTS { ?element a cams:ResourceTypeToken }
    FILTER NOT EXISTS { ?asset cams:ownsResource ?element }
    BIND("Resource" AS ?kind)
    BIND("Resource never owned by any Asset" AS ?impact)
  }
  UNION
  {
    ?element a cams:Asset .
    FILTER NOT EXISTS { ?team cams:includesMember ?element }
    BIND("Asset" AS ?kind)
    BIND("Asset is not a member of any Team" AS ?impact)
  }
}
ORDER BY ?kind ?element
```

### Coverage

```table
---
stylesheet:
  - selector: cell[col === "impact"]
    style:
      color: "#c0392b"
      font-weight: bold
---
PREFIX cams: <https://example.com/cams/vocabulary#>

# Coverage orphans: Active Objective with no OPM that satisfies it on any Engagement

SELECT ?element ?kind ?impact
WHERE {
  ?element a cams:Objective ;
           cams:activationStatus "Active" .
  FILTER NOT EXISTS {
    ?opm a cams:OPM ;
         cams:satisfies ?element .
    ?ep a cams:EngagementPlan ;
        cams:contains ?opm .
  }
  BIND("Objective" AS ?kind)
  BIND("Active Objective has no satisfying OPM on any Engagement" AS ?impact)
}
ORDER BY ?element
```

## Baseline OPM precedes graph

```graph
---
layout:
  mode: force
  running: true
  fit: true
  padding: 24
stylesheet:
  - selector: node
    style:
      fill: "#2980b9"
      stroke: "#1a5276"
      color: white
---
PREFIX cams: <https://example.com/cams/vocabulary#>

# Graph: OPM precedes chain (baseline serial plan)

CONSTRUCT {
  ?opm cams:precedes ?next .
  ?opm a cams:OPM .
  ?next a cams:OPM .
}
WHERE {
  ?opm a cams:OPM ;
       cams:precedes ?next .
}
```
