"""Reusable normalization helpers for report review scripts."""

from __future__ import annotations

from typing import List, Optional


INSPECT_MODEL_PREFIX = "Evaluation of the LLM "
INSPECT_MODEL_SUFFIX = " on the "


def _to_list(value):
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def extract_model_names(
    report: dict,
    preferred_model_name: Optional[str] = None,
) -> List[str]:
    model_names: List[str] = []

    if preferred_model_name:
        model_names.append(str(preferred_model_name))

    affects = report.get("affects", {})
    artifacts = affects.get("artifacts")
    if isinstance(artifacts, list):
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            artifact_name = artifact.get("name")
            if artifact_name:
                model_names.append(str(artifact_name))

    problem_desc = (
        report.get("problemtype", {})
        .get("description", {})
        .get("value", "")
    )
    if (
        isinstance(problem_desc, str)
        and problem_desc.startswith(INSPECT_MODEL_PREFIX)
        and INSPECT_MODEL_SUFFIX in problem_desc
    ):
        model_name = (
            problem_desc[len(INSPECT_MODEL_PREFIX):]
            .split(INSPECT_MODEL_SUFFIX, 1)[0]
            .strip()
        )
        if model_name:
            model_names.append(model_name)

    deduped: List[str] = []
    seen = set()
    for name in model_names:
        normalized = name.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)

    return deduped


def _infer_developer_from_models(model_names: List[str]) -> Optional[str]:
    for model_name in model_names:
        normalized = model_name.lower()
        if "llama" in normalized:
            return "Meta"
        if "mistral" in normalized:
            return "Mistral"
        if "deepseek" in normalized:
            return "DeepSeek"
    return None


def apply_model_developer_mapping(
    report: dict,
    model_names: Optional[List[str]] = None,
) -> bool:
    affects = report.setdefault("affects", {})
    if model_names is None:
        model_names = extract_model_names(report)

    inferred = _infer_developer_from_models(model_names)
    if inferred is None:
        return False

    affects["developer"] = [inferred]
    deployer = _to_list(affects.get("deployer"))
    if not deployer:
        affects["deployer"] = [inferred]
    return True


def apply_openai_system_artifact_type(
    report: dict,
    model_names: Optional[List[str]] = None,
) -> bool:
    affects = report.setdefault("affects", {})
    artifacts = affects.get("artifacts")
    if not isinstance(artifacts, list):
        return False

    if model_names is None:
        model_names = extract_model_names(report)

    developer_values = _to_list(affects.get("developer"))
    deployer_values = _to_list(affects.get("deployer"))

    openai_context = (
        any("gpt" in model.lower() for model in model_names)
        or any("openai" in value.lower() for value in developer_values)
        or any("openai" in value.lower() for value in deployer_values)
    )

    updated = False
    gpt_artifact_found = False

    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        artifact_name = str(artifact.get("name", ""))
        if "gpt" in artifact_name.lower():
            artifact["type"] = "System"
            updated = True
            gpt_artifact_found = True

    if openai_context and not gpt_artifact_found:
        for artifact in artifacts:
            if isinstance(artifact, dict):
                artifact["type"] = "System"
                updated = True
                break

    return updated


def apply_review_normalizations(
    report: dict,
    preferred_model_name: Optional[str] = None,
) -> bool:
    model_names = extract_model_names(
        report,
        preferred_model_name=preferred_model_name,
    )
    artifacts_updated = apply_openai_system_artifact_type(
        report,
        model_names=model_names,
    )
    developer_updated = apply_model_developer_mapping(
        report,
        model_names=model_names,
    )
    return artifacts_updated or developer_updated
