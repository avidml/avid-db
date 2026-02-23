#!/usr/bin/env python3

"""Garak-specific review script for AVID report JSON and JSONL files."""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).parent.parent))

from review.normalizers import (  # noqa: E402
    apply_review_normalizations,
    choose_model_subject_label,
)


PROBE_PATTERN = re.compile(r"probe\s+`([^`]+)`")
GITHUB_PROBE_BLOB_BASE = (
    "https://github.com/NVIDIA/garak/blob/main/garak/probes"
)
GARAK_REFERENCE_BASE = "https://reference.garak.ai/en/latest"
CACHE_PATH = Path(__file__).parent / ".garak_probe_summary_cache.json"


def _to_list(value):
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _get_openai_api_key() -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key.strip().strip('"').strip("'")

    candidate_env_paths = [
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
        Path.cwd() / ".env",
    ]

    line_pattern = re.compile(
        r"^(?:export\s+)?OPENAI_API_KEY\s*=\s*(.+?)\s*$"
    )

    for env_path in candidate_env_paths:
        if not env_path.exists():
            continue
        try:
            with env_path.open("r", encoding="utf-8") as file_obj:
                for line in file_obj:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    match = line_pattern.match(stripped)
                    if not match:
                        continue
                    value = match.group(1).split(" #", 1)[0].strip()
                    cleaned = value.strip().strip('"').strip("'")
                    if cleaned:
                        os.environ["OPENAI_API_KEY"] = cleaned
                        return cleaned
        except Exception:
            continue

    return None


def _extract_probe_name(report: dict) -> Optional[str]:
    candidates = [
        (
            report.get("problemtype", {})
            .get("description", {})
            .get("value", "")
        ),
        report.get("description", {}).get("value", ""),
    ]

    for text in candidates:
        if not isinstance(text, str):
            continue
        match = PROBE_PATTERN.search(text)
        if match:
            return match.group(1).strip()

    return None


def _probe_urls(probe_name: str):
    module_name = probe_name.split(".", 1)[0]
    return (
        f"{GITHUB_PROBE_BLOB_BASE}/{module_name}.py",
        f"{GARAK_REFERENCE_BASE}/garak.probes.{module_name}.html",
    )


def _failsafe_probe_description(probe_name: str) -> str:
    browser_url, _ = _probe_urls(probe_name)
    return (
        f"More information on the probe `{probe_name}` is available "
        f"[here]({browser_url})"
    )


def _module_name_from_probe(probe_name: str) -> str:
    return probe_name.split(".", 1)[0] if "." in probe_name else probe_name


def _ensure_required_probe_suffix(
    probe_name: str,
    summary: str,
    module_behavior: str,
) -> str:
    module_name = _module_name_from_probe(probe_name)
    base = summary.strip().rstrip(".")
    behavior = module_behavior.strip().rstrip(".")

    tests_clause = base
    lower_base = base.lower()
    if " tests " in lower_base:
        split_index = lower_base.find(" tests ")
        tests_clause = base[split_index + len(" tests "):].strip()
    elif lower_base.startswith("tests "):
        tests_clause = base[len("tests "):].strip()
    elif lower_base.startswith("this probe tests "):
        tests_clause = base[len("this probe tests "):].strip()

    if not tests_clause:
        tests_clause = "model behavior under this probe scenario"
    if not behavior:
        behavior = "evaluates model behavior for this probe family"

    return (
        f"The probe {probe_name} tests {tests_clause}. "
        f"This probe is part of the {module_name} module which {behavior}."
    )


def _normalize_probe_summary_with_suffix(
    probe_name: str,
    summary: str,
) -> str:
    text = summary.strip()
    if not text:
        return _ensure_required_probe_suffix(
            probe_name,
            "",
            "evaluates model behavior for this probe family",
        )

    marker = "this probe is part of the "
    lower_text = text.lower()

    summary_core = text
    module_behavior = "evaluates model behavior for this probe family"

    marker_index = lower_text.find(marker)
    if marker_index >= 0:
        summary_core = text[:marker_index].strip().rstrip(".")
        behavior_match = re.search(
            r"which(?:\s+does)?\s+([^\.]+)",
            text[marker_index:],
            flags=re.I,
        )
        if behavior_match:
            module_behavior = behavior_match.group(1).strip()
    else:
        behavior_match = re.search(
            r"which(?:\s+does)?\s+([^\.]+)",
            text,
            flags=re.I,
        )
        if behavior_match:
            module_behavior = behavior_match.group(1).strip()

    return _ensure_required_probe_suffix(
        probe_name,
        summary_core,
        module_behavior,
    )


