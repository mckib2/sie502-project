---
ontology: https://example.com/cams/denied/project/description
---

# CAMS Analysis Dashboard

Methodology analysis layer evaluating collaborative autonomy models against core competence questions.

---

## 1. Methodology questions

### Q1. Does a set of ordered behaviors satisfy an Intent?

Active commander intents, spawned objectives, and assigned-team engagement OPMs/Roles in execution sequence.

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

Rows reflect active intent-to-objective decomposition and the chronological sequence of OPMs with their allocated platform assets.  Columns identify team assignments, next-objective transitions, and sequential predecessors along the plan.  Candidate OPMs that satisfy active objectives appear alongside the primary execution sequence as alternate branch plays.

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

Rows with status `covered` indicate objectives where the executing team's allocated assets provide all capabilities required by the OPM behaviors.  Rows flagged with `missing coverage` identify capability deficits where an assigned team composition cannot realize commander intent -- diagnosing a team composition or assignment gap in the mission plan rather than an ontology flaw.

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

Identifies orphaned or disconnected behavior definitions.  Empty results confirm full end-to-end traceability from asset capabilities through behaviors to commander intents.  Flagged rows highlight behaviors lacking required capabilities, unassigned behaviors, or behaviors with no path to an active intent.  Data interface message contracts (ICDs) are outside the model scope.

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

Verifies resource accessibility for allocated roles.  Each role resolves its resource requirements through asset ownership (`owns`) or peer sharing (`shares`).  An access status of `none` flags an unfulfilled requirement and indicates a plan feasibility gap.  Continuous physics calculations (such as sensor resolution or RF link budgets) are evaluated via external scripts.

---

### Q5. Can concurrent execution lead to resource contention?

#### Evidence

```table
---
stylesheet:
  - selector: cell[col === "availability"]
    style:
      color: "#c0392b"
      font-weight: bold
---
PREFIX cams: <https://example.com/cams/vocabulary#>


SELECT ?resource ?opm1 ?role1 ?asset1 ?opm2 ?role2 ?asset2 ?availability
WHERE {
  ?asset1 cams:isExecuting ?opm1 .
  ?asset2 cams:isExecuting ?opm2 .
  ?opm1 cams:contains ?role1 .
  ?opm2 cams:contains ?role2 .
  ?role1 cams:allocatedTo ?asset1 ;
         cams:realizesBehavior ?b1 .
  ?role2 cams:allocatedTo ?asset2 ;
         cams:realizesBehavior ?b2 .
  ?b1 cams:requiresResource ?resource .
  ?b2 cams:requiresResource ?resource .
  OPTIONAL { ?resource cams:availabilityStatus ?availability }
  FILTER(?role1 != ?role2)
  FILTER(STR(?role1) < STR(?role2))
}
ORDER BY ?resource ?role1 ?role2
```

#### Interpretation

Identifies concurrent resource contention where distinct executing roles demand the same physical resource.  An empty result confirms that active execution is free of contention.  The methodology models resource occupancy (marking resources Busy during execution), while dynamic time-slot scheduling and real-time preemption are platform runtime concerns outside the model.

---

### Q6. How does mission assessment monitor PoS and trigger contingency responses?

#### Evidence

```table
---
stylesheet:
  - selector: cell[col === "response"]
    style:
      font-weight: bold
---
PREFIX cams: <https://example.com/cams/vocabulary#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>


SELECT ?assessment ?composed ?response ?opm ?estimate ?prob ?objective ?threshold
WHERE {
  ?assessment a cams:MissionAssessment ;
              cams:monitors ?mission ;
              cams:composedSuccessProbability ?composed .
  OPTIONAL { ?assessment cams:triggers ?response }
  ?assessment cams:aggregates ?estimate .
  ?estimate cams:estimatedSuccessProbability ?prob .
  OPTIONAL {
    ?est cams:yields ?estimate .
    ?opm cams:usesEstimator ?est ;
         cams:satisfies ?objective .
    ?objective cams:activationStatus "Active" ;
               cams:successProbabilityThreshold ?threshold .
  }
}
ORDER BY ?assessment ?opm
```

#### Interpretation

Displays mission assessments, aggregated success probability estimates, and triggered automated responses.  Assessments whose composed probabilities satisfy objective thresholds trigger proactive replanning actions to adapt to newly spawned goals.  Assessments detecting threshold violations generate operational alerts (such as commander notices) addressed via reasoner rules.  Non-linear probability arithmetic is evaluated in the computed analysis layer below.

---

### Q7. Does the mission plan maintain sequential world-state continuity?

#### Evidence

```table
---
stylesheet:
  - selector: cell[col === "ok"][value === "chain-break"]
    style:
      color: "#c0392b"
      font-weight: bold
---
PREFIX cams: <https://example.com/cams/vocabulary#>


SELECT ?opm1 ?opm2 ?successor ?input ?ok
WHERE {
  ?opm1 a cams:OPM ;
        cams:precedes ?opm2 ;
        cams:predictsSuccessor ?successor .
  ?opm2 a cams:OPM .
  OPTIONAL { ?opm2 cams:startsFrom ?input }
  BIND(IF(BOUND(?input) && ?input = ?successor, "chain-ok", "chain-break") AS ?ok)
}
ORDER BY ?successor
```

#### Interpretation

