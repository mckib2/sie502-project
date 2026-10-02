---
ontology: https://example.com/cams/denied/project/description
---

# CAMS Analysis Dashboard

Analysis layer over the denied scenario.

---

## 1. Methodology questions

### Q1. Does a set of ordered behaviors satisfy an Intent?

Active Intents --> Active Objectives --> assigned-team Engagement OPMs/Roles (with `precedes` sequence).

#### Evidence

```table
PREFIX cams: <https://example.com/cams/vocabulary#>

SELECT ?intent ?objective ?opm ?role ?asset ?team ?nextObjective ?nextOpm
       (COUNT(DISTINCT ?predOpm) AS ?seq)
WHERE {
  ?intent a cams:Intent ;
          cams:activationStatus "Active" ;
          cams:spawns ?objective .
  ?objective cams:activationStatus "Active" .
  ?mission cams:includesIntent ?intent ;
           cams:includesObjective ?objective ;
           cams:assignedTo ?team .
  ?ep cams:realizes ?mission ;
      cams:isExecutedBy ?team ;
      cams:contains ?opm .
  ?opm cams:satisfies ?objective ;
       cams:contains ?role .
  ?role cams:allocatedTo ?asset .
  OPTIONAL { ?objective cams:precedes ?nextObjective }
  OPTIONAL { ?opm cams:precedes ?nextOpm }
  OPTIONAL { ?predOpm cams:precedes+ ?opm }
}
GROUP BY ?intent ?objective ?opm ?role ?asset ?team ?nextObjective ?nextOpm
ORDER BY ?seq ?intent ?role
```

#### Interpretation

Rows show Alpha's Active Search / Strike / BDA chain with Roles filled.  Candidate OPMs (wide search, radar, strike solo) also appear when they satisfy Active Objectives on EngagementAlpha.  These are alternate plays.

---

### Q2. Is team composition sufficient for all commander Intents?

#### Evidence

```table
---
stylesheet:
  - selector: cell[col === "status"][value === "missing coverage"]
    style:
      color: "#c0392b"
      font-weight: bold
---
PREFIX cams: <https://example.com/cams/vocabulary#>

SELECT ?mission ?team ?objective ?status ?opm ?role ?asset ?capability
WHERE {
  {
    ?mission a cams:MissionPlan ;
             cams:assignedTo ?team ;
             cams:includesObjective ?objective .
    ?objective cams:activationStatus "Active" .
    ?ep cams:realizes ?mission ;
        cams:isExecutedBy ?team ;
        cams:contains ?opm .
    ?opm cams:satisfies ?objective ;
         cams:contains ?role .
    ?role cams:allocatedTo ?asset ;
          cams:realizesBehavior ?behavior .
    ?behavior cams:requiresCapability ?capability .
    ?asset cams:providesCapability ?capability .
    BIND("covered" AS ?status)
  }
  UNION
  {
    ?mission a cams:MissionPlan ;
             cams:includesObjective ?objective .
    ?objective cams:activationStatus "Active" .
    ?epB cams:realizes ?mission ;
         cams:isExecutedBy ?team .
    FILTER NOT EXISTS {
      ?epB cams:contains ?opmB .
      ?opmB cams:satisfies ?objective ;
            cams:contains ?roleB .
      ?roleB cams:allocatedTo ?assetB ;
             cams:realizesBehavior ?behaviorB .
      ?behaviorB cams:requiresCapability ?capabilityB .
      ?assetB cams:providesCapability ?capabilityB .
    }
    BIND("missing coverage" AS ?status)
  }
}
ORDER BY ?team ?objective ?status
```

#### Interpretation

TeamAlpha covers Active Search/Strike/BDA. TeamBravo shows missing coverage for Strike and BDA -- diagnosed gap in team composition / process (Bravo is recon-only), not a vocabulary deficiency.

---

### Q3. Do all behaviors have mappings for platforms and Intents?

#### Evidence

```table
---
stylesheet:
  - selector: cell[col === "problem"]
    style:
      color: "#c0392b"
      font-weight: bold
---
PREFIX cams: <https://example.com/cams/vocabulary#>

SELECT ?behavior ?problem
WHERE {
  ?behavior a cams:Behavior .
  {
    FILTER NOT EXISTS { ?behavior cams:requiresCapability ?cap }
    BIND("missing requiresCapability" AS ?problem)
  }
  UNION
  {
    FILTER NOT EXISTS { ?role cams:realizesBehavior ?behavior }
    BIND("no Role realizes behavior" AS ?problem)
  }
  UNION
  {
    ?role cams:realizesBehavior ?behavior .
    FILTER NOT EXISTS { ?role cams:allocatedTo ?asset }
    BIND("Role missing allocatedTo" AS ?problem)
  }
  UNION
  {
    ?role cams:realizesBehavior ?behavior .
    ?opm cams:contains ?role .
    FILTER NOT EXISTS {
      ?opm cams:satisfies ?obj .
      ?obj cams:isSpawnedBy ?intent .
    }
    FILTER NOT EXISTS {
      ?opm cams:satisfies ?obj2 .
      ?plan cams:includesObjective ?obj2 ;
           cams:includesIntent ?intent2 .
    }
    BIND("no path to Intent" AS ?problem)
  }
}
ORDER BY ?behavior ?problem
```

#### Interpretation

Behaviors on allocated Roles should have capability + Intent path. Behavior data ICDs contracts are not currently concerns of this CAMS model.

---

### Q4. Is the mission plan feasible for resource requirements?

