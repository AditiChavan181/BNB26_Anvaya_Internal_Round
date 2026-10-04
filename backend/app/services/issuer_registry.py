from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


# --------------------------------------------------
# Trusted issuer registry
# --------------------------------------------------
#
# IMPORTANT:
# The model name is NOT what makes an issuer trusted.
#
# We trust an issuer only when its signing certificate
# matches a certificate fingerprint that we have
# explicitly registered.
#
# The local C2PA demo certificate is treated as a testing
# credential, not as a Google/Gemini official issuer.
# --------------------------------------------------

TRUSTED_ISSUERS: dict[str, dict[str, Any]] = {}


def calculate_certificate_fingerprint(
    certificate_path: str,
) -> str:
    """Calculate the SHA-256 fingerprint for a PEM certificate blob."""

    path = Path(certificate_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Certificate not found: {certificate_path}"
        )

    certificate_data = path.read_bytes()
    return hashlib.sha256(certificate_data).hexdigest()


def _canonical_name(name: str | None) -> str:
    return (name or "").strip().casefold()


def register_trusted_issuer(
    name: str,
    certificate_path: str,
    organization: str,
) -> str:
    """Register a certificate as a trusted issuer and return its fingerprint."""

    fingerprint = calculate_certificate_fingerprint(certificate_path)

    TRUSTED_ISSUERS[fingerprint] = {
        "name": name,
        "organization": organization,
        "certificate_path": certificate_path,
    }

    return fingerprint


def is_trusted_issuer(
    certificate_fingerprint: str | None = None,
    issuer_name: str | None = None,
) -> bool:
    """Check whether a certificate fingerprint or issuer name matches a trusted registry entry."""

    if certificate_fingerprint:
        return certificate_fingerprint in TRUSTED_ISSUERS

    if not issuer_name:
        return False

    issuer_key = _canonical_name(issuer_name)
    for trusted in TRUSTED_ISSUERS.values():
        if _canonical_name(trusted.get("name")) == issuer_key:
            return True
        if _canonical_name(trusted.get("organization")) == issuer_key:
            return True

    return False


def get_issuer(
    certificate_fingerprint: str,
) -> dict[str, Any] | None:
    """Return trusted issuer information for a fingerprint."""

    return TRUSTED_ISSUERS.get(certificate_fingerprint)


