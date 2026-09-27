---
template:
  id: https://example.com/cams/coverage
  name: "Coverage (Objectives x OPMs x Assets)"
  rank: 50
  expose:
    - kind: compose
  params:
    - id: ontology
      type: iri
      defaultValue: ${context.ontology}
      required: true
---

# Coverage

Which OPMs satisfy which Objectives, and which Assets are allocated vs "capability-able" for those OPMs.

## How to read

| Matrix | Meaning |
|--------|---------|
| Objectives x OPMs | `1` = OPM `satisfies` that Objective; `0` = no |
| OPMs x Assets | `2` = some Role on the OPM is `allocatedTo` that Asset; `1` = Asset provides every Capability required by some Role's Behavior on the OPM but is not allocated; `0` = neither |

Notes: create Assets / Imaging or Radar sensors / Capabilities / Behaviors on the Platform view; create OPMs / Roles / estimators on Engagement view.

### Objectives x OPMs

Which candidate plays satisfy each objective (`1` = satisfies).

```matrix
---
rowColumnLabel: Objective / OPM
stylesheet:
  - selector: cell [Number(value) > 0]
    style:
      background-color: lightgreen
---
PREFIX cams: <https://example.com/cams/vocabulary#>

SELECT ?row ?column (COALESCE(?n, 0) AS ?value)
WHERE {
  ?row a cams:Objective .
  ?column a cams:OPM .

  OPTIONAL {
    SELECT ?row ?column (COUNT(*) AS ?n)
    WHERE {
      ?column cams:satisfies ?row .
    }
    GROUP BY ?row ?column
  }
}
ORDER BY ?row ?column
```

### OPMs x Assets

Allocated (`2`) vs capability-able but not allocated (`1`).

```matrix
---
rowColumnLabel: OPM / Asset
stylesheet:
  - selector: cell [Number(value) = 2]
    style:
      background-color: "#5cb85c"
  - selector: cell [Number(value) = 1]
    style:
      background-color: "#d9edf7"
---
PREFIX cams: <https://example.com/cams/vocabulary#>

SELECT ?row ?column (COALESCE(?n, 0) AS ?value)
WHERE {
  ?row a cams:OPM .
  ?column a cams:Asset .

  OPTIONAL {
    SELECT ?row ?column (MAX(?score) AS ?n)
    WHERE {
      {
        ?row cams:contains ?role .
        ?role cams:allocatedTo ?column .
        BIND(2 AS ?score)
      }
      UNION
      {
        ?row cams:contains ?role .
        ?role cams:realizesBehavior ?beh .
        FILTER NOT EXISTS { ?role cams:allocatedTo ?column }
        FILTER EXISTS { ?beh cams:requiresCapability ?anyCap }
        FILTER NOT EXISTS {
          ?beh cams:requiresCapability ?cap .
          FILTER NOT EXISTS { ?column cams:providesCapability ?cap }
        }
        BIND(1 AS ?score)
      }
    }
    GROUP BY ?row ?column
  }
}
ORDER BY ?row ?column
```
