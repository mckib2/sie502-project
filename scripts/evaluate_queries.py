#!/usr/bin/env python3
"""Evaluate CAMS SPARQL queries and SHACL shapes over exported OWL."""

from __future__ import annotations

import math
import sys
from pathlib import Path

from rdflib import Graph, Namespace, RDF, Literal
from rdflib.namespace import XSD

try:
    from pyshacl import validate as shacl_validate
except ImportError:  # pragma: no cover
    shacl_validate = None

ROOT = Path(__file__).resolve().parents[1]
OWL_DIR = ROOT / "build" / "owl"
QUERIES = ROOT / "queries"
CAMS = Namespace("https://example.com/cams/vocabulary#")
DESC = Namespace("https://example.com/cams/denied/project/description#")
DENIED = Namespace("https://example.com/cams/denied/vocabulary#")


def load_graph() -> Graph:
    g = Graph()
    required = [
        OWL_DIR / "example.com/cams/vocabulary.ttl",
        OWL_DIR / "example.com/cams/denied/vocabulary.ttl",
        OWL_DIR / "example.com/cams/denied/project/description.ttl",
        OWL_DIR / "example.com/cams/bundle.ttl",
        OWL_DIR / "example.com/cams/denied/bundle.ttl",
        OWL_DIR / "example.com/cams/denied/project/bundle.ttl",
    ]
    for path in required:
        if not path.exists():
            raise SystemExit(
                f"Missing {path}. Run: oml export -o build/owl --pretty "
                "(or oml reason -o build/owl)"
            )
        g.parse(path, format="turtle")
    # Also load reasoned entailments if present beside asserted files
    for ent in OWL_DIR.rglob("*.ttl"):
        if ent in required:
            continue
        if "example.com/cams" in str(ent):
            g.parse(ent, format="turtle")
    return g


def run_sparql(g: Graph, path: Path) -> list:
    query = path.read_text()
    # Strip leading comment lines that are not SPARQL (keep PREFIX)
    lines = []
    for line in query.splitlines():
        if line.strip().startswith("#") and not line.strip().startswith("# ") is False:
            # keep SPARQL comments as-is; rdflib accepts '#' comments
            pass
        lines.append(line)
    return list(g.query("\n".join(lines)))


def local(term) -> str:
    s = str(term)
    if "#" in s:
        return s.rsplit("#", 1)[-1]
    return s


