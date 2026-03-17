#!/usr/bin/env python3

"""CLI for Inspect report normalize in AVID DB."""

import argparse
import json
import sys
from pathlib import Path
from typing import List

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
    convert_eval_log,
    process_report,
)


parser = argparse.ArgumentParser(
    description=(
        "Normalize Inspect report JSON files or convert Inspect eval logs "
        "into one review JSONL."
    )
)
parser.add_argument(
    "input_paths",
    type=Path,
    nargs="+",
    help="One or more report/eval files or directories",
)
parser.add_argument(
    "--convert-evals",
    action="store_true",
    help="Convert .eval/.json Inspect logs into AVID reports JSONL",
)
parser.add_argument(
    "--normalize",
    action="store_true",
    help="Apply Inspect normalization while converting eval logs",
)
parser.add_argument(
    "--output",
    type=Path,
    default=(
        Path(__file__).resolve().parent.parent.parent
        / "reports"
        / "review"
        / "inspect_eval_reports.jsonl"
    ),
    help="Output JSONL path for --convert-evals mode",
)
parser.add_argument(
    "--s3-bucket",
    type=str,
    default=None,
    help="Optional S3 bucket for uploading eval logs",
)
parser.add_argument(
    "--s3-prefix",
    type=str,
    default="inspect-evals",
    help="S3 key prefix for uploaded eval logs",
)
parser.add_argument(
    "--s3-region",
    type=str,
    default=None,
    help="Optional AWS region for S3 upload",
)
parser.add_argument(
    "--s3-endpoint-url",
    type=str,
    default=None,
    help="Optional custom S3 endpoint URL",
)
args = parser.parse_args()

resolved_inputs = [path.resolve() for path in args.input_paths]


def _collect_files(paths: List[Path], suffixes: tuple[str, ...]) -> List[Path]:
    files: List[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(
                sorted(
                    [
                        candidate
                        for candidate in path.iterdir()
                        if candidate.is_file()
                        and candidate.suffix.lower() in suffixes
                    ]
                )
            )
        elif path.is_file() and path.suffix.lower() in suffixes:
            files.append(path)
    return files


def _report_payload(report):
    if hasattr(report, "model_dump"):
        return report.model_dump(mode="json")
    return report.dict()


if args.convert_evals:
    eval_files = _collect_files(resolved_inputs, (".eval", ".json"))
    if not eval_files:
        print("ERROR: No .eval or .json eval log files found in input paths")
        sys.exit(1)

    converted_reports = []
    for eval_path in eval_files:
        try:
            reports = convert_eval_log(
                str(eval_path),
                normalize=args.normalize,
                s3_bucket=args.s3_bucket,
                s3_key_prefix=args.s3_prefix,
                s3_region=args.s3_region,
                s3_endpoint_url=args.s3_endpoint_url,
            )
            converted_reports.extend(reports)
            print(
                f"Converted {len(reports)} report(s) from eval log: {eval_path}"
            )
        except UnsupportedInspectBenchmarkError as error:
            print(f"Skipped unsupported benchmark eval log: {eval_path} ({error})")
        except Exception as error:
            print(f"ERROR processing eval log {eval_path}: {error}")
            sys.exit(1)

    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file_obj:
        for report in converted_reports:
            file_obj.write(json.dumps(_report_payload(report)))
            file_obj.write("\n")

    print(
        f"Wrote {len(converted_reports)} report(s) to consolidated JSONL: "
        f"{output_path}"
    )
    sys.exit(0)

report_files = _collect_files(resolved_inputs, (".json",))
if not report_files:
    print("ERROR: No report JSON files found in input paths")
    sys.exit(1)

for report_path in report_files:
    try:
        process_report(report_path)
    except UnsupportedInspectBenchmarkError:
        report_path.unlink(missing_ok=True)
        print(f"Deleted unsupported Inspect benchmark report: {report_path}")
    except Exception as error:
        print(f"ERROR: {error}")
        sys.exit(1)
