#!/usr/bin/env python3

# pyright: reportMissingImports=false, reportMissingModuleSource=false

"""Filter AI supply-chain CVE reports for AVID suitability using an LLM."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import re
import sys
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI
from tqdm import tqdm


DEFAULT_INPUT = (
    Path(__file__).resolve().parent.parent
    / "reports"
    / "review"
    / "ai_supply_chain_cve_reports_2021_2025_openai_gpt-4o-mini.jsonl"
)
DEFAULT_DECISIONS = (
    Path(__file__).resolve().parent.parent
    / "reports"
    / "review"
    / (
        "ai_supply_chain_cve_reports_2021_2025_openai_gpt-4o-mini."
        "filter_decisions.jsonl"
    )
)
DEFAULT_PASSED = (
    Path(__file__).resolve().parent.parent
    / "reports"
    / "review"
    / (
        "ai_supply_chain_cve_reports_2021_2025_openai_gpt-4o-mini."
        "filtered_pass.jsonl"
    )
)

CVE_REGEX = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)

SYSTEM_PROMPT = """
You are a strict AVID review filter.

Task:
Given one AVID report candidate converted from a CVE,
decide if it should be kept for AVID curation as a vulnerability
in the supply chain of general-purpose AI systems.

IMPORTANT SCOPE:
- Focus on software supply chain issues.
- Exclude hardware-only or firmware-only vulnerabilities unless there is
    clear software supply-chain impact in AI software stacks.

Return JSON only with this schema:
{
  "pass": boolean,
  "reasoning": string,
  "labels": {
    "is_ai_related": boolean,
    "is_gpai_supply_chain": boolean,
    "is_security_or_safety_vuln": boolean,
    "sufficient_evidence": boolean
  },
  "confidence": "high" | "medium" | "low"
}

Decision guidance:
- pass=true only if all four label checks are true.
- is_ai_related: vulnerability concerns AI/ML systems, models,
    AI frameworks, AI tooling, AI hardware/firmware usage,
    or software commonly used in ML pipelines.
- is_gpai_supply_chain: issue is in components used to build, train,
    package, deploy, serve, or run general-purpose AI systems
    (dependencies, runtimes, kernels, drivers, orchestration,
    model-serving libraries, data/feature pipelines, etc.).
    Prefer software packages, frameworks, model serving stacks,
    dependency chains, CI/CD, and artifact ecosystems.
    Hardware-only and firmware-only issues should be false.
- is_security_or_safety_vuln: includes CVE-style vulnerability behavior
    (RCE, privilege escalation, tampering, DoS, data exfiltration,
    integrity compromise, etc.).
- sufficient_evidence: report text/reference gives enough signal
    for this classification.