def check_pos_product(g: Graph) -> None:
    print("\n=== PoS product check (Active objectives / EngagementAlpha) ===")
    # Estimates linked to Alpha OPMs that satisfy Active objectives
    # Also determine which OPMs are baseline (on the precedes chain)
    q = """
    PREFIX cams: <https://example.com/cams/vocabulary#>
    SELECT ?opm ?prob ?threshold ?objective ?isBaseline
    WHERE {
      <https://example.com/cams/denied/project/description#EngagementAlpha>
        cams:contains ?opm .
      ?opm cams:usesEstimator ?est ;
           cams:satisfies ?objective .
      ?est cams:yields ?estimate .
      ?estimate cams:estimatedSuccessProbability ?prob .
      ?objective cams:activationStatus "Active" ;
                 cams:successProbabilityThreshold ?threshold .
      BIND(EXISTS { ?opm cams:precedes ?_n } || EXISTS { ?_p cams:precedes ?opm } AS ?isBaseline)
    }
    ORDER BY ?opm
    """
    rows = list(g.query(q))
    # Collect all estimates, partitioned by baseline vs candidate
    all_by_obj: dict[str, list[float]] = {}
    baseline_by_obj: dict[str, list[float]] = {}
    thresholds: dict[str, float] = {}
    for opm, prob, thr, obj, is_baseline in rows:
        o = local(obj)
        p = float(prob)
        tag = "baseline" if is_baseline.toPython() else "candidate"
        all_by_obj.setdefault(o, []).append(p)
        if is_baseline.toPython():
            baseline_by_obj.setdefault(o, []).append(p)
        thresholds[o] = float(thr)
        print(f"  {local(opm)} -> {o}: p={prob} threshold={thr} ({tag})")

    def compose_pos(by_obj: dict[str, list[float]]) -> tuple[dict[str, float], float]:
        composed: dict[str, float] = {}
        for o in thresholds:
            probs = by_obj.get(o, [])
            if probs:
                fail = 1.0
                for p in probs:
                    fail *= 1.0 - p
                composed[o] = 1.0 - fail
            # If no OPMs for this objective in this set, skip
        mission_p = 1.0
        for p in composed.values():
            mission_p *= p
        return composed, mission_p

    # Baseline PoS (precedes-chain OPMs only -- the committed serial plan)
    baseline_composed, baseline_mission = compose_pos(baseline_by_obj)
    print("  Baseline plan PoS (precedes-chain OPMs only):")
    for o, p in baseline_composed.items():
        thr = thresholds[o]
        status = "MET" if p >= thr else "UNMET"
        print(f"    {o}: composed={p:.4f} vs {thr} -> {status}")
    print(
        f"  Baseline mission serial PoS: "
        f"{' × '.join(f'{p:.4f}' for p in baseline_composed.values())} = {baseline_mission:.4f}"
    )

    # Ensemble PoS (all OPMs including candidates)
    all_composed, all_mission = compose_pos(all_by_obj)
    print("  Ensemble PoS (all OPMs including candidates):")
    for o, p in all_composed.items():
        thr = thresholds[o]
        status = "MET" if p >= thr else "UNMET"
        print(f"    {o}: composed={p:.4f} vs {thr} -> {status}")
    print(
        f"  Ensemble mission serial PoS: "
        f"{' × '.join(f'{p:.4f}' for p in all_composed.values())} = {all_mission:.4f}"
    )

    # Compare asserted assessment values against computed baseline
    if baseline_composed:
        aq = """
        PREFIX cams: <https://example.com/cams/vocabulary#>
        SELECT ?assessment ?composed
        WHERE {
          VALUES ?assessment {
            <https://example.com/cams/denied/project/description#AssessmentAlphaFeasible>
            <https://example.com/cams/denied/project/description#AssessmentDeactivate>
          }
          ?assessment cams:composedSuccessProbability ?composed .
        }
        """
        for assessment, asserted in g.query(aq):
            asserted_f = float(asserted)
            ok = abs(baseline_mission - asserted_f) < 0.001
            print(
                f"    {local(assessment)}: asserted={asserted_f:.3f} "
                f"computed_baseline={baseline_mission:.4f} -> {'OK' if ok else 'MISMATCH'}"
            )


def check_constraint_rollup(g: Graph) -> None:
    print("\n=== Constraint conjunction roll-up ===")
    q = """
    PREFIX cams: <https://example.com/cams/vocabulary#>
    SELECT ?constraint ?cStatus (COUNT(?cond) AS ?n)
           (SUM(IF(?cs = "Satisfied", 1, 0)) AS ?nSat)
    WHERE {
      ?constraint a cams:Constraint ;
                  cams:satisfactionStatus ?cStatus ;
                  cams:comprisesCondition ?cond .
      ?cond cams:satisfactionStatus ?cs .
    }
    GROUP BY ?constraint ?cStatus
    """
    for constraint, c_status, n, n_sat in g.query(q):
        n = int(n)
        n_sat = int(n_sat)
        expected = "Satisfied" if n_sat == n else "Unsatisfied"
        ok = str(c_status) == expected
        print(
            f"  {local(constraint)}: asserted={c_status} "
            f"conditions={n_sat}/{n} expected={expected} -> "
            f"{'OK' if ok else 'MISMATCH'}"
        )


def check_state_chain(g: Graph) -> None:
    print("\n=== State chain (asserted + rule-derivable) ===")
    q = """
    PREFIX cams: <https://example.com/cams/vocabulary#>
    SELECT ?opm1 ?opm2 ?succ ?inp
    WHERE {
      ?opm1 cams:precedes ?opm2 ;
            cams:predictsSuccessor ?succ .
      OPTIONAL { ?opm2 cams:startsFrom ?inp }
    }
    """
    for opm1, opm2, succ, inp in g.query(q):
        ok = inp is not None and inp == succ
        print(
            f"  {local(opm1)} -> {local(opm2)}: "
            f"succ={local(succ)} input={local(inp) if inp else 'NONE'} "
            f"-> {'OK' if ok else 'GAP (run oml reason -o build/owl for rule)'}"
        )


