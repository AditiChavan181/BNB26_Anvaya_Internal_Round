from __future__ import annotations

from typing import Any

from .c2pa_service import verify_c2pa


TRUSTED = "TRUSTED"
SELF_ASSERTED = "SELF_ASSERTED"
UNVERIFIABLE = "UNVERIFIABLE"
INCONSISTENT = "INCONSISTENT"


def determine_trust(c2pa_result: dict[str, Any]) -> str:
    """
    Classify provenance based on cryptographic C2PA validation.

    TRUSTED:
        C2PA provenance exists and the SDK reports it as valid/trusted.

    INCONSISTENT:
        C2PA provenance exists, but validation reports a problem.

    UNVERIFIABLE:
        No usable C2PA provenance exists.

    SELF_ASSERTED:
        Reserved for future integration with user/system claims that
        are not backed by trusted C2PA evidence.
    """

    if not c2pa_result.get("c2pa_found"):
        return UNVERIFIABLE

    validation_state = str(
        c2pa_result.get("validation_state", "")
    ).lower()

    if _is_trusted_validation(validation_state):
        return TRUSTED

    if _is_invalid_validation(validation_state):
        return INCONSISTENT

    return UNVERIFIABLE


def analyze_provenance(file_path: str) -> dict[str, Any]:
    """
    Main ModelLedger provenance analysis entry point.

    The backend/API layer can call this function with a local asset path
    and directly return the resulting dictionary to the frontend.
    """

    c2pa_result = verify_c2pa(file_path)

    trust_status = determine_trust(c2pa_result)

    return {
        "status": trust_status,

        # AI model information
        "model": c2pa_result.get("model"),
        "model_identifier": c2pa_result.get(
            "model_identifier"
        ),
        "model_type": c2pa_result.get(
            "model_type"
        ),

        # Generator/application information
        "tool": c2pa_result.get("tool"),

        # Cryptographic signer
        "issuer": c2pa_result.get("issuer"),

        # Validation
        "c2pa_found": c2pa_result.get(
            "c2pa_found",
            False,
        ),
        "validation_state": c2pa_result.get(
            "validation_state"
        ),
        "validation_results": c2pa_result.get(
            "validation_results",
            [],
        ),

        # Provenance history
        "actions": c2pa_result.get(
            "actions",
            [],
        ),
        "ingredients": c2pa_result.get(
            "ingredients",
            [],
        ),
        "has_provenance_chain": c2pa_result.get(
            "has_provenance_chain",
            False,
        ),

        # Error information
        "error": c2pa_result.get("error"),
    }


def _is_trusted_validation(validation_state: str) -> bool:
    """
    Recognize successful validation states while avoiding overly broad
    substring matching.
    """

    trusted_states = {
        "valid",
        "trusted",
        "validmanifest",
        "trustedmanifest",
        "validasset",
        "trustedasset",
    }

    normalized = (
        validation_state
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
    )

    return normalized in trusted_states


def _is_invalid_validation(validation_state: str) -> bool:
    """
    Detect validation states that indicate a provenance inconsistency
    rather than simply missing provenance.
    """

    invalid_terms = (
        "invalid",
        "tamper",
        "mismatch",
        "untrusted",
        "error",
        "failure",
    )

    return any(
        term in validation_state
        for term in invalid_terms
    )