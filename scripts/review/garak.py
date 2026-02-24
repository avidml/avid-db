#!/usr/bin/env python3

"""CLI for Garak report enrich in AVID DB."""

import argparse
import sys
from pathlib import Path

script_dir_path = Path(__file__).resolve().parent
sys.path = [
    path
    for path in sys.path
    if Path(path or ".").resolve() != script_dir_path
]

avidtools_path = (
    Path(__file__).resolve().parent.parent.parent.parent / "avidtools"
)
sys.path.insert(0, str(avidtools_path))

from avidtools.connectors.garak import enrich_file  # noqa: E402


parser = argparse.ArgumentParser(
    description="Enrich Garak reports and normalize input files in place."
)
parser.add_argument(
    "input_path",
    type=Path,
    help="Path to .json or .jsonl file",
)
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Show enrich count without writing changes",
)

args = parser.parse_args()

input_path = args.input_path.resolve()
if not input_path.exists() or not input_path.is_file():
    print(f"ERROR: Input file does not exist: {input_path}")
    sys.exit(1)

try:
    reports_enriched = enrich_file(input_path, dry_run=args.dry_run)
except Exception as error:
    print(f"ERROR: {error}")
    sys.exit(1)

print(f"Enriched {reports_enriched} report(s) in {input_path}")
if args.dry_run:
    print("Dry run complete: no file changes were written")
else:
    print("Saved normalized updates in place")