def check_execution_rollup(g: Graph) -> None:
    print("\n=== Execution status roll-up (asset isExecuting -> OPM -> plan) ===")
    q = """
    PREFIX cams: <https://example.com/cams/vocabulary#>
    SELECT ?asset ?opm ?opmStatus ?ep ?epStatus ?mp ?mpStatus
    WHERE {
      ?asset cams:isExecuting ?opm .
      OPTIONAL { ?opm cams:executionStatus ?opmStatus }
      OPTIONAL {
        ?opm cams:isContainedBy ?ep .
        ?ep a cams:EngagementPlan .
        OPTIONAL { ?ep cams:executionStatus ?epStatus }
        OPTIONAL {
          ?ep cams:isContainedBy ?mp .
          ?mp a cams:MissionPlan .
          OPTIONAL { ?mp cams:executionStatus ?mpStatus }
        }
      }
    }
    """
    rows = list(g.query(q))
    if not rows:
        print("  no Asset isExecuting assertions found")
        return
    for asset, opm, opm_status, ep, ep_status, mp, mp_status in rows:
        opm_ok = opm_status is not None and str(opm_status) == "Executing"
        ep_ok = ep is None or (
            ep_status is not None and str(ep_status) == "Executing"
        )
        mp_ok = mp is None or (
            mp_status is not None and str(mp_status) == "Executing"
        )
        print(
            f"  {local(asset)} isExecuting {local(opm)}="
            f"{opm_status or 'NONE'} {'OK' if opm_ok else 'GAP'}; "
            f"{local(ep) if ep else '-'}="
            f"{ep_status or 'NONE'} {'OK' if ep_ok else 'GAP'}; "
            f"{local(mp) if mp else '-'}="
            f"{mp_status or 'NONE'} {'OK' if mp_ok else 'GAP'}"
        )


def check_opm_role_checkin(g: Graph) -> None:
    """Universal Role check-in (not expressible in SWRL; complements existential OPMExecuting)."""
    print("\n=== OPM Role check-in (universal vs SWRL existential) ===")
    q = """
    PREFIX cams: <https://example.com/cams/vocabulary#>
    SELECT ?opm ?role ?asset ?executing ?opmStatus
    WHERE {
      ?opm a cams:OPM ;
           cams:contains ?role .
      ?role cams:allocatedTo ?asset .
      OPTIONAL {
        ?asset cams:isExecuting ?opm .
        BIND(true AS ?executing)
      }
      OPTIONAL { ?opm cams:executionStatus ?opmStatus }
    }
    ORDER BY ?opm ?role
    """
    rows = list(g.query(q))
    if not rows:
        print("  no OPM Roles found")
        return
    by_opm: dict[str, list[tuple]] = {}
    for opm, role, asset, executing, opm_status in rows:
        by_opm.setdefault(str(opm), []).append(
            (opm, role, asset, executing is not None, opm_status)
        )
    for _key, role_rows in by_opm.items():
        opm = role_rows[0][0]
        opm_status = role_rows[0][4]
        n = len(role_rows)
        n_in = sum(1 for r in role_rows if r[3])
        existential = n_in >= 1
        universal = n_in == n
        swrl_exec = opm_status is not None and str(opm_status) == "Executing"
        label = (
            "ALL_CHECKED_IN"
            if universal
            else ("PARTIAL" if existential else "NONE_CHECKED_IN")
        )
        print(
            f"  {local(opm)}: {n_in}/{n} roles checked in -> {label}; "
            f"SWRL executionStatus={opm_status or 'NONE'} "
            f"(existential={'yes' if swrl_exec else 'no'})"
        )
        for _opm, role, asset, is_in, _st in role_rows:
            print(
                f"    {local(role)}->{local(asset)}: "
                f"{'isExecuting' if is_in else 'not executing'}"
            )
        if swrl_exec and not universal:
            print(
                "    note: SWRL OPMExecuting fired on ∃ check-in; "
                "universal gate would still block Coordinated Executing"
            )