Validates topological world-state continuity across chained plays.  A status of `chain-ok` confirms that the predicted successor state of a preceding OPM matches the starting state of the succeeding OPM.  SWRL rules can infer state continuity when omitted from assertions.  Continuous physical state estimation and sensor filtering remain outside the model.

---

### Q8. How do operational and environmental conditions gate Intent and Objective activation?

#### Evidence

```table
---
stylesheet:
  - selector: cell[col === "activation"][value === "Inactive"]
    style:
      color: "#c0392b"
      font-weight: bold
  - selector: cell[col === "condStatus"][value === "Unsatisfied"]
    style:
      color: "#c0392b"
---
PREFIX cams: <https://example.com/cams/vocabulary#>


SELECT ?owner ?ownerType ?constraint ?cStatus ?condition ?condStatus ?activation ?spawned
WHERE {
  {
    ?owner a cams:Intent ;
           cams:isGatedBy ?constraint ;
           cams:activationStatus ?activation .
    BIND("Intent" AS ?ownerType)
    OPTIONAL { ?owner cams:spawns ?spawned }
  }
  UNION
  {
    ?owner a cams:Objective ;
           cams:isGatedBy ?constraint ;
           cams:activationStatus ?activation .
    BIND("Objective" AS ?ownerType)
  }
  ?constraint cams:satisfactionStatus ?cStatus ;
              cams:comprisesCondition ?condition .
  ?condition cams:satisfactionStatus ?condStatus .
}
ORDER BY ?ownerType ?owner ?condition
```

#### Interpretation

Evaluates constraint conjunctions governing the activation of commander intents and mission objectives.  An intent or objective activates when all conjunct conditions are satisfied; any unsatisfied condition causes the constraint to fail, holding the element in an inactive state.  SWRL rules derive activation statuses automatically from condition satisfaction.  Temporal gate expiry and condition freshness monitoring are handled as operational processes.

---

## 2. Computed analysis -- PoS composition

Scripted parallel-then-serial Probability of Success evaluated across active engagement plans (`pos_inputs.sparql` via adapter).

```python
include('src/method/py/oml_adapter.py')

adapter = OmlQueryAdapter(query_executor=query, sparql_dir='src/method/sparql')
result = await adapter.execute('pos_inputs')
rows = result.get('rows', [])

# Group by engagement plan
by_ep = {}
for r in rows:
    ep = str(r.get('ep', '')).split('#')[-1] or "Plan"
    by_ep.setdefault(ep, []).append(r)

def card(title, value, sub, color):
    return f'''<div style="background:#fdfefe;border:1px solid #e1e8ed;border-left:5px solid {color};border-radius:6px;padding:14px 20px;flex:1;min-width:160px;">
      <div style="font-size:11px;text-transform:uppercase;color:#7f8c8d;font-weight:600;">{title}</div>
      <div style="font-size:28px;font-weight:bold;color:{color};margin-top:4px;">{value}</div>
      <div style="font-size:12px;color:#95a5a6;margin-top:2px;">{sub}</div>
    </div>'''

html_blocks = []
for ep, ep_rows in by_ep.items():
    thresholds = {}
    baseline_by_obj = {}
    all_by_obj = {}
    for r in ep_rows:
        obj = str(r.get('objective', '')).split('#')[-1]
        p = float(r.get('prob', 0))
        thr = float(r.get('threshold', 0))
        is_base = bool(r.get('isBaseline', False))
        thresholds[obj] = thr
        all_by_obj.setdefault(obj, []).append(p)
        if is_base:
            baseline_by_obj.setdefault(obj, []).append(p)

    def compose_pos(by_o):
        c = {}
        for o, probs in by_o.items():
            fail = 1.0
            for p in probs:
                fail *= (1.0 - p)
            c[o] = 1.0 - fail
        prod = 1.0
        for p in c.values():
            prod *= p
        return c, prod

    base_c, base_prod = compose_pos(baseline_by_obj)
    all_c, all_prod = compose_pos(all_by_obj)

    obj_cards = "".join(
        card(obj, f"{all_c[obj]:.3f}", f"threshold {thresholds[obj]:.2f} · {'MET' if all_c[obj] >= thresholds[obj] else 'UNMET'}",
             "#27ae60" if all_c[obj] >= thresholds[obj] else "#e74c3c")
        for obj in all_c
    )
    base_color = "#27ae60" if base_prod >= 0.7 else "#f39c12"
    all_color = "#27ae60" if all_prod >= 0.7 else "#f39c12"

    html_blocks.append(f'''<div style="margin-bottom:20px;">
      <h4 style="margin:8px 0;color:#2c3e50;">Engagement: {ep}</h4>
      <div style="display:flex;gap:16px;margin:12px 0;flex-wrap:wrap;">
        {obj_cards}
        {card("Baseline serial PoS", f"{base_prod:.3f}", "committed precedes chain", base_color) if base_c else ""}
        {card("Ensemble serial PoS", f"{all_prod:.3f}", "all candidate plays included", all_color)}
      </div>
    </div>''')

display("".join(html_blocks) +
    '<p style="color:#7f8c8d;font-size:13px;">Parallel within objective: 1−∏(1−p). Serial across active objectives per engagement plan. Baseline evaluates committed precedes-chain plays; ensemble includes alternate candidate plays.</p>')
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
