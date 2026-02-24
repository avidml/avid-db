#!/usr/bin/env python3

"""CLI for Inspect report enrich in AVID DB."""

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

from avidtools.connectors.inspect import (  # noqa: E402
    UnsupportedInspectBenchmarkError,
    process_report,
)


parser = argparse.ArgumentParser(
    description="Enrich and correct Inspect Evals AVID report JSON files."
)
parser.add_argument("report", type=Path, help="Path to report JSON file")
args = parser.parse_args()

report_path = args.report.resolve()
if not report_path.exists() or not report_path.is_file():
    print(f"ERROR: Report file does not exist: {report_path}")
    sys.exit(1)

try:
    process_report(report_path)
except UnsupportedInspectBenchmarkError:
    report_path.unlink(missing_ok=True)
    print(f"Deleted unsupported Inspect benchmark report: {report_path}")
except Exception as error:
    print(f"ERROR: {error}")
    sys.exit(1)