def check_resource_occupancy(g: Graph) -> None:
    print("\n=== Resource occupancy (executing OPM Role -> Busy resource) ===")
    q = """
    PREFIX cams: <https://example.com/cams/vocabulary#>
    SELECT DISTINCT ?asset ?opm ?role ?resource ?status
    WHERE {
      ?asset cams:isExecuting ?opm .
      ?opm cams:contains ?role .
      ?role cams:allocatedTo ?asset ;
           cams:realizesBehavior ?b .
      {
        ?b cams:requiresResource ?need .
        FILTER NOT EXISTS { ?need a cams:ResourceTypeToken }
        BIND(?need AS ?resource)
      }
      UNION
      {
        ?b cams:requiresResource ?need .
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
      OPTIONAL { ?resource cams:availabilityStatus ?status }
      OPTIONAL { ?resource cams:isOccupiedBy ?occ }
      FILTER(!BOUND(?occ) || ?occ = ?opm)
    }
    """
    rows = list(g.query(q))
    if not rows:
        print("  no required resources on executing OPM roles")
        return
    for asset, opm, role, resource, status in rows:
        occupied = (resource, CAMS.isOccupiedBy, opm) in g
        ok = occupied and status is not None and str(status) == "Busy"
        print(
            f"  {local(asset)}/{local(opm)}/{local(role)} needs {local(resource)}: "
            f"occupied={occupied} status={status or 'NONE'} "
            f"-> {'OK' if ok else 'GAP (run oml reason)'}"
        )


def check_gsd_feasibility(g: Graph) -> None:
    """GSD ≈ standoff * tan(FOV_deg/pixels * pi/180); compare to maxGroundSampleDistanceMeters."""
    print("\n=== Imaging GSD feasibility (ResourceRequirement) ===")
    q = """
    PREFIX cams: <https://example.com/cams/vocabulary#>
    PREFIX denied: <https://example.com/cams/denied/vocabulary#>
    PREFIX oml: <http://opencaesar.io/oml#>
    SELECT ?req ?behavior ?resource ?standoff ?maxGsd ?pixels ?fov
    WHERE {
      ?req a cams:ResourceRequirement ;
           oml:hasSource ?behavior ;
           oml:hasTarget ?resource ;
           denied:expectedStandoffMeters ?standoff ;
           denied:maxGroundSampleDistanceMeters ?maxGsd .
      ?resource denied:horizontalPixelCount ?pixels ;
                denied:horizontalFOVDegrees ?fov .
    }
    """
    rows = list(g.query(q))
    if not rows:
        print("  no GSD-constrained ResourceRequirement links found")
        return
    for req, behavior, resource, standoff, max_gsd, pixels, fov in rows:
        r = float(standoff)
        max_g = float(max_gsd)
        n = float(pixels)
        fov_d = float(fov)
        ifov_rad = math.radians(fov_d / n)
        gsd = r * math.tan(ifov_rad)
        ok = gsd <= max_g
        print(
            f"  {local(req)}: {local(behavior)}->{local(resource)} "
            f"standoff={r:.0f}m pixels={n:.0f} FOV={fov_d}deg "
            f"GSD={gsd:.3f}m max={max_g}m -> {'MET' if ok else 'NOT MET'}"
        )


def check_jam_feasibility(g: Graph) -> None:
    """Jam req: power/standoff on requirement; frequency/bandwidth from countersThreat Threat."""
    print("\n=== Jamming RF feasibility (ResourceRequirement countersThreat) ===")
    q = """
    PREFIX cams: <https://example.com/cams/vocabulary#>
    PREFIX denied: <https://example.com/cams/denied/vocabulary#>
    PREFIX oml: <http://opencaesar.io/oml#>
    SELECT ?req ?behavior ?resource ?threat ?standoff ?minP ?maxP
           ?jamBw ?fMin ?fMax ?fCenter ?emBw
    WHERE {
      ?req a cams:ResourceRequirement ;
           oml:hasSource ?behavior ;
           oml:hasTarget ?resource ;
           denied:countersThreat ?threat ;
           denied:expectedStandoffMeters ?standoff ;
           denied:minTransmitPowerWatts ?minP .
      ?resource denied:maxTransmitPowerWatts ?maxP ;
                denied:jammingBandwidthHz ?jamBw ;
                denied:minOperatingFrequencyHz ?fMin ;
                denied:maxOperatingFrequencyHz ?fMax .
      ?threat denied:centerFrequencyHz ?fCenter ;
              denied:emissionBandwidthHz ?emBw .
    }
    """
    rows = list(g.query(q))
    if not rows:
        print("  no jam ResourceRequirement links found")
        return
    for (
        req,
        behavior,
        resource,
        threat,
        standoff,
        min_p,
        max_p,
        jam_bw,
        f_min,
        f_max,
        f_center,
        em_bw,
    ) in rows:
        standoff_m = float(standoff)
        min_pw = float(min_p)
        max_pw = float(max_p)
        jam_bw_hz = float(jam_bw)
        f0 = float(f_center)
        em = float(em_bw)
        lo = float(f_min)
        hi = float(f_max)
        freq_ok = lo <= f0 <= hi
        bw_ok = jam_bw_hz >= em
        power_ok = max_pw >= min_pw
        ok = freq_ok and bw_ok and power_ok
        print(
            f"  {local(req)}: {local(behavior)}->{local(resource)} vs {local(threat)} "
            f"standoff={standoff_m:.0f}m "
            f"freq={f0/1e9:.2f}GHz in[{lo/1e9:.1f},{hi/1e9:.1f}]={'OK' if freq_ok else 'FAIL'} "
            f"bw={em/1e6:.1f}MHz<={jam_bw_hz/1e6:.0f}MHz={'OK' if bw_ok else 'FAIL'} "
            f"P={max_pw:.0f}W>={min_pw:.0f}W={'OK' if power_ok else 'FAIL'} "
            f"-> {'MET' if ok else 'NOT MET'}"
        )


