"""
Publish reports from review folder to final locations.

This script:
1. Reads JSONL files from reports/review/ directory
2. Assigns AVID Report IDs to each report
3. Saves reports to reports/YYYY/ directory
4. Optionally creates vulnerabilities from reports
5. Assigns AVID Vulnerability IDs
6. Saves vulnerabilities to vulnerabilities/YYYY/ directory
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.id_manager import IDManager  # noqa: E402
from utils.publisher import (  # noqa: E402
    load_report_from_json,
    assign_report_id,
    create_vulnerability_from_report,
    publish_report,
    publish_vulnerability,
)

# Add avidtools to path
avidtools_path = Path(__file__).parent.parent.parent / "avidtools"
sys.path.insert(0, str(avidtools_path))

from avidtools.datamodels.report import Report  # noqa: E402
from avidtools.connectors.base import normalize_file  # noqa: E402


CVE_REGEX = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


def _extract_cve_id(report_data: dict) -> str | None:
    """Extract CVE ID from report references/problemtype/description."""
    references = report_data.get("references") or []
    for ref in references:
        if not isinstance(ref, dict):
            continue
        for key in ("url", "label"):
            value = str(ref.get(key) or "")
            match = CVE_REGEX.search(value)
            if match:
                return match.group(0).upper()

    problemtype = report_data.get("problemtype") or {}
    problem_desc = (problemtype.get("description") or {}).get("value") or ""
    match = CVE_REGEX.search(str(problem_desc))
    if match:
        return match.group(0).upper()

    description = (report_data.get("description") or {}).get("value") or ""
    match = CVE_REGEX.search(str(description))
    if match:
        return match.group(0).upper()

    return None


def _collect_existing_cves(
    report_root: Path, years: tuple[int, ...]
) -> set[str]:
    """Collect CVE IDs already present in reports/{years}/ directories."""
    existing_cves: set[str] = set()

    for year in years:
        year_dir = report_root / str(year)
        if not year_dir.exists():
            continue

        for report_path in year_dir.glob("AVID-*.json"):
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    report_data = json.load(f)
                cve_id = _extract_cve_id(report_data)
                if cve_id:
                    existing_cves.add(cve_id)
            except Exception:
                continue

    return existing_cves


def _report_years_from(report_root: Path, start_year: int) -> tuple[int, ...]:
    """Return sorted report year directories from start_year onward."""
    years: list[int] = []
    for child in report_root.iterdir():
        if not child.is_dir():
            continue
        if not child.name.isdigit():
            continue

        year = int(child.name)
        if year >= start_year:
            years.append(year)

    return tuple(sorted(years))


def _is_filtered_pass_jsonl(path: Path) -> bool:
    return (
        path.suffix == ".jsonl"
        and path.name.endswith("filtered_pass.jsonl")
    )


def _coerce_legacy_metrics(data: dict) -> dict:
    """Convert legacy flat metrics format to Report Metric schema."""

    metrics = data.get("metrics")
    if not isinstance(metrics, list):
        return data

    coerced_metrics = []
    changed = False
    for metric in metrics:
        if (
            isinstance(metric, dict)
            and "name" not in metric
            and "metrics" in metric
            and "value" in metric
        ):
            scorer = metric.get("scorer")
            coerced_metrics.append(
                {
                    "name": metric.get("metrics"),
                    "detection_method": {
                        "type": "Significance Test",
                        "name": scorer or "unknown",
                    },
                    "results": {
                        "value": metric.get("value"),
                        "scorer": scorer,
                    },
                }
            )
            changed = True
        else:
            coerced_metrics.append(metric)

    if changed:
        data = dict(data)
        data["metrics"] = coerced_metrics
    return data


def process_jsonl_file(
    jsonl_path: Path,
    id_manager: IDManager,
    create_vulns: bool = False,
    year: int = None,
    dry_run: bool = False,
    existing_cves: set[str] | None = None,
):
    """
    Process a JSONL file containing reports.
    
    Args:
        jsonl_path: Path to JSONL file
        id_manager: IDManager instance for tracking IDs
        create_vulns: Whether to create vulnerabilities from reports
        year: Year for ID generation. Defaults to current year.
        dry_run: If True, don't actually save files
    """
    if year is None:
        year = datetime.now().year
    
    print(f"Processing: {jsonl_path}")
    print("-" * 80)
    
    reports_processed = 0
    vulns_created = 0
    reports_skipped = 0
    seen_cves_in_file: set[str] = set()
    
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                # Parse JSON line
                data = json.loads(line)
                data = _coerce_legacy_metrics(data)

                cve_id = _extract_cve_id(data)
                if existing_cves is not None and cve_id:
                    if cve_id in existing_cves or cve_id in seen_cves_in_file:
                        print(f"\nLine {line_num}:")
                        print(
                            "  Skipping report (CVE already covered): "
                            f"{cve_id}"
                        )
                        reports_skipped += 1
                        continue

                report = Report(**data)
                
                # Get next report ID
                report_id = id_manager.get_next_report_id(year)
                
                print(f"\nLine {line_num}:")
                print(f"  Assigning Report ID: {report_id}")
                
                if not dry_run:
                    # Publish report
                    report_path = publish_report(report, report_id, year)
                    print(f"  Saved report: {report_path}")
                else:
                    report_loc = f"reports/{year}/{report_id}.json"
                    print(f"  [DRY RUN] Would save report to: {report_loc}")
                
                reports_processed += 1

                if cve_id:
                    seen_cves_in_file.add(cve_id)
                    if existing_cves is not None:
                        existing_cves.add(cve_id)
                
                # Create vulnerability if requested
                if create_vulns:
                    vuln_id = id_manager.get_next_vuln_id(year)
                    print(f"  Creating Vulnerability ID: {vuln_id}")
                    
                    if not dry_run:
                        # Need to reload report with assigned ID
                        report = assign_report_id(report, report_id)
                        vuln = create_vulnerability_from_report(
                            report, vuln_id
                        )
                        vuln_path = publish_vulnerability(
                            vuln, vuln_id, year
                        )
                        print(f"  Saved vulnerability: {vuln_path}")
                    else:
                        vuln_loc = f"vulnerabilities/{year}/{vuln_id}.json"
                        print(f"  [DRY RUN] Would save to: {vuln_loc}")
                    
                    vulns_created += 1
                
            except json.JSONDecodeError as e:
                print(f"  ERROR: Invalid JSON on line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"  ERROR: Failed to process line {line_num}: {e}")
                continue
    
    print()
    print("=" * 80)
    print("Summary:")
    print(f"  Reports processed: {reports_processed}")
    if existing_cves is not None:
        print(f"  Reports skipped (duplicate CVE): {reports_skipped}")
    if create_vulns:
        print(f"  Vulnerabilities created: {vulns_created}")
    print("=" * 80)


def process_json_file(
    json_path: Path,
    id_manager: IDManager,
    create_vuln: bool = False,
    year: int = None,
    dry_run: bool = False,
):
    """
    Process a single JSON file containing a report.
    
    Args:
        json_path: Path to JSON file
        id_manager: IDManager instance for tracking IDs
        create_vuln: Whether to create vulnerability from report
        year: Year for ID generation. Defaults to current year.
        dry_run: If True, don't actually save files
    """
    if year is None:
        year = datetime.now().year
    
    print(f"Processing: {json_path}")
    print("-" * 80)
    
    try:
        # Load report
        report = load_report_from_json(json_path)
        
        # Get next report ID
        report_id = id_manager.get_next_report_id(year)
        
        print(f"Assigning Report ID: {report_id}")
        
        if not dry_run:
            # Publish report
            report_path = publish_report(report, report_id, year)
            print(f"Saved report: {report_path}")
        else:
            report_loc = f"reports/{year}/{report_id}.json"
            print(f"[DRY RUN] Would save report to: {report_loc}")
        
        # Create vulnerability if requested
        if create_vuln:
            vuln_id = id_manager.get_next_vuln_id(year)
            print(f"Creating Vulnerability ID: {vuln_id}")
            
            if not dry_run:
                # Reload report with assigned ID
                report = assign_report_id(report, report_id)
                vuln = create_vulnerability_from_report(report, vuln_id)
                vuln_path = publish_vulnerability(vuln, vuln_id, year)
                print(f"Saved vulnerability: {vuln_path}")
            else:
                vuln_loc = f"vulnerabilities/{year}/{vuln_id}.json"
                print(f"[DRY RUN] Would save vulnerability to: {vuln_loc}")
        
        print()
        print("=" * 80)
        print("Complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"ERROR: Failed to process file: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Publish reports from review folder to final locations"
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to JSONL file or JSON file in review folder",
    )
    parser.add_argument(
        "--create-vulns",
        action="store_true",
        help="Create vulnerabilities from reports",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Year for ID generation (default: current year)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    
    args = parser.parse_args()
    
    if not args.input_path.exists():
        print(f"ERROR: File not found: {args.input_path}")
        sys.exit(1)
    
    # Create ID manager for this session
    id_manager = IDManager()

    existing_cves = None
    if _is_filtered_pass_jsonl(args.input_path):
        print("Running default normalization for filtered pass reports...")
        normalized_count = normalize_file(
            args.input_path, dry_run=args.dry_run
        )
        print(
            "Default normalization complete: "
            f"{normalized_count} report(s) normalized"
        )

        report_root = Path(__file__).resolve().parent.parent / "reports"
        years_to_scan = _report_years_from(report_root, start_year=2025)
        if years_to_scan:
            year_label = f"reports/{years_to_scan[0]} onwards"
        else:
            year_label = "reports/2025 onwards"
        print(f"Indexing existing CVEs in {year_label}...")
        existing_cves = _collect_existing_cves(report_root, years_to_scan)
        print(f"Indexed {len(existing_cves)} existing CVE(s)")
    
    # Process based on file type
    if args.input_path.suffix == ".jsonl":
        process_jsonl_file(
            args.input_path,
            id_manager,
            create_vulns=args.create_vulns,
            year=args.year,
            dry_run=args.dry_run,
            existing_cves=existing_cves,
        )
    elif args.input_path.suffix == ".json":
        process_json_file(
            args.input_path,
            id_manager,
            create_vuln=args.create_vulns,
            year=args.year,
            dry_run=args.dry_run,
        )
    else:
        print(f"ERROR: Unsupported file type: {args.input_path.suffix}")
        print("Supported types: .jsonl, .json")
        sys.exit(1)


if __name__ == "__main__":
    main()
