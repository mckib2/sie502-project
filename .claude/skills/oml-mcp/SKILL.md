---
name: oml-mcp
description: 'Use when working with OML ontologies, models, validation, reasoning, containment, or SPARQL and the OML MCP tools are available. Prefer this skill before text search or direct file reads/writes for OML questions.'
---

# OML MCP Skill

Use this skill whenever interacting with OML ontologies in this workspace. All OML operations MUST use the OML MCP tools (`call_mcp_tool` with `ServerName: "oml"`).

## Workspace Context

- **Root Bundle Context**: `https://example.com/cams/denied/project/bundle` (use for `oml_workspace`, `oml_sparql`, and `oml_paths` for full import closure).
- **Target Description Ontology**: `https://example.com/cams/denied/project/description` (target for `createInstance`, `addAssertion`, and `oml_update`).
- **Core Vocabulary**: `https://example.com/cams/vocabulary#` (`cams`)
- **Denied Domain Vocabulary**: `https://example.com/cams/denied/vocabulary#` (`denied`)

## Execution Discipline

1. **MCP Tools First; No Shell Grep/Find Drift**:
   - Never use shell commands (`grep`, `find`, `cat`, or text-edit tools) to explore vocabularies or edit OML files.
   - Use `oml_shapes` to discover valid predicates, `oml_search`/`oml_about` to discover existing instances, and `oml_update` to write.
2. **Trust Results; Do Not Loop**:
   - Once a tool returns an answer, do not repeat it or query it with different syntax to "double check".
   - State the answer once retrieved.
3. **Strictly Single-Call Atomic Updates**:
   - Every update task must be executed in **one single atomic `oml_update` call**.
   - Bundle all `createInstance`, type assertions, required scalar properties, and relational cross-links in the `operations` array. Never split one logical change into sequential `oml_update` calls.

---

## Retrieve Context Workflow

The standard progression is: **search → about → (members or paths if needed) → sparql**.

**1. Search first (`oml_search`):**
Use short, specific keywords from the prompt (e.g. `"TeamAlpha"`, `"ObjInactiveLoiter"`, `"Strike"`).

**2. Learn about found members (`oml_about`):**
Pass all relevant IRIs in a single batch call. This reveals asserted/inferred predicates, types, and neighbors without writing SPARQL. Use `https://example.com/cams/denied/project/bundle` as the context.

**3. Discover Predicates & Paths (`oml_paths`, `oml_members`):**
- Use `oml_paths` to discover connection chains between source and target IRIs.
- Use `oml_members(ontology, kind)` to list all members of an ontology.

**4. Precise Queries with SPARQL (`oml_sparql`):**
Use `oml_sparql` only for filtered, aggregated, or multi-hop relationship checks. Always provide the root bundle `https://example.com/cams/denied/project/bundle` as the context parameter.

---

## Update Ontologies Workflow

Follow this strict 5-step sequence for every modification:

### 1. Retrieve Context & Inspect Shapes
- Identify existing instances and classes to link.
- Call `oml_shapes` on the class IRI of **every** instance type you plan to create or modify.
- **CRITICAL SHAPE AUDIT**: Scan the shape output for `sh:minCount >= 1`:
  - Every property with `sh:minCount >= 1` is **mandatory**. You MUST include an `addAssertion` for it in the creation call.
  - In CAMS, notable mandatory shape rules include:
    * `cams:OPM`: Must assert `cams:usesEstimator` pointing to a `cams:SuccessProbabilityEstimator` (e.g., `EstStrike`, `EstSearch`, `EstBravoSearch`), `cams:satisfies` (an Objective), and `cams:contains` (at least one Role).
    * `cams:Role`: Must assert `cams:allocatedTo` (Asset), `cams:realizesBehavior` (Behavior), and `cams:isContainedBy` (owning OPM).
    * `cams:Intent` / `cams:Objective`: Must assert `cams:isGatedBy` (exactly 1 Constraint).
    * `cams:Constraint`: Must assert `cams:comprisesCondition` (at least 1 Condition).
  - Extract the exact predicate IRIs from `sh:path`. Never invent or guess predicate IRIs.

### 2. Plan and Execute a Single Atomic `oml_update`
Structure all changes into a single `oml_update` call:
- Ordering inside the `operations` array:
  1. `createInstance` for all new entities.
  2. `addAssertion` asserting the `rdf:type` for each created instance.
  3. `addAssertion` / `addAnnotation` for all required scalars (`cams:name`, status values).
  4. `addAssertion` for all required relations (`cams:usesEstimator`, `cams:allocatedTo`, `cams:realizesBehavior`, etc.).
  5. `addAssertion` linking the new instances to existing container/parent entities (e.g. `TeamBravo cams:includesMember BravoStrike`, `EngagementBravo cams:contains OPM_BravoStrike`).

### 3. Verify Integrity in One Round-Trip
Immediately following a successful `oml_update`, verify the model:
- Call `oml_validate` with `{"only": true}` for SHACL validation.
- Call `oml_reason` with `{"only": true, "explanation": false}` for OWL DL consistency.

### 4. Deterministic Error Recovery (If Validation Fails)
If `oml_validate` reports a failing block:
- Read the failure message (e.g. `"property: Uses Estimator, message: OPM should use at least one success-probability estimator"`).
- **DO NOT** repeat `oml_validate` with alternate arguments.
- **DO NOT** execute shell commands (`oml validate`, `grep`).
- Immediately construct a single corrective `oml_update` that adds the missing assertion.
- Re-run `oml_validate` once to confirm resolution.
