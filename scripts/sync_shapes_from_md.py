#!/usr/bin/env python3
"""Extract SHACL Turtle from method pattern markdown editor fences into queries/shapes.ttl."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD_DIR = ROOT / "src/method/md/example.com/cams"
OUT = ROOT / "queries/shapes.ttl"

FENCE = re.compile(
    r"```(?:table-editor|tree-editor)\n(?:---\n.*?\n---\n)?(.*?)```",
    re.S,
)


def main() -> None:
    blocks: list[str] = []
    for md in sorted(MD_DIR.glob("*.md")):
        for match in FENCE.finditer(md.read_text()):
            turtle = match.group(1).strip()
            if turtle:
                blocks.append(f"# from {md.name}\n{turtle}\n")
    if not blocks:
        raise SystemExit(f"No editor SHACL found under {MD_DIR}")
    header = (
        "# Generated from src/method/md/example.com/cams/*.md — do not hand-edit.\n"
        "# Source of truth: pattern markdown. Refresh: python scripts/sync_shapes_from_md.py\n\n"
    )
    OUT.write_text(header + "\n".join(blocks))
    print(f"Wrote {OUT} ({len(blocks)} editor blocks)")


if __name__ == "__main__":
    main()
