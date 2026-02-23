#!/usr/bin/env python3

"""Generic review script for AVID report JSON and JSONL files."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from review.normalizers import apply_review_normalizations  # noqa: E402


def _review_report(report: dict) -> None:
    apply_review_normalizations(report)


def process_json_file(
    input_path: Path,
    dry_run: bool,
):
    with input_path.open("r", encoding="utf-8") as file_obj:
        payload = json.load(file_obj)

    reports_reviewed = 0

    if isinstance(payload, dict):
        _review_report(payload)
        reports_reviewed += 1
    elif isinstance(payload, list):
        for index, report in enumerate(payload, 1):
            if not isinstance(report, dict):
                raise ValueError(
                    "Invalid item at index "
                    f"{index} in JSON list: expected object"
                )
            _review_report(report)
            reports_reviewed += 1
    else:
        raise ValueError("Unsupported JSON structure: expected object or list")

    if not dry_run:
        with input_path.open("w", encoding="utf-8") as file_obj:
            json.dump(payload, file_obj, indent=2)
            file_obj.write("\n")

    return reports_reviewed


def process_jsonl_file(
    input_path: Path,
    dry_run: bool,
):
    reports_reviewed = 0
    reviewed_lines = []

    with input_path.open("r", encoding="utf-8") as file_obj:
        for line_num, line in enumerate(file_obj, 1):
            raw_line = line.strip()
            if not raw_line:
                continue

            try:
                report = json.loads(raw_line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_num}: {error.msg}"
                ) from error

            if not isinstance(report, dict):
                raise ValueError(
                    f"Invalid JSON object on line {line_num}: expected object"
                )

            _review_report(report)
            reports_reviewed += 1
            reviewed_lines.append(json.dumps(report, ensure_ascii=False))

    if not dry_run:
        with input_path.open("w", encoding="utf-8") as file_obj:
            if reviewed_lines:
                file_obj.write("\n".join(reviewed_lines) + "\n")

    return reports_reviewed


def main():
    parser = argparse.ArgumentParser(
        description="Review reports and normalize input files in place."
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to .json or .jsonl file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show review count without writing changes",
    )

    args = parser.parse_args()

    input_path = args.input_path.resolve()
    if not input_path.exists() or not input_path.is_file():
        print(f"ERROR: Input file does not exist: {input_path}")
        sys.exit(1)

    try:
        if input_path.suffix == ".json":
            reports_reviewed = process_json_file(
                input_path,
                args.dry_run,
            )
        elif input_path.suffix == ".jsonl":
            reports_reviewed = process_jsonl_file(
                input_path,
                args.dry_run,
            )
        else:
            print(f"ERROR: Unsupported file type: {input_path.suffix}")
            print("Supported types: .json, .jsonl")
            sys.exit(1)
    except Exception as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    print(f"Reviewed {reports_reviewed} report(s) in {input_path}")
    if args.dry_run:
        print("Dry run complete: no file changes were written")
    else:
        print("Saved normalized updates in place")


if __name__ == "__main__":
    main()