#### Evidence

```table
PREFIX cams: <https://example.com/cams/vocabulary#>
PREFIX denied: <https://example.com/cams/denied/vocabulary#>
PREFIX oml: <http://opencaesar.io/oml#>

SELECT ?opm ?role ?behavior ?need ?resource ?asset ?access ?standoffM ?maxGsdM ?pixels ?fovDeg
WHERE {
  ?opm a cams:OPM ;
       cams:contains ?role .
  ?role cams:realizesBehavior ?behavior ;
        cams:allocatedTo ?asset .
  {
    ?behavior cams:requiresResource ?need .
    FILTER NOT EXISTS { ?need a cams:ResourceTypeToken }
    BIND(?need AS ?resource)
  }
  UNION
  {
    ?behavior cams:requiresResource ?need .
    ?need a cams:ResourceTypeToken .
    ?asset cams:ownsResource|cams:sharesResource ?resource .
    FILTER(?resource != ?need)
    FILTER(
      (EXISTS { ?need a cams:SensorResourceToken } && EXISTS { ?resource a cams:SensorResource }) ||
      (EXISTS { ?need a cams:ImagingSensorResourceToken } && EXISTS { ?resource a cams:ImagingSensorResource }) ||
      (EXISTS { ?need a cams:RadarSensorResourceToken } && EXISTS { ?resource a cams:RadarSensorResource }) ||
      (EXISTS { ?need a cams:ComputeResourceToken } && EXISTS { ?resource a cams:ComputeResource }) ||
      (EXISTS { ?need a cams:CommResourceToken } && EXISTS { ?resource a cams:CommResource })
    )
  }
  OPTIONAL { ?asset cams:ownsResource ?resource . BIND(true AS ?owns) }
  OPTIONAL { ?asset cams:sharesResource ?resource . BIND(true AS ?shares) }
  BIND(
    IF(BOUND(?owns), "owns",
      IF(BOUND(?shares), "shares", "none")) AS ?access
  )
  OPTIONAL {
    ?req a cams:ResourceRequirement ;
         oml:hasSource ?behavior ;
         oml:hasTarget ?resource .
    OPTIONAL { ?req denied:expectedStandoffMeters ?standoffM }
    OPTIONAL { ?req denied:maxGroundSampleDistanceMeters ?maxGsdM }
  }
  OPTIONAL { ?resource denied:horizontalPixelCount ?pixels }
  OPTIONAL { ?resource denied:horizontalFOVDegrees ?fovDeg }
}
ORDER BY ?opm ?role ?need ?resource
```

#### Interpretation

Allocated Roles resolve specific resources or type tokens (`owns` / `shares`). Access `none` would be a feasibility gap. Imaging GSD / jam RF math are scripted in `evaluate_queries.py`.

---

## 2. Computed analysis -- PoS composition

Scripted parallel-then-serial Probability of Success over EngagementAlpha Active objectives (`pos_inputs.sparql` via adapter).

```python
include('src/method/py/oml_adapter.py')

adapter = OmlQueryAdapter(query_executor=query, sparql_dir='src/method/sparql')
result = await adapter.execute('pos_inputs')
rows = result.get('rows', [])

by_obj = {}
thresholds = {}
for r in rows:
    obj = str(r.get('objective', '')).split('#')[-1]
    opm = str(r.get('opm', '')).split('#')[-1]
    p = float(r.get('prob', 0))
    thr = float(r.get('threshold', 0))
    by_obj.setdefault(obj, []).append((opm, p))
    thresholds[obj] = thr

composed = {}
for obj, pairs in by_obj.items():
    fail = 1.0
    for _opm, p in pairs:
        fail *= (1.0 - p)
    composed[obj] = 1.0 - fail

mission_p = 1.0
for p in composed.values():
    mission_p *= p

def card(title, value, sub, color):
    return f'''<div style="background:#fdfefe;border:1px solid #e1e8ed;border-left:5px solid {color};border-radius:6px;padding:14px 20px;flex:1;min-width:160px;">
      <div style="font-size:11px;text-transform:uppercase;color:#7f8c8d;font-weight:600;">{title}</div>
      <div style="font-size:28px;font-weight:bold;color:{color};margin-top:4px;">{value}</div>
      <div style="font-size:12px;color:#95a5a6;margin-top:2px;">{sub}</div>
    </div>'''

obj_cards = "".join(
    card(obj, f"{composed[obj]:.3f}", f"threshold {thresholds[obj]:.2f} · {'MET' if composed[obj] >= thresholds[obj] else 'UNMET'}",
         "#27ae60" if composed[obj] >= thresholds[obj] else "#e74c3c")
    for obj in composed
)
mission_color = "#27ae60" if mission_p >= 0.7 else "#f39c12"
display(f'''<div style="display:flex;gap:16px;margin:16px 0;flex-wrap:wrap;">
{obj_cards}
{card("Mission serial PoS", f"{mission_p:.3f}", "product of per-objective parallel PoS", mission_color)}
</div>
<p style="color:#7f8c8d;font-size:13px;">Parallel within objective: 1−∏(1−p). Serial across Active objectives on EngagementAlpha. Candidate OPMs with estimates are included when they satisfy those objectives.</p>''')
```

---

## 3. Fit and structure (three view types)

### Matrix -- Objectives x OPMs / OPMs x Assets

```compose
template: https://example.com/cams/coverage
```

### Table + graph -- orphans and baseline precedes

```compose
template: https://example.com/cams/analysis-bundle
```