def _clean_html_to_text(fragment: str) -> str:
    text = re.sub(r"<script[\\s\\S]*?</script>", " ", fragment, flags=re.I)
    text = re.sub(r"<style[\\s\\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = re.sub(r"\\s+", " ", text)
    return text.strip()


def _extract_probe_reference_text(html: str, probe_name: str) -> str:
    module_name, class_name = (
        probe_name.split(".", 1)
        if "." in probe_name
        else (probe_name, "")
    )

    class_markers = [
        f"garak.probes.{module_name}.{class_name}",
        f'class="sig-name descname"><span class="pre">{class_name}</span>',
        f'id="garak.probes.{module_name}.{class_name}"',
    ]

    marker_index = -1
    for marker in class_markers:
        marker_index = html.find(marker)
        if marker_index >= 0:
            break

    if marker_index >= 0:
        start = max(0, marker_index - 5000)
        end = min(len(html), marker_index + 20000)
        fragment = html[start:end]
    else:
        fragment = html[:30000]

    return _clean_html_to_text(fragment)


def _fetch_probe_reference_text(probe_name: str) -> Optional[str]:
    _, reference_url = _probe_urls(probe_name)
    request = Request(
        reference_url,
        headers={"User-Agent": "avid-db-garak-review/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError):
        return None

    text = _extract_probe_reference_text(html, probe_name)
    return text or None


async def _summarize_probe_docstring(
    api_key: Optional[str],
    probe_name: str,
) -> str:
    reference_text = await asyncio.to_thread(
        _fetch_probe_reference_text,
        probe_name,
    )
    if not reference_text:
        return _failsafe_probe_description(probe_name)

    if not api_key:
        return _failsafe_probe_description(probe_name)

    try:
        text = await asyncio.to_thread(
            _summarize_docstring_via_openai_http,
            api_key,
            probe_name,
            reference_text,
        )
        if text:
            return text
    except Exception:
        return _failsafe_probe_description(probe_name)

    return _failsafe_probe_description(probe_name)


def _load_probe_summary_cache(cache_path: Path) -> Dict[str, str]:
    if not cache_path.exists():
        return {}

    try:
        with cache_path.open("r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
        if isinstance(data, dict):
            return {str(key): str(value) for key, value in data.items()}
    except Exception:
        return {}

    return {}


def _save_probe_summary_cache(cache_path: Path, cache: Dict[str, str]):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as file_obj:
        json.dump(cache, file_obj, indent=2, ensure_ascii=False)
        file_obj.write("\n")


def _summarize_docstring_via_openai_http(
    api_key: str,
    probe_name: str,
    reference_text: str,
) -> str:
    snippet = reference_text[:12000]
    payload = {
        "model": "gpt-4o-mini",
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Summarize security probe documentation for technical "
                    "incident reports. Return strict JSON with keys "
                    "summary and module_behavior."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Use only the documentation text provided. Return JSON "
                    "with: (1) summary = one short sentence about what this "
                    "specific probe tests (<=25 words), (2) module_behavior "
                    "= short phrase starting with a verb that describes what "
                    "the module does (<=12 words).\n\n"
                    f"Probe: {probe_name}\n"
                    f"Reference text:\n{snippet}"
                ),
            },
        ],
    }

    response_data = None
    max_attempts = 4
    for attempt in range(1, max_attempts + 1):
        request = Request(
            url="https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=45) as response:
                response_data = json.loads(
                    response.read().decode("utf-8", errors="replace")
                )
            break
        except HTTPError as error:
            status = getattr(error, "code", None)
            is_retryable = (
                status == 429
                or (status is not None and status >= 500)
            )
            if attempt >= max_attempts or not is_retryable:
                raise
            time.sleep(1.5 * attempt)
        except URLError:
            if attempt >= max_attempts:
                raise
            time.sleep(1.5 * attempt)

    if response_data is None:
        return ""

    choices = response_data.get("choices", [])
    if not choices:
        return ""

    message = choices[0].get("message", {})
    content = message.get("content", "")
    payload_text = str(content).strip()
    if not payload_text:
        return ""

    if payload_text.startswith("```"):
        payload_text = re.sub(
            r"^```(?:json)?\s*",
            "",
            payload_text,
            flags=re.I,
        )
        payload_text = re.sub(r"\s*```$", "", payload_text)
        payload_text = payload_text.strip()

    try:
        parsed = json.loads(payload_text)
        summary = str(parsed.get("summary", "")).strip()
        module_behavior = str(parsed.get("module_behavior", "")).strip()
        if summary and module_behavior:
            return _ensure_required_probe_suffix(
                probe_name,
                summary,
                module_behavior,
            )
    except Exception:
        match = re.search(r"\{[\s\S]*\}", payload_text)
        if match:
            try:
                parsed = json.loads(match.group(0))
                summary = str(parsed.get("summary", "")).strip()
                module_behavior = str(
                    parsed.get("module_behavior", "")
                ).strip()
                if summary and module_behavior:
                    return _ensure_required_probe_suffix(
                        probe_name,
                        summary,
                        module_behavior,
                    )
            except Exception:
                pass

    return ""


async def _get_probe_summaries_async(
    probe_names,
    cache_path: Path,
) -> Dict[str, str]:
    cache = _load_probe_summary_cache(cache_path)
    unresolved = [
        probe_name
        for probe_name in sorted(set(probe_names))
        if probe_name and probe_name not in cache
    ]

    if not unresolved:
        return cache

    api_key = _get_openai_api_key()
    if not api_key:
        print(
            "WARNING: OPENAI_API_KEY not found in environment/.env; "
            "using failsafe probe descriptions"
        )

    semaphore = asyncio.Semaphore(3)

    async def summarize_one(probe_name: str):
        async with semaphore:
            summary = await _summarize_probe_docstring(api_key, probe_name)
            return probe_name, summary

    results = await asyncio.gather(
        *(summarize_one(probe_name) for probe_name in unresolved),
        return_exceptions=True,
    )

    for result in results:
        if isinstance(result, Exception):
            continue
        probe_name, summary = result
        cache[probe_name] = summary

    generated = len(unresolved)
    fallback_count = 0
    for probe_name in unresolved:
        summary = cache.get(probe_name, "")
        if summary.startswith("More information on the probe `"):
            fallback_count += 1
    api_count = generated - fallback_count
    print(
        "Probe summary cache update: "
        f"generated={generated}, via_openai={api_count}, "
        f"fallback={fallback_count}"
    )

    _save_probe_summary_cache(cache_path, cache)
    return cache


def _shorten_artifact_model_names(report: dict) -> Optional[str]:
    affects = report.setdefault("affects", {})
    artifacts = affects.get("artifacts")
    if not isinstance(artifacts, list):
        return None

    preferred_model = None
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        name = artifact.get("name")
        if not isinstance(name, str):
            continue

        shortened = name.split("/", 1)[1] if "/" in name else name
        artifact["name"] = shortened
        if preferred_model is None:
            preferred_model = shortened

    return preferred_model


def _apply_litellm_deployer_mapping(report: dict):
    affects = report.setdefault("affects", {})
    deployer = _to_list(affects.get("deployer"))

    mapped = []
    changed = False
    for value in deployer:
        if value.strip().lower() == "litellm":
            mapped.append("Together AI")
            changed = True
        else:
            mapped.append(value)

    if changed:
        deduped = []
        seen = set()
        for value in mapped:
            key = value.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(value)
        affects["deployer"] = deduped


def _rebuild_text_descriptions(
    report: dict,
    model_name: str,
    deployer_name: str,
    probe_name: Optional[str],
    probe_summary: str,
    subject_label: str,
):
    if not probe_name:
        return

    problemtype_description = report.setdefault("problemtype", {}).setdefault(
        "description", {}
    )
    problemtype_description["lang"] = "eng"
    problemtype_description["value"] = (
        f"The model {model_name} from {deployer_name} was evaluated by the "
        f"Garak LLM Vulnerability scanner using the probe `{probe_name}`."
    )

    description = report.setdefault("description", {})
    description["lang"] = "eng"
    subject_label_display = "LLM" if subject_label == "llm" else "AI system"
    description["value"] = (
        f"{probe_summary}\n\n"
        f"The {subject_label_display} {model_name} was evaluated on this "
        "probe.\n\n"
        f"The model {model_name} from {deployer_name} was evaluated by the "
        f"Garak LLM Vulnerability scanner using the probe `{probe_name}`."
    )


def _normalize_metric_results(report: dict):
    metrics = report.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        return

    first_metric = metrics[0]
    if not isinstance(first_metric, dict):
        return

    results = first_metric.get("results")
    if isinstance(results, list):
        return

    if not isinstance(results, dict) or not results:
        return

    if not all(isinstance(value, dict) for value in results.values()):
        return

    row_keys = set()
    for column_values in results.values():
        row_keys.update(str(key) for key in column_values.keys())

    def sort_key(item: str):
        if item.isdigit():
            return (0, int(item))
        return (1, item)

    normalized_rows = []
    for row_key in sorted(row_keys, key=sort_key):
        row = {}
        for column_name, column_values in results.items():
            row[column_name] = column_values.get(row_key)
        normalized_rows.append(row)

    first_metric["results"] = normalized_rows


def _extract_primary_model_and_deployer(report: dict):
    affects = report.get("affects", {})

    model_name = None
    artifacts = affects.get("artifacts")
    if isinstance(artifacts, list):
        for artifact in artifacts:
            if isinstance(artifact, dict) and artifact.get("name"):
                model_name = str(artifact["name"])
                break

    if not model_name:
        model_name = "the model"

    deployer = _to_list(affects.get("deployer"))
    deployer_name = deployer[0] if deployer else "the deployment platform"

    return model_name, deployer_name


def _review_report(report: dict, probe_summaries: Dict[str, str]):
    preferred_model_name = _shorten_artifact_model_names(report)
    _apply_litellm_deployer_mapping(report)
    apply_review_normalizations(
        report,
        preferred_model_name=preferred_model_name,
    )

    probe_name = _extract_probe_name(report)
    if probe_name:
        raw_summary = probe_summaries.get(
            probe_name,
            _failsafe_probe_description(probe_name),
        )
        probe_summary = _normalize_probe_summary_with_suffix(
            probe_name,
            raw_summary,
        )
    else:
        probe_summary = "Garak probe metadata is available in the report."

    model_name, deployer_name = _extract_primary_model_and_deployer(report)
    subject_label = choose_model_subject_label(report)
    _rebuild_text_descriptions(
        report,
        model_name=model_name,
        deployer_name=deployer_name,
        probe_name=probe_name,
        probe_summary=probe_summary,
        subject_label=subject_label,
    )
    _normalize_metric_results(report)


def _load_reports(input_path: Path):
    if input_path.suffix == ".json":
        with input_path.open("r", encoding="utf-8") as file_obj:
            payload = json.load(file_obj)

        if isinstance(payload, dict):
            if "data_type" in payload:
                return [payload], "json-single"
            return [], "json-single"

        if isinstance(payload, list):
            reports = []
            for index, item in enumerate(payload, 1):
                if not isinstance(item, dict):
                    raise ValueError(
                        "Invalid item at index "
                        f"{index} in JSON list: expected object"
                    )
                reports.append(item)
            return reports, "json-list"

        raise ValueError("Unsupported JSON structure: expected object or list")

    if input_path.suffix == ".jsonl":
        reports = []
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
                        f"Invalid JSON object on line {line_num}: "
                        "expected object"
                    )
                reports.append(report)

        return reports, "jsonl"

    raise ValueError(f"Unsupported file type: {input_path.suffix}")


def _save_reports(input_path: Path, reports, shape: str):
    if shape == "json-single":
        payload = reports[0] if reports else {}
        with input_path.open("w", encoding="utf-8") as file_obj:
            json.dump(payload, file_obj, indent=2)
            file_obj.write("\n")
        return

    if shape == "json-list":
        with input_path.open("w", encoding="utf-8") as file_obj:
            json.dump(reports, file_obj, indent=2)
            file_obj.write("\n")
        return

    if shape == "jsonl":
        with input_path.open("w", encoding="utf-8") as file_obj:
            if reports:
                for report in reports:
                    file_obj.write(
                        json.dumps(report, ensure_ascii=False) + "\n"
                    )
        return

    raise ValueError(f"Unknown shape: {shape}")


def main():
    parser = argparse.ArgumentParser(
        description="Review Garak reports and normalize input files in place."
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
        reports, shape = _load_reports(input_path)

        probe_names = []
        for report in reports:
            probe_name = _extract_probe_name(report)
            if probe_name:
                probe_names.append(probe_name)

        probe_summaries = asyncio.run(
            _get_probe_summaries_async(probe_names, CACHE_PATH)
        )

        for report in reports:
            _review_report(report, probe_summaries)

        if not args.dry_run:
            _save_reports(input_path, reports, shape)
    except Exception as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    print(f"Reviewed {len(reports)} report(s) in {input_path}")
    if args.dry_run:
        print("Dry run complete: no file changes were written")
    else:
        print("Saved normalized updates in place")


if __name__ == "__main__":
    main()
