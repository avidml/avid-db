"""
Publisher module for AVID database.

Handles conversion of Reports to Vulnerabilities and file management.
"""

import json
import sys
from datetime import date
from pathlib import Path
from typing import Optional

# Add avidtools to path for imports
avidtools_path = Path(__file__).parent.parent.parent.parent / "avidtools"
sys.path.insert(0, str(avidtools_path))

from avidtools.datamodels.report import Report, ReportMetadata  # noqa: E402
from avidtools.datamodels.vulnerability import (  # noqa: E402
    Vulnerability,
    VulnMetadata,
    ReportSummary,
)
from avidtools.datamodels.components import AvidTaxonomy  # noqa: E402


def _flatten_report_metrics(data: dict) -> dict:
    """Convert Metric schema entries to legacy flat report metric objects."""

    metrics = data.get("metrics")
    if not isinstance(metrics, list):
        return data

    flattened = []
    changed = False
    for metric in metrics:
        if (
            isinstance(metric, dict)
            and "name" in metric
            and "results" in metric
            and "detection_method" in metric
        ):
            results = metric.get("results") or {}
            detection_method = metric.get("detection_method") or {}
            flattened.append(
                {
                    "scorer": results.get("scorer")
                    or detection_method.get("name"),
                    "metrics": metric.get("name"),
                    "value": results.get("value"),
                }
            )
            changed = True
        else:
            flattened.append(metric)

    if changed:
        data = dict(data)
        data["metrics"] = flattened
    return data


def load_report_from_json(file_path: Path) -> Report:
    """
    Load a Report object from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Report object
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Report(**data)


def save_report_to_json(report: Report, file_path: Path):
    """
    Save a Report object to a JSON file.
    
    Args:
        report: Report object to save
        file_path: Path to save the JSON file
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        report_data = report.model_dump(mode="json", exclude_none=True)
        report_data = _flatten_report_metrics(report_data)
        json.dump(report_data, f, indent=2)


def save_vulnerability_to_json(vuln: Vulnerability, file_path: Path):
    """
    Save a Vulnerability object to a JSON file.
    
    Args:
        vuln: Vulnerability object to save
        file_path: Path to save the JSON file
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json_str = vuln.model_dump_json(exclude_none=True, indent=2)
        f.write(json_str)


def assign_report_id(report: Report, report_id: str) -> Report:
    """
    Assign an AVID Report ID to a report.
    
    Args:
        report: Report object
        report_id: AVID Report ID (e.g., 'AVID-2025-R0001')
        
    Returns:
        Report with assigned ID
    """
    if report.metadata is None:
        report.metadata = ReportMetadata(report_id=report_id)
    else:
        report.metadata.report_id = report_id
    return report


def create_vulnerability_from_report(
    report: Report, vuln_id: str
) -> Vulnerability:
    """
    Create a Vulnerability object from a Report.
    
    Uses the Vulnerability.ingest() pattern but properly sets up the
    vulnerability with metadata and dates.
    
    Args:
        report: Report object to convert
        vuln_id: AVID Vulnerability ID (e.g., 'AVID-2025-V001')
        
    Returns:
        Vulnerability object
    """
    vuln = Vulnerability(
        metadata=VulnMetadata(vuln_id=vuln_id),
        data_type=report.data_type,
        data_version=report.data_version,
        affects=report.affects,
        problemtype=report.problemtype,
        description=report.description,
        references=report.references,
        impact=report.impact,
        credit=report.credit,
        published_date=date.today(),
        last_modified_date=date.today(),
    )
    
    # Remove vuln_id from impact.avid if it exists (per ingest pattern)
    if vuln.impact is not None and vuln.impact.avid is not None:
        vuln.impact.avid = AvidTaxonomy(
            risk_domain=vuln.impact.avid.risk_domain,
            sep_view=vuln.impact.avid.sep_view,
            lifecycle_view=vuln.impact.avid.lifecycle_view,
            taxonomy_version=vuln.impact.avid.taxonomy_version,
        )
    
    # Add report summary if report has an ID
    if report.metadata and report.metadata.report_id:
        report_summary = ReportSummary(
            report_id=report.metadata.report_id,
            type=report.problemtype.type if report.problemtype else None,
            name=report.description.value if report.description else vuln_id,
        )
        vuln.reports = [report_summary]
    
    return vuln


def publish_report(
    report: Report, report_id: str, year: Optional[int] = None
) -> Path:
    """
    Publish a report: assign ID and save to year directory.
    
    Args:
        report: Report object
        report_id: AVID Report ID to assign
        year: Year for directory structure. Defaults to current year.
        
    Returns:
        Path where the report was saved
    """
    if year is None:
        year = date.today().year
    
    # Assign ID
    report = assign_report_id(report, report_id)
    
    # Determine output path
    script_dir = Path(__file__).parent.parent.parent
    reports_dir = script_dir / "reports" / str(year)
    output_path = reports_dir / f"{report_id}.json"
    
    # Save
    save_report_to_json(report, output_path)
    
    return output_path


def publish_vulnerability(
    vuln: Vulnerability, vuln_id: str, year: Optional[int] = None
) -> Path:
    """
    Publish a vulnerability: save to year directory.
    
    Args:
        vuln: Vulnerability object
        vuln_id: AVID Vulnerability ID (should already be in vuln.metadata)
        year: Year for directory structure. Defaults to current year.
        
    Returns:
        Path where the vulnerability was saved
    """
    if year is None:
        year = date.today().year
    
    # Determine output path
    script_dir = Path(__file__).parent.parent.parent
    vulns_dir = script_dir / "vulnerabilities" / str(year)
    output_path = vulns_dir / f"{vuln_id}.json"
    
    # Save
    save_vulnerability_to_json(vuln, output_path)
    
    return output_path
