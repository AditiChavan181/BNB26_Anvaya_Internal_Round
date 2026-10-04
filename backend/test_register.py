import hashlib
import json

from app.services.provenance import analyze_provenance
from app.services.hash_service import calculate_sha256
from app.services.blockchain_service import (
    register_artifact,
    verify_artifact,
    get_artifact,
)


FILE_PATH = "../sample-assets/trusted/signed.jpg"


# --------------------------------
# 1. Analyze C2PA provenance
# --------------------------------

provenance = analyze_provenance(FILE_PATH)

print("\nPROVENANCE")
print(provenance)


# --------------------------------
# 2. Calculate file SHA-256
# --------------------------------

sha256_hex = calculate_sha256(FILE_PATH)

print("\nFILE SHA-256")
print(sha256_hex)


# --------------------------------
# 3. Create provenance hash
# --------------------------------

provenance_json = json.dumps(
    provenance,
    sort_keys=True,
    separators=(",", ":"),
    default=str,
)

provenance_hash_hex = hashlib.sha256(
    provenance_json.encode("utf-8")
).hexdigest()

print("\nPROVENANCE SHA-256")
print(provenance_hash_hex)


# --------------------------------
# 4. Convert hashes to bytes32
# --------------------------------

artifact_hash = bytes.fromhex(sha256_hex)
provenance_hash = bytes.fromhex(provenance_hash_hex)

artifact_id = hashlib.sha256(
    sha256_hex.encode("utf-8")
).digest()

parent_id = bytes(32)


# --------------------------------
# 5. Check if artifact already exists
# --------------------------------

existing_artifact = get_artifact(artifact_id)


# --------------------------------
# 6. Register on blockchain
# --------------------------------

if existing_artifact["exists"]:

    print("\nBLOCKCHAIN REGISTRATION")
    print("Artifact already registered.")
    print("Skipping registration transaction.")

else:

    result = register_artifact(
        artifact_id=artifact_id,
        artifact_hash=artifact_hash,
        provenance_hash=provenance_hash,
        model=provenance.get("model") or "Unknown",
        issuer=provenance.get("issuer") or "Unknown",
        parent_id=parent_id,
    )

    print("\nBLOCKCHAIN REGISTRATION")
    print(result)


# --------------------------------
# 7. Verify artifact from blockchain
# --------------------------------

verified = verify_artifact(
    artifact_id,
    artifact_hash,
    provenance_hash,
)

print("\nBLOCKCHAIN VERIFICATION")
print("Verified:", verified)


# --------------------------------
# 8. Read artifact from blockchain
# --------------------------------

blockchain_artifact = get_artifact(artifact_id)

print("\nBLOCKCHAIN ARTIFACT")
print(blockchain_artifact)