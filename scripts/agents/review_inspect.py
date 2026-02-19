#!/usr/bin/env python3

import argparse
import json
import re
import sys
from html import unescape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


SITE_ROOT = "https://ukgovernmentbeis.github.io/inspect_evals"
CYSE2_URL = (
    "https://ukgovernmentbeis.github.io/inspect_evals/evals/"
    "cybersecurity/cyberseceval_2/"
)
PATTERN = re.compile(
    r"^Evaluation of the LLM (.+?) on the (.+?) benchmark using Inspect Evals$"
)
CATEGORY_CANDIDATES = ("safeguards", "scheming", "bias")


def _to_list(value):
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _clean_html_to_text(fragment: str) -> str:
    text = re.sub(r"<script[\\s\\S]*?</script>", "", fragment, flags=re.I)
    text = re.sub(r"<style[\\s\\S]*?</style>", "", text, flags=re.I)
    text = re.sub(r"<br\\s*/?>", "\\n", text, flags=re.I)
    text = re.sub(r"</p>", "\\n\\n", text, flags=re.I)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.I)
    text = re.sub(r"</li>", "\\n", text, flags=re.I)
    text = re.sub(
        r"</(h[1-6]|div|section|article|ul|ol|table|tr)>",
        "\\n",
        text,
        flags=re.I,
    )
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = text.replace("\\\\n", "\n")
    text = text.replace("\\\\t", "\t")
    text = re.sub(r"\\r", "", text)
    text = re.sub(r"[ \t]+\\n", "\\n", text)
    text = re.sub(r"\\n{3,}", "\\n\\n", text)
    return text.strip()


def _extract_section(html: str, section_id: str) -> str:
    candidates = [
        section_id,
        f"{section_id}Anchor",
        f"{section_id.lower()}anchor",
    ]

    marker_index = -1
    for candidate in candidates:
        marker = f'id="{candidate}"'
        marker_index = html.find(marker)
        if marker_index >= 0:
            break

    if marker_index < 0:
        return ""

    heading_start = html.rfind("<h", 0, marker_index)
    if heading_start < 0:
        return ""

    heading_close_tag_start = html.find("</h", marker_index)
    if heading_close_tag_start < 0:
        return ""

    heading_close_tag_end = html.find(">", heading_close_tag_start)
    if heading_close_tag_end < 0:
        return ""

    section_start = heading_close_tag_end + 1

    next_heading = re.search(
        r"<h[1-6][^>]*id=\"[^\"]+\"",
        html[section_start:],
        flags=re.I,
    )
    if next_heading:
        section_end = section_start + next_heading.start()
    else:
        section_end = len(html)

    fragment = html[section_start:section_end]
    return _clean_html_to_text(fragment)


def _fetch_sections(benchmark: str):
    if benchmark.startswith("cyse2_"):
        try:
            with urlopen(CYSE2_URL, timeout=30) as response:
                html = response.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError) as error:
            raise RuntimeError(
                "Failed to fetch Inspect Evals page for cyse2 benchmark: "
                f"{error}"
            ) from error

        overview = _extract_section(html, "overview")
        scoring = _extract_section(html, "scoring")
        if not overview or not scoring:
            fallback_overview = (
                f"The benchmark {benchmark} is implemented by "
                "Inspect Evals. More details are available "
                f"[here]({CYSE2_URL})."
            )
            fallback_scoring = (
                "Scoring details are available "
                f"[here]({CYSE2_URL})."
            )
            return benchmark, fallback_overview, fallback_scoring

        return benchmark, overview, scoring

    candidates = [benchmark]
    if "_" in benchmark:
        candidates.append(benchmark.split("_", 1)[0])

    for category in CATEGORY_CANDIDATES:
        for slug in candidates:
            try:
                url = f"{SITE_ROOT}/evals/{category}/{slug}/"
                with urlopen(url, timeout=30) as response:
                    html = response.read().decode("utf-8", errors="replace")
            except (HTTPError, URLError):
                continue

            overview = _extract_section(html, "overview")
            scoring = _extract_section(html, "scoring")
            if not overview or not scoring:
                fallback_overview = (
                    f"The benchmark {benchmark} is implemented by "
                    "Inspect Evals. More details are available "
                    f"[here]({url})."
                )
                fallback_scoring = (
                    "Scoring details are available "
                    f"[here]({url})."
                )
                return slug, fallback_overview, fallback_scoring

            return slug, overview, scoring

    raise RuntimeError(
        "No matching Inspect Evals page found under categories "
        f"{CATEGORY_CANDIDATES} for benchmark '{benchmark}'"
    )


def _update_developer_deployer(report: dict):
    affects = report.setdefault("affects", {})
    developer = _to_list(affects.get("developer"))
    deployer = _to_list(affects.get("deployer"))

    if developer:
        canonical = developer
    else:
        canonical = deployer

    affects["developer"] = canonical
    affects["deployer"] = canonical


def _build_new_description(
    model_name: str,
    overview: str,
    scoring: str,
) -> str:
    return (
        f"{overview}\n\n"
        f"We evaluated the LLM {model_name} on this benchmark.\n\n"
        "## Measurement details\n\n"
        f"{scoring}"
    )


def _first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def process_report(file_path: Path):
    with file_path.open("r", encoding="utf-8") as file_obj:
        report = json.load(file_obj)

    problem_desc = (
        report.get("problemtype", {})
        .get("description", {})
        .get("value", "")
    )
    match = PATTERN.match(problem_desc)
    if not match:
        sys.exit(
            "problemtype.description.value is not in expected format: "
            "Evaluation of the LLM $X on the $Y benchmark using Inspect Evals"
        )

    model_name = match.group(1)
    benchmark = match.group(2)

    _, overview, scoring = _fetch_sections(benchmark)
    overview = _first_line(overview)

    description = report.setdefault("description", {})
    description["value"] = _build_new_description(
        model_name=model_name,
        overview=overview,
        scoring=scoring,
    )
    if "lang" not in description:
        description["lang"] = "eng"

    _update_developer_deployer(report)

    with file_path.open("w", encoding="utf-8") as file_obj:
        json.dump(report, file_obj, indent=2)
        file_obj.write("\n")

    print(f"Updated {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Review and correct Inspect Evals AVID report JSON files."
    )
    parser.add_argument("report", type=Path, help="Path to report JSON file")
    args = parser.parse_args()

    report_path = args.report.resolve()
    if not report_path.exists() or not report_path.is_file():
        sys.exit(f"Report file does not exist: {report_path}")

    process_report(report_path)


if __name__ == "__main__":
    main()
