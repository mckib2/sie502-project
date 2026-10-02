#!/usr/bin/env python3
"""Synchronize and verify SPARQL queries between Markdown notebooks and src/method/sparql/.

Analogous to sync_shapes_from_md.py. Ensures that queries embedded in Markdown fences
(Dashboard.md, analysis-bundle.md) and standalone .sparql files stay 100% aligned.

Usage:
    python scripts/sync_queries.py --check        # Verify all queries match (default)
    python scripts/sync_queries.py --from-md      # Extract queries from Markdown -> .sparql
    python scripts/sync_queries.py --to-md        # Inject queries from .sparql -> Markdown fences
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_MD = ROOT / "src/model/md/CAMS Denied/Analysis/Dashboard.md"
BUNDLE_MD = ROOT / "src/method/md/example.com/cams/analysis-bundle.md"
SPARQL_DIR = ROOT / "src/method/sparql"


@dataclass
class QueryMapping:
    name: str
    md_file: Path
    md_regex: re.Pattern
    sparql_file: Path


def make_pattern(prefix: str, fence_type: str = "table") -> re.Pattern:
    return re.compile(
        rf"({re.escape(prefix)}.*?```{fence_type}\n(?:---\n.*?\n---\n)?)(.*?)(```)",
        re.S,
    )


def make_python_query_pattern(prefix: str) -> re.Pattern:
    return re.compile(
        rf"({re.escape(prefix)}.*?```python\n(?:.*?await query\(\"\"\"\n)?)(.*?)(\"\"\"\)\n.*?```)",
        re.S,
    )


QUERY_MAPPINGS: list[QueryMapping] = [
    # Dashboard Q1-Q8
    QueryMapping(
        name="PoS-Inputs",
        md_file=DASHBOARD_MD,
        md_regex=make_python_query_pattern("## 2. Computed analysis -- PoS composition"),
        sparql_file=SPARQL_DIR / "pos_inputs.sparql",
    ),
    QueryMapping(
        name="Q1",
        md_file=DASHBOARD_MD,
        md_regex=make_pattern("### Q1."),
        sparql_file=SPARQL_DIR / "q1_intent_opm_roles.sparql",
    ),
    QueryMapping(
        name="Q2",
        md_file=DASHBOARD_MD,
        md_regex=make_pattern("### Q2."),
        sparql_file=SPARQL_DIR / "q2_team_intent_coverage.sparql",
    ),
    QueryMapping(
        name="Q3",
        md_file=DASHBOARD_MD,
        md_regex=make_pattern("### Q3."),
        sparql_file=SPARQL_DIR / "q3_behavior_mapping_gaps.sparql",
    ),
    QueryMapping(
        name="Q4",
        md_file=DASHBOARD_MD,
        md_regex=make_pattern("### Q4."),
        sparql_file=SPARQL_DIR / "q4_resource_feasibility.sparql",
    ),
    QueryMapping(
        name="Q5",
        md_file=DASHBOARD_MD,
        md_regex=make_pattern("### Q5."),
        sparql_file=SPARQL_DIR / "q5_resource_contention.sparql",
    ),
    QueryMapping(
        name="Q6",
        md_file=DASHBOARD_MD,
        md_regex=make_pattern("### Q6."),
        sparql_file=SPARQL_DIR / "q6_success_probability_monitor.sparql",
    ),
    QueryMapping(
        name="Q7",
        md_file=DASHBOARD_MD,
        md_regex=make_pattern("### Q7."),
        sparql_file=SPARQL_DIR / "q7_sequential_world_state_prediction.sparql",
    ),
    QueryMapping(
        name="Q8",
        md_file=DASHBOARD_MD,
        md_regex=make_pattern("### Q8."),
        sparql_file=SPARQL_DIR / "q8_constraint_condition_gating.sparql",
    ),
    # analysis-bundle orphans
    QueryMapping(
        name="Orphan-Authority",
        md_file=BUNDLE_MD,
        md_regex=make_pattern("### Authority"),
        sparql_file=SPARQL_DIR / "orphan_authority.sparql",
    ),
    QueryMapping(
        name="Orphan-Mission",
        md_file=BUNDLE_MD,
        md_regex=make_pattern("### Mission"),
        sparql_file=SPARQL_DIR / "orphan_mission.sparql",
    ),
    QueryMapping(
        name="Orphan-Engagement",
        md_file=BUNDLE_MD,
        md_regex=make_pattern("### Engagement"),
        sparql_file=SPARQL_DIR / "orphan_engagement.sparql",
    ),
    QueryMapping(
        name="Orphan-Platform",
        md_file=BUNDLE_MD,
        md_regex=make_pattern("### Platform"),
        sparql_file=SPARQL_DIR / "orphan_platform.sparql",
    ),
    QueryMapping(
        name="Orphan-Coverage",
        md_file=BUNDLE_MD,
        md_regex=make_pattern("### Coverage"),
        sparql_file=SPARQL_DIR / "orphan_coverage.sparql",
    ),
    # analysis-bundle precedes graph
    QueryMapping(
        name="Graph-Precedes",
        md_file=BUNDLE_MD,
        md_regex=make_pattern("## Baseline OPM precedes graph", fence_type="graph"),
        sparql_file=SPARQL_DIR / "opm_precedes_graph.sparql",
    ),
]


def normalize_query(query_text: str) -> str:
    """Strip comments and normalize whitespace for semantic equality comparison."""
    lines = []
    for line in query_text.strip().splitlines():
        line_s = line.strip()
        if not line_s or line_s.startswith("#"):
            continue
        lines.append(line_s)
    return "\n".join(lines)


def extract_header_comment(text: str) -> str:
    """Extract initial comment lines from a query file, if present."""
    comments = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            comments.append(line)
        elif line.strip().startswith("PREFIX"):
            continue
        elif line.strip():
            break
    return "\n".join(comments)


def extract_query_from_md(mapping: QueryMapping) -> str:
    content = mapping.md_file.read_text(encoding="utf-8")
    match = mapping.md_regex.search(content)
    if not match:
        raise ValueError(f"Could not find query for {mapping.name} in {mapping.md_file}")
    return match.group(2).strip()


def check_sync() -> int:
    """Verify all queries are synchronized between Markdown and .sparql."""
    mismatches = 0
    print("=== Checking SPARQL Query Synchronization ===")

    for m in QUERY_MAPPINGS:
        md_query = extract_query_from_md(m)
        norm_md = normalize_query(md_query)

        # Check .sparql file
        if not m.sparql_file.is_file():
            print(f"  [MISSING] {m.name}: {m.sparql_file.name} does not exist!")
            mismatches += 1
            continue

        sp_text = m.sparql_file.read_text(encoding="utf-8")
        norm_sp = normalize_query(sp_text)

        if norm_md != norm_sp:
            print(f"  [DRIFT] {m.name}: {m.md_file.name} != {m.sparql_file.name}")
            diff = difflib.unified_diff(
                norm_md.splitlines(),
                norm_sp.splitlines(),
                fromfile=f"MD:{m.name}",
                tofile=f"SPARQL:{m.sparql_file.name}",
                lineterm="",
            )
            for line in diff:
                print(f"    {line}")
            mismatches += 1
            continue

        print(f"  [OK] {m.name:18}: {m.md_file.name} == {m.sparql_file.name}")

    if mismatches == 0:
        print(f"All {len(QUERY_MAPPINGS)} queries synchronized.")
        return 0
    else:
        print(f"Synchronization failed with {mismatches} mismatch(es).")
        return 1


def sync_from_md() -> int:
    """Extract queries from Markdown and write to .sparql files."""
    print("=== Syncing Queries: Markdown -> .sparql ===")
    updated = 0
    for m in QUERY_MAPPINGS:
        md_query = extract_query_from_md(m)

        # Preserve existing comment header if present in target
        comment = ""
        if m.sparql_file.is_file():
            comment = extract_header_comment(m.sparql_file.read_text(encoding="utf-8"))

        sparql_content = md_query
        if comment and comment not in md_query:
            # Place comment after PREFIXes if any, or at top
            lines = md_query.splitlines()
            prefix_end = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("PREFIX"):
                    prefix_end = i + 1
            if prefix_end > 0:
                sparql_content = (
                    "\n".join(lines[:prefix_end])
                    + f"\n\n{comment}\n"
                    + "\n".join(lines[prefix_end:])
                )
            else:
                sparql_content = f"{comment}\n{md_query}"

        m.sparql_file.write_text(sparql_content.strip() + "\n", encoding="utf-8")
        print(f"  Updated {m.sparql_file.relative_to(ROOT)}")
        updated += 1

    print(f"Successfully synced {updated} file(s) from Markdown.")
    return 0


def sync_to_md() -> int:
    """Inject queries from .sparql files into Markdown fences."""
    print("=== Syncing Queries: .sparql -> Markdown ===")
    # Group mappings by Markdown file to perform batch replacements
    by_file: dict[Path, list[QueryMapping]] = {}
    for m in QUERY_MAPPINGS:
        by_file.setdefault(m.md_file, []).append(m)

    for md_file, mappings in by_file.items():
        content = md_file.read_text(encoding="utf-8")
        for m in mappings:
            sp_text = m.sparql_file.read_text(encoding="utf-8").strip()
            # In markdown fences, strip leading descriptive comments if preferred
            fence_lines = [
                line for line in sp_text.splitlines()
                if not (line.strip().startswith("#") and ("Q" in line or "Runtime" in line or "Sequential" in line or "PoS" in line))
            ]
            clean_query = "\n".join(fence_lines).strip()

            def replacer(match: re.Match) -> str:
                return f"{match.group(1)}{clean_query}\n{match.group(3)}"

            content, n = m.md_regex.subn(replacer, content)
            if n == 0:
                print(f"  [WARN] Failed to replace {m.name} in {md_file.name}")
            else:
                print(f"  Injected {m.name} ({m.sparql_file.name}) -> {md_file.name}")

        md_file.write_text(content, encoding="utf-8")

    print("Successfully updated Markdown files from .sparql.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", default=True, help="Check synchronization (default)")
    group.add_argument("--from-md", action="store_true", help="Extract from Markdown to .sparql")
    group.add_argument("--to-md", action="store_true", help="Inject from .sparql into Markdown fences")

    args = parser.parse_args()

    if args.from_md:
        return sync_from_md()
    elif args.to_md:
        return sync_to_md()
    else:
        return check_sync()


if __name__ == "__main__":
    ret = main()
    if ret != 0:
        sys.exit(ret)
