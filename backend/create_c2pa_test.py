import json
from pathlib import Path

import c2pa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend


BASE_DIR = Path(__file__).resolve().parent.parent

SOURCE_IMAGE = (
    BASE_DIR
    / "sample-assets"
    / "unknown"
    / "test.jpg"
)

OUTPUT_IMAGE = (
    BASE_DIR
    / "sample-assets"
    / "trusted"
    / "signed.jpg"
)

CERT_FILE = (
    BASE_DIR
    / "backend"
    / "certs"
    / "es256_certs.pem"
)

KEY_FILE = (
    BASE_DIR
    / "backend"
    / "certs"
    / "es256_private.key"
)


# --------------------------------
# Load certificate chain
# --------------------------------

with open(CERT_FILE, "rb") as f:
    certs = f.read()


# --------------------------------
# Load private key
# --------------------------------

with open(KEY_FILE, "rb") as f:
    private_key = f.read()


# --------------------------------
# C2PA signing function
# --------------------------------

def sign_data(data: bytes) -> bytes:
    """
    Sign C2PA data using ES256.
    """

    key = serialization.load_pem_private_key(
        private_key,
        password=None,
        backend=default_backend(),
    )

    return key.sign(
        data,
        ec.ECDSA(hashes.SHA256()),
    )


# --------------------------------
# C2PA manifest
# --------------------------------

manifest = {
    "claim_generator_info": [
        {
            "name": "ModelLedger Test Generator",
            "version": "1.0.0",
        }
    ],

    "format": "image/jpeg",

    "title": "ModelLedger Gemini Test Image",

    "assertions": [

        # ----------------------------
        # Normal C2PA creation action
        # ----------------------------

        {
            "label": "c2pa.actions",
            "data": {
                "actions": [
                    {
                        "action": "c2pa.created",

                        "softwareAgent": {
                            "name": "ModelLedger Test Generator",
                            "version": "1.0.0",
                        },

                        "digitalSourceType": (
                            "http://cv.iptc.org/"
                            "newscodes/digitalsourcetype/"
                            "digitalCreation"
                        ),
                    }
                ]
            },
        },

        # ----------------------------
        # AI model disclosure
        # ----------------------------

        {
            "label": "c2pa.ai-disclosure",
            "data": {
                "modelName": "Gemini",
                "modelIdentifier": "gemini",
                "modelType": "generative-ai",
            },
        },
    ],
}


# --------------------------------
# Create output directory
# --------------------------------

OUTPUT_IMAGE.parent.mkdir(
    parents=True,
    exist_ok=True,
)


print("C2PA version:", c2pa.sdk_version())
print("Source:", SOURCE_IMAGE)
print("Output:", OUTPUT_IMAGE)


# --------------------------------
# Create signed C2PA asset
# --------------------------------

with c2pa.Context() as context:

    with c2pa.Signer.from_callback(
        sign_data,
        c2pa.C2paSigningAlg.ES256,
        certs.decode("utf-8"),
        "http://timestamp.digicert.com",
    ) as signer:

        with c2pa.Builder(
            json.dumps(manifest),
            context,
        ) as builder:

            builder.sign_file(
                str(SOURCE_IMAGE),
                str(OUTPUT_IMAGE),
                signer,
            )


print()
print("SUCCESS!")
print("C2PA signed image created:")
print(OUTPUT_IMAGE)