Be conservative: if uncertain, set pass=false and explain why.
""".strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run an LLM filter over AI-supply-chain CVE report JSONL and keep "
            "only entries that pass AVID suitability criteria."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_PASSED)
    parser.add_argument(
        "--model",
        default="gpt-5-nano",
        help="Model to use for filtering",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=64,
        help="Maximum concurrent LLM calls",
    )
    parser.add_argument("--max-items", type=int, default=None)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse existing decisions file and process only missing entries",
    )
    return parser.parse_args()


def load_dotenv_if_needed() -> None:
    if os.getenv("OPENAI_API_KEY"):
        return
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key == "OPENAI_API_KEY" and value:
            os.environ[key] = value
            return


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def extract_cve_id(report: dict[str, Any]) -> str:
    references = report.get("references") or []
    for ref in references:
        url = str((ref or {}).get("url") or "")
        match = CVE_REGEX.search(url)
        if match:
            return match.group(0).upper()

    problemtype = report.get("problemtype") or {}
    description = (problemtype.get("description") or {}).get("value") or ""
    match = CVE_REGEX.search(str(description))
    if match:
        return match.group(0).upper()

    return "UNKNOWN-CVE"


def compact_report_payload(report: dict[str, Any]) -> dict[str, Any]:
    affects = report.get("affects") or {}
    problemtype = report.get("problemtype") or {}
    description = report.get("description") or {}
    impact = report.get("impact") or {}
    references = report.get("references") or []

    return {
        "problemtype": problemtype,
        "description": description,
        "affects": {
            "developer": affects.get("developer"),
            "deployer": affects.get("deployer"),
            "artifacts": affects.get("artifacts"),
        },
        "impact": impact,
        "references": references[:8],
    }


async def call_filter_agent(
    client: AsyncOpenAI,
    model: str,
    cve_id: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    payload = compact_report_payload(report)
    user_prompt = (
        f"CVE ID: {cve_id}\n"
        "Evaluate the following AVID candidate report:\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )

    retry_delay = 0.4
    response = None
    last_error: Exception | None = None

    while True:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            break
        except Exception as exc:
            last_error = exc
            msg = str(exc).lower()
            is_rate_limited = (
                "rate limit" in msg
                or "429" in msg
                or "rate_limit_exceeded" in msg
            )
            if not is_rate_limited:
                raise

            jitter = random.uniform(0.0, 0.25)
            await asyncio.sleep(retry_delay + jitter)
            retry_delay = min(retry_delay * 2, 8.0)

    if response is None:
        raise RuntimeError("No response from model") from last_error

    content = response.choices[0].message.content or "{}"
    decision = json.loads(content)

    labels = decision.get("labels") or {}
    required = [
        bool(labels.get("is_ai_related")),
        bool(labels.get("is_gpai_supply_chain")),
        bool(labels.get("is_security_or_safety_vuln")),
        bool(labels.get("sufficient_evidence")),
    ]
    decision["pass"] = bool(decision.get("pass")) and all(required)

    return {
        "cve_id": cve_id,
        "pass": decision["pass"],
        "reasoning": str(decision.get("reasoning") or ""),
        "labels": {
            "is_ai_related": bool(labels.get("is_ai_related")),
            "is_gpai_supply_chain": bool(labels.get("is_gpai_supply_chain")),
            "is_security_or_safety_vuln": bool(
                labels.get("is_security_or_safety_vuln")
            ),
            "sufficient_evidence": bool(labels.get("sufficient_evidence")),
        },
        "confidence": str(decision.get("confidence") or "low"),
        "model": model,
    }


def append_pass_reason_to_description(
    report: dict[str, Any],
    reasoning: str,
) -> dict[str, Any]:
    updated = dict(report)
    description = dict(updated.get("description") or {})
    lang = description.get("lang") or "eng"
    existing = str(description.get("value") or "").strip()
    reason = reasoning.strip()

    if not reason:
        return updated

    rationale = f"[AVID Filter Pass Reason] {reason}"
    description["lang"] = lang
    description["value"] = (
        f"{existing}\n\n{rationale}" if existing else rationale
    )
    updated["description"] = description
    return updated


def load_prior_decisions(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    prior: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            cve_id = str(item.get("cve_id") or "")
            if cve_id:
                prior[cve_id] = item
    return prior


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    args = parse_args()
    load_dotenv_if_needed()

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set", file=sys.stderr)
        return 1

    input_path = args.input.resolve()
    decision_path = args.decisions.resolve()
    output_path = args.output.resolve()

    reports = read_jsonl(input_path)
    if args.max_items is not None:
        reports = reports[: args.max_items]

    prior = load_prior_decisions(decision_path) if args.resume else {}
    model = str(args.model).strip()
    if not model:
        print("No model provided", file=sys.stderr)
        return 1

    if args.max_concurrent < 1:
        print("--max-concurrent must be >= 1", file=sys.stderr)
        return 1

    decisions: list[dict[str, Any] | None] = [None] * len(reports)
    passed_reports: list[tuple[int, dict[str, Any]]] = []

    async def run_async() -> None:
        client = AsyncOpenAI()
        semaphore = asyncio.Semaphore(args.max_concurrent)

        async def process_one(index: int, report: dict[str, Any]) -> None:
            cve_id = extract_cve_id(report)
            if cve_id in prior:
                decisions[index] = prior[cve_id]
                return

            async with semaphore:
                decisions[index] = await call_filter_agent(
                    client=client,
                    model=model,
                    cve_id=cve_id,
                    report=report,
                )

        tasks = [
            asyncio.create_task(process_one(index, report))
            for index, report in enumerate(reports)
        ]

        with tqdm(
            total=len(tasks),
            desc="Filtering reports",
            unit="report",
        ) as bar:
            for done in asyncio.as_completed(tasks):
                await done
                bar.update(1)

                completed = sum(item is not None for item in decisions)
                passed = sum(
                    1
                    for item in decisions
                    if item is not None and bool(item.get("pass"))
                )
                bar.set_postfix(
                    passed=passed,
                    rejected=completed - passed,
                )

    try:
        asyncio.run(run_async())
    except Exception as error:
        print(f"Filtering failed: {error}", file=sys.stderr)
        return 1

    finalized_decisions: list[dict[str, Any]] = []
    for index, item in enumerate(decisions):
        if item is None:
            print(f"Missing decision for index {index}", file=sys.stderr)
            return 1
        finalized_decisions.append(item)
        if item.get("pass"):
            passed_reports.append(
                (
                    index,
                    append_pass_reason_to_description(
                        reports[index],
                        str(item.get("reasoning") or ""),
                    ),
                )
            )

    passed_reports_sorted = [report for _, report in sorted(passed_reports)]

    write_jsonl(decision_path, finalized_decisions)
    write_jsonl(output_path, passed_reports_sorted)

    print(f"Input reports: {len(reports)}")
    print(f"Passed reports: {len(passed_reports_sorted)}")
    print(f"Rejected reports: {len(reports) - len(passed_reports_sorted)}")
    print(f"Decisions file: {decision_path}")
    print(f"Filtered output: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
