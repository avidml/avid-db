#!/usr/bin/env python3
"""
Fetch a CVE from MITRE and create an AVID report.

Usage:
    python fetch_cve_report.py CVE-2026-33634
"""

import sys
from pathlib import Path

# Add avidtools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "avidtools"))

from avidtools.connectors.cve import import_cve, convert_cve_to_report


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_cve_report.py CVE-XXXX-XXXXX")
        sys.exit(1)

    cve_id = sys.argv[1]

    print(f"Fetching {cve_id} from MITRE CVE API...")
    try:
        cve_data = import_cve(cve_id)
    except Exception as e:
        print(f"Error fetching CVE: {e}")
        sys.exit(1)

    print(f"Converting to AVID report...")
    try:
        report = convert_cve_to_report(cve_data)
    except Exception as e:
        print(f"Error converting to report: {e}")
        sys.exit(1)

    # Save to review folder
    review_dir = Path(__file__).parent.parent / "reports" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)

    output_file = review_dir / f"{cve_id}_report.json"
    print(f"Saving report to {output_file}...")

    try:
        report.save(str(output_file))
        print(f"✓ Report saved successfully")
        print(f"  File: {output_file}")
    except Exception as e:
        print(f"Error saving report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