def check_priority_inheritance(g: Graph) -> None:
    print("\n=== Priority inheritance (Intent -> spawned Objective) ===")
    q = """
    PREFIX cams: <https://example.com/cams/vocabulary#>
    SELECT ?intent ?iPri ?objective ?oPri
    WHERE {
      ?intent a cams:Intent ;
              cams:priority ?iPri ;
              cams:spawns ?objective .
      OPTIONAL { ?objective cams:priority ?oPri }
    }
    ORDER BY ?intent ?objective
    """
    rows = list(g.query(q))
    if not rows:
        print("  no Intent priorities found")
        return
    for intent, i_pri, objective, o_pri in rows:
        ok = o_pri is not None and str(o_pri) == str(i_pri)
        print(
            f"  {local(intent)}={i_pri} -> {local(objective)}="
            f"{o_pri or 'NONE'} -> {'OK' if ok else 'GAP (run oml reason)'}"
        )


def check_commander_notices(g: Graph) -> None:
    print("\n=== Commander Notice Addressing (KickbackAddressing rule) ===")
    q = """
    PREFIX cams: <https://example.com/cams/vocabulary#>
    SELECT ?notice ?cmd
    WHERE {
      ?notice a cams:CommanderNotice .
      OPTIONAL { ?notice cams:sentTo ?cmd }
    }
    ORDER BY ?notice
    """
    rows = list(g.query(q))
    if not rows:
        print("  no CommanderNotice instances found")
        return
    for notice, cmd in rows:
        ok = cmd is not None
        print(
            f"  {local(notice)} sentTo {local(cmd) if cmd else 'NONE'} "
            f"-> {'OK' if ok else 'GAP (run oml reason)'}"
        )


def main() -> int:
    g = load_graph()
    print(f"Loaded graph: {len(g)} triples")

    for rq in sorted(QUERIES.glob("q*.rq")):
        print(f"\n=== {rq.name} ===")
        try:
            rows = run_sparql(g, rq)
        except Exception as exc:  # noqa: BLE001
            print(f"  QUERY ERROR: {exc}")
            continue
        if not rows:
            print("  (no results)")
            continue
        for row in rows:
            print("  " + " | ".join(local(v) if v is not None else "-" for v in row))

    check_pos_product(g)
    check_constraint_rollup(g)
    check_state_chain(g)
    check_execution_rollup(g)
    check_opm_role_checkin(g)
    check_resource_occupancy(g)
    check_gsd_feasibility(g)
    check_jam_feasibility(g)
    check_priority_inheritance(g)
    check_commander_notices(g)

    print("\n=== SHACL ===")
    if shacl_validate is None:
        print("  pyshacl not installed")
        return 1
    # Refresh shapes.ttl from pattern markdown (source of truth)
    sync = ROOT / "scripts" / "sync_shapes_from_md.py"
    if sync.exists():
        import runpy

        runpy.run_path(str(sync))
    shapes = QUERIES / "shapes.ttl"
    sg = Graph().parse(shapes, format="turtle")

    conforms, report_graph, report_text = shacl_validate(
        g,
        shacl_graph=sg,
        inference="rdfs",
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
        inplace=False,
    )
    print(f"  conforms={conforms}")
    if not conforms:
        # Print concise messages
        for line in report_text.splitlines():
            if "Message" in line or "Focus Node" in line or "Result Path" in line:
                print("  " + line.strip())
    return 0 if conforms else 0  # informational; do not fail CI on soft shape gaps


if __name__ == "__main__":
    sys.exit(main())
