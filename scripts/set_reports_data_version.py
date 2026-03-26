"""Set report data_version in reports/<year> folders from a release tag.

Example:
    python set_reports_data_version.py --tag v0.3.3
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def normalize_release_version(tag: str) -> str:
    """Convert a release tag to data_version by removing a leading 'v'."""
    return tag[1:] if tag.startswith("v") else tag


def report_year_directories(report_root: Path, start_year: int) -> list[Path]:
    """Find report year directories from start_year onward."""
    year_dirs: list[Path] = []
    for child in report_root.iterdir():
        if not child.is_dir() or not child.name.isdigit():
            continue

        year = int(child.name)
        if year >= start_year:
            year_dirs.append(child)

    return sorted(year_dirs, key=lambda path: int(path.name))


def set_data_version(
    report_root: Path,
    data_version: str,
    start_year: int,
    dry_run: bool,
) -> tuple[int, int]:
    """Apply data_version to all report JSON files from start_year onward.

    Returns:
        (files_changed, files_examined)
    """
    files_changed = 0
    files_examined = 0

    year_dirs = report_year_directories(
        report_root, start_year=start_year
    )
    for year_dir in year_dirs:
        for report_file in sorted(year_dir.glob("AVID-*.json")):
            files_examined += 1

            with open(report_file, "r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)

            if data.get("data_version") == data_version:
                continue

            data["data_version"] = data_version
            files_changed += 1

            if not dry_run:
                with open(report_file, "w", encoding="utf-8") as file_obj:
                    json.dump(data, file_obj, indent=2)
                    file_obj.write("\n")

    return files_changed, files_examined


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Set data_version on report JSON files in reports/<year> "
            "directories from a start year onward."
        )
    )
    parser.add_argument(
        "--tag",
        required=True,
        help="Release tag (example: v0.3.3 or 0.3.3)",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2025,
        help="Lowest report year directory to include (default: 2025)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    report_root = repo_root / "reports"
    data_version = normalize_release_version(args.tag)

    changed, examined = set_data_version(
        report_root=report_root,
        data_version=data_version,
        start_year=args.start_year,
        dry_run=args.dry_run,
    )

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"{mode}Release tag: {args.tag}")
    print(f"{mode}Applied data_version: {data_version}")
    print(f"{mode}Years covered: reports/{args.start_year} onwards")
    print(f"{mode}Files examined: {examined}")
    print(f"{mode}Files updated: {changed}")


if __name__ == "__main__":
    main()
