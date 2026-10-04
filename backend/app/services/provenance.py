from __future__ import annotations

import hashlib
import json
from typing import Any

from .c2pa_service import verify_c2pa
from .issuer_registry import is_trusted_issuer

TRUSTED = "TRUSTED"
SELF_ASSERTED = "SELF_ASSERTED"
UNVERIFIABLE = "UNVERIFIABLE"
INCONSISTENT = "INCONSISTENT"
TAMPERED = "TAMPERED"


def compute_provenance_hash(provenance_data: Any) -> str:
    canonical = json.dumps(
        provenance_data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def determine_trust(c2pa_result: dict[str, Any]) -> str:
    if not c2pa_result.get("c2pa_found"):
        return UNVERIFIABLE

    validation_state = str(
        c2pa_result.get("validation_state", "")
    ).lower()

    validation_results = c2pa_result.get("validation_results", [])

    if _has_failure(validation_state, validation_results):
        return TAMPERED

    if _has_valid_signature(validation_state, validation_results):
        if _has_trusted_issuer(c2pa_result):
            return TRUSTED
        return SELF_ASSERTED

    if c2pa_result.get("model") or c2pa_result.get("issuer") or c2pa_result.get("tool"):
        return SELF_ASSERTED

    return UNVERIFIABLE


def analyze_provenance(file_path: str) -> dict[str, Any]:
    c2pa_result = verify_c2pa(file_path)
    trust_status = determine_trust(c2pa_result)

    signature_valid = _has_valid_signature(
        str(c2pa_result.get("validation_state", "")).lower(),
        c2pa_result.get("validation_results", []),
    )
    issuer_trusted = _has_trusted_issuer(c2pa_result)

    return {
        "status": trust_status,
        "model": c2pa_result.get("model"),
        "model_identifier": c2pa_result.get("model_identifier"),
        "model_type": c2pa_result.get("model_type"),
        "tool": c2pa_result.get("tool"),
        "issuer": c2pa_result.get("issuer"),
        "c2pa_found": c2pa_result.get("c2pa_found", False),
        "validation_state": c2pa_result.get("validation_state"),
        "validation_results": c2pa_result.get("validation_results", []),
        "actions": c2pa_result.get("actions", []),
        "ingredients": c2pa_result.get("ingredients", []),
        "has_provenance_chain": c2pa_result.get("has_provenance_chain", False),
        "error": c2pa_result.get("error"),
        "verification": {
            "signature_valid": signature_valid,
            "content_binding_valid": signature_valid,
            "issuer_trusted": issuer_trusted,
            "blockchain_match": False,
        },
    }


def _has_valid_signature(
    validation_state: str,
    validation_results: Any,
) -> bool:
    if validation_state in {"invalid", "error", "failure"}:
        return False

    if not isinstance(validation_results, dict):
        return False

    active_manifest = validation_results.get("activeManifest", {})
    if not isinstance(active_manifest, dict):
        return False

    success = active_manifest.get("success", [])
    success_codes = {
        item.get("code")
        for item in success
        if isinstance(item, dict)
    }

    return (
        "claimSignature.validated" in success_codes
        and "assertion.dataHash.match" in success_codes
    )


def _has_failure(
    validation_state: str,
    validation_results: Any,
) -> bool:
    if any(
        term in validation_state
        for term in ("invalid", "tamper", "mismatch", "failure", "error")
    ):
        return True

    if not isinstance(validation_results, dict):
        return False

    active_manifest = validation_results.get("activeManifest", {})
    if not isinstance(active_manifest, dict):
        return False

    failures = active_manifest.get("failure", [])
    if not isinstance(failures, list):
        return False

    for item in failures:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code", "")).lower()
        if code in {"signingcredential.untrusted", "timestamp.untrusted"}:
            continue
        if "untrusted" in code:
            continue
        return True

    return False


def _has_trusted_issuer(c2pa_result: dict[str, Any]) -> bool:
    issuer_name = c2pa_result.get("issuer")
    return bool(issuer_name and is_trusted_issuer(issuer_name=issuer_name))