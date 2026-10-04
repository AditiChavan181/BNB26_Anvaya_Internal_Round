from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import c2pa


ACTIONS_ASSERTION_LABELS = {
    "c2pa.actions",
    "c2pa.actions.v2",
}

AI_DISCLOSURE_LABEL = "c2pa.ai-disclosure"


def verify_c2pa(file_path: str) -> dict[str, Any]:
    """
    Read and validate C2PA provenance from an asset.

    This service:
    - detects whether C2PA provenance exists
    - validates the manifest through the C2PA SDK
    - extracts AI model disclosure when available
    - extracts generator/tool and issuer information
    - extracts transformation actions
    - extracts ingredient/source history
    - returns a normalized result for ModelLedger

    Important:
    This function NEVER guesses an AI model.
    A model is reported only when the C2PA manifest explicitly
    provides model information.
    """

    path = Path(file_path)

    if not path.is_file():
        return _error_result(
            validation_state="FILE_NOT_FOUND",
            error="File does not exist.",
        )

    try:
        reader = c2pa.Reader(str(path))

        manifest_store = json.loads(reader.json())
        validation_state = str(reader.get_validation_state())

        active_manifest = reader.get_active_manifest()

        if not active_manifest:
            active_manifest_id = manifest_store.get("active_manifest")

            if not active_manifest_id:
                return _error_result(
                    validation_state=validation_state,
                    error="No active C2PA manifest found.",
                )

            active_manifest = (
                manifest_store.get("manifests", {})
                .get(active_manifest_id, {})
            )

        if not isinstance(active_manifest, dict) or not active_manifest:
            return _error_result(
                validation_state=validation_state,
                error="Active C2PA manifest is empty or invalid.",
            )

        validation_results = _safe_validation_results(reader)

        model_info = extract_model(active_manifest)
        tool = extract_tool(active_manifest)
        issuer = extract_issuer(active_manifest)
        actions = extract_actions(active_manifest)
        ingredients = extract_ingredients(active_manifest)

        return {
            "c2pa_found": True,
            "validation_state": validation_state,
            "validation_results": validation_results,
            "model": model_info.get("name"),
            "model_identifier": model_info.get("identifier"),
            "model_type": model_info.get("type"),
            "tool": tool,
            "issuer": issuer,
            "actions": actions,
            "ingredients": ingredients,
            "has_provenance_chain": bool(ingredients),
            "manifest": {
                "claim_generator": active_manifest.get("claim_generator"),
                "title": active_manifest.get("title"),
            },
            "error": None,
        }

    except Exception as exc:
        return _error_result(
            validation_state="ERROR",
            error=f"C2PA verification failed: {exc}",
        )


def extract_model(manifest: dict[str, Any]) -> dict[str, Any]:
    """
    Extract explicitly declared AI model information.

    Priority:
    1. Standard c2pa.ai-disclosure assertion
    2. Explicit model fields in claim-generator metadata

    We deliberately do NOT treat claim_generator/name as the AI model.
    A claim generator identifies the software/actor making the provenance
    claim, not necessarily the underlying AI model.
    """

    for assertion in manifest.get("assertions", []):
        if not isinstance(assertion, dict):
            continue

        if assertion.get("label") != AI_DISCLOSURE_LABEL:
            continue

        data = assertion.get("data", {})

        if not isinstance(data, dict):
            continue

        # Current C2PA AI Disclosure structure.
        model_name = data.get("modelName")
        model_identifier = data.get("modelIdentifier")
        model_type = data.get("modelType")

        if model_name or model_identifier or model_type:
            return {
                "name": model_name,
                "identifier": model_identifier,
                "type": model_type,
            }

    # Provider-specific / legacy explicit model metadata.
    claim_generator_info = manifest.get("claim_generator_info", [])

    if isinstance(claim_generator_info, list):
        for item in claim_generator_info:
            if not isinstance(item, dict):
                continue

            model = item.get("model")

            if isinstance(model, dict):
                return {
                    "name": model.get("name"),
                    "identifier": model.get("identifier"),
                    "type": model.get("type"),
                }

            if isinstance(model, str):
                return {
                    "name": model,
                    "identifier": None,
                    "type": None,
                }

    return {
        "name": None,
        "identifier": None,
        "type": None,
    }


def extract_tool(manifest: dict[str, Any]) -> str | None:
    """
    Extract the software/application that generated the C2PA claim.

    This is intentionally separate from the AI model.
    """

    claim_generator = manifest.get("claim_generator")

    if isinstance(claim_generator, str) and claim_generator.strip():
        return claim_generator.strip()

    claim_generator_info = manifest.get("claim_generator_info", [])

    if isinstance(claim_generator_info, list):
        for item in claim_generator_info:
            if not isinstance(item, dict):
                continue

            name = item.get("name")

            if isinstance(name, str) and name.strip():
                version = item.get("version")

                if version:
                    return f"{name.strip()} {version}"

                return name.strip()

    return None


def extract_issuer(manifest: dict[str, Any]) -> str | None:
    """
    Extract the signer/issuer from the C2PA signature information.
    """

    signature_info = manifest.get("signature_info", {})

    if not isinstance(signature_info, dict):
        return None

    issuer = signature_info.get("issuer")

    if isinstance(issuer, str) and issuer.strip():
        return issuer.strip()

    return None


def extract_actions(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract C2PA creation/edit/transformation actions.

    Examples may include:
    - c2pa.created
    - c2pa.opened
    - editing operations
    - resizing/cropping/filtering operations
    """

    actions: list[dict[str, Any]] = []

    for assertion in manifest.get("assertions", []):
        if not isinstance(assertion, dict):
            continue

        label = assertion.get("label")

        if label not in ACTIONS_ASSERTION_LABELS:
            continue

        data = assertion.get("data", {})

        if not isinstance(data, dict):
            continue

        assertion_actions = data.get("actions", [])

        if isinstance(assertion_actions, list):
            for action in assertion_actions:
                if isinstance(action, dict):
                    actions.append(action)

    return actions


def extract_ingredients(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract source/parent assets used to create the current asset.

    Ingredients are important for ModelLedger because they allow
    provenance to be represented as a chain rather than a single event.
    """

    ingredients = manifest.get("ingredients", [])

    if not isinstance(ingredients, list):
        return []

    return [
        ingredient
        for ingredient in ingredients
        if isinstance(ingredient, dict)
    ]


def _safe_validation_results(reader: Any) -> list[dict[str, Any]]:
    """
    Get detailed SDK validation results without making verification
    fail if the installed SDK version does not expose the method.
    """

    try:
        results = reader.get_validation_results()

        if results is None:
            return []

        if isinstance(results, list):
            return [
                result
                for result in results
                if isinstance(result, dict)
            ]

        return []

    except (AttributeError, TypeError):
        return []


def _error_result(
    validation_state: str,
    error: str,
) -> dict[str, Any]:
    """
    Return a consistent result shape for all failure cases.
    """

    return {
        "c2pa_found": False,
        "validation_state": validation_state,
        "validation_results": [],
        "model": None,
        "model_identifier": None,
        "model_type": None,
        "tool": None,
        "issuer": None,
        "actions": [],
        "ingredients": [],
        "has_provenance_chain": False,
        "manifest": {},
        "error": error,
    }