#!/usr/bin/env python3

# pyright: reportMissingImports=false, reportMissingModuleSource=false

"""Generate AVID report JSONL for AI supply chain CVEs from AI-CVE-Analyser."""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen

from tqdm import tqdm

avid_db_root = Path(__file__).resolve().parent.parent
workspace_root = avid_db_root.parent
avidtools_path = workspace_root / "avidtools"
sys.path.insert(0, str(avidtools_path))

from avidtools.connectors.cve import (  # noqa: E402
    convert_cve_to_report,
    import_cve,
    save_reports_to_jsonl,
)
from avidtools.datamodels.report import Report  # noqa: E402

DATASET_URL = (
    "https://raw.githubusercontent.com/marcellomaugeri/AI-CVE-Analyser/"
    "refs/heads/main/dataset/"
    "cve_published_labeled_2021-2025_openai_gpt-4o-mini.csv"
)
DATASET_FILENAME = "cve_published_labeled_2021-2025_openai_gpt-4o-mini.csv"
OUTPUT_FILENAME = (
    "ai_supply_chain_cve_reports_2021_2025_openai_gpt-4o-mini.jsonl"
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Download the AI-CVE-Analyser CSV, filter AI-Supply-Chain CVEs, "
            "fetch CVE reports with avidtools, and write them to JSONL."
        )
    )
    parser.add_argument(
        "--dataset-url",
        default=DATASET_URL,
        help="CSV dataset URL to download",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=avid_db_root / "reports" / "review" / DATASET_FILENAME,
        help="Local path for the downloaded CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=avid_db_root / "reports" / "review" / OUTPUT_FILENAME,
        help="Output JSONL path",
    )
    parser.add_argument(
        "--classification",
        default="AI-Supply-Chain",
        help="Classification label to extract from the CSV",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=10,
        help="Maximum number of concurrent CVE fetches",
    )
    return parser.parse_args()


def download_dataset(url: str, destination: Path) -> None:
    """Download the CSV dataset to the requested destination."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(
        url,
        headers={"User-Agent": "avid-db-cve-report-generator/0.1"},
    )
    with urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())


def load_cve_ids(csv_path: Path, classification: str) -> list[str]:
    """Load deduplicated CVE IDs for a classification from the CSV."""
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        cve_ids = {
            (row.get("cve_id") or "").strip()
            for row in reader
            if (row.get("Classification") or "").strip() == classification
            and (row.get("cve_id") or "").strip()
        }
    return sorted(cve_ids)


async def fetch_reports(
    cve_ids: list[str],
    max_concurrent: int,
) -> tuple[list[Report], list[tuple[str, str]]]:
    """Fetch CVEs concurrently and convert them to AVID reports."""
    semaphore = asyncio.Semaphore(max_concurrent)
    reports: list[tuple[str, Report]] = []
    failures: list[tuple[str, str]] = []

    async def process_one(
        cve_id: str,
    ) -> tuple[str, Optional[Report], Optional[str]]:
        async with semaphore:
            try:
                cve = await asyncio.to_thread(import_cve, cve_id)
                report = convert_cve_to_report(cve)
                return cve_id, report, None
            except Exception as exc:  # pragma: no cover
                return cve_id, None, f"{type(exc).__name__}: {exc}"

    tasks = [asyncio.create_task(process_one(cve_id)) for cve_id in cve_ids]

    with tqdm(total=len(tasks), desc="Fetching CVEs", unit="cve") as progress:
        for task in asyncio.as_completed(tasks):
            cve_id, report, error = await task
            if report is not None:
                reports.append((cve_id, report))
            else:
                failures.append((cve_id, error or "Unknown error"))
            progress.update(1)
            progress.set_postfix(success=len(reports), failed=len(failures))

    reports.sort(key=lambda item: item[0])
    failures.sort(key=lambda item: item[0])
    return [report for _, report in reports], failures


def write_failure_log(
    failures: list[tuple[str, str]],
    output_path: Path,
) -> Path:
    """Write a failure log next to the JSONL output."""
    failure_path = output_path.with_suffix(".failures.txt")
    failure_path.write_text(
        "\n".join(f"{cve_id}\t{error}" for cve_id, error in failures) + "\n",
        encoding="utf-8",
    )
    return failure_path


async def main_async(args: argparse.Namespace) -> int:
    """Run the report generation workflow."""
    csv_path = args.csv_path.resolve()
    output_path = args.output.resolve()

    print(f"Downloading dataset to: {csv_path}")
    download_dataset(args.dataset_url, csv_path)

    cve_ids = load_cve_ids(csv_path, args.classification)
    if not cve_ids:
        print(
            (
                "No CVE IDs found for classification "
                f"'{args.classification}' in {csv_path}"
            ),
            file=sys.stderr,
        )
        return 1

    print(
        f"Found {len(cve_ids)} unique CVE IDs with classification "
        f"'{args.classification}'"
    )
    print(f"Writing reports to: {output_path}")

    reports, failures = await fetch_reports(cve_ids, args.max_concurrent)
    save_reports_to_jsonl(reports, str(output_path))

    print(f"Saved {len(reports)} report(s) to {output_path}")
    print(f"Failed to fetch {len(failures)} CVE(s)")

    if failures:
        failure_path = write_failure_log(failures, output_path)
        print(f"Failure log written to: {failure_path}")

    return 0


def main() -> int:
    """CLI entrypoint."""
    args = parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